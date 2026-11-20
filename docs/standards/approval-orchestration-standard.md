# SDD Approval 编排标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** G1–G6 审批与显式安全授权（SA）在 Orchestration 中的对象、生命周期、绑定、过期、失效和拒绝处理
**权威关系：** G1–G6 规则见 [ADR-006](../decisions/ADR-006-quality-gates.md)；R0–R4 与 SA 见 [security-architecture.md](../architecture/security-architecture.md)；Gate 编排见 [gate-orchestration-standard.md](./gate-orchestration-standard.md)。

---

## 1. 审批、权限与门禁的区别

| 机制 | 回答的问题 | 权威定义 |
|------|------------|----------|
| 权限 R0–R4 | Agent 能做什么 | 安全架构 |
| 审批 G1–G6 | 阶段质量/部署是否放行 | ADR-006 |
| SA | 单次高风险操作是否获显式授权 | 安全架构 |
| Approval 对象 | 本次审批的绑定、状态、有效期和证据 | 本文件 |

**不可混淆：**

- 有权限不等于已获审批；已获审批不自动提升权限。
- G6 不是权限检查；R4 不等于 G6；SA 不替代 R3/R4 权限检查。
- 生产部署必须同时满足 R3 + G6 + SA。
- 生产数据库普通迁移按 R3；破坏性操作按 R4 + SA；只有同时涉及实际生产部署时才加 G6。
- 审批不能被批量授予，也不能跨 Task/操作/产物复用。

---

## 2. Approval 对象

| 字段 | 必需 | 说明 |
|------|------|------|
| `approval_id` | 是 | 唯一标识 |
| `task_id` / `workflow_id` / `node_id` | 是 | 绑定位置 |
| `type` | 是 | `gate` / `sa` / `both` |
| `gate` | 条件 | G1–G6；type 含 gate 时必需 |
| `operation` | 是 | 被批准的具体操作，如 `deploy_to_production` |
| `target` | 是 | 目标环境/系统/资源 |
| `environment` | 是 | dev/test/staging/prod/other |
| `risk_level` | 是 | low/medium/high/critical |
| `permission_level` | 是 | R0–R4；审批不授予权限 |
| `requested_by` | 是 | 发起者（Agent/用户/策略） |
| `requested_at` | 是 | 请求时间 |
| `reason` | 是 | 为什么需要审批 |
| `impact` | 是 | 影响范围 |
| `rollback` | 是 | 回滚/补偿方案（适用时） |
| `scope` | 是 | 操作范围/参数约束 |
| `subject_hash` | 条件 | commit/产物 hash；G4/G5/G6 相关时必需 |
| `evidence_refs` | 是 | 支持审批的证据 |
| `expires_at` | 是 | 过期时间；不得无限期 |
| `single_use` | 是 | 必须为 true |
| `status` | 是 | REQUESTED/PENDING/APPROVED/CONSUMED/REJECTED/EXPIRED/REVOKED/INVALIDATED |
| `decided_by` | 否 | 授权人/策略控制者 |
| `decided_at` | 否 | 决定时间 |
| `decision_reason` | 否 | 批准/拒绝原因 |
| `consumed_at` | 条件 | 消费时间；`status=CONSUMED` 时必需 |
| `consumed_by` | 条件 | 消费执行者；`status=CONSUMED` 时必需 |
| `consumption_ref` | 否 | 消费对应的执行/证据引用 |

### 2.1 绑定要求

Approval 必须绑定：

1. `task_id` + `workflow_id` + `node_id`；
2. `operation` + `target` + `environment`；
3. `scope`（允许的参数/路径/资源）；
4. `subject_hash`（如涉及代码/产物）；
5. 有效期；
6. 单次使用。

任何一项变化 → Approval 失效，必须重新申请。

### 2.2 Scope 与 subject_hash 语义

**Scope：**

- Approval Scope 是**完整授权范围**，不是“至少包含”范围。
- 当前模型采用**规范化后的完整 Scope 精确匹配**（排序后的 JSON 语义）；不采用无约束子集/超集授权。
- 空 Scope **不表示无限授权**：空 Scope 只能匹配空请求；**所有 `type=sa` 和 `type=both` 的 Approval 必须有非空 Scope**；`type=gate` + `gate=G6` 也必须有非空 Scope；纯操作 Approval 按既有规则。
- 请求新增参数、资源、路径、目标、扩大参数范围，均视为新范围，必须重新审批。
- Scope 缩小同样不匹配；如需缩小范围，重新申请并记录新 Scope。

**subject_hash：**

1. 如果当前操作需要代码/产物绑定，Approval 必须有非空 `subject_hash`，且与上下文完全一致。
2. Approval 有 `subject_hash` 而上下文没有/为空 → 拒绝。
3. 上下文有 `subject_hash` 而 Approval 没有/为空 → 拒绝。
4. 仅当操作明确不涉及代码/产物绑定时，双方均不提供 `subject_hash` 才允许。
5. G4/G5/G6 相关 Approval 必须提供非空 `subject_hash`。

### 2.3 时间与原子消费

- `expires_at` 和 `now` **必须存在**，且必须是带时区的合法 ISO 8601 字符串；缺失、null、空字符串、非字符串、非法日期、非法时区、无时区、解析异常均**拒绝**。
- 使用 `datetime.fromisoformat` 严格解析，统一转换为 UTC；不假设本地时间，不使用系统时间静默兜底。
- `now >= expires_at` 即视为过期；临界时刻不得使用。
- 任何 `expires_at`/`now` 校验失败都必须 **Fail-Closed**，不得跳过过期检查继续授权。
- 消费必须在**原子临界区**内验证：状态、有效期、Task、Workflow、Node、Operation、Target、Environment、Scope、subject_hash。
- 校验与消费之间不得存在重复消费窗口；并发消费只能一个成功。
- 任何检查失败都不得修改 Approval 状态、不得写 `consumed_at`/`consumed_by`。
- 本节的锁/原子性测试只代表静态校验器实现，不代表生产级分布式原子保证。

---

## 3. 发起与批准权限

| 角色 | 可以发起 | 可以批准 |
|------|----------|----------|
| Agent / Skill | 是（通过 Orchestrator/Skill 输出 `needs_approval`） | **否**（高风险不得自批） |
| Orchestrator | 是（Gate/SA 请求） | 否 |
| 授权人类 | 是 | 是（按权限/职责） |
| 策略控制器 | 是 | 是（仅限预定义策略；不得替代高风险人工） |

**规则：**

- 高风险操作（生产部署、生产数据破坏、敏感凭证）必须由授权人类批准；Agent 不得自批。
- 审查者/批准者不得同时是同一变更的执行作者（高风险任务）。
- 审批人必须能看到：操作、目标、环境、风险、影响、回滚方案、证据。
- 审批决定必须显式；超时、沉默、默认值不等于批准。

---

## 4. 生命周期

```text
REQUESTED → PENDING → APPROVED ──→ CONSUMED
                    ├── REJECTED
                    ├── EXPIRED
                    ├── REVOKED
                    └── INVALIDATED
APPROVED → EXPIRED / REVOKED / INVALIDATED
```

| 状态 | 含义 | 可执行被绑定操作 |
|------|------|------------------|
| REQUESTED | 已创建，尚未送达 | 否 |
| PENDING | 等待授权人决定 | 否 |
| APPROVED | 显式批准，绑定有效 | 是（仅绑定范围/有效期，且未消费） |
| CONSUMED | 已单次消费（终态） | 否 |
| REJECTED | 显式拒绝（终态） | 否 |
| EXPIRED | 超过有效期（终态） | 否 |
| REVOKED | 使用前被撤销（终态） | 否 |
| INVALIDATED | 任务/操作/产物/scope 变化（终态） | 否 |

- `APPROVED → CONSUMED` 必须通过原子 compare-and-set 完成；同一 Approval 只能成功消费一次。
- 并发消费只能有一个成功；其余必须返回 `already_consumed`，不得重复执行副作用。
- `CONSUMED` 是终态，不得恢复为 `APPROVED`。
- `APPROVED` 不是永久状态；使用前必须再次校验任务、scope、subject hash 和有效期。
- 状态转换详见 [orchestration-state-machine.md](./orchestration-state-machine.md)。

---

## 5. 过期与失效

### 5.1 过期

- 每个 Approval 必须有 `expires_at`；建议不超过当前节点/任务，生产操作按最小必要时间。
- 到期自动变为 EXPIRED；不得继续执行。
- 过期后需要重新申请，不得复用旧 ID。

### 5.2 失效

以下任一变化立即使 Approval INVALIDATED：

1. Task/Workflow/节点变化；
2. 操作、目标或环境变化；
3. scope 参数变化；
4. commit/产物 hash 变化；
5. 任务重新分类/复杂度/风险升级；
6. 审批被撤销；
7. 证据被证明无效。

失效后必须重新申请；不得“沿用原批准继续执行”。

---

## 6. 拒绝与阻塞

- 审批拒绝 → Approval REJECTED；Gate FAILED 或 Task/Workflow CANCELLED/BLOCKED（按策略）。
- 拒绝后不得换路径、换目标或拆分任务绕过审批。
- 未获批准时，被绑定操作必须保持 BLOCKED；不得执行。
- 审批等待期间不得执行其他等价高风险操作。
- 拒绝/过期/失效必须记录原因、actor、时间和影响。

---

## 7. 防复用与防自批

1. Approval 单次使用；消费时必须在原子临界区内重新验证状态、有效期、Task/Workflow/Node/Operation/Target/Environment/Scope/subject_hash，再从 `APPROVED` 转为 `CONSUMED`。
2. 同一 Approval 的并发消费只能有一个成功；其他请求返回 `already_consumed`，不得重复执行副作用。
3. 不得跨 Task、跨操作、跨目标、跨产物复用。
4. 不得把 G6 批准用于非部署操作；不得把 SA 当作 G6。
5. 不得把权限 lease 当作审批；不得把审批当作权限提升。
6. Agent 不得批准自己的高风险操作；不得由同一执行者自审。
7. 批量/通配审批禁止；每次高风险操作单独授权。

---

## 8. 审计与证据

每次审批记录：

- approval_id、task_id、workflow_id、node_id；
- 操作、目标、环境、风险、权限级别；
- 请求者、批准者、时间、决定、原因；
- 绑定 scope、subject_hash、有效期；
- 证据引用；
- 使用时间、使用结果、是否消费、`consumed_at`/`consumed_by`/`consumption_ref`；
- 失效/撤销原因。

审计追加写入、脱敏、不可静默修改。

---

## 9. G6 / R3 / R4 / SA 组合

| 场景 | 权限 | 审批 | 说明 |
|------|------|------|------|
| 生产部署 | R3 | G6 + SA | 缺一不可 |
| 非生产部署 | R0–R3 | 按权限模型 | 不触发 G6 |
| 生产配置变更（非部署） | R3 | SA | 不自动触发 G6 |
| 生产数据库普通迁移 | R3 | 授权/安全检查 | 不自动触发 G6；涉及部署时加 G6 |
| 生产数据库破坏性操作 | R4 | SA + 安全审查 | 涉及部署时加 G6 |
| 敏感凭证读取 | R4 | SA + 安全审查 | 不强制业务备份；禁止凭证泄漏 |
| 不可逆高危操作（非凭证） | R4 | SA + 安全审查 | 适用备份/恢复 |

- G6 不是权限检查，R4 不等于 G6，SA 不替代权限检查。
- 生产部署必须 R3 + G6 + SA 同时满足。
- 普通生产数据库迁移不得被自动升级为 R4；破坏性操作不得降级为 R3。

---

## 10. 不变量

1. 超时/沉默/默认值不等于批准。
2. Agent 不得自批高风险操作。
3. Approval 单次使用，绑定 task/operation/target/scope/subject_hash。
4. Scope 必须规范化后精确匹配；空 Scope 不是无限授权；所有 SA/both 和 G6 Approval 必须有非空 Scope。
5. subject_hash 必须双向绑定；一方缺失/为空而另一方存在时拒绝。
6. `APPROVED → CONSUMED` 只能成功一次；并发消费只能一个成功。
7. 过期/失效/已消费的 Approval 不得使用；时间比较统一为 UTC。
8. 拒绝后不得绕过。
9. 未批准时高风险操作必须 BLOCKED。
10. 审批不授予权限，不替代 R0–R4 检查。
11. G6 仅生产部署触发；非生产部署不得要求 G6。
12. 审批记录追加写入、脱敏；不得批量/通配批准高风险操作。

---

## 11. 实现状态

| 能力 | 状态 |
|------|------|
| ApprovalCoordinator / 持久化 | 未实现（P2/P5） |
| Approval 与 Gate/R3/R4/SA 联动 | 未实现（P2/P5） |
| Approval Schema/静态测试 | 本轮提供，不是 Runtime |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 12. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [task-standard.md](./task-standard.md)
- [orchestration-state-machine.md](./orchestration-state-machine.md)
- [execution-evidence-standard.md](./execution-evidence-standard.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)
- [security-architecture.md](../architecture/security-architecture.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现 ApprovalCoordinator。
