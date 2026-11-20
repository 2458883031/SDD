# SDD Analysis 标准

**状态：** P1-003-R2 Draft（待 ChatGPT 评审）
**适用范围：** Analysis Clarity 的技术分析职责、输入输出、候选方案、可行性、风险、比较、推荐和证据
**权威关系：** 通用 Skill/IO 见 [skill-standard.md](./skill-standard.md) 与 [skill-io-contract.md](./skill-io-contract.md)；Artifact/Task/Gate 见 [ADR-005](../decisions/ADR-005-task-context.md)、[task-standard.md](./task-standard.md)、[gate-orchestration-standard.md](./gate-orchestration-standard.md)；Requirements 输入见 [requirements-standard.md](./requirements-standard.md)。

---

## 1. 职责与非职责

### 1.1 职责

Analysis 将已结构化的 Requirements 转化为有证据、有边界、有风险判断的技术分析结果，为 Design 提供依据：

- 明确问题、目标、范围、约束和当前条件；
- 描述技术上下文、系统结构、依赖和环境；
- 识别候选技术方案；
- 评估可行性、风险、成本、性能、安全、维护性、扩展性和迁移影响；
- 提供可解释的方案比较；
- 形成推荐、条件、未解决风险和下一步；
- 记录事实、证据、假设和未知项；
- 为 Design 提供设计考虑，但不做最终设计。

### 1.2 非职责

Analysis **不负责**：

- 重新解释/篡改用户原始需求；
- 静默修改 Requirements Artifact；
- 将假设伪装成事实；
- 将无证据结论写成已验证事实；
- 确定最终系统架构；
- 输出正式 Design Artifact；
- 输出正式 implementation-plan；
- 代替 Planning 拆解任务；
- 代替 G2/G3 审批；
- 伪造用户确认、GateDecision 或 Approval；
- 执行代码/数据库/部署操作。

**推荐方案不是设计批准。** 最终设计选择由 Design 活动完成。

### 1.3 Analysis vs Design

| Analysis | Design |
|----------|--------|
| 分析候选方案 | 确定最终设计方案 |
| 比较技术路径 | 定义系统架构 |
| 识别技术风险 | 制定设计级风险控制 |
| 评估可行性 | 输出设计规格 |
| 提出推荐 | 正式确定设计决策 |
| 标记未知/待验证 | 将已确认事项纳入设计 |
| 不产生 implementation-plan | 不产生正式 implementation-plan |

---

## 2. 适用与不适用

**适用：**

- 需求已结构化，需评估技术可行性和方案；
- 需求与现有系统存在差异/影响；
- 需要多方案比较、风险/成本/性能/安全分析；
- 需要为 Design 提供依据和推荐；
- 需求变更需要重新评估影响。

**可裁剪/不适用：**

- 需求仍存在阻塞性未决项：先返回 `needs_input`/`blocked`，不输出可进入 Design 的完整结论；
- 纯咨询且不需要技术方案：可用 consultation 流程；
- 简单局部修改：可只做轻量影响/风险分析；
- 设计已确定：不重复做完整 Analysis；仍可记录验证证据。

不得为了流程完整而编造候选方案或分析结论。

---

## 3. 输入契约

遵循 `skills/analysis/schemas/input.schema.json`：

| 字段 | 必需 | 说明 |
|------|------|------|
| `requirements_ref` | 是 | Requirements Artifact 引用（path/version/sha256/type=requirements） |
| `requirements` | 否 | 已解析的 Requirements `data.requirements`；由校验器复用 requirements-clarity/output.schema.json 校验 |
| `project_context` | 否 | 项目上下文摘要 |
| `technical_context` | 否 | 已知技术环境摘要；缺失项在分析中标记 unknown |
| `constraints` | 否 | 调用方补充约束 |
| `existing_analysis` | 否 | 已有分析 Artifact 引用 |
| `evidence_refs` | 否 | 外部证据引用 |
| `change_context` | 否 | 变更原因、变更项、上一版 Requirements 引用 |
| `requested_scope` | 否 | 本次分析范围 |

**输入状态判断：**

- 输入缺失/结构无效 → `failed`/`input_invalid`；
- Requirements 存在 blocking open question/unknown 或未解决冲突 → `needs_input`/`blocked`，不得输出完整可进入 Design 的 `ok`；
- 关键约束/外部依赖不足 → 标记 unknown/assumption，降低结论置信度；
- 上游 Artifact 引用不一致 → `blocked`，不得自行猜测版本；
- 不得仅凭字段存在就认定输入有效。

---

## 4. 输出契约

复用 P1-001 五状态 Envelope：

```json
{
  "status": "ok | needs_input | needs_approval | blocked | failed",
  "data": {},
  "artifacts": [],
  "errors": [],
  "evidence": []
}
```

`data.analysis` 主要包括：

| 字段 | 说明 |
|------|------|
| `analysis_id` / `analysis_version` | 分析标识与 SemVer |
| `source_requirements_ref` | 来源 Requirements Artifact 引用 |
| `source_requirements_version` | 来源需求版本（如提供） |
| `source_refs` | 分析证据/来源引用 |
| `problem_statement` | 问题、目标、范围、非目标、约束、已知条件 |
| `technical_context` | 技术栈、结构、外部系统、依赖、数据/运行环境、限制、未知 |
| `candidate_solutions` | 候选方案数组 |
| `feasibility_assessment` | 可行性评估 |
| `risk_assessment` | 风险清单 |
| `comparison_matrix` | 方案比较矩阵 |
| `recommendation` | 推荐方案、依据、权衡、未解决风险、条件 |
| `facts` | user_stated/evidence_backed 事实 |
| `assumptions` | unconfirmed 假设 |
| `unknowns` | 未知项 |
| `requirements_traceability` | 上游 Requirements 关键条目的处理/追踪关系 |
| `next_steps` | blocking/non-blocking 问题、证据需求、验证任务、设计考虑 |
| `single_solution_rationale` | 仅单一候选方案时解释其他方案为何不适用 |

**禁止字段：**

- `implementation_plan`、`design_spec`（Analysis 不输出正式计划/设计）；
- `design_approved`、`gate_approved`、`confirmation_ref`（推荐不等于审批/确认）；
- 任何伪造的 G2/用户确认字段。

**`status=ok` 语义：**

- 分析完成且无 blocking 未决项；
- **不表示 Design 已批准、G2 已通过、用户已确认**；
- 推荐不等于设计决策。

### 4.1 Requirements Traceability

Analysis 不得静默丢弃 Requirements 的关键信息。`requirements_traceability.items` 必须为上游关键条目建立处理关系：

| 上游类型 | `source_type` | `source_id` |
|----------|---------------|-------------|
| FR | `functional_requirement` | FR ID |
| NFR | `non_functional_requirement` | NFR ID |
| 约束 | `constraint` | 约束文本 |
| 依赖 | `dependency` | DEP ID |
| 假设 | `assumption` | ASM ID |
| 未知项 | `unknown` | UNK ID |
| 未决问题 | `open_question` | Q ID |
| 验收标准 | `acceptance_criterion` | AC ID 或标准文本 |
| 非目标 | `non_goal` | 非目标文本 |
| 来源引用 | `source_ref` | `path@version#sha256` |

`disposition`：

- `analyzed`：已纳入技术分析；必须提供可解析的 `analysis_refs`（候选方案/风险/设计考虑/技术上下文/问题/可行性/比较维度），不能只加标签；
- `mapped`：已映射到候选方案/风险/设计考虑，必须提供 `analysis_refs`；
- `retained`：保留为假设/未知项/问题/非目标等，必须能在实际 Analysis 输出中找到对应内容；Acceptance Criterion retained 时必须在 `next_steps.design_considerations` 中提供 `AC-<id>: <非空 consideration>`，单独的 `AC-<id>`、空考虑或其他 AC 的考虑均不合格；
- `resolved`：已解决，必须提供 `resolution_evidence_refs`，且引用必须包含不可变 SHA-256（如 `path@version#sha256` 或裸 sha256），只能来自事实 `evidence_refs`、候选方案 `evidence_refs` 或风险 `evidence_refs`；`source_requirements_ref`、普通 `source_refs` 登记、纯 path、`user_stated`/`assumption` statement 均不得充当解决证据；Artifact 身份以 SHA-256 为准，不得通过更换 path 绕过；
- `not_applicable` / `deferred`：不适用/延后，必须提供非空 `rationale`。

规则：

1. 不要求机械复制上游内容；只要求逐项建立处理关系。
2. 不适用/延后必须解释原因；不得静默删除。
3. `mapped` 的 `analysis_refs` 必须指向存在的候选方案、风险或设计考虑。
4. `retained` 必须闭环到实际输出：Unknown→`analysis.unknowns`，Assumption→`analysis.assumptions`，Non-goal→`problem_statement.non_goals`，Open Question→`next_steps` 的对应问题，Acceptance Criterion→`next_steps.design_considerations` 的 `AC-<id>: <非空 consideration>`，Constraint/Dependency 等→对应上下文/分析结果。
5. `resolved` 的证据只接受事实/候选/风险中的显式 evidence_refs，且必须包含不可变 SHA-256；`source_requirements_ref`、普通 source_refs 登记、纯 path、`user_stated`/`assumption` 的普通陈述不得作为解决证据。Artifact 身份以 SHA-256 判定，相同 SHA 的不同 path/目录/文件名仍是同一 Artifact。
6. Requirements Artifact 不被修改；Analysis 不是第二个 Requirements 生产者。
7. 只做最小追踪，不引入新的全局 Artifact 类型或状态机。

---

## 5. Problem Statement

必须包含：

- `description`：问题是什么；
- `goal`：分析目标；
- `scope`：本次分析范围；
- `non_goals`：明确不分析的内容；
- `constraints`：来自 Requirements/项目的关键约束；
- `known_conditions`：已知环境/前提。

不得扩大需求范围；发现需求问题时记录并回指 Requirements，不自行修改上游。

---

## 6. Technical Context

至少考虑：

- 技术栈；
- 当前系统结构；
- 外部系统；
- 技术依赖；
- 数据环境；
- 运行环境；
- 已知技术限制；
- 信息缺失（unknown）。

未提供的信息必须标记 unknown，不得自行补齐为事实。

---

## 7. Candidate Solutions

每个候选方案包含：

- `solution_id`、`name`、`description`、`approach`；
- `applicable_requirements`（FR/NFR ID）；
- `prerequisites`、`advantages`、`disadvantages`；
- `technical_complexity`（low/medium/high/unknown）；
- `implementation_cost_estimate`、`operational_cost_estimate`（estimate/basis/confidence）；
- `performance_impact`、`security_impact`、`maintainability`、`scalability`、`migration_impact`、`compatibility_impact`（low/medium/high/unknown）；
- `dependencies`、`risks`（RISK-*）、`evidence_refs`、`assumptions`、`unknowns`。

规则：

1. 不机械要求三个候选；只有一个合理方案时，必须用 `single_solution_rationale` 解释其他方案为何不适用/不可行。
2. 不得为满足数量编造候选方案。
3. 成本/性能/复杂度估计必须说明依据和置信度，不得伪装成精确事实。
4. 无证据比较不得写成客观测量。

---

## 8. Feasibility Assessment

至少覆盖以下领域（按实际适用性填写）：

- technical；resource；compatibility；performance；security；operations；data_migration；external_dependencies；delivery。

每项包含：

- `assessment`、`status`（feasible/conditionally_feasible/infeasible/unknown）；
- `evidence_refs`、`assumptions`、`unknowns`、`rationale`。

---

## 9. Risk Assessment

每个风险包含：

- `risk_id`、`description`、`category`；
- `likelihood`、`impact`、`severity`、`severity_basis`；
- `mitigation`、`residual_risk`、`evidence_refs`、`owner`、`status`（known/suspected/not_assessed）。

不得把风险等级写成经过量化评估，除非有依据；无依据的风险标记 `unknown`/`suspected`。

---

## 10. Comparison Matrix

比较矩阵包含：

- `method`：比较方法；
- `weighted`：是否加权；
- `weight_basis`：权重来源（加权时必需）；
- `dimensions`：维度、权重、评分；
- `comparison_summary`。

每个评分包含：

- `solution_id`、`score`（0–5 或 null）、`not_applicable`；
- `basis`、`confidence`（low/medium/high/unknown）。

规则：

- 加权评分必须明确权重来源/方法；不得把主观评分伪装成精确结论。
- 评分必须引用存在的 solution_id；不适用项使用 `not_applicable=true` 且 score 为 null。
- 比较结果必须可解释，不得只给总分。

---

## 11. Recommendation

推荐包含：

- `recommended_solution_id`；
- `recommendation_summary`、`rationale`；
- `trade_offs`、`unresolved_risks`、`conditions`；
- `evidence_refs`、`confidence`；
- `recommendation_status`（recommended/conditionally_recommended/no_recommendation）。

**必须明确：**

- 推荐不等于设计批准；不得输出 `design_approved`/G2 Approval/confirmation_ref。
- 推荐方案必须存在于 `candidate_solutions`；未解决风险必须存在于 `risk_assessment`。
- 推荐必须说明条件、置信度和未解决风险。

---

## 12. 事实、证据和假设

沿用 R1 分类：

| 类型 | 规则 |
|------|------|
| `user_stated` | 用户明确提供，可记录为事实 |
| `evidence_backed` | 有可核验证据，必须有 evidence_refs |
| `assumption` | 只能 `unconfirmed`；不得当作事实 |
| `unknown` | 必须标记 `status=unknown`；不得伪造为已验证 |

- 不得引用不存在/不可核验的证据。
- 不得静默删除 Requirements 的关键约束、依赖、未知项、验收标准。
- 发现上游需求问题应记录并回指，不修改上游。
- 证据不足时降低 confidence，不编造依据。

---

## 13. 状态和完成条件

沿用五状态 Envelope，不新增通用状态机。

| 状态 | 含义 | 进入 Design？ |
|------|------|----------------|
| `needs_input` | 输入不足/需澄清 | 否 |
| `blocked` | 阻塞问题/上游冲突 | 否 |
| `needs_approval` | 需要 G/SA 审批建议 | 否，等待审批 |
| `failed` | 分析执行失败 | 否 |
| `ok` | 分析完成、无 blocking 未决项 | 可进入 Design 评估，但不代表 G2 通过/设计批准 |

- Skill 执行成功不等于分析结论正确。
- Analysis 完成不等于 Design 已批准、G2 通过或用户确认。
- `status=ok` 不得包含 blocking 问题/未知项或未解决冲突；可包含非阻塞问题。
- 部分分析结果允许在 `needs_input`/`blocked` 中返回，但必须明确阻塞原因和需补充信息。
- 只要输出包含 `data.analysis`，`source_requirements_ref` 必须与输入 `requirements_ref` 完全一致；`ok`、`needs_input`、`needs_approval`、`blocked`、含分析产物的 `failed` 都适用。
- `status=ok` 的 `artifacts` 至少包含一个 `type=analysis` 的 Artifact；不得用 `source_refs` 替代。部分分析可以按实际产物决定是否生成 Artifact，但不得伪造完成的分析 Artifact。

---

## 14. Artifact 和版本引用

- Analysis 输出是独立 `type=analysis` Artifact。
- `source_requirements_ref` 必须引用 Requirements Artifact（path/version/sha256/type=requirements）。
- `source_requirements_version` 可选记录需求版本；`source_refs` 记录证据来源。
- Requirements 版本变化时，Analysis 应重新评估适用性；本阶段**不实现**自动失效 Runtime。
- 不创建新 Artifact 类型体系；复用 ADR-005 `requirements/analysis/design/plan/report`。
- ADR-009 Proposed 的 G1/G2/G3 Artifact binding 仍为提案；本 Skill 不实现 GateDecision/Approval。
- 不得伪造 G1/G2/G3 结果。

---

## 15. 安全与权限

- Analysis 默认 R0 读取、R1 写分析产物；不执行代码修改/数据库/部署。
- 不读取生产凭证/敏感数据；分析证据不得包含原始 Token/密码/私钥。
- 涉及安全/权限风险时记录风险和建议；不重新定义 R0–R4/SA。
- 不得通过分析输出构造审批绕过路径。
- 平台能力未实测时保持 Unknown/Assumed，不得写 Verified。

---

## 16. 异常处理

| 情况 | 处理 |
|------|------|
| Requirements 引用缺失/无效 | `failed`/`blocked` |
| Requirements 存在 blocking 未决项 | `needs_input`/`blocked` + 部分分析 |
| 候选方案不足/无法比较 | `needs_input` 或明确 `unknown`，不编造 |
| 推荐方案不存在 | `failed`/`needs_input`，不得伪造 |
| 证据不足 | 降低 confidence，标记 unknown/assumption |
| 成本/风险无法估计 | `unknown` + 依据/不确定性 |
| 需要 G/SA 审批 | 返回 `needs_approval` 建议，不自行批准 |
| 超时 | Orchestration 处理；Skill 返回 timeout 错误 |

---

## 17. 验收标准和测试要求

R2 至少验证：

1. 输入/输出 Schema Draft 2020-12；状态相关 data。
2. 多候选比较、单一方案解释。
3. 可行性覆盖领域。
4. 风险字段完整、severity_basis。
5. 比较矩阵 solution_id/权重/评分依据/置信度。
6. 推荐引用存在、推荐≠设计批准。
7. 事实/假设/unknown 区分；evidence-backed 有证据；unknown 不得 verified。
8. 上游 Requirements 约束/未决项不被静默丢弃。
9. 阻塞输入不得返回可进入 Design 的 `ok`。
10. 禁止 implementation_plan/design_spec/design_approved/gate_approved/confirmation_ref。
11. Artifact version/hash/source。
12. Requirements traceability：FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/acceptance_criteria/non_goals/source_refs 不缺项，不适用/延后有理由。
13. 所有含 `data.analysis` 的状态执行来源绑定；`ok` 必须有 analysis Artifact。
14. R1/P1-001/P1-002 回归；链接/JSON/YAML/重复键。

**运行时状态：** `runtime_behavior = NOT_EXECUTED`。本文件是标准与静态契约，不代表 Analysis Runtime 已实现。

---

## 18. 相关标准

- [requirements-standard.md](./requirements-standard.md)
- [skill-standard.md](./skill-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [skill-security-standard.md](./skill-security-standard.md)
- [skill-versioning-standard.md](./skill-versioning-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)
- [ADR-009](../decisions/ADR-009-predevelopment-artifact-binding.md)（Proposed）

---

**P1-003-R2 状态：** Analysis 标准 Draft；Runtime 未实现。
