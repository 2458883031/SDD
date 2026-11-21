# SDD P1-003-R3-R0 Design Skill 实施计划

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-003-R3-R0 |
| 分支 | `feature/p1-003-r2-analysis` |
| 授权基线 | `7c57ecbc1d970f1f2757427e3b115d9338ad849c` |
| main / origin/main | `50df231d2de15b4dc33407798cce36f7d2178ee5` |
| 当前 HEAD | `7c57ecbc1d970f1f2757427e3b115d9338ad849c` |
| 日期 | 2026-11-21 |
| 本轮性质 | 规划报告；**不实施 Design Skill、不启动 R1** |
| 当前状态 | **P1-003-R3-R0 COMPLETE；R3 Design 实施 NOT STARTED；ADR-009 PROPOSED / NOT ACCEPTED** |

> 本计划基于 [差异分析报告](./2026-11-21-P1-003-R3-R0-difference-analysis.md) 的实际盘点结果。所有阶段只在 ChatGPT 评审通过后逐段启动。

---

## 一、R3 目标

在复用 P1-001 Skill/IO、ADR-005 Artifact、P1-002 Task/Workflow/Gate/Approval/Evidence、ADR-006 G2 和现有 Requirements/Analysis 契约的前提下，建立一个**静态、可审查、可追溯的 Design 参考 Skill**：

1. 明确 Design 的职责、非职责和上下游边界；
2. 定义 Design Input/Output 契约与 Schema；
3. 定义设计规格、决策、备选方案、追踪、风险、unknown 和变更影响；
4. 输出 `type=design` Artifact，并能被 G2/Builder Check 审查；
5. 明确 Design 不输出正式 implementation-plan，Planning 属于 Orchestration；
6. 为后续 Coding/Review/Testing 提供设计符合性基准；
7. 不新增并行状态机、Gate、Approval、Evidence 或平台机制。

**R3 不包含：** GateController、Planning Runtime、Coding/Testing Skill、平台适配、自动 Artifact 失效、ADR-009 接受或 ADR-006 修改。

---

## 二、设计原则

1. **复用优先**：统一信封、artifactRef、R0–R4、G1–G6、Task/Gate/Approval 全部复用，不重造。
2. **设计规格而非实现**：Design 输出技术栈无关的架构/接口/数据/状态/失败/安全/性能/测试策略约束；不输出最终代码、任务拆解或排期。
3. **推荐不等于决定**：Analysis 推荐是输入，不是强制决定；Design 可选择其他方案，但必须有理由和证据。
4. **决策可追溯**：每个关键设计决策记录备选方案、理由、后果和关联需求/分析条目。
5. **不静默遗漏**：不适用/延后必须记录理由；blocking 未决项不得 `ok`。
6. **G2 分离**：Design 完成不等于 G2 通过；Design 不写 GateDecision/Approval，不自批。
7. **Planning 分离**：Design 不输出 `implementation_plan`；Planning 由 Orchestration 内部活动产生，G3 审查/批准 plan。
8. **按复杂度裁剪**：L1/L2/L3 使用不同设计深度；Design 不能自行降低复杂度。
9. **静态优先**：R3 只交付标准、Schema、示例和静态测试；Runtime 明确未实现。

---

## 三、Design Skill 职责

### 3.1 负责

- 读取 Requirements Artifact 和 Analysis Artifact，校验引用类型/版本/SHA-256；
- 将已确认需求和分析结论转化为可实施、可验证的设计规格；
- 选择最终技术方案，并记录与 Analysis 推荐的一致/偏离理由；
- 定义架构、组件/模块、接口、数据模型/数据流、状态转换、失败路径、安全边界、性能/容量、迁移/回滚；
- 定义测试策略和验收标准到设计的追踪；
- 记录设计决策、备选方案、风险、假设、unknown、open questions；
- 输出 `type=design` Artifact；
- 为 G2/Builder Check、Coding、Code Review、Testing 提供结构化依据；
- 对缺失输入返回 `needs_input`/`blocked`，对执行错误返回 `failed`。

### 3.2 不负责

- 重新定义/改写 Requirements；
- 代替 Analysis 做候选比较/可行性调查；
- 输出正式 implementation-plan、任务拆解、排期或负责人分配；
- 批准 G1/G2/G3/SA 或写 GateDecision/Approval；
- 输出 `design_approved`、`gate_approved`、`confirmation_ref`；
- 代替 Coding 写最终实现，或代替技术栈 Skill 决定框架/库实现细节；
- 代替 Code Review（G4）或 Testing（G5）；
- 自行降低任务复杂度；
- 自行更新 ADR、P0/P1 已验收规则或其他 Skill；
- 执行 Shell/数据库/部署/生产操作。

---

## 四、Design Artifact 建议

### 4.1 Artifact 身份

- 复用 ADR-005 `type=design`，不新增 Artifact 类型。
- Skill 在统一信封 `artifacts` 中输出 `{path, version, sha256, type=design}`。
- `source`/`source_refs` 记录 Requirements、Analysis 和其他证据的版本+sha256。
- `design_version` 是设计内容版本（建议 SemVer）；Artifact `version` 仍是 ADR-005 的整数版本，两者不混用。
- `status=ok` 至少包含一个 `type=design` Artifact；不得用 `source_refs` 替代。
- 旧设计版本按 ADR-005 标记 `superseded`；本 Skill 不直接修改历史 Artifact。

### 4.2 字段分层

| 分层 | 内容 |
|------|------|
| **Required** | `design_id`、`design_version`、`created_at`、`source_requirements_ref`、`source_analysis_ref`、`design_summary`、`decisions`、`architecture_overview`、`test_strategy`、`requirements_traceability`、`risks`、`assumptions`、`unknowns`、`open_questions` |
| **Conditional Required** | `selected_solution`/`alternatives`（有方案选择/偏离推荐时）、`components`/`modules`（新模块或跨模块）、`interfaces`（接口变化）、`data_models`/`data_flows`（数据变化）、`state_model`（有状态变化）、`failure_handling`（外部依赖/失败路径）、`security_design`（安全敏感/信任边界）、`performance_scalability`（性能/容量 NFR）、`migration_rollback`（数据/接口/生产架构变更）、`analysis_traceability`（有 Analysis 时）、`design_change_impact`（变更设计时） |
| **Optional** | `implementation_constraints`、图表、ADR 链接、可观测性/运维细节、补充 references |
| **Not Applicable** | 对不适用的条件字段记录 `not_applicable` + 理由，不得静默省略 |

### 4.3 设计决策结构建议

每个决策至少记录：

- `decision_id`；
- `decision`（决定了什么）；
- `rationale`（理由/证据）；
- `alternatives_considered`（至少记录未选方案及不选原因）；
- `related_requirements`（FR/NFR/constraint ID）；
- `related_analysis`（候选/风险/unknown/design consideration ID）；
- `consequences`（对实现、测试、运维、安全、性能的影响）；
- `deviation_from_recommendation`（如偏离 Analysis 推荐，记录理由与证据）。

**约束：**

- 推荐方案不是强制决定；
- Design 选择 Analysis 未列出的新方案时，必须提供 `new_solution_rationale` 和证据，或返回 `needs_input`；
- 不得用 Design 决策字段写 G2 审批结果。

### 4.4 Requirements/Analysis 追踪

**Requirements traceability** 建议覆盖：

- `functional_requirement`；
- `non_functional_requirement`；
- `constraint`；
- `dependency`；
- `assumption`；
- `unknown`；
- `open_question`；
- `acceptance_criterion`；
- `non_goal`；
- `source_ref`。

每个条目的 disposition 建议：

- `designed`：映射到组件/接口/数据/状态/安全/测试策略等设计元素；
- `mapped`：映射到决策/风险/验证方法；
- `retained`：保留为设计假设/unknown/open question/非目标，必须闭环到实际输出；
- `resolved`：已由设计决策/证据解决，必须有规范 Artifact 证据（沿用 R2 的严格 SHA-256 引用规则，不另造宽松规则）；
- `not_applicable` / `deferred`：必须给理由。

**Analysis traceability** 建议覆盖候选方案、风险、unknowns/open questions、design considerations；Design 必须说明承接、偏离或拒绝理由。

---

## 五、Schema 规划

### 5.1 Input Schema

建议 `skills/design/schemas/input.schema.json`：

**Required：**

- `requirements_ref`：ADR-005 artifactRef，`type=requirements`；
- `analysis_ref`：ADR-005 artifactRef，`type=analysis`。

**Optional：**

- `requirements`：已解析的 Requirements `data.requirements`（复用 Requirements Schema，不复制第二套）；
- `analysis`：已解析的 Analysis `data.analysis`（复用 Analysis Schema，不复制第二套）；
- `project_context`；
- `constraints`；
- `existing_design`（Artifact 引用数组）；
- `evidence_refs`；
- `change_context`；
- `complexity`（L1/L2/L3，由 Orchestration 提供；Design 不自行判定/降低）；
- `requested_scope`。

**校验规则：**

- `requirements_ref.type == requirements`；
- `analysis_ref.type == analysis`；
- 若同时提供 Requirements/Analysis 内容，其内部 `source_requirements_ref` 必须与 `requirements_ref` 一致；
- 不得通过“最新版本”隐式选取；
- 不包含平台专属字段或凭证。

### 5.2 Output Schema

建议 `skills/design/schemas/output.schema.json`：

- 统一五状态信封；
- `ok` 要求 `data.design` 达到最低完整度；
- `needs_input` 要求 `questions` + 可带部分 design；
- `needs_approval` 要求 `approval_request` + 可带部分 design，但不得表示 G2；
- `blocked` 要求 `blocked_reason` + 可带部分 design；
- `failed` 至少一个 error，不得强制完整 design；
- `data.design` 使用 Required/Conditional Required/Optional 分层；
- 禁止字段：`implementation_plan`、`design_approved`、`gate_approved`、`confirmation_ref`、`gate_decision`、`approval`、`code_review_approved`、`testing_approved`。

### 5.3 Schema 交付判断

| Schema/配套 | 建议 | 理由 |
|-------------|------|------|
| Design Input Schema | 必须 | 绑定 Requirements/Analysis Artifact 类型与 hash |
| Design Output Schema | 必须 | 状态相关 data、禁止伪造 G2 |
| 新 Artifact 类型 Schema | 不需要 | ADR-005 已有 `design` |
| 新 Gate/Approval Schema | 不需要 | P1-002 已有通用 Schema；G2 专项扩展属 R4 |
| Design Examples | 必须 | L1/L2/L3/partial/negative |
| Design Checklist | 必须 | G2/Builder Check 可操作化 |
| Design Validator | 必须 | 静态 Schema/语义/回归 |
| Design Invalid Cases | 必须 | 防止伪造审批、缺追踪、无理由决策 |

---

## 六、状态语义

| 状态 | 使用条件 | 禁止 |
|------|----------|------|
| `ok` | 设计达到最低完整度；无 blocking 未决项；Required 完整；Conditional 有内容或 N/A 理由 | 不得写 `design_approved`/`gate_approved`/`confirmation_ref`；不得表示 G2 |
| `needs_input` | 缺需求/分析信息；设计选择需用户确认；关键 unknown/open question | 不得输出“完整可实施设计”或伪造确认 |
| `needs_approval` | 具体设计决策/安全事项需要显式人工批准后才能定稿 | 不得表示 G2 已通过；不得自批；不得写 GateDecision |
| `blocked` | 缺上游 Artifact/权限/环境/外部依赖；上游 blocking 未关闭 | 不得编造设计或跳过依赖 |
| `failed` | 输入无效、内部错误、无法生成设计 | 不得伪装 `ok`；不得强制完整 design |

**三层状态分离：**

1. Skill `status`：本次执行结果；
2. Artifact `status`：draft/approved/superseded（ADR-005）；
3. Gate `status`：PENDING/PASSED/FAILED 等（ADR-006/P1-002）。

Design Skill 只负责第 1 层并输出第 2 层的引用；G2/Gate 由 Orchestration 负责。

---

## 七、复杂度与设计深度

复用 P1-002 L1/L2/L3，不按代码行数判断。Orchestration 拥有分类权；Design 只能建议升级，不能降低。

| 等级 | 设计深度 |
|------|----------|
| L1 | 轻量设计说明：受影响组件/接口/数据、至少一个决策、AC 验证方法、风险/unknown；可省略完整架构章节，但 N/A 必须记录 |
| L2 | 架构概览、组件职责、接口/数据（如变化）、失败处理、安全边界、测试策略、决策/备选、追踪 |
| L3 | L2 + 完整架构/数据流/状态转换、安全/信任边界、性能/容量、迁移/回滚、运维/可观测、偏离推荐理由、变更影响、完整追踪 |

**必须升级：** 系统/跨系统影响、架构变更、数据模型/迁移、认证/授权/加密、外部服务/API、不可逆/高风险、关键未知、多模块/多团队。

**降级：** 仅当局部、可逆、无接口/数据/安全变化且有证据；必须由 Orchestration 确认并记录；Design 不得自行降级。

---

## 八、上下游交接契约

### 8.1 Requirements → Design

- 输入 `requirements_ref` 必须为 `type=requirements`，记录 path/version/sha256；
- Design 不重写需求；追踪 FR/NFR/constraints/dependencies/assumptions/unknowns/open questions/AC/non_goals/source_refs；
- blocking 未决项不得 `ok`；
- 需求变化时生成新 Design 版本，旧版本按 ADR-005 `superseded`；G2 失效规则依赖 ADR-009（Proposed），R3 不宣称已生效；
- 不得无依据增加设计目标。

### 8.2 Analysis → Design

- 输入 `analysis_ref` 必须为 `type=analysis`；
- Analysis 推荐不等于设计决定；Design 可选择其他方案，但必须记录理由、证据和重新评估条件；
- Analysis 的候选、风险、unknowns、design considerations 必须有承接/偏离说明；
- Analysis 的 blocking unknown/open question 不得被 Design 静默忽略；
- Analysis 新版本使旧 Design 需重新评估；具体自动失效属 R4/Runtime。

### 8.3 Design → Planning

- Design 输出 `type=design` Artifact，不输出 `implementation_plan`；
- Planning 由 Orchestration 内部活动执行，消费 Requirements/Analysis/Design，生成 `type=plan` Artifact；
- G3 检查/批准 plan，不生成 plan；
- 当前 P1-002 `feature-development.yaml` 在 G2 后直接 G3，没有 plan 节点/生产者；该缺口**不在 R3 修改**，由 R4 处理；
- R3 只在 Design 标准中明确交接边界，不实现 Planning。

### 8.4 Design → Coding

Design 应提供：

- 组件/模块 ID、职责、依赖方向；
- 接口契约（输入/输出/错误/版本/兼容性）；
- 数据模型/数据流/敏感数据；
- 状态与转换、失败/重试/补偿/降级；
- 安全/信任边界和 R0–R4/SA 约束；
- 性能/容量约束；
- AC → 验证方法；
- `implementation_constraints`（技术栈边界，不写完整实现）。

Coding 遇到设计缺失时必须反馈/返回 `needs_input`，不得自行做出重大架构决策。Coding Skill 尚未实现，R3 只定义 handoff 契约。

### 8.5 Design → Review / Testing

- Code Review 使用组件/接口/数据/决策/约束作为设计符合性基准；
- Testing 使用 `test_strategy` 和 AC 映射设计测试；
- Design 的 test strategy 不是测试结果，不产生 G5 证据；
- Design 不替代 G4/G5，不写 `code_review_approved`/`testing_approved`；
- Design 变更应说明对现有代码/测试/部署的下游影响。

---

## 九、G2 与 Builder Check 边界

### 9.1 当前规则

- ADR-006 §4 是 G2 权威规则；
- `gate-orchestration-standard.md §3/§6` 定义挂载与 Builder Check；
- GateDecision Schema 通用 `subject_hash`；G2 PASSED 至少需要非空 subject_hash，但不强制 Design path/version/type；
- Approval Schema 只强制 G4/G5/G6 的 subject_hash；
- 没有 G2 专项示例或 Design 语义测试；
- ADR-009 Proposed 才要求 G2 绑定 Design Artifact path/version/sha256 和失效链。

### 9.2 R3 范围

- Design 输出可供 G2 审查的结构化设计；
- Checklist 覆盖 ADR-006 G2 自动检查：设计文档、架构影响、接口/数据模型、安全、备选方案、可测试性、回滚/迁移；
- 支持 Builder Check 独立审查所需证据：设计 Artifact hash、检查项、决策/备选、风险/异常场景；
- 不实现 G2 审批、GateDecision、Approval 或自动失效。

### 9.3 R4 范围

- 若 ADR-009 被接受，扩展 GateDecision/Approval 的 Design Artifact binding；
- 增加 G2 静态示例/测试；
- 处理 Design 新版本失效 G2/G3；
- 关闭 Planning/plan 生产者缺口；
- 更新 P1-002 Workflow 示例（需另行授权）。

---

## 十、阶段实施计划

> 每个阶段单独提交；前一阶段通过 ChatGPT 评审后才启动下一阶段。R0 本报告不启动任何阶段。

### R1：Design Standard / 职责边界 / 完整度标准

**范围：**

- `docs/standards/design-standard.md`（新）；
- 职责/非职责、输入双引用、输出字段分层、状态语义、复杂度、G2/Planning/Coding/Review/Testing 边界；
- 统一 Skill 路径建议（`skills/design/`，不修改 P0）。

**交付物：**

- Design 标准文档；
- 设计完整度与 N/A 记录规则；
- 决策/备选/偏离推荐规则；
- G2 检查项映射表；
- Design → Planning 不输出 plan 的明确约束。

**验证：**

- 与 ADR-005/ADR-006/P1-001/P1-002/R1/R2 交叉引用；
- Markdown 链接/围栏；
- 不得宣称 G2 binding 已生效或 Runtime 已实现。

**Git：** 单独提交 + 阶段报告；不修改既有标准。

### R2：Design Skill / Input / Output / Schema

**范围：**

- `skills/design/SKILL.md`；
- `skills/design/skill.yaml`；
- `skills/design/schemas/input.schema.json`；
- `skills/design/schemas/output.schema.json`。

**交付物：**

- 五状态 Skill；
- Requirements/Analysis 双引用输入；
- `type=design` Artifact 输出；
- Required/Conditional/Optional/N/A 字段；
- 禁止伪造 G2/Plan 字段；
- 版本/依赖声明。

**验证：**

- Draft 2020-12 Schema 自检；
- 最小正/负向实例；
- Artifact type/path/version/sha256；
- 无 `implementation_plan`/`design_approved`/GateDecision/Approval。

**Git：** 单独提交 + 阶段报告。

### R3：Examples / Checklist / Invalid Cases

**范围：**

- `skills/design/examples/`；
- `skills/design/references/design-checklist.md`；
- `skills/design/tests/cases.yaml`；
- `skills/design/tests/invalid-cases.yaml`。

**交付物：**

- L1 轻量、L2 标准、L3 完整示例；
- `needs_input`/`blocked`/`failed` 部分输出示例；
- 需求/分析追踪示例；
- 决策/备选/偏离推荐示例；
- G2/Builder Check checklist；
- 缺输入、错 Artifact 类型、缺追踪、无理由决策、伪造 G2、输出 plan 等 invalid cases。

**验证：**

- 示例通过 Output Schema；
- invalid cases 被拒绝；
- 链接/围栏/JSON/YAML；
- 不执行 Runtime。

**Git：** 单独提交 + 阶段报告。

### R4：Validator / Tests / 质量验证

**范围：**

- `tests/unit/design/validate_design_skill.py`；
- `tests/unit/design/requirements.txt`；
- 完整正/负向静态测试。

**交付物：**

- Schema 校验；
- 状态条件测试；
- Artifact 绑定/类型测试；
- Requirements/Analysis 追踪测试；
- 决策/备选/偏离测试；
- 禁止字段测试；
- 复杂度/设计深度测试；
- 全量回归（P1-001/R1/R2/P1-002）。

**验证：**

- Analysis/R1/P1-002 validator 全部通过；
- 全仓 JSON/YAML、重复键、Markdown、SemVer、diff check；
- `runtime_behavior=NOT_EXECUTED`。

**Git：** 单独提交 + 阶段报告。

### R5：跨模块契约与 G2 / ADR-009 兼容性审查

**范围：**

- 审查 Design ↔ Requirements/Analysis/Planning/Coding/Review/Testing 契约；
- 审查 G2 Builder Check 与 Design 字段映射；
- 审查 ADR-009 Proposed 的影响；
- 产出集成差距/变更提案报告，不直接修改 P1-002/ADR-006/ADR-009。

**交付物：**

- 跨模块契约差距清单；
- G2/G3 集成建议；
- ADR-009 接受前/后的分支处理；
- R4 跨模块集成任务清单；
- 明确哪些事项必须由 ChatGPT 裁定。

**验证：**

- 不把 Proposed 写成 Accepted；
- 不修改已验收模块；
- 静态检查通过。

**Git：** 单独提交 + 阶段报告。

### R6：独立审查 / 整改 / PR

**范围：**

- 独立复审（既有 OpenClaw 会话只读审查或人工/ChatGPT 复审，不新建会话）；
- 修复审查发现；
- 最终报告；
- 经明确授权后创建 PR。

**交付物：**

- 复审报告；
- 整改提交；
- 最终交付报告；
- PR（仅在另行授权时）。

**验证：**

- 全量回归；
- Git 历史完整；
- 无 main 修改、无未授权合并；
- 不自行宣布验收通过。

**Git：** 整改/报告单独提交；PR/合并必须另行授权。

---

## 十一、每阶段验收标准

| 阶段 | 必须满足 |
|------|----------|
| R1 | Design 标准与现有架构/标准无冲突；明确双引用、无 plan、G2 边界、复杂度；静态链接检查通过 |
| R2 | Skill/Schema 可解析；Input 强制 requirements/analysis 类型；Output 五状态与禁止字段；`ok` 至少一个 design Artifact |
| R3 | 示例覆盖 L1/L2/L3/partial；invalid cases 覆盖关键绕过；Checklist 可映射 G2 |
| R4 | Validator 全部通过；R1/R2/P1-002/P1-001 回归通过；静态边界如实报告 |
| R5 | 跨模块差距与 ADR-009 状态清晰；未把 Proposed 当 Accepted；未修改 P1-002/ADR-006 |
| R6 | 独立复审完成；整改闭环；Git 证据完整；PR 仅在授权后创建 |

---

## 十二、测试计划

### 12.1 Schema 正向

- 最小 L1 设计；
- L2 标准设计；
- L3 完整设计；
- 双 Artifact 引用（Requirements+Analysis）；
- 决策/备选/偏离推荐；
- Requirements/Analysis 追踪；
- `needs_input`/`blocked`/`failed` 部分输出。

### 12.2 Schema/语义负向

- 缺 `requirements_ref` 或 `analysis_ref`；
- Artifact type 错误（analysis 当 requirements，反之）；
- Artifact version/sha256 缺失/非法；
- Requirements 与 Analysis 的 `source_requirements_ref` 不一致；
- 缺失设计决策理由；
- 多候选但无备选/偏离说明；
- 静默遗漏 FR/NFR/AC/constraint/unknown；
- blocking unknown/open question 却 `ok`；
- `design_approved`/`gate_approved`/`confirmation_ref`/GateDecision/Approval；
- 输出 `implementation_plan`/任务拆解/排期；
- 缺 `type=design` Artifact 却 `ok`；
- 条件字段应适用却既无内容也无 N/A 理由；
- 设计安全字段重定义 R0–R4/SA；
- Design 自行降低复杂度；
- 测试策略写成测试执行结果/G5 通过。

### 12.3 边界与回归

- G2 Builder Check 独立性（作者≠审查者）静态结构测试；
- G2 不等于 G4/G5；
- Design 不替代 Code Review/Testing；
- Requirements/Analysis 新版本 scenario（静态记录，不实现自动失效）；
- P1-001/R1/R2/P1-002 全量回归；
- JSON/YAML 解析、重复键、Markdown 链接/围栏、SemVer、`git diff --check`。

### 12.4 验证层级

| 层级 | R3 可做 | 不可做 |
|------|---------|--------|
| 静态 Schema/语义 | 是 | — |
| Skill 示例解析 | 是 | — |
| Workflow/G2 集成 | 只做静态契约审查 | 不执行 WorkflowRunner/GateController |
| Runtime | 否 | 不声称已执行 |
| 平台兼容 | 否 | 不声称六平台兼容 |

---

## 十三、风险与缓解

| 风险 | 缓解 |
|------|------|
| G3/Plan 生产者未关闭 | R3 明确 Design 不输出 plan；R4 关闭 |
| ADR-009 未接受 | R3 只设计兼容字段，不实施 binding；R5 审查 |
| G2 无专项示例 | R3 Checklist + R4 G2 静态测试 |
| 设计过度/输出膨胀 | 复杂度裁剪 + Required/Conditional/Optional/N/A |
| 重复 Requirements/Analysis | 只引用和追踪，不复制全文 |
| 重定义安全/审批 | 只引用 R0–R4/SA 和 P1-002 |
| 下游 Coding/Testing 未实现 | R3 只定义 handoff；端到端留后续 |
| 路径不一致 | R1 先统一 `skills/design/` 建议，不修改 P0 |
| Design 自行降级复杂度 | Orchestration 拥有分类权；设计只能建议升级 |
| 静态测试被误当 Runtime | 报告固定 `runtime_behavior=NOT_EXECUTED` |

---

## 十四、未实现边界

- `runtime_behavior = NOT_EXECUTED`；
- Design Skill 尚未实施（本 R0 只规划）；
- Analysis Runtime / Design Runtime / Planning Runtime 未实现；
- GateController / GateDecision 持久化未实现；
- 自动 Artifact 失效未实现；
- G2 Artifact binding 仅 ADR-009 Proposed，未生效；
- Coding/Code Review/Testing Skill 未实现；
- 六平台 SDD 语义兼容未实测；
- 静态 Schema/测试不能证明设计结论真实、完整或可实施；
- 不把文档/静态测试描述为 Runtime 已验证。

---

## 十五、R0 验证结果（实际执行）

以下检查均在授权基线 `7c57ecb` 上实际执行，退出码为 0；报告新增后仅重新执行静态解析检查。

### 15.1 P1-002 Orchestration

```text
ORCHESTRATION VALIDATION PASSED
schemas=5 state_machines=5
examples: workflows=10 tasks=5 gates=3 approvals=3 evidence=3
schema_positive=24 schema_negative=32
workflow_graph_positive=10 workflow_graph_negative=21
state_transitions_positive=77 state_transitions_negative=245
transition_definitions=77 transition_tests=322 guard_cases=18
parallel_cases=19 task_context_cases=11 gate_cases=15
approval_cases=111 scope_cases=15 expiry_cases=6 time_fail_closed_cases=15 path_cases=12
dag_branch_cases=4 parallel_join_cases=6
failure_cases=16 security_cases=134
yaml_blocks_checked=12 registry_ids=7
runtime_behavior=NOT_EXECUTED
```

### 15.2 Requirements R1

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=2 examples_out=7
cases_input_validated=8 invalid_cases_rejected=6
semver_valid=6 semver_invalid=6
yaml_blocks_checked=12 metadata_examples=1 registry_ids=7
negative_metadata_cases_passed=5
optional_positive_cases_passed=2 optional_negative_cases_passed=9
requirements_semantic_positive=7 requirements_schema_negative=13 requirements_semantic_negative=6
runtime_behavior=NOT_EXECUTED platform_entries=1
```

### 15.3 Analysis R2

```text
ANALYSIS VALIDATION PASSED
schemas=2 input_examples=3 output_examples=3
input_positive=3 output_positive=3 cases=3 invalid_cases=4
schema_negative=19 semantic_negative=22
f1_negative=8 f1_positive=1 f2_cases=8 f3_cases=2
trace_negative=6 trace_positive=2
resolved_negative=42 resolved_positive=4
f7_negative=16 f7_negative_passed=16
f7_vectors=30 f7_vectors_passed=30 f7_identity_positive=4
acceptance_retained_negative=6 acceptance_retained_positive=1
runtime_behavior=NOT_EXECUTED
```

### 15.4 全仓静态检查

```text
STATIC VALIDATION PASSED json=43 yaml=17 markdown=78
duplicate_json_yaml_keys=checked markdown_links=ok markdown_fences=ok
```

- JSON 43 个文件解析成功；
- YAML 17 个文件解析成功，重复键检查通过；
- Markdown 78 个文件链接 0 断链，代码围栏无未闭合；
- SemVer 由 Requirements R1 校验器覆盖（`semver_valid=6 semver_invalid=6`）；
- `git diff --check` 无错误；
- `git show --check` 对 R0 两个提交均无错误。

### 15.5 未执行

- 未执行 Design Skill Runtime；
- 未执行 WorkflowRunner / GateController / Approval Runtime；
- 未执行六平台兼容性测试；
- 未配置或未声称 CI；
- 所有测试均为静态/只读校验。

---

## 十六、最终状态

**P1-003-R3-R0 COMPLETE（本计划）**

**R3 Design 实施 NOT STARTED**

**ADR-009 PROPOSED / NOT ACCEPTED**

**PR NOT CREATED**

**MAIN UNMODIFIED**

完成后停止，等待 ChatGPT 独立复审；不自行启动 R1。
