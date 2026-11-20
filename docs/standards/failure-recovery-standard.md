# SDD 失败处理与恢复标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** Orchestration 中 Skill、Agent、Tool、依赖、审批、超时、上下文、平台能力和产物失败的分类、重试、补偿与恢复
**权威关系：** Task 调度与状态见 [task-standard.md](./task-standard.md)；状态转换见 [orchestration-state-machine.md](./orchestration-state-machine.md)；门禁规则见 [ADR-006](../decisions/ADR-006-quality-gates.md)；安全边界见 [security-architecture.md](../architecture/security-architecture.md)。

---

## 1. 原则

1. **失败必须显式记录**：不得静默忽略、降级为成功或伪装成“部分完成”。
2. **可逆性决定重试**：只有可重试且幂等的操作才允许自动重试；不可逆操作不得自动重试。
3. **重试有预算**：次数、退避和总时长必须有上限，不得无限重试。
4. **恢复不篡改历史**：终态任务不能原地恢复；重试创建新 Task，并关联原任务。
5. **副作用必须补偿**：外部写操作失败时按补偿/回滚方案处理。
6. **人工决策不能被自动化替代**：审批拒绝、安全风险、不可逆操作必须人工介入。

---

## 2. 失败分类

| 类别 | 典型错误 | 默认处理 |
|------|----------|----------|
| `retryable` | 临时网络错误、可恢复 Tool 错误、Agent 暂时不可用、租约冲突 | 按策略重试 |
| `non_retryable` | 输入非法、契约不匹配、权限拒绝、逻辑错误、未知工具 | 失败/回退，不自动重试 |
| `needs_human` | 审批拒绝、需求歧义、安全风险、敏感凭证 | BLOCKED/人工介入 |
| `needs_replan` | 依赖失败、复杂度变化、方案不可行、范围变化 | 回退到规划/分析 |
| `terminal` | 不可逆操作失败、产物不可恢复损坏、策略终止 | 终止 Workflow |

错误对象至少包含：`code`、`message`、`retryable`、`category`、`details`、`evidence_refs`。

---

## 3. 失败类型与处理

| 失败 | 分类 | 处理 |
|------|------|------|
| Skill 执行失败 | 视错误码 | 可重试 → 重试；不可重试 → 回退/FAILED |
| Agent 不可用 | retryable / blocked | 等待/重新分配；超过阈值 → BLOCKED |
| Tool 调用失败 | retryable / non_retryable | 按 Tool 错误码；权限/参数错误不重试 |
| 依赖任务失败 | needs_replan | 下游 BLOCKED/FAILED；按 Workflow 回退 |
| 审批被拒绝 | needs_human / terminal | Task CANCELLED；Workflow 按策略终止/回退 |
| 超时 | retryable / terminal | 停止执行、释放租约；按策略重试或 FAILED |
| 上下文丢失 | needs_replan | 从持久化 Task Context/Artifact 重建；无法重建 → FAILED |
| 平台能力不支持 | non_retryable / blocked | 标记 `not_ready`/BLOCKED；不得用更高权限工具替代 |
| 产物损坏 | retryable / terminal | 校验 hash；可重建则重跑生产者，否则 FAILED |
| 执行中断 | retryable | 检查点/租约恢复；验证幂等后再执行 |
| 重复请求 | duplicate | 幂等键去重；返回已有结果或拒绝并发 |

---

## 4. 重试策略

### 4.1 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `max_attempts` | 3 | 含首次执行；可配置上限 |
| `backoff` | exponential | fixed / exponential |
| `initial_delay_seconds` | 5 | 首次退避 |
| `max_delay_seconds` | 300 | 单次退避上限 |
| `jitter` | true | 避免惊群 |
| `retry_budget_seconds` | 900 | 总重试预算；超预算失败 |
| `retry_on` | `[retryable]` | 可重试错误类别 |

### 4.2 规则

1. 只重试 `retryable` 错误；`non_retryable`/`needs_human`/`terminal` 不自动重试。
2. 重试必须复用同一 `idempotency_key`，防止重复副作用。
3. 非幂等操作必须先补偿或转人工，不得直接重试。
4. **不可逆操作不得自动重试**：生产数据破坏、不可逆部署、敏感凭证操作、不可恢复删除。
5. 重试耗尽 → FAILED；保留每次尝试的错误和证据。
6. 重试不得跳过 Gate、审批或权限检查。
7. 重试不得把旧版本 G4/G5 结果用于新版本。

---

## 5. 补偿与回滚

- 有外部副作用（部署、数据库写入、外部 API 写）时，必须定义补偿/回滚动作。
- 补偿动作本身必须幂等、可审计、有超时和失败升级路径。
- 补偿失败 → 人工介入；不得静默标记为成功。
- 不可逆操作必须在执行前获得 SA，并有备份/恢复方案（适用时）。
- 补偿/回滚结果写入 Evidence，包含目标、结果、时间和证据引用。

---

## 6. 恢复

### 6.1 可恢复场景

| 场景 | 恢复方式 |
|------|----------|
| WAITING（依赖/容量/退避） | 条件满足后回 READY |
| BLOCKED（审批/权限/能力） | 外部条件恢复后回 READY；重新校验绑定 |
| 执行中断（有检查点） | 重新分配；验证幂等键和产物 hash |
| Agent 不可用 | 重新分配；新 Agent 权限不得提升 |
| 产物损坏（可重建） | 重跑生产者；校验新 hash |
| 重复请求 | 返回已有结果或拒绝并发 |

### 6.2 不可恢复场景

- 终态 SUCCEEDED/FAILED/CANCELLED 不得原地恢复。
- 不可逆操作失败且无法补偿 → FAILED + 人工介入。
- 审批拒绝/过期/失效 → 需重新申请；不得沿用旧批准。
- 上下文无法重建 → FAILED。

### 6.3 恢复前校验

1. Task Context 完整性；
2. Artifact 路径/版本/hash；
3. Gate 的 subject hash 与当前代码/产物一致；
4. Approval 未过期且绑定当前操作；
5. 幂等键未被其他实例占用；
6. 依赖仍满足。

---

## 7. 重复请求与幂等

- 同一 `idempotency_key` 的请求只能有一个执行实例。
- 并发重复 → 返回 `duplicate` 或等待已有结果；不得重复执行副作用。
- 重放必须校验输入/产物 hash；hash 变化视为新请求。
- 幂等窗口和结果保留时间必须可配置；过期后仍需防止意外重复副作用。
- 外部系统若不支持幂等键，必须使用补偿/人工确认。

---

## 8. 超时

- 每个 Task 必须有 `timeout_policy`；超时按失败处理。
- 超时后停止执行、释放租约、记录 `timeout` 错误和证据。
- 长任务使用心跳/检查点；心跳丢失按 Agent 不可用处理。
- 超时不得当作成功、批准或“稍后继续”。
- 超时重试仅适用于可重试且幂等的操作。

---

## 9. 失败传播

| 场景 | 传播 |
|------|------|
| 关键路径 Task 失败 | Workflow FAILED；不进入 Gate/部署 |
| 并行分支失败 | 质量门禁不得通过；独立安全分支可完成但整体不得成功 |
| Gate 失败 | 按 ADR-006 回退；不得进入下一阶段 |
| 审批拒绝 | Task/Workflow CANCELLED 或按策略终止 |
| 策略终止 | 所有运行中 Task 取消；保留证据 |
| 用户取消 | 传播取消；执行补偿（适用时） |

---

## 10. 不变量

1. 不可逆操作不得自动重试。
2. 非幂等操作不得自动重试。
3. 重试不得绕过权限/Gate/审批。
4. 失败不得标记为成功。
5. 终态不得原地恢复。
6. 补偿失败必须升级人工。
7. 同一幂等键不得并发执行。
8. 超时不得视为成功/批准。
9. 恢复前必须校验产物/Gate/审批绑定。
10. 失败/恢复证据必须可追溯。

---

## 11. 实现状态

| 能力 | 状态 |
|------|------|
| 重试/退避/预算执行 | 未实现（P2） |
| 补偿/回滚协调 | 未实现（P2/P5） |
| 租约/检查点/恢复 | 未实现（P2） |
| 失败恢复静态测试 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 12. 相关标准

- [task-standard.md](./task-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [orchestration-state-machine.md](./orchestration-state-machine.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [security-architecture.md](../architecture/security-architecture.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现重试/补偿/恢复 Runtime。
