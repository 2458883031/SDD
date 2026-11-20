# SDD 执行上下文与证据标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** Workflow/Task/Skill 执行期间的上下文分层、证据记录、日志/事件/审计关系和可观测性指标
**权威关系：** Task Context 与 Artifact 的权威模型见 [ADR-005](../decisions/ADR-005-task-context.md)；Skill IO 见 [skill-io-contract.md](./skill-io-contract.md)；安全审计见 [security-architecture.md](../architecture/security-architecture.md)。

---

## 1. 目标

本文件回答：

- Workflow、Task、Skill 之间传递什么上下文？
- 哪些上下文可共享、哪些必须隔离？
- 一次执行需要留下哪些证据？
- 日志、事件、审计记录如何区分？
- 需要观测哪些 Orchestration 指标？
- 如何避免证据记录泄露敏感信息？

---

## 2. 上下文分层

| 层 | 内容 | 所有者 | 生命周期 | 可变性 | 访问边界 |
|----|------|--------|----------|--------|----------|
| User Input | 用户原始请求、约束、偏好 | 用户/交互层 | 任务期间 | 不可变（追加修订需新版本） | 任务参与者只读 |
| Workflow Context | Workflow ID/版本、运行参数、全局策略、Run 状态 | Orchestrator | 一次 Workflow Run | 由 Orchestrator 受控更新 | Task 只读 |
| Task Context | task-id、父任务、类型、复杂度、状态、约束、Artifact 引用 | ContextPort/ADR-005 | 任务期间 + 归档 | 仅授权写入者更新状态字段 | 任务参与者按权限读写；根 Context 与 node scoped Context 分离 |
| Skill Input | 传给 Skill 的结构化输入/Artifact 引用 | Orchestrator/Skill | 单次调用 | 调用后不可变 | Skill 只读 |
| Skill Output | 统一输出信封、业务输出、Artifact 引用、错误、证据 | Skill | 单次调用 | 不可变（新结果=新版本） | Orchestrator 校验/路由 |
| Artifact | 需求/设计/代码/测试/审查/部署/报告等产物 | ArtifactManager/ContextPort | 任务期间 + 归档 | 版本化；已批准/完成不可原地改 | 通过引用读取；单写者 |
| Execution Evidence | 输入摘要、执行主体、Skill/Tool、Gate/Approval、commit/hash、时间、失败/恢复 | EvidenceRecorder/审计层 | 任务期间 + 保留期 | 追加写入、不可静默修改 | 审计/授权只读；敏感字段脱敏 |

### 2.1 上下文规则

1. **单一来源**：Task Context 以 ADR-005 为准；不得另建第二套任务状态。
2. **根/节点分离**：Workflow Run 根 Task Context 拥有 ADR-005 生命周期；node scoped Context 只记录节点状态，不得写根 `task-status` 为 completed。
3. **引用而非复制**：跨 Task/Skill 传递 Artifact 引用（path + version + sha256），不复制内容。
4. **默认隔离**：不同 task-id 命名空间默认不可互读；跨任务引用必须显式登记。
5. **最小暴露**：Skill 只获得完成当前节点所需的上下文；不得读取其他任务的私有状态。
6. **不可变输入**：Skill Input 调用后不可变；需要修改时生成新调用/新版本。
7. **输出校验**：Skill Output 必须通过 IO Schema/契约校验后才能写入 Artifact。
8. **凭证隔离**：凭证只以引用形式传递，由有权限的适配器解析；不得进入 Task Context、Artifact 或证据正文。

---

## 3. Evidence 模型

### 3.1 字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `evidence_id` | 是 | 唯一标识 |
| `task_id` / `workflow_id` / `node_id` | 是 | 定位 |
| `type` | 是 | input/output/tool/gate/approval/test/review/command/artifact/failure/recovery/metric |
| `actor` | 是 | `{type, id}`：agent/skill/tool/orchestrator/human |
| `skill` | 否 | `{name, version}` |
| `tool` | 否 | Tool 名称/类别 |
| `input_refs` | 是 | 输入 Artifact/证据引用 |
| `output_refs` | 是 | 输出 Artifact/证据引用 |
| `input_summary` | 否 | 输入摘要（脱敏；不记录原文凭证） |
| `subject_hash` | 否 | commit/产物 hash |
| `result` | 是 | success/failure/blocked/skipped |
| `timestamp` | 是 | 时间 |
| `redacted` | 是 | 必须为 true；敏感字段已脱敏 |
| `details` | 否 | 结构化补充（不得含凭证） |
| `parent_evidence_id` | 否 | 证据链父节点 |

### 3.2 证据类型与要求

| 类型 | 何时记录 | 至少包含 |
|------|----------|----------|
| input | Task/Skill 开始 | 输入引用、摘要、hash |
| output | Task/Skill 完成 | 输出引用、hash、契约校验结果 |
| tool | Tool 调用 | Tool 名、参数摘要（脱敏）、结果、耗时 |
| gate | Gate 评估 | GateDecision ID、subject hash、检查结果、审批 ID |
| approval | 审批 | Approval ID、批准人、时间、scope、有效期 |
| test | 测试 | 命令、环境、结果、失败/重试、证据路径 |
| review | 审查 | Reviewer、问题级别、结论、commit/hash |
| command | 受控命令 | 命令类别（脱敏）、退出码、输出引用 |
| artifact | 产物写入 | path/version/sha256、写者、租约 |
| failure | 失败 | 错误码、分类、重试次数、回退路径 |
| recovery | 恢复 | 恢复点、校验结果、补偿/回滚结果 |
| metric | 观测 | 指标名、值、时间窗、维度 |

---

## 4. 证据链与完整性

1. 每个 Task 至少有一条 input、一条 output（成功时）和失败/恢复证据（如适用）。
2. GateDecision、Approval、Artifact 引用必须可互相追溯。
3. 关键证据记录 `sha256`/`subject_hash`；读取时校验。
4. 证据追加写入；不得静默修改历史；修订以新证据/新版本表达。
5. 证据链断裂（缺父节点、hash 不匹配）→ 不得作为 Gate 通过依据。
6. 证据不得只存在于模型上下文；必须持久化到允许的存储。

---

## 5. 日志、事件与审计

| 类型 | 用途 | 是否权威 | 内容 | 保留 |
|------|------|----------|------|------|
| 日志 Log | 诊断/排错 | 否 | 时间、级别、组件、消息、关联 ID | 短期/可配置 |
| 事件 Event | 状态变化/调度 | 是（状态事实） | event_id、from/to、reason、actor、timestamp | 任务/审计周期 |
| 审计 Audit | 安全/审批/权限决定 | 是（合规证据） | actor、action、target、permission、approval、result | 建议 ≥90 天 |

**规则：**

- 日志不得作为 Gate 通过或审批的唯一证据。
- 事件是状态机的权威变更记录；必须追加写入。
- 审计记录安全/审批/权限决定；不可静默修改。
- 三者共享关联 ID（task_id/event_id/approval_id），但不得混用。
- 任何一类都不得记录原始凭证；统一脱敏。

---

## 6. 可观测性指标

| 指标 | 定义 | 用途 |
|------|------|------|
| Workflow 成功率 | 成功 Workflow / 已结束 Workflow | 流程健康度 |
| Task 成功率 | SUCCEEDED Task / 已结束 Task | 执行质量 |
| Task 失败率 | FAILED Task / 已结束 Task | 失败热点 |
| 重试率 | 发生重试的 Task / 总 Task | 稳定性/幂等性 |
| 平均执行时间 | Task/Workflow 从 RUNNING 到终态 | 性能 |
| 阻塞时间 | BLOCKED 状态总时长 | 审批/能力瓶颈 |
| 人工审批等待时间 | Approval PENDING 时长 | 审批效率 |
| Gate 通过率 | PASSED Gate / 已评估 Gate | 质量趋势 |
| 任务取消率 | CANCELLED Task / 总 Task | 需求/策略稳定性 |

- 指标按 task_type、workflow_id、complexity、platform、environment 维度聚合。
- 指标不得包含个人敏感信息或凭证。
- 指标异常（失败率/阻塞时间突增）应触发告警/审计复核（实现阶段）。

---

## 7. 敏感信息与脱敏

**禁止记录：**

- 原始密码、Token、API Key、私钥；
- 完整凭证 URL、命令历史中的凭证；
- 个人敏感数据（超出任务必要范围）；
- 其他项目的私有内容。

**要求：**

1. 输出/日志/证据/审计统一脱敏；敏感值替换为 `[REDACTED]`。
2. 凭证只保存引用/标识，由有权限的适配器解析。
3. 证据 `redacted` 必须为 true；发现未脱敏 → 阻断并审计。
4. 脱敏不能替代权限、沙箱和审批。
5. 证据访问按最小权限；跨任务读取需显式授权。

---

## 8. 保留与归档

- 任务完成后 Evidence 冻结；按保留策略归档（建议 ≥90 天，可配置）。
- 归档只读；删除需显式审批。
- 审计记录保留期限不得短于合规要求。
- 归档索引保留 task_id/workflow_id/时间/证据类型，便于追溯。

---

## 9. 不变量

1. 证据不得含原始凭证。
2. Gate 通过必须有完整 GateDecision 和证据。
3. 日志不能替代事件/审计。
4. 证据链断裂不得作为通过依据。
5. Task Context 不得被 Skill 或 Adapter 越权修改。
6. 跨任务读取必须显式引用。
7. 产物读取必须校验 hash。
8. 指标不得泄露个人信息/凭证。
9. 审计追加写入，不可静默修改。
10. 上下文隔离不得因并行而破坏。

---

## 10. 实现状态

| 能力 | 状态 |
|------|------|
| EvidenceRecorder/持久化 | 未实现（P2/P5） |
| 事件流/审计日志 | 未实现（P2/P5） |
| 指标采集/告警 | 未实现（P5/P7） |
| Evidence Schema/静态测试 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 11. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [task-standard.md](./task-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [approval-orchestration-standard.md](./approval-orchestration-standard.md)
- [failure-recovery-standard.md](./failure-recovery-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)
- [security-architecture.md](../architecture/security-architecture.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现 EvidenceRecorder 或观测系统。
