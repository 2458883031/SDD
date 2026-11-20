# ADR-005：任务上下文与产物管理

**状态：** 已采纳  
**日期：** 2026-11-20

## 背景

多个 Skill 协作完成一个任务时，需要统一的方式传递上下文和共享产物。

## 问题

如何解决：
- 每个 Skill 重复理解需求？
- 产物散落各处难以追踪？
- 上下文丢失导致后续步骤出错？

## 候选方案

### 方案 A：全局变量

使用全局变量存储上下文。

**优点：** 访问简单  
**缺点：** 状态混乱，难以追踪，并发不安全

### 方案 B：文件系统统一存储（选定）

通过 `artifacts/` 目录统一管理所有产物和上下文。

**优点：**
- 持久化，可追溯
- 独立于执行环境
- 易于版本控制
- 支持并行访问

**缺点：**
- 需要约定目录结构
- 大文件可能影响性能

### 方案 C：内存对象传递

通过函数参数传递上下文对象。

**优点：** 类型安全  
**缺点：** 跨 Skill 传递复杂，持久化困难

## 决策

采用**方案 B：文件系统统一存储**，并定义以下权威模型。本 ADR 是 Task Context 与 Artifact 语义的唯一定义来源；其他文档引用本 ADR，不重复定义。

### 1. Task Context

Task Context 是任务执行期间的统一上下文，至少包含：

| 字段 | 说明 |
|------|------|
| `task-id` | 任务唯一标识，格式 `task-YYYYMMDD-<short-uuid>` |
| `parent-task-id` | 可选；重试实例或派生任务指向原任务 |
| `project-root` | 项目根目录（规范化绝对路径） |
| `task-type` | 任务类型（与 orchestration-architecture.md 一致） |
| `complexity` | L1 / L2 / L3 |
| `task-status` | 任务状态（见状态机） |
| `current-stage` | 当前 Workflow 节点 ID |
| `user-preferences` | 任务范围内生效的用户偏好（快照或引用） |
| `platform-config` | **平台配置引用**（adapter id / config ref），不是平台配置内容 |
| `task-constraints` | 安全、环境、时间、审批等约束 |
| `artifact-references` | Artifact 引用列表：`{id, path, version, sha256, required}` |

**创建与维护：**

- 由 Orchestration Engine 在任务入口创建 `task-id`。
- 无编排引擎时，由执行的 Agent 创建，并记录 `created_by`（Agent/Skill/用户）。
- Orchestration Engine（或 ArtifactManager）维护 `task-status` 与 `current-stage`。
- 其他 Agent 只能读取 Task Context，不得修改状态字段。

**状态机：**

**正常流程（无需审批）：**

```text
created
  ↓
planned
  ↓
executing
  │  （无需审批且节点完成）
  ↓
verifying
  ↓
completed
```

**审批流程：**

```text
executing
  ↓
awaiting_approval
  ├── approved → executing（恢复原 current-stage）
  ├── rejected → aborted
  └── timeout  → aborted（原因 approval_timeout）
```

**异常流程：**

```text
executing / verifying
  ├── failed   （执行已发生但不可恢复）
  └── aborted  （主动终止/审批拒绝/审批超时/策略停止）
```

**状态转换表：**

| From | To | 条件 | 说明 |
|------|----|------|------|
| created | planned | Task Context 初始化完成 | 尚未开始执行 |
| planned | executing | Workflow 开始 | 进入当前节点 |
| executing | verifying | 无需审批且节点完成 | 允许直接进入验证 |
| executing | awaiting_approval | 触发审批条件（G 门禁/SA） | 暂停并保存 current-stage |
| awaiting_approval | executing | 显式批准 | 恢复原 current-stage，不丢上下文 |
| awaiting_approval | aborted | 显式拒绝 | 记录拒绝原因与审批记录 |
| awaiting_approval | aborted | 审批超时 | 原因 `approval_timeout`；超时不等于批准 |
| executing | failed | 不可恢复执行错误 | 保留产物与错误详情 |
| verifying | failed | 验证不可恢复失败 | 保留产物与错误详情 |
| executing / verifying | aborted | 用户取消或策略终止 | 记录终止原因 |
| verifying | completed | 验证通过 | Task Context 冻结 |

**规则：**

1. 不需要审批的任务允许直接从 `executing` 进入 `verifying`；只有触发审批条件的任务才能进入 `awaiting_approval`。
2. 审批通过后恢复**原 current-stage**，不得丢失 Task Context、Artifact 引用或审批记录。
3. 审批拒绝的终止语义为 `aborted`；不可当作 `failed` 或继续执行。
4. 审批超时的处理为 `aborted`（`approval_timeout`）；超时不得视为批准，也不得自动放行。
5. `failed` 表示执行已尝试但不可恢复；`aborted` 表示主动终止、拒绝或策略停止。两者都必须保留原因和产物。
6. 重试必须保留原任务与 Artifact 历史；重试在**新的 task-id** 下进行，并通过 `parent-task-id` 指向原任务（或作为明确的 retry 实例）。
7. `completed` / `failed` / `aborted` 为终止状态，**禁止从终止状态直接恢复执行**；如需重新执行，创建新任务或新重试实例。
8. Workflow 的节点状态（如 `awaiting_approval`）与 Task Context 的 `task-status` 同名但作用域不同：节点状态描述单个节点，`task-status` 描述整个任务；两者必须同步记录。

### 2. Artifact

Artifact 是任务过程中产生的文件或结果。每个 Artifact 至少记录：

| 字段 | 说明 |
|------|------|
| `artifact-id` | Artifact 唯一标识 |
| `path` | 相对 `project-root` 的路径，必须在 `artifacts/{task-id}/` 内 |
| `type` | requirements / analysis / design / plan / implementation / review / test / deployment / report |
| `stage` | 产生它的 Workflow 节点 |
| `created_by` | Agent / Skill / 用户标识 |
| `created_at` | 时间戳 |
| `source` | 输入引用（artifact-id + version + sha256） |
| `version` | 整数，从 1 开始 |
| `sha256` | 内容哈希 |
| `status` | draft / approved / superseded |
| `references` | 该产物引用的其他 Artifact |

**归属：**

- 产物归创建它的阶段/Agent 所有，但属于任务（task-id）。
- 其他 Agent 默认只读；需要写入时按权限模型申请。
- `approved` 或任务 `completed` 后的产物不可原地修改，只能生成新版本。

### 3. 目录规划

```text
artifacts/
└── {task-id}/
    ├── context.json
    ├── metadata.json
    ├── requirements/
    ├── analysis/
    ├── design/
    ├── implementation/
    ├── testing/
    ├── review/
    ├── reports/
    └── logs/
```

> P0 仅定义规划，不创建实际目录和文件。

### 4. 写入权限与并发

1. **单写者**：同一 Artifact 路径同一时间只允许一个写者；并行节点写入不同目录。
2. **锁/租约**：写入前获取任务级或路径级锁；租约过期可回收，但必须记录。
3. **原子写入**：临时文件 + 重命名；避免部分写入。
4. **禁止静默覆盖**：冲突时生成新 `version`，旧版本标记 `superseded`，记录冲突原因。
5. **只读共享**：其他 Agent 通过 `artifact-references` 读取；不得写入他人产物目录。
6. **写入边界**：每任务只能写 `artifacts/{task-id}/` 和工作区允许路径，符合 security-architecture.md 的文件边界。

### 5. 版本、来源与归档

- 版本递增，`source` 记录输入引用；`sha256` 用于完整性校验。
- 读取方必须校验 `sha256`；不得隐式使用「最新版本」。
- 任务完成后产物冻结；按保留策略归档（建议保留 90 天以上，可配置）。
- 归档后只读；删除需要显式审批，不得由 Agent 自动执行。

### 6. 上下文隔离与跨 Agent 引用

- 不同任务使用不同 `task-id` 命名空间，默认不可互相读写。
- 跨任务引用必须显式登记到 `artifact-references`（路径 + 版本 + hash），不得遍历其他任务目录。
- `platform-config` 只保存引用，不复制平台配置；核心 Skill 不得读取平台专属字段。
- 凭证不得写入 Task Context 或 Artifact；只传递凭证引用，由有权限的适配器解析。

## 理由

1. **可追溯性** — 每个产物的创建时间、来源可查
2. **独立性** — Skill 间通过文件解耦
3. **调试友好** — 可检查中间产物定位问题
4. **复用性** — 相同输入产生相同输出

## 注意事项

1. **原子写入** — 使用临时文件 + 重命名避免部分写入。
2. **冲突检测** — 禁止静默覆盖；冲突时生成新版本并标记 `superseded`。
3. **清理/归档** — 已完成任务冻结并按保留策略归档；删除需显式审批。
4. **契约** — 每个 Skill 仍需定义 Input Contract、Output Contract、Prerequisite；产物路径与版本遵循本 ADR。
5. **实现状态** — P0 只有设计；ArtifactManager、锁、版本索引和归档机制尚未实现（P2）。

## 后续影响

- P2 阶段实现 ArtifactManager
- 需定义 `context.json` / `metadata.json` 的 Schema
- 各 Skill 需遵守产物契约
- 安全架构需实现文件边界、写入隔离和只读共享

## 修订记录

- **2026-11-20（P0-002）**：补充 Task Context 字段与状态机、Artifact 归属/版本/来源、写入权限与并发、跨任务隔离与归档；明确 `platform-config` 只是引用，不混入平台配置；与安全架构的只读共享和写入隔离对齐。
- **2026-11-20（P0-003）**：补全正常/审批/异常状态机；明确审批通过恢复原 current-stage、拒绝/超时终止、failed 与 aborted 区别、终止状态不可恢复、重试实例与新 `task-id`；新增 `parent-task-id`。
