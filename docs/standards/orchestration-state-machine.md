# SDD Orchestration 状态机标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** Task、Workflow、Node、Gate、Approval 的状态、合法转换、守卫条件和终态
**权威关系：** Task Context 生命周期见 [ADR-005](../decisions/ADR-005-task-context.md)；Task 模型见 [task-standard.md](./task-standard.md)；Workflow 模型见 [workflow-standard.md](./workflow-standard.md)；门禁规则见 [ADR-006](../decisions/ADR-006-quality-gates.md)。

---

## 1. 状态分层

P1-002 区分以下状态，不得混用：

| 状态机 | 所有者 | 作用域 | 是否持久化 |
|--------|--------|--------|------------|
| Task Execution State | Orchestrator/StateStore | 单个 Task | 是（事件 + 快照） |
| Workflow Run State | Orchestrator/StateStore | 一次 Workflow 运行 | 是 |
| Node State | WorkflowRunner | Workflow 节点 | 是（事件） |
| Gate State | GateCoordinator | 单次 Gate 决定 | 是（GateDecision） |
| Approval State | ApprovalCoordinator + 授权人 | 单次审批 | 是（Approval） |
| Root Task Context `task-status` | ContextPort/Orchestrator | 整个 Workflow Run 生命周期 | 是（context.json） |
| Node Task Context（本地投影） | Orchestrator/StateStore | 单个节点 Task | 是（不写根状态） |

**规则：**

- Task Execution State 不等于 ADR-005 `task-status`；两者通过映射表同步。
- Gate/Approval 状态是各自对象的生命周期，不是 Task 状态。
- 状态变更必须产生事件；事件追加写入，不得静默改写历史。

---

## 2. Task Execution State

### 2.1 状态

| 状态 | 含义 |
|------|------|
| `PENDING` | 已创建，依赖/计划未满足 |
| `READY` | 依赖满足，可调度 |
| `RUNNING` | 已分配并执行 |
| `WAITING` | 等待依赖、容量、退避或可自动恢复条件 |
| `BLOCKED` | 等待审批、权限、能力或人工决策 |
| `SUCCEEDED` | 输出有效、证据完整（终态） |
| `FAILED` | 不可恢复失败或重试耗尽（终态） |
| `CANCELLED` | 用户/策略取消或审批拒绝（终态） |

初始状态：`PENDING`。
终态：`SUCCEEDED`、`FAILED`、`CANCELLED`。

### 2.2 合法转换

| From | To | 守卫条件 |
|------|----|----------|
| PENDING | READY | 依赖解析完成且全部满足；计划/输入有效 |
| PENDING | CANCELLED | 取消请求 |
| READY | RUNNING | 已分配 Agent/Skill；租约获取；权限/审批有效 |
| READY | WAITING | 无并发槽、依赖重新等待、退避等待 |
| READY | BLOCKED | 需要审批、缺少权限/能力 |
| READY | CANCELLED | 取消请求 |
| RUNNING | SUCCEEDED | 输出契约通过；Artifact/hash 有效；证据完整；Gate 结果满足 |
| RUNNING | FAILED | 不可重试错误或重试耗尽；错误已记录 |
| RUNNING | WAITING | 可重试错误进入退避；执行暂停但可恢复 |
| RUNNING | BLOCKED | 执行中触发审批/权限/能力阻塞 |
| RUNNING | CANCELLED | 取消请求；执行已停止 |
| WAITING | READY | 等待条件清除（依赖/容量/退避） |
| WAITING | BLOCKED | 等待转为审批/权限/能力阻塞 |
| WAITING | FAILED | 依赖失败、超时耗尽或不可恢复 |
| WAITING | CANCELLED | 取消请求 |
| BLOCKED | READY | 审批通过、权限/能力恢复 |
| BLOCKED | FAILED | 阻塞不可恢复 |
| BLOCKED | CANCELLED | 审批拒绝或取消请求 |

**非法转换示例：**

- PENDING → RUNNING（未 READY）；
- READY → SUCCEEDED（未执行）；
- RUNNING → PENDING（不得回退创建态）；
- 任何终态 → 任何状态（除新 Task 外）；
- SUCCEEDED → FAILED（不得改写历史）；
- CANCELLED → RUNNING（取消不可恢复）。

### 2.3 ADR-005 映射

| Task Execution State | ADR-005 `task-status` | 同步时机 |
|----------------------|------------------------|----------|
| PENDING | `created` / `planned` | 创建/计划完成 |
| READY | `planned` | 依赖满足 |
| RUNNING | `executing` | 开始执行 |
| WAITING | `executing` | 等待不改变持久化生命周期 |
| BLOCKED（审批） | `awaiting_approval` | 审批请求发出 |
| BLOCKED（非审批） | 保持 `executing` + `blocked_reason` | 记录阻塞原因，不伪造审批态 |
| SUCCEEDED | `completed` | Workflow 验证完成 |
| FAILED | `failed` | 不可恢复失败 |
| CANCELLED | `aborted` | 取消/拒绝/策略终止 |

> 该表用于 `context_scope=root` 的根 Task Context。`context_scope=node` 的 `context_status` 只是本地投影；节点 SUCCEEDED 不得把根 `task-status` 写成 `completed`。

> ADR-005 的 `verifying` 阶段对应 Workflow 级验证；Task 级 `SUCCEEDED` 不等于整个 Workflow `completed`。

### 2.4 根 Context 完成规则

1. Workflow Run 拥有独立的根 Task Context；根 `task-status` 按 ADR-005 生命周期演进。
2. 节点级 Task 拥有 scoped Context，`parent_task_id` 指向根任务；节点 Context 不拥有 Run 的全局完成权。
3. 节点 Task 进入 `SUCCEEDED` 只更新节点本地状态和本地 `context_status`，不得把根 `task-status` 写成 `completed`。
4. 根 Context 只有在所有必需 Task 成功/允许跳过、必需 Gate 通过、Workflow 级验证完成后，才能从 `verifying` 进入 `completed`；Schema 要求根 `context_status=completed` 时 `workflow_verified=true`。
5. `context_scope=root` 的 `context_status` 是权威生命周期；`context_scope=node` 的 `context_status` 只是本地投影。root 不得有 `parent_task_id`，node 必须有有效根 Task ID 格式的 `parent_task_id`。

---

## 3. Workflow Run State

### 3.1 状态

`PENDING`、`RUNNING`、`WAITING`、`BLOCKED`、`SUCCEEDED`、`FAILED`、`CANCELLED`。

### 3.2 合法转换

| From | To | 守卫条件 |
|------|----|----------|
| PENDING | RUNNING | Workflow 校验通过；Task 计划生成；资源可用 |
| PENDING | CANCELLED | 取消请求 |
| RUNNING | WAITING | 所有可运行任务等待依赖/容量/退避 |
| RUNNING | BLOCKED | 存在需要审批/权限/能力的阻塞 |
| RUNNING | SUCCEEDED | 所有必需 Task 成功/允许跳过；必需 Gate 通过；证据完整 |
| RUNNING | FAILED | 关键 Task 失败且不可恢复；Gate 失败；策略终止 |
| RUNNING | CANCELLED | 取消请求 |
| WAITING | RUNNING | 等待条件清除 |
| WAITING | BLOCKED | 等待转为审批/权限/能力阻塞 |
| WAITING | FAILED | 依赖失败/超时耗尽 |
| WAITING | CANCELLED | 取消请求 |
| BLOCKED | RUNNING | 审批通过/权限/能力恢复 |
| BLOCKED | FAILED | 阻塞不可恢复 |
| BLOCKED | CANCELLED | 审批拒绝/取消 |

终态不可恢复；重试需新 Workflow Run（`parent_run_id`）。

### 3.3 P0 状态映射

| P1-002 | P0 `workflow_states` |
|--------|----------------------|
| PENDING | `pending` |
| RUNNING | `running` |
| WAITING | `paused`（非审批） |
| BLOCKED | `awaiting_approval`（审批）或 `paused`（能力/权限） |
| SUCCEEDED | `completed` |
| FAILED | `failed` |
| CANCELLED | `aborted` |

---

## 4. Node State

### 4.1 状态

`PENDING`、`READY`、`RUNNING`、`WAITING`、`BLOCKED`、`SUCCEEDED`、`FAILED`、`SKIPPED`、`CANCELLED`。

### 4.2 合法转换

| From | To | 守卫条件 |
|------|----|----------|
| PENDING | READY | 依赖满足；节点激活 |
| PENDING | SKIPPED | 条件不满足且规范允许跳过；记录理由 |
| PENDING | CANCELLED | 取消 |
| READY | RUNNING | 节点开始执行 |
| READY | WAITING | 等待资源/依赖 |
| READY | BLOCKED | 审批/权限/能力阻塞 |
| READY | CANCELLED | 取消 |
| RUNNING | SUCCEEDED | 节点输出/证据有效 |
| RUNNING | FAILED | 不可恢复失败 |
| RUNNING | WAITING | 可恢复等待/退避 |
| RUNNING | BLOCKED | 审批/权限/能力阻塞 |
| RUNNING | CANCELLED | 取消 |
| WAITING | READY | 等待条件清除 |
| WAITING | BLOCKED | 转为阻塞 |
| WAITING | FAILED | 等待超时/依赖失败 |
| WAITING | CANCELLED | 取消 |
| BLOCKED | READY | 阻塞解除 |
| BLOCKED | FAILED | 阻塞不可恢复 |
| BLOCKED | CANCELLED | 拒绝/取消 |

终态：`SUCCEEDED`、`FAILED`、`SKIPPED`、`CANCELLED`。

### 4.3 P0 节点状态映射

| P1-002 | P0 `node_states` |
|--------|------------------|
| PENDING | `queued` |
| READY | `queued` |
| RUNNING | `executing` |
| WAITING | `blocked`（等待） |
| BLOCKED | `awaiting_approval` / `blocked` |
| SUCCEEDED | `succeeded` |
| FAILED | `failed` |
| SKIPPED | `skipped` |
| CANCELLED | 无直接对应；记录 `cancelled` 事件，不映射为 `succeeded`/`failed` |

---

## 5. Gate State

### 5.1 GateDecision

每次 Gate 评估产生一个不可变的 `GateDecision`：

- `decision_id`、`gate_id`、`task_id`、`workflow_id`、`node_id`；
- `required`、`status`、`subject_type`、`subject_hash`；
- `automated_checks`、`approval_ref`、`decision_reason`；
- `decided_by`、`decided_at`、`expires_at`、`evidence_refs`；
- `invalidation_reason`。

### 5.2 状态

`NOT_REQUIRED`、`PENDING`、`EVALUATING`、`PASSED`、`FAILED`、`BLOCKED`、`INVALIDATED`、`EXPIRED`。

### 5.3 合法转换

| From | To | 守卫条件 |
|------|----|----------|
| PENDING | EVALUATING | 开始自动检查 |
| PENDING | INVALIDATED | subject 变化/任务取消 |
| PENDING | EXPIRED | 超时未评估 |
| EVALUATING | PASSED | 自动检查通过；所需审批通过；证据完整 |
| EVALUATING | FAILED | 自动检查失败；审批拒绝 |
| EVALUATING | BLOCKED | 等待人工审批/外部证据 |
| EVALUATING | INVALIDATED | subject 变化 |
| EVALUATING | EXPIRED | 评估超时 |
| BLOCKED | EVALUATING | 审批/证据到达 |
| BLOCKED | FAILED | 审批拒绝/证据不可得 |
| BLOCKED | INVALIDATED | subject 变化 |
| BLOCKED | EXPIRED | 审批/评估超时 |
| PASSED | INVALIDATED | subject hash 变化（新 commit/产物） |
| PASSED | EXPIRED | 超过有效期 |
| FAILED | INVALIDATED | subject 变化/重新评估创建新 decision |
| NOT_REQUIRED | — | 终态 |
| INVALIDATED / EXPIRED | — | 终态；重新评估创建新 decision |

**规则：**

- GateDecision 不可原地修改；重新评估创建新 `decision_id`。
- `FAILED` 可因 subject 变化被 `INVALIDATED`；`INVALIDATED`/`EXPIRED` 为终态。
- G4/G5 的 `subject_hash` 必须相同；不同则质量门禁不得 PASSED。
- 生产部署 G6 不得自动批准；缺少人工审批只能 BLOCKED。
- Gate 状态与 Task 状态独立；Task SUCCEEDED 不代表 Gate 通过。

---

## 6. Approval State

### 6.1 Approval

Approval 对象字段与绑定规则见 [approval-orchestration-standard.md](./approval-orchestration-standard.md)。

### 6.2 状态

`REQUESTED`、`PENDING`、`APPROVED`、`CONSUMED`、`REJECTED`、`EXPIRED`、`REVOKED`、`INVALIDATED`。

### 6.3 合法转换

| From | To | 守卫条件 |
|------|----|----------|
| REQUESTED | PENDING | 请求已送达授权人/策略控制器 |
| PENDING | APPROVED | 授权人显式批准；绑定有效 |
| PENDING | REJECTED | 授权人显式拒绝 |
| PENDING | EXPIRED | 超过有效期 |
| PENDING | REVOKED | 请求方/授权人撤销 |
| PENDING | INVALIDATED | 任务/操作/产物/scope 变化 |
| APPROVED | CONSUMED | 原子单次消费成功；绑定仍有效 |
| APPROVED | INVALIDATED | 使用前 subject/scope 变化 |
| APPROVED | EXPIRED | 超过有效期 |
| APPROVED | REVOKED | 授权人撤销（使用前） |
| CONSUMED / REJECTED / EXPIRED / REVOKED / INVALIDATED | — | 终态；不得复用 |

**规则：**

- Approval 单次使用；批准后只能用于绑定的 task/operation/target/subject_hash。
- `APPROVED → CONSUMED` 必须原子完成；并发消费只能一个成功，其余返回 `already_consumed`。
- 任务变更、产物 hash 变化、scope 变化 → 立即 INVALIDATED。
- 超时、沉默、默认值不等于批准。
- Agent 不得批准自己的高风险操作。
- 拒绝后不得换路径绕过；Task 进入 CANCELLED/BLOCKED，按策略处理。

---

## 7. 全局不变量

1. 终态不得直接转换到任何其他状态。
2. Task 进入 SUCCEEDED 必须有有效输出和证据。
3. Workflow 进入 SUCCEEDED 必须所有必需 Task 成功/允许跳过，且必需 Gate PASSED。
4. Gate PASSED 必须有完整自动检查和所需审批；G4/G5 同一 subject hash。
5. G6 不得自动批准；生产部署必须 R3 + G6 + SA。
6. Approval 不得跨 Task/操作/产物复用；消费后必须为 CONSUMED。
7. Task Execution State 与 ADR-005 `task-status` 必须按映射同步。
8. 节点 Task SUCCEEDED 不得把根 Task Context 设置为 completed；根 completed 只在 Workflow 验证完成后写入。
9. 状态变更必须记录事件（from/to/reason/actor/timestamp）。
10. 取消后不得继续执行；取消是终态。
11. 不得用 Task SUCCEEDED 替代 GateDecision。

---

## 8. 事件与审计

每次状态转换至少记录：

```json
{
  "event_id": "uuid",
  "event_type": "task.state_changed",
  "task_id": "task-...",
  "workflow_id": "feature-development",
  "node_id": "coding",
  "from": "RUNNING",
  "to": "SUCCEEDED",
  "reason": "outputs_valid_and_evidence_complete",
  "actor": {"type": "orchestrator", "id": "..."},
  "timestamp": "ISO8601",
  "evidence_refs": []
}
```

事件追加写入；不得静默修改历史。Gate/Approval 事件另见对应标准。

---

## 9. 机器可读定义

状态机以 JSON 形式提供，供校验器加载：

- `schemas/orchestration/task-state-machine.json`
- `schemas/orchestration/workflow-state-machine.json`
- `schemas/orchestration/node-state-machine.json`
- `schemas/orchestration/gate-state-machine.json`
- `schemas/orchestration/approval-state-machine.json`

文档与 JSON 不一致时，以本标准的语义为准，并在 R5 测试中校验；不得只改 JSON 而不更新文档。

---

## 10. 实现状态

| 能力 | 状态 |
|------|------|
| 状态机执行/持久化 | 未实现（P2） |
| 事件流/StateStore | 未实现（P2） |
| 状态机 JSON/静态测试 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 11. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [task-standard.md](./task-standard.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [approval-orchestration-standard.md](./approval-orchestration-standard.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)、[ADR-006](../decisions/ADR-006-quality-gates.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现状态机 Runtime。
