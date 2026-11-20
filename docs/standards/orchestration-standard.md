# SDD Orchestration 标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** Orchestration 编排层的职责、组件边界、运行时模型、生命周期和跨标准关系
**权威关系：** 六个核心概念见 [system-architecture.md §2](../architecture/system-architecture.md#2-核心概念权威定义)；P0 编排架构见 [orchestration-architecture.md](../architecture/orchestration-architecture.md)；门禁规则见 [ADR-006](../decisions/ADR-006-quality-gates.md)。本文件不重新定义 G1–G6、R0–R4 或 Task Context。

---

## 1. 目的与边界

本文件定义 SDD Orchestration 的**运行时职责模型**，回答：

- 谁识别任务、判断复杂度、选择 Workflow；
- 谁创建 Task、管理依赖、调度执行；
- 谁判定节点完成、Gate 通过、Workflow 完成；
- 谁处理失败、重试、阻塞、审批和恢复；
- 谁负责执行证据和可观测性。

**不属于本文件：**

- G1–G6 的触发、跳过和审批规则（ADR-006）；
- R0–R4、SA 的安全定义（安全架构）；
- Skill 的专业能力与 IO 契约（P1-001 标准）；
- Platform Adapter 的平台映射（P1-001 适配架构）；
- 实际 Runtime 实现（P2）。

---

## 2. Orchestrator 的定义

**Orchestrator** 是 Orchestration Engine 的控制面。它负责流程控制和状态协调，不负责替代 Skill 的专业工作。

| 维度 | 定义 |
|------|------|
| 输入 | 用户请求、Task Context、Workflow 定义、Artifact 引用、能力/权限声明 |
| 输出 | Workflow Run 状态、Task 状态、调度决定、Gate 请求、审批请求、汇总结果、执行证据 |
| 决策范围 | 任务分类、复杂度、Workflow 选择、Task 拆分、依赖、并发、重试、回退、终止 |
| 不决策 | 专业内容质量、G/SA 的人工决定、权限授予、平台能力声明 |
| 状态所有权 | Workflow Run / Task 执行状态归 Orchestrator；Task Context 持久化按 ADR-005；Artifact 归 ArtifactManager/ContextPort |

### 2.1 核心原则

1. **流程控制与专业能力分离**：Orchestrator 决定“何时、调用谁、如何验收”，不生成专业结论。
2. **声明式优先**：Workflow 由声明式定义驱动，不把流程硬编码进 Skill 或平台适配器。
3. **单一状态所有者**：每个状态字段只有一个权威写入者；其他组件通过事件/引用同步。
4. **默认保守**：分类或复杂度不确定时，采用更高风险等级和更严格流程。
5. **不可逆操作不自动重试**：重试策略必须服从操作的可逆性和幂等性。
6. **证据先行**：任何 Gate 通过、审批、重试、回退都必须有可追溯证据。
7. **设计不等于实现**：本文件是规范，不代表 Runtime 已实现。

---

## 3. 组件与职责

| 组件 | 职责 | 不负责 | 对应 P0 组件 |
|------|------|--------|--------------|
| TaskIdentifier | 解析用户请求，输出任务类型、候选 Workflow、缺失信息 | 复杂度最终判定、执行 | TaskIdentifier |
| ComplexityEvaluator | 按影响、风险、依赖、不确定性、安全/生产影响判定 L1/L2/L3 | 选择具体节点、执行 Skill | ComplexityEvaluator |
| WorkflowSelector | 根据任务类型、复杂度、风险、环境选择/组合 Workflow | 修改 Workflow 规则、绕过 Gate | SkillRouter / 路由规则 |
| Planner | 把 Workflow 展开为 Task DAG，校验依赖、并行和资源 | 执行 Task、批准 Gate | WorkflowRunner（规划部分） |
| Scheduler | 计算 READY 集合、分配 Agent/Skill、控制并发和租约 | 执行专业工作、批准审批 | WorkflowRunner（调度部分） |
| TaskExecutor | 调用 Skill/Tool/Subworkflow，校验输入输出，回传结果 | 决定流程、修改全局状态 | WorkflowRunner（执行部分） |
| GateCoordinator | 在挂载点触发 Gate、收集证据、等待审批、记录决定 | 重新定义 G1–G6 规则 | GateController |
| ApprovalCoordinator | 创建 Approval 请求、绑定操作/产物、等待显式决定、失效管理 | 代替人工批准、授予权限 | ApprovalPort 的上层协调 |
| EvidenceRecorder | 记录 Task 事件、Gate 决定、审批、工具调用、失败/恢复证据 | 保存原始凭证、替代审计系统 | ArtifactManager / 审计层 |
| StateStore | 持久化 Workflow Run/Task 执行状态和事件序列 | 保存专业产物内容 | ContextPort / ADR-005 |

**边界规则：**

- Orchestrator 不得直接实现 Skill 的专业逻辑，也不得把全部流程写进一个 Skill。
- GateCoordinator 只执行 ADR-006 的规则；不得自行放宽或新增门禁。
- ApprovalCoordinator 只协调交互和记录；批准权属于授权人类/策略控制者。
- EvidenceRecorder 不记录原始凭证；敏感字段必须脱敏或只保存引用。

---

## 4. 运行时模型

### 4.1 主流程

```text
接收请求
  → 任务分类（TaskIdentifier）
  → 复杂度与风险判定（ComplexityEvaluator）
  → Workflow 选择/组合（WorkflowSelector）
  → 创建 Workflow Run + Task Context
  → 规划 Task DAG（Planner）
  → 调度 READY Task（Scheduler）
  → 执行 Skill/Tool/Subworkflow（TaskExecutor）
  → Gate/Approval（GateCoordinator + ApprovalCoordinator）
  → 汇总结果与证据（EvidenceRecorder）
  → Workflow 完成/失败/取消
```

### 4.2 阶段说明

| 阶段 | 输入 | 输出 | 失败处理 |
|------|------|------|----------|
| 分类 | 用户请求、项目上下文 | 任务类型、候选 Workflow、缺失信息 | 信息不足 → `needs_input`；无法分类 → consultation + 人工确认 |
| 复杂度 | 分类结果、影响/风险/依赖/安全信号 | L1/L2/L3、风险等级、依据 | 不确定 → 最低 L2；涉及生产/数据/安全 → L3 + 人工确认 |
| 选择 | 分类、复杂度、环境、用户约束 | Workflow 版本、必需 Gate | 无匹配 → consultation 或阻止并请求确认 |
| 规划 | Workflow、Artifact 引用、能力 | Task DAG、并行组、资源需求 | 循环依赖/缺节点 → 拒绝，不执行 |
| 调度 | READY Task、Agent/Skill 能力、权限 | 分配、租约、并发槽 | 无可用 Agent/能力 → BLOCKED |
| 执行 | Task 输入、Skill 版本、权限 | Skill 输出信封、Artifact、证据 | 按失败恢复标准处理 |
| 门禁 | 产物、commit/hash、证据 | GateDecision | 失败 → 回退/阻止；审批 → BLOCKED |
| 汇总 | Task 输出、Gate 结果、证据 | Workflow 结果、证据链 | 缺证据/冲突 → 不得标记成功 |

### 4.3 Workflow Run 生命周期

Workflow Run 使用以下执行状态（详见 [orchestration-state-machine.md](./orchestration-state-machine.md)）：

```text
PENDING → RUNNING → SUCCEEDED
              ├── WAITING → RUNNING
              ├── BLOCKED → RUNNING / FAILED / CANCELLED
              ├── FAILED
              └── CANCELLED
```

- `WAITING`：等待依赖、容量、退避或可自动恢复条件。
- `BLOCKED`：等待审批、权限、能力或人工决策。
- `SUCCEEDED` / `FAILED` / `CANCELLED` 为终态，不可直接恢复执行。
- 需要重试终态任务时，创建新 Task/Workflow Run，并通过 `parent_task_id` / `parent_run_id` 关联。

---

## 5. 状态所有权与同步

| 状态 | 权威所有者 | 其他组件权限 |
|------|------------|--------------|
| Workflow Run 执行状态 | Orchestrator / StateStore | 只读；通过事件订阅 |
| Task 执行状态 | Orchestrator / StateStore | 只读；TaskExecutor 只能报告结果 |
| 根 Task Context `task-status` | ADR-005 / ContextPort | 只有 Workflow 级验证完成后才能 `completed` |
| 节点 Task Context（本地投影） | Orchestrator / StateStore | 只写本节点；不得写根 `task-status` |
| Artifact 版本/hash | ArtifactManager / ContextPort | 只读引用；写入需单写者租约 |
| Gate 决定 | GateCoordinator | 只读；不得改写历史决定 |
| Approval 决定 | 授权人类/策略控制者 + ApprovalCoordinator 记录 | Orchestrator 只读决定，不代替批准 |
| Skill 结果 | Skill 自身（输出信封） | Orchestrator 校验和路由，不篡改 |
| 执行证据 | EvidenceRecorder / 审计层 | 追加写入；不得静默修改 |

**规则：**

- Task 执行状态与 ADR-005 `task-status` 不是同一字段；根 Task Context 使用 ADR-005 生命周期，节点 Task 的 `context_status` 只是本地投影，映射见状态机标准。
- 节点 Task 进入 SUCCEEDED 不得把根 Task Context 设置为 completed；根 completed 只在 Workflow 级验证完成后写入。
- 任何组件不得直接写其他组件的状态；必须通过事件/接口。
- 状态变更必须记录 `event_id`、`task_id`、`from`、`to`、`reason`、`timestamp`、`actor`。

---

## 6. 动态编排原则

1. **选择而非硬编码**：TaskIdentifier + ComplexityEvaluator + WorkflowSelector 选择 Workflow；不得在 Orchestrator 中写死某业务分支。
2. **组合而非复制**：通过 Subworkflow 组合已有流程；组合不得改变子流程的门禁语义。
3. **跳过有边界**：只允许跳过可选阶段；G4/G5（代码变更）、安全控制、G6/R3/R4/SA 不得跳过。
4. **追加不削弱**：可以追加 Review/Testing/安全审查；不得删除已有依赖或降低 Gate。
5. **终止不可恢复**：取消是终态；恢复执行必须新建 Task/Workflow Run。
6. **变更需重规划**：任务范围、复杂度、产物 hash 或风险变化时，必须重新评估受影响 Task 和 Gate。

具体规则见 [workflow-standard.md](./workflow-standard.md) 与 [task-standard.md](./task-standard.md)。

---

## 7. 失败、审批与证据

- 失败分类、重试、超时、幂等、补偿、恢复：见 [failure-recovery-standard.md](./failure-recovery-standard.md)、[task-standard.md](./task-standard.md) 与 [execution-evidence-standard.md](./execution-evidence-standard.md)。
- G1–G6 的编排机制：见 [gate-orchestration-standard.md](./gate-orchestration-standard.md)。
- Approval 对象、绑定、过期和失效：见 [approval-orchestration-standard.md](./approval-orchestration-standard.md)。
- 上下文分层、证据、日志/事件/审计、观测指标：见 [execution-evidence-standard.md](./execution-evidence-standard.md)。

**不可违反：**

- 超时、沉默、默认值不等于批准。
- Agent 不得批准自己的高风险操作。
- G6 不是权限检查；R4 不等于 G6；SA 不替代权限检查。
- 不可逆操作不得配置为自动重试。
- 任何“成功”必须有输出校验和证据，不得仅凭状态为 SUCCEEDED。

---

## 8. 不变量

1. 没有满足依赖的 Task 不得进入 RUNNING。
2. 没有有效输出和证据的 Task 不得进入 SUCCEEDED。
3. 没有同一 subject hash 的 G4 AND G5 不得通过质量门禁。
4. 生产部署未满足 R3 + G6 + SA 不得执行。
5. 审批不得跨 Task、跨操作或跨产物复用；`APPROVED → CONSUMED` 只能成功一次。
6. 终态 Task/Workflow 不得直接恢复执行。
7. 同一 Artifact 路径不得并发多写。
8. 同一幂等键不得并发创建两个执行实例。
9. Gate 失败不得被下游节点“猜测修复”或静默跳过。
10. 执行证据不得包含原始凭证。
11. 节点 Task SUCCEEDED 不得把根 Task Context 设置为 completed。
12. 根 Task Context 只有在 Workflow 级验证完成后才能 completed。

---

## 9. 实现状态

| 能力 | 状态 |
|------|------|
| Orchestrator / WorkflowRunner | 未实现（P2） |
| Task Scheduler / StateStore | 未实现（P2） |
| GateController | 未实现（P2） |
| ApprovalCoordinator | 未实现（P2/P5） |
| EvidenceRecorder / 审计 | 未实现（P2/P5） |
| Workflow/Task Schema 校验 | 本轮提供静态 Schema 与测试，不是 Runtime |
| 平台适配 | 未实现（P2/P7） |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 10. 相关标准

- [task-classification-standard.md](./task-classification-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [task-standard.md](./task-standard.md)
- [orchestration-state-machine.md](./orchestration-state-machine.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [approval-orchestration-standard.md](./approval-orchestration-standard.md)
- [failure-recovery-standard.md](./failure-recovery-standard.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [orchestration-architecture.md](../architecture/orchestration-architecture.md)
- [ADR-003](../decisions/ADR-003-orchestration.md)、[ADR-005](../decisions/ADR-005-task-context.md)、[ADR-006](../decisions/ADR-006-quality-gates.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现 Orchestration Runtime。
