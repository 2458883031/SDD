# SDD Task 标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** Task 数据模型、状态、依赖、调度、超时、重试、取消、恢复和幂等
**权威关系：** Task Context / Artifact 的持久化语义见 [ADR-005](../decisions/ADR-005-task-context.md)；状态转换的完整表见 [orchestration-state-machine.md](./orchestration-state-machine.md)；Workflow 定义见 [workflow-standard.md](./workflow-standard.md)。

---

## 1. Task 的定义

**Task 是可调度、可追踪的最小执行单元。** 一个 Workflow 节点在运行时产生一个或多个 Task；Task 引用 Skill/Tool/Subworkflow，并由 Orchestrator 调度。

Task **不是**：

- Skill 本身；
- Workflow；
- Agent；
- Artifact；
- 平台会话。

---

## 2. Task 数据模型

### 2.1 字段集合

| 字段 | 必需 | 类型 | 必要性 |
|------|------|------|--------|
| `schema_version` | 是 | integer | 模型版本；当前为 1 |
| `task_id` | 是 | string | 全局唯一；格式 `task-YYYYMMDD-<short-id>` |
| `parent_task_id` | 否 | string/null | 重试/派生任务指向原任务（ADR-005） |
| `run_id` | 是 | string | 所属 Workflow Run |
| `workflow_id` | 是 | string | 来源 Workflow |
| `workflow_version` | 是 | string | 固定 Workflow 版本 |
| `node_id` | 是 | string | 对应 Workflow 节点 |
| `task_type` | 是 | enum | 任务分类标准中的 9 类 |
| `status` | 是 | enum | 执行状态：PENDING/READY/RUNNING/WAITING/BLOCKED/SUCCEEDED/FAILED/CANCELLED |
| `context_status` | 是 | enum | ADR-005 `task-status` 投影 |
| `complexity` | 是 | enum | L1/L2/L3 |
| `risk_level` | 是 | enum | low/medium/high/critical |
| `permission_level` | 是 | enum | R0/R1/R2/R3/R4 |
| `inputs` | 是 | array | Artifact 引用：path/version/sha256/type |
| `outputs` | 是 | array | Artifact 引用；SUCCEEDED 时必须有有效输出 |
| `dependencies` | 是 | array[string] | 前置 Task ID；必须全部 SUCCEEDED |
| `assigned_agent` | 否 | object | `{id, role}`；执行主体 |
| `assigned_skill` | 否 | object | `{name, version}`；Skill 任务必需 |
| `retry_policy` | 是 | object | 最大次数、退避、可重试错误 |
| `timeout_policy` | 是 | object | 超时时间与超时动作 |
| `approval_requirement` | 否 | object | 需要的 G/SA、绑定范围 |
| `evidence_refs` | 是 | array[string] | 证据 ID/引用 |
| `idempotency_key` | 是 | string | 防重复调度/执行 |
| `subject_hash` | 否 | string | commit/产物 hash；G4/G5 绑定用 |
| `attempt` | 是 | integer | 当前尝试次数，从 1 开始 |
| `lease` | 否 | object | `{owner, expires_at}`；防并发执行 |
| `error` | 否 | object | 失败码、消息、可重试性、详情 |
| `created_at` | 是 | date-time | 创建时间 |
| `started_at` | 否 | date-time/null | 开始执行时间 |
| `completed_at` | 否 | date-time/null | 终态时间 |
| `metadata` | 否 | object | 非语义扩展；不得绕过权限/Gate |

> 字段必要性：`task_id`/`run_id`/`workflow_id`/`node_id` 用于定位与审计；`status`/`context_status` 分离调度状态与 ADR-005 生命周期；`inputs`/`outputs`/`dependencies` 保证可重放；`retry_policy`/`timeout_policy`/`idempotency_key` 保证失败恢复可控；`evidence_refs` 保证可追溯。

### 2.2 Task Context 字段

Task Context 仍按 ADR-005 保存：

- `task-id`、`parent-task-id`、`project-root`；
- `task-type`、`complexity`、`task-status`、`current-stage`；
- `user-preferences`、`platform-config`（引用）、`task-constraints`；
- `artifact-references`（path/version/sha256/required）。

Task 模型中的 `status` 是执行状态，不得覆盖 ADR-005 的 `task-status`；`context_status` 必须与 ADR-005 同步。

---

## 3. Task 状态语义

| 状态 | 含义 | 是否可自动恢复 | ADR-005 投影 |
|------|------|----------------|--------------|
| `PENDING` | 已创建，依赖/计划尚未满足 | 是（条件满足后） | `created` / `planned` |
| `READY` | 依赖满足，可调度 | 是 | `planned` |
| `RUNNING` | 已分配并执行 | 否（需完成/失败/阻塞） | `executing` |
| `WAITING` | 等待依赖、容量、退避或可恢复条件 | 是 | `executing` |
| `BLOCKED` | 等待审批、权限、能力或人工决策 | 需外部动作 | `awaiting_approval`（审批）或保持 `executing` + blocked 记录 |
| `SUCCEEDED` | 输出有效、证据完整 | 否（终态） | `completed` |
| `FAILED` | 不可恢复失败或重试耗尽 | 否（终态） | `failed` |
| `CANCELLED` | 用户/策略取消或审批拒绝 | 否（终态） | `aborted` |

- 终态：`SUCCEEDED` / `FAILED` / `CANCELLED`，不可直接恢复；重试需新 Task（`parent_task_id`）。
- `WAITING` 与 `BLOCKED` 的区别：前者可自动恢复，后者需要外部动作（审批/权限/能力/人工）。
- 状态转换的完整合法性由 [orchestration-state-machine.md](./orchestration-state-machine.md) 和 `schemas/orchestration/task-state-machine.json` 定义。

---

## 4. Task 创建与分配

### 4.1 创建

1. Orchestrator 根据 Workflow 节点和当前上下文创建 Task。
2. `task_id` 全局唯一；建议 `task-YYYYMMDD-<short-id>`。
3. `idempotency_key` 必须由 `run_id + node_id + subject_hash + attempt_scope` 等稳定输入生成；同一键不得并发创建两个执行实例。
4. 创建时写入 `context_status`、输入引用、依赖、权限需求、超时/重试策略和证据要求。
5. 创建事件写入 Evidence/事件流。

### 4.2 分配

1. 只有 `READY` Task 可分配。
2. 按 Skill 名称/版本、Agent 能力、权限子集、平台能力匹配。
3. 默认最小权限；不得分配超出 Task 声明的权限。
4. 每个 Task 只有一个主执行 Agent/Skill；协作者只读或写独立产物。
5. 分配必须获取租约（lease），防止重复执行。
6. 无可用 Agent/Skill/能力 → `BLOCKED`，不得降级为更高权限或非声明工具。

### 4.3 队列与优先级

- 优先级考虑：关键路径、风险等级、依赖阻塞、公平性。
- 同优先级按创建时间/确定性排序，避免饥饿。
- 并发上限默认 5（P0 建议）；单 Skill 并发 ≤2。
- 队列状态变化必须记录事件。

---

## 5. 依赖与调度

1. `dependencies` 必须引用同一 Workflow Run 内的 Task；不得跨 Run 隐式依赖。
2. 依赖必须全部 `SUCCEEDED` 才能进入 `READY`。
3. 任一依赖 `FAILED`/`CANCELLED` → 下游 `BLOCKED` 或 `FAILED`（按 Workflow 失败策略）；不得提前执行。
4. 依赖图必须无环；循环依赖直接拒绝创建/调度。
5. 并行任务必须写入不同 Artifact 路径；共享输入只读。
6. 调度器不得重复调度同一 `task_id`；租约未过期时不得再次分配。
7. 未满足依赖、权限、能力或审批时不得执行。

---

## 6. 执行与完成

### 6.1 执行前检查

- 输入符合 Skill/Tool 契约；
- 依赖全部成功；
- 权限已授予且在有效期内；
- 审批（如有）已通过且绑定当前操作/产物；
- 平台能力可用；
- 租约有效；
- Artifact hash 与引用一致。

### 6.2 执行

- 通过 ToolPort 调用 Tool；不得直接调用平台 SDK/CLI。
- Skill 返回统一输出信封；Orchestrator 校验 `status`/`data`/`artifacts`/`errors`/`evidence`。
- `needs_input`/`needs_approval`/`blocked`/`failed` 按对应状态处理；不得当作成功。
- 输出写入遵循 ADR-005：单写者、原子写入、版本/hash。

### 6.3 完成判定

Task 进入 `SUCCEEDED` 必须同时满足：

1. 进程/调用正常结束；
2. 输出符合契约；
3. 必需的 Artifact 已写入且 hash 可校验；
4. 必需证据已记录；
5. 关联 Gate（如有）已通过或明确 N/A；
6. 没有未处理的错误/阻塞。

**仅凭“执行结束”不得标记 SUCCEEDED。**

---

## 7. 超时

- 每个 Task 必须有 `timeout_policy`：`timeout_seconds`、`on_timeout`（`fail`/`block`/`cancel`）、清理动作。
- 超时按失败处理；不得把超时当作成功或批准。
- 超时后必须：
  - 停止/取消执行；
  - 释放租约；
  - 记录 `timeout` 错误和证据；
  - 按策略重试（仅当可重试且幂等）或失败。
- 长任务应支持心跳/检查点；心跳丢失按 Agent 不可用处理。

---

## 8. 失败与重试

### 8.1 错误分类

| 类别 | 例子 | 处理 |
|------|------|------|
| `retryable` | 临时网络错误、可恢复工具错误、Agent 暂时不可用 | 按策略重试 |
| `non_retryable` | 输入非法、权限拒绝、契约不匹配、逻辑错误 | 不自动重试；失败/回退 |
| `needs_human` | 审批拒绝、需求歧义、安全风险 | BLOCKED/人工介入 |
| `needs_replan` | 依赖失败、复杂度变化、方案不可行 | 回退到规划/分析 |
| `terminal` | 不可逆操作失败、数据损坏、策略终止 | 终止 Workflow |

### 8.2 重试策略

- 默认 `max_attempts=3`，指数退避 + jitter；可配置上限。
- 只重试 `retryable` 错误；重试必须有预算，不得无限重试。
- 重试必须使用同一 `idempotency_key` 防止重复副作用；非幂等操作必须先补偿或转为人工。
- **不可逆操作不得自动重试**：生产数据破坏、不可逆部署、敏感凭证操作等。
- 重试耗尽 → `FAILED`；不得静默降级或跳过。
- 跨终态恢复 → 新 Task（`parent_task_id`），不得修改原 Task 历史。

### 8.3 重复请求与幂等

- 同一 `idempotency_key` 的重复请求必须去重或返回已有结果。
- 并发相同键 → 只允许一个执行实例；其他返回 `duplicate` 或等待。
- 重放必须验证输入/产物 hash；hash 变化视为新请求。
- 外部副作用必须使用幂等键或补偿机制。

---

## 9. 取消

1. 用户/策略可请求取消；Orchestrator 传播到所有运行中 Task。
2. 取消是终态 `CANCELLED`；不得继续执行或恢复。
3. 取消时：
   - 停止新调度；
   - 向运行中任务发送取消；
   - 保留已完成产物和证据；
   - 对有副作用操作执行补偿/回滚（适用时）；
   - 记录取消原因、发起者、时间。
4. 审批拒绝按 `CANCELLED` 处理（ADR-005 `aborted`），不得当作 `FAILED` 继续。

---

## 10. 恢复

允许恢复：

- `WAITING`：条件满足后回 `READY`；
- `BLOCKED`：审批/权限/能力恢复后回 `READY`；
- 执行中断但有检查点且租约过期：重新分配，验证幂等。

恢复前必须：

1. 校验 Task Context 完整性；
2. 校验 Artifact 路径/版本/hash；
3. 校验 Gate subject hash 与当前代码/产物一致；
4. 校验审批未过期且绑定当前操作；
5. 确认没有重复副作用。

终态 Task 不得恢复；需要重试时创建新 Task 并关联 `parent_task_id`。

---

## 11. 结果覆盖与并发写

1. 同一 Artifact 路径同一时间只允许一个写者。
2. 写入前获取路径级/任务级租约；租约过期可回收并记录。
3. 使用临时文件 + 重命名原子写入。
4. 版本递增；不得静默覆盖已批准/已完成产物。
5. 写入时校验期望版本/hash（compare-and-swap）；不匹配 → 冲突失败。
6. 并行任务写入不同目录；共享产物只读。
7. 任务结果合并不得覆盖其他 Task 的输出；冲突必须显式解决。

---

## 12. 不变量

1. 依赖未满足不得执行。
2. 无有效输出/证据不得 SUCCEEDED。
3. 终态不可直接恢复。
4. 不可逆操作不得自动重试。
5. 同一幂等键不得并发执行。
6. 同一路径不得并发多写。
7. 失败不得标记为成功。
8. 取消后不得继续执行。
9. 审批过期/失效后不得继续使用。
10. Task 执行状态与 ADR-005 `task-status` 必须按映射同步。

---

## 13. 实现状态

| 能力 | 状态 |
|------|------|
| Task 创建/调度/状态机 | 未实现（P2） |
| 重试/超时/取消/恢复 | 未实现（P2） |
| 幂等/租约/并发写控制 | 未实现（P2） |
| Task Schema/静态测试 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 14. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [task-classification-standard.md](./task-classification-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [orchestration-state-machine.md](./orchestration-state-machine.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现 Task Scheduler 或 StateStore。
