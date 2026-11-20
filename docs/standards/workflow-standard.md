# SDD Workflow 标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** Workflow 定义、选择、组合、动态阶段、并行、终止与恢复
**权威关系：** 核心概念见 [system-architecture.md §2](../architecture/system-architecture.md#2-核心概念权威定义)；P0 编排架构见 [orchestration-architecture.md](../architecture/orchestration-architecture.md)；门禁规则见 [ADR-006](../decisions/ADR-006-quality-gates.md)。

---

## 1. 定义与边界

**Workflow 是声明式的研发流程定义**，描述节点、依赖、并行、条件、门禁、审批和失败路径。

Workflow **不是**：

- Skill 的简单集合；
- 运行时引擎；
- 单个 Agent 的提示词；
- 平台专属脚本。

Workflow 由 Orchestrator 解释和执行；节点通过 `depends_on` 组织 DAG；Skill/Tool/Gate 是节点类型。

---

## 2. Workflow 数据模型

### 2.1 顶层字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `schema_version` | 是 | 当前为 1 |
| `id` | 是 | 小写字母/数字/连字符，Workflow 内稳定唯一 |
| `version` | 是 | SemVer 2.0.0 |
| `name` | 是 | 人类可读名称 |
| `description` | 否 | 用途、适用范围 |
| `status` | 是 | `draft/review/tested/published/deprecated/retired/archived` |
| `trigger` | 是 | 任务类型、复杂度、风险、环境匹配条件 |
| `inputs` | 否 | Workflow 级输入契约 |
| `outputs` | 否 | Workflow 级输出契约 |
| `nodes` | 是 | 至少一个节点 |
| `policies` | 否 | 并发、超时、失败策略、证据级别 |
| `metadata` | 否 | 非语义扩展；不得改变门禁/权限 |

### 2.2 节点字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `id` | 是 | Workflow 内唯一；小写字母/数字/下划线/连字符 |
| `type` | 是 | `skill/tool/gate/parallel/check/end/subworkflow/approval` |
| `name` / `description` | 否 | 可读说明 |
| `skill` | 条件 | `type=skill` 时必需；引用 Skill 名称 |
| `tool` | 条件 | `type=tool` 时必需；引用已授权 Tool 类别 |
| `workflow_ref` | 条件 | `type=subworkflow` 时必需；引用已发布 Workflow |
| `gate` / `gates` | 条件 | `type=gate` 时至少一个；G1–G6 |
| `approval` | 否 | `type=approval` 或需要 SA 的节点 |
| `depends_on` | 否 | 前置节点 ID；空表示入口 |
| `inputs` / `outputs` | 否 | Artifact 引用契约（路径/版本/hash） |
| `condition` | 否 | 条件表达式；仅可读取 Task Context/Artifact/显式变量 |
| `parallel_group` | 否 | 并行组标识；同组节点可并行 |
| `join_policy` | 否 | `all` / `any` / `quorum`；默认 `all` |
| `quorum` | 条件 | `join_policy=quorum` 时必需 |
| `retry_policy` | 否 | 最大次数、退避、可重试错误 |
| `timeout_seconds` | 否 | 节点超时；超时按失败处理 |
| `on_success` / `on_failure` | 否 | 下一节点/结束/回退节点 |
| `artifacts` | 否 | 必须产出的 Artifact 清单 |
| `risk_level` | 否 | `low/medium/high/critical` |
| `permissions` | 否 | 节点所需权限类别；不是授权 |
| `idempotency_key` | 否 | 幂等键模板；用于防重复执行 |

### 2.3 节点类型

| 类型 | 作用 | 约束 |
|------|------|------|
| `skill` | 调用一个 Skill | 必须声明 `skill`；输出需符合 Skill IO 契约 |
| `tool` | 直接调用已授权 Tool | 必须声明 `tool`；不得绕过 ToolPort/R0–R4 |
| `gate` | 执行 G1–G6 检查 | 必须声明 `gate`/`gates`；G4/G5 绑定 subject hash |
| `parallel` | 显式分叉/汇合 | 必须有 `depends_on`/后继；汇合策略明确 |
| `check` | 健康检查/冒烟/验收检查 | 不产生业务结论；失败按失败路径 |
| `end` | 终止节点 | 不得有出边 |
| `subworkflow` | 组合另一个 Workflow | `workflow_ref` 必须存在；禁止递归/循环；深度 ≤3 |
| `approval` | 显式 SA/权限审批 | 只用于 G1–G6 之外的显式安全授权；不得替代 Gate |

> `subworkflow` 与 `approval` 是 P1-002 的**新增节点类型**，用于组合和显式授权；不改变 P0 既有节点语义。

---

## 3. DAG 规则

1. 节点 `id` 在 Workflow 内唯一。
2. `depends_on` 只能引用本 Workflow 内节点；不得自依赖。
3. 依赖图必须是有向无环图（DAG）；循环依赖直接拒绝。
4. 至少有一个入口节点（无 `depends_on`）和一个可达的 `end`。
5. 所有非入口节点必须可达；不得有孤立节点。
6. `gate` 节点必须可达且位于其检查对象之后。
7. `subworkflow` 引用必须存在、版本固定、无递归；组合后的 Gate 不得被移除。
8. `parallel_group` 内节点必须共享明确的汇合点；不得无限并行。
9. `condition` 只能读取显式上下文；不得依赖隐藏全局状态。
10. `on_success`/`on_failure` 只能指向存在的节点或终止语义。

**不允许：**

- 循环依赖；
- 依赖未完成即执行；
- 通过跳过 Gate 节点绕过质量门禁；
- 在 Workflow 内硬编码平台专属分支。

---

## 4. Workflow 选择

### 4.1 选择输入

- 任务类型（`task-classification-standard.md`）；
- 复杂度 L1/L2/L3；
- 风险等级；
- 目标环境（dev/test/staging/prod）；
- 变更类型（代码/配置/数据/文档/部署）；
- 用户显式约束；
- 可用 Agent/Skill/平台能力。

### 4.2 选择顺序

1. 按 `trigger.task_types` 精确匹配。
2. 按复杂度/风险/环境过滤。
3. 优先选择 `status=published` 且版本固定的 Workflow。
4. 多个匹配时，选择更严格（Gate 更多、证据更强）的 Workflow。
5. 无匹配 → `consultation` 澄清，或阻止并请求人工确认；不得默认走最简单流程。
6. 用户指定 Workflow 时，只能选择同等或更严格流程；不得弱化 G4/G5、G6、R3/R4/SA。

### 4.3 选择证据

选择结果必须记录：

- 候选列表与排除原因；
- 最终 Workflow ID/版本；
- 复杂度、风险、环境；
- 用户覆盖（如有）及其边界；
- 选择时间和依据。

---

## 5. Workflow 目录

以下 9 个 Workflow 覆盖 P1-002 要求。具体 YAML 示例见 `examples/orchestration/workflows/`。

### 5.1 `consultation` — 技术咨询

- **触发：** `technical_consultation`；L1/L2。
- **阶段：** 问题澄清 → 分析/方案比较 → 结论与依据 → 可选独立复核 → end。
- **门禁：** 无代码门禁；G1/G2 按需；若产出代码/配置，则按实际变更追加 G4/G5。
- **禁止：** 把未执行的分析写成“已验证”；虚构测试/运行结果。

### 5.2 `simple-task` — 简单代码修改

- **触发：** `simple_change`；L1。
- **阶段：** coding → {code-review(G4), testing(G5)} 并行 → quality gate(G4 AND G5) → end。
- **简化：** 可跳过 G1/G2/G3，但必须记录理由；G4 独立 Review 不得跳过；G5 至少执行变更相关测试。
- **纯文档：** G4 可 N/A；任何代码变更不得跳过 G4。
- **部署：** 本 Workflow 不包含生产部署；如需部署，切换到 `deployment` 或 `feature-development`。

### 5.3 `bug-fix` — Bug 修复

- **触发：** `bug_fix`；L2（复杂 Bug 可 L3）。
- **阶段：** analysis → coding → {code-review(G4), testing(G5)} 并行 → quality gate → end。
- **可选：** 需求不清晰时增加 requirements/G1；需要部署时追加 deployment 子流程。
- **失败：** Review 严重问题回 coding；测试失败按缺陷类型回 coding/analysis/requirements。

### 5.4 `feature-development` — 功能开发

- **触发：** `feature_development`；L2/L3。
- **阶段：** requirements → G1 → analysis → design → G2（含 Builder Check）→ plan → G3 → coding → {G4, G5} → quality gate → documentation/feedback。
- **部署：** 仅当请求生产部署时追加 deployment（G6 + R3 + SA）；否则不触发 G6。
- **跳过：** G1–G3 仅在 ADR-006 允许的情况下简化；G4/G5 不得跳过。

### 5.5 `refactoring` — 系统重构

- **触发：** `system_refactoring`；L3。
- **阶段：** requirements → G1 → analysis → design → G2 → plan → G3 → coding → G4/G5 → quality gate → regression → documentation。
- **额外要求：** 必须包含回归测试和迁移/回滚方案；跨模块变更需要独立性审查。
- **部署：** 生产部署时追加 G6 + R3 + SA。

### 5.6 `new-project` — 新项目开发

- **触发：** `new_project`；L3。
- **阶段：** requirements → G1 → analysis → design → G2 → plan → G3 → coding → G4/G5 → quality gate → documentation。
- **部署：** 仅计划生产部署时追加 G6；纯代码交付不触发 G6。
- **额外要求：** 架构方案、技术选型、依赖和安全评估必须可追溯。

### 5.7 `testing` — 测试任务

- **触发：** `testing_task`；L1/L2/L3。
- **阶段：** 测试计划 → 测试用例/环境准备 → 执行 → G5 → 报告 → end。
- **G4：** 仅当修改测试代码/测试基础设施时触发；纯执行不触发 G4。
- **G5：** 必须记录测试范围、环境、结果、失败/重试和证据；不得用“测试通过”替代独立 Review。
- **部署：** 测试任务本身不触发 G6；若随后生产部署，另走 deployment Workflow。

### 5.8 `deployment` — 部署任务

- **触发：** `deployment_task`；L2/L3。
- **阶段：** preflight → 代码/配置变更时 G4/G5 → 生产环境时 G6 + R3 + SA → deploy → verification → end/rollback。
- **非生产部署：** 不触发 G6；按 R0–R4 权限模型审批。
- **生产部署：** 必须 G6 + R3 + SA；缺少任一不得执行。
- **生产数据库：** 普通迁移按 R3；破坏性操作按 R4 + SA；只有同时涉及实际生产部署时才加 G6。
- **失败：** 部署失败/健康检查失败 → 回滚；不得把失败标记为成功。

### 5.9 `documentation` — 文档任务

- **触发：** `documentation_task`；L1（涉及代码示例/代码变更时按实际风险升级）。
- **阶段：** 文档分析 → 草稿 → 独立复核 → 发布 → end。
- **G4/G5：** 纯文档可 N/A；修改代码示例或代码文件时，按代码变更执行 G4/G5。
- **一致性：** 必须检查链接、术语、版本和与现有标准的一致性。

---

## 6. 动态调整

### 6.1 跳过阶段

允许：

- 跳过不适用的 G1/G2/G3（ADR-006 允许时）；
- 跳过可选的 documentation/feedback；
- 文档任务的 G4/G5 按 N/A 规则处理。

禁止：

- 跳过代码变更的 G4 或 G5；
- 跳过生产部署的 G6 + R3 + SA；
- 跳过生产数据破坏性操作的 R4 + SA；
- 跳过安全审查、权限检查、审计或脱敏。

跳过必须记录：节点、理由、批准人（如需）、影响、证据。

### 6.2 追加阶段

允许追加：

- 额外 Review/Testing/安全审查；
- 回归测试、性能测试、迁移演练；
- 额外的文档/验收步骤。

追加阶段不得：

- 删除已有依赖或 Gate；
- 降低 G4/G5 独立性；
- 把 G6 加到非生产部署；
- 绕过权限或审批。

### 6.3 组合

- 通过 `subworkflow` 引用已发布 Workflow。
- 组合必须保持子 Workflow 的 Gate 和证据要求。
- 组合深度 ≤3；禁止递归和循环。
- 子 Workflow 的输入/输出必须映射到父 Workflow 的 Artifact 引用。
- 组合后的 Workflow 仍需通过自身 DAG 校验。

### 6.4 条件分支

- `condition` 只能读取 Task Context、Artifact 引用和显式变量。
- 分支不得隐藏状态或修改全局变量。
- 每个分支必须最终到达 `end` 或明确的失败/终止节点。
- 条件无法求值时 → BLOCKED/needs_input，不得默认选择宽松分支。

### 6.5 终止

- 用户取消、审批拒绝、不可恢复错误、策略终止 → CANCELLED/FAILED。
- 终止是终态；不得直接恢复。
- 终止时必须保留已生成 Artifact、Gate 结果和失败证据。
- 有副作用的外部操作必须执行补偿/回滚（适用时）。

### 6.6 恢复

- 只允许从 WAITING/BLOCKED 恢复；终态不可恢复。
- 恢复前重新校验：
  - Task Context 完整性；
  - Artifact 路径/版本/hash；
  - Gate 的 subject hash；
  - 审批有效期和绑定。
- 恢复不得重跑已成功且产物未变更的节点。
- 失败后的重试若跨越终态，必须创建新 Task/Workflow Run，并用 `parent_task_id`/`parent_run_id` 关联。

---

## 7. 并行执行

### 7.1 Requirements 与 Analysis

- 默认**串行**：analysis 依赖 requirements；G1 未通过不得进入 analysis。
- 仅当存在独立子分析且不依赖需求基线时，可显式拆分并行；必须有聚合节点和证据。
- 不得用并行绕过 G1 或需求确认。

### 7.2 Code Review 与 Testing

- coding 完成后，G4 与 G5 **允许并行**。
- 两者必须针对**同一 commit 或产物 hash**（`subject_hash`）。
- quality gate 必须等待两者都完成，并验证：
  - G4 通过；
  - G5 通过；
  - 两者 subject hash 相同且等于当前代码版本。
- Coding 产生新版本 → 旧 G4/G5 失效，必须重跑。
- 任一失败 → 不得进入 deployment/G6。
- **不得**仅凭两个 Task 状态为 SUCCEEDED 认定质量门禁通过；必须校验 GateDecision。

### 7.3 多模块拆分

- 按模块边界、Artifact 路径和依赖关系拆分。
- 每个 Task 有独立输出路径；不得并发写同一 Artifact。
- 跨模块依赖必须显式声明；共享输入只读。
- 聚合节点负责合并结果；冲突 → FAILED，不得静默覆盖。

### 7.4 多 Agent 协作

- 默认最大并发 5（P0 建议）；单 Skill 并发 ≤2。
- 子 Agent 权限不得超过父 Agent；不得转授 R4。
- 上下文隔离；通过 Artifact 引用共享，不共享可变内存。
- 每个 Task 只有一个主执行 Agent/Skill；协作者只读或写独立产物。
- Agent 不可用 → WAITING/BLOCKED，按失败恢复标准处理。

### 7.5 共享文件

- 同一路径同一时间只允许一个写者；使用租约。
- 其他 Task 只读引用；不得直接写他人产物。
- 原子写入（临时文件 + 重命名）；冲突时生成新版本并标记旧版本 `superseded`。
- 并行分支不得依赖“最后写入者获胜”。

### 7.6 结果汇总

- 聚合策略：`all`（全部成功）、`any`（任一成功）、`quorum`（达到阈值）。
- 聚合结果必须记录每个分支的状态、Artifact 引用和证据。
- 冲突/缺失/哈希不匹配 → 聚合失败。
- 质量门禁聚合必须使用 `all`（G4 AND G5），不得用 `any` 或 `quorum` 替代。

### 7.7 并行失败

- 与质量门禁/关键路径相关的分支失败 → 整个 Workflow 不得成功；按失败路径回退。
- 独立且无副作用的分支可允许完成，但必须记录部分结果；不得把部分成功标记为整体成功。
- 有副作用的分支失败 → 执行补偿/回滚；不可逆操作不得自动重试。
- 取消时向所有运行中分支传播取消；保留已完成产物和证据。

---

## 8. Workflow 生命周期

P1-002 使用以下运行状态（权威转换见 [orchestration-state-machine.md](./orchestration-state-machine.md)）：

```text
PENDING → RUNNING → SUCCEEDED
              ├── WAITING → RUNNING
              ├── BLOCKED → RUNNING / FAILED / CANCELLED
              ├── FAILED
              └── CANCELLED
```

与 P0 状态的映射：

| P1-002 | P0 状态 |
|--------|---------|
| PENDING | `pending` |
| RUNNING | `running` |
| WAITING | `paused`（非审批等待） |
| BLOCKED | `awaiting_approval`（审批）或 `paused`（能力/权限） |
| SUCCEEDED | `completed` |
| FAILED | `failed` |
| CANCELLED | `aborted` |

---

## 9. 不变量

1. 依赖未满足的节点不得执行。
2. DAG 不得有循环。
3. G4/G5 必须同一 subject hash；新版本使旧结果失效。
4. 质量门禁必须 G4 AND G5；不得用 Task SUCCEEDED 代替。
5. 生产部署必须 G6 + R3 + SA。
6. 非生产部署不得触发 G6。
7. 终态 Workflow 不得直接恢复。
8. 同一 Artifact 不得并发多写。
9. 并行聚合不得静默丢弃失败分支。
10. 任何跳过/追加/组合都必须记录证据。

---

## 10. 实现状态

| 能力 | 状态 |
|------|------|
| Workflow 解析/DAG 执行 | 未实现（P2） |
| WorkflowSelector | 未实现（P2） |
| 动态组合/跳过/追加 | 未实现（P2） |
| 并行调度 | 未实现（P2） |
| Workflow Schema/示例/静态校验 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 11. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [task-classification-standard.md](./task-classification-standard.md)
- [task-standard.md](./task-standard.md)
- [orchestration-state-machine.md](./orchestration-state-machine.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [approval-orchestration-standard.md](./approval-orchestration-standard.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [ADR-003](../decisions/ADR-003-orchestration.md)、[ADR-006](../decisions/ADR-006-quality-gates.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现 WorkflowRunner。
