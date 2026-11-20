# SDD Gate 编排标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** G1–G6 在 Orchestration 中的挂载、评估、审批、版本绑定、失败和恢复
**权威关系：** **G1–G6 的唯一权威定义是 [ADR-006](../decisions/ADR-006-quality-gates.md)。** 本文件只定义编排层的 GateDecision、评估流程、版本绑定和失败路径，不重新定义门禁规则。R0–R4/SA 见 [security-architecture.md](../architecture/security-architecture.md)。

---

## 1. 原则

1. **继承而非重定义**：G1–G6 的触发、自动检查、人工审批、跳过、失败回退和审计以 ADR-006 为准。
2. **Gate 决定与 Task 状态分离**：Task SUCCEEDED 不等于 Gate PASSED；Gate PASSED 必须有独立证据。
3. **版本绑定**：G4/G5 必须针对同一 commit 或产物 hash；新版本使旧结果失效。
4. **审批不等于权限**：G6 不是权限检查；R4 不等于 G6；SA 不替代权限检查。
5. **不允许自动批准**：超时、沉默、默认值不等于批准；Agent 不得自批高风险操作。
6. **不可绕过**：Gate 失败不得被下游节点“猜测修复”或静默跳过。

---

## 2. GateDecision 对象

每次 Gate 评估产生一个不可变的 GateDecision：

| 字段 | 必需 | 说明 |
|------|------|------|
| `decision_id` | 是 | 决定唯一标识 |
| `gate_id` | 是 | G1–G6 |
| `task_id` / `workflow_id` / `node_id` | 是 | 定位 |
| `required` | 是 | 是否必需；N/A 时为 false |
| `status` | 是 | NOT_REQUIRED/PENDING/EVALUATING/PASSED/FAILED/BLOCKED/INVALIDATED/EXPIRED |
| `subject_type` | 是 | commit/artifact/task/other |
| `subject_hash` | 条件 | commit SHA 或产物 hash；G4/G5 在所有状态下必需；G6 必需 |
| `deployment_target` | 条件 | G6 必需；生产部署目标/环境对象 |
| `automated_checks` | 是 | 检查项、结果、证据引用 |
| `approval_ref` | 否 | 关联 Approval ID（如需人工审批） |
| `decision_reason` | 是 | 通过/失败/阻塞原因 |
| `decided_by` | 是 | `system` / `human:<id>` / `policy:<id>` |
| `decided_at` | 是 | 时间 |
| `expires_at` | 否 | 有效期 |
| `evidence_refs` | 是 | 证据引用 |
| `invalidation_reason` | 否 | 失效原因 |

- GateDecision 不可原地修改；重新评估创建新 `decision_id`。
- G4/G5 在 PENDING/EVALUATING/BLOCKED/PASSED/FAILED 等所有状态下都必须绑定有效 `subject_hash`，不得用 null/缺失绕过。
- G6 必须绑定有效部署对象（`deployment_target`）和 `subject_hash`；生产部署前不得为空。
- 状态转换见 [orchestration-state-machine.md](./orchestration-state-machine.md)。

---

## 3. Gate 挂载点

| Gate | 挂载位置 | 主要控制 | 人工审批 |
|------|----------|----------|----------|
| G1 | requirements 之后 | 需求范围、目标、约束、验收标准 | L2/L3、安全敏感、外部依赖、需求不清晰时 |
| G2 | design 之后 | 技术方案、架构影响、Builder Check | L3、跨模块、安全敏感、新依赖 |
| G3 | coding 之前 | 计划、拆解、依赖、顺序、风险 | L3、多 Agent、跨团队、高风险 |
| G4 | code-review 之后 | 代码质量、独立 Review | 所有代码变更（独立 Review）；L1 可简化但不能自审 |
| G5 | testing 之后 | 测试结果、验收标准、回归 | L2/L3 验收；生产发布前 |
| G6 | **实际生产部署动作之前** | 部署目标、环境风险、回滚、授权 | 所有生产部署必须人工授权 |

**G6 边界：**

- 仅实际生产部署触发 G6。
- 非生产部署不触发 G6；生产环境非部署变更不自动触发 G6。
- 生产部署 = R3 + G6 + SA。
- 生产数据库普通迁移 = R3；破坏性操作 = R4 + SA；只有同时涉及实际生产部署时才加 G6。
- G6 不替代 G4/G5、R3/R4 权限检查或 SA。

具体规则见 [ADR-006 §8–§10](../decisions/ADR-006-quality-gates.md) 与 [security-architecture.md §5.3](../architecture/security-architecture.md)。

---

## 4. Gate 评估流程

```text
节点完成
  → 判断 Gate 是否适用（required / N/A）
  → 收集 subject（commit/产物 hash）与证据
  → 执行自动检查
  → 如需人工审批：创建 Approval，Gate BLOCKED
  → 审批通过：继续评估；拒绝/过期：FAILED/EXPIRED
  → 形成 GateDecision
  → 通过：路由到后继；失败：按失败路径回退
  → 记录事件/证据
```

### 4.1 适用性

- `required=true`：必须评估，不得跳过。
- `required=false`（N/A）：必须记录 N/A 理由和证据；不得静默省略。
- 仅文档变更时 G4/G5 可按 ADR-006 记 N/A；任何代码变更不得跳过 G4。
- 无可行测试时 G5 必须显式记录风险并获用户接受，不得静默跳过。

### 4.2 等待与恢复

- Gate 需要人工审批时，关联 Task/Workflow 进入 BLOCKED。
- 审批通过后恢复 Gate 评估；不得跳过未完成的自动检查。
- 审批拒绝 → Gate FAILED；Task/Workflow 按失败路径处理。
- 审批过期/失效 → Gate EXPIRED/INVALIDATED；不得使用旧批准。
- 超时/沉默不等于批准。

---

## 5. 质量门禁与 G4/G5 版本绑定

### 5.1 判定公式

质量门禁只有在以下条件全部满足时 PASSED：

```text
G4.status == PASSED
AND G5.status == PASSED
AND G4.subject_hash == G5.subject_hash
AND G4.subject_hash == current_subject_hash
AND G4/G5 evidence 完整
```

- `current_subject_hash` 是当前代码 commit SHA 或产物 hash。
- 任一条件不满足 → FAILED/BLOCKED，不得进入 deployment。
- **不得**用两个 Task 状态都是 SUCCEEDED 代替 GateDecision。
- **不得**用 Testing/Lint/Typecheck 替代独立 Code Review。
- **不得**用 Review 替代测试。

### 5.2 版本失效

1. Coding 产生新 commit/产物 → 旧 G4/G5 立即 INVALIDATED。
2. 新版本必须重新执行 G4 和 G5。
3. 只允许同一版本的 G4 AND G5 通过质量门禁。
4. 文档变更按 N/A 规则处理；代码变更不得沿用旧版本结果。

### 5.3 失败路径

| 失败 | 回退 |
|------|------|
| Review 严重问题 | coding；修复后重新 G4 |
| Review 轻微问题 | 修复后继续，或记录为用户接受的后续项；不得静默放过 |
| Testing 代码缺陷 | coding；重新 G4/G5（如代码变化） |
| Testing 需求/设计缺陷 | requirements/analysis/design |
| 生产发布前 G5 失败 | 不得继续部署 |

---

## 6. Builder Check

Builder Check 是 G2 的独立审查环节（ADR-006 §12）：

- **审查者独立**：审查者 ID 不得等于设计/执行作者 ID；作者自审不算。
- **高风险任务**：必须由独立 Agent/人类审查；不得复用执行者自我评价。
- **检查清单**：需求遗漏、设计矛盾、过度设计、安全风险、不可落地方案、异常场景。
- **结果**：`approved` / `needs_revision` / `escalated`。
- **证据**：审查者、检查项、结论、时间、关联设计产物 hash。
- **失败**：needs_revision 返回 design；escalated 进入人工决策；不得跳过。

---

## 7. Gate 证据

每个 GateDecision 至少记录：

- gate_id、task_id、workflow_id、node_id；
- subject_type/subject_hash；
- 自动检查项、结果、证据引用；
- 人工审批 ID、批准人、时间、有效期（如有）；
- 通过/失败/阻塞原因；
- 失败回退路径；
- 审计时间、actor、脱敏标记。

证据必须可追溯、追加写入；不得包含原始凭证。

---

## 8. 不变量

1. G4/G5 在所有状态下必须绑定有效 subject_hash；G6 必须绑定 subject_hash + deployment_target。
2. G4/G5 必须同一 subject hash；新版本使旧结果失效。
3. 质量门禁必须 G4 AND G5，不得用 Task SUCCEEDED 代替。
4. 生产部署必须 R3 + G6 + SA；缺一不可。
5. 非生产部署不得触发 G6。
6. G6 不得自动批准；R4 不等于 G6；SA 不替代权限检查。
7. Gate 失败不得进入下一阶段。
8. N/A 必须记录理由，不得静默跳过。
9. 审批过期/失效/已消费后不得使用。
10. GateDecision 不可原地修改。
11. 超时/沉默不等于批准。

---

## 9. 实现状态

| 能力 | 状态 |
|------|------|
| GateController / GateDecision 持久化 | 未实现（P2） |
| G4/G5 版本绑定执行 | 未实现（P2） |
| G6/R3/SA 运行时联动 | 未实现（P2/P5） |
| Gate Schema/静态测试 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 10. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [task-standard.md](./task-standard.md)
- [orchestration-state-machine.md](./orchestration-state-machine.md)
- [approval-orchestration-standard.md](./approval-orchestration-standard.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)
- [security-architecture.md](../architecture/security-architecture.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现 GateController。
