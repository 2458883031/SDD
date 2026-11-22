# SDD Design 标准

**状态：** P1-003-R3-R1 Draft（待 ChatGPT 评审）
**适用范围：** Design 的职责、输入输出、设计规格、决策、追踪、完整度、边界和 G2/Planning/Coding 交接
**权威关系：** 通用 Skill/IO 见 [skill-standard.md](./skill-standard.md) 与 [skill-io-contract.md](./skill-io-contract.md)；Artifact/Task/Gate 见 [ADR-005](../decisions/ADR-005-task-context.md)、[task-standard.md](./task-standard.md)、[gate-orchestration-standard.md](./gate-orchestration-standard.md)；Requirements 输入见 [requirements-standard.md](./requirements-standard.md)；Analysis 输入见 [analysis-standard.md](./analysis-standard.md)。

---

## 1. 职责与非职责

### 1.1 职责

Design 将已确认的 Requirements 和 Analysis 结论转化为可实施、可验证的设计规格，为 Planning/Coding/Review/Testing 提供结构化依据：

- 读取 Requirements Artifact 和 Analysis Artifact，校验引用类型/版本/SHA-256；
- 将已确认需求和分析结论转化为可实施、可验证的设计规格；
- 选择最终技术方案，并记录与 Analysis 推荐的一致/偏离理由；
- 定义架构、组件/模块、接口、数据模型/数据流、状态转换、失败路径、安全边界、性能/容量、迁移/回滚；
- 定义测试策略和验收标准到设计的追踪；
- 记录设计决策、备选方案、风险、假设、unknown、open questions；
- 输出 `type=design` Artifact；
- 为 G2/Builder Check、Coding、Code Review、Testing 提供结构化依据；
- 对缺失输入返回 `needs_input`/`blocked`，对执行错误返回 `failed`。

### 1.2 非职责

Design **不负责**：

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

**推荐方案不是设计决定。** Design 可以基于证据选择 Analysis 未推荐的方案，但必须记录理由、证据和重新评估条件。

### 1.3 Design vs Analysis vs Planning

| Design | Analysis | Planning |
|--------|----------|----------|
| 确定最终设计方案 | 分析候选方案 | 拆解实现任务 |
| 定义架构/接口/数据 | 评估可行性/风险 | 生成 Plan Artifact（实施计划） |
| 输出设计规格 | 提出推荐 | G3 审查/批准 Plan Artifact |
| 记录设计决策 | 不产出正式设计 | 属于 Orchestration 内部活动 |
| 不输出 implementation-plan | 不做最终设计 | 不定义架构 |

---

## 2. 适用与不适用

**适用：**

- Requirements 已结构化且无 blocking 未决项；
- Analysis 已完成并提供候选方案、可行性、风险和推荐；
- 需要确定最终系统架构、接口、数据模型、状态机；
- 需要记录设计决策、备选方案和偏离推荐理由；
- 需要为 Coding/Review/Testing 提供设计符合性基准。

**可裁剪/不适用：**

- Requirements 存在 blocking 未决项：先返回 `needs_input`/`blocked`；
- Analysis 未完成或关键 unknown 未闭环：先返回 `needs_input`/`blocked`；
- 纯文档更新且不改架构/接口/数据：可只做轻量设计说明；
- 复杂度过低（L1）：可跳过完整架构章节，但 N/A 必须记录。

不得为了流程完整而编造设计内容或扩大设计范围。

---

## 3. 输入契约

遵循 `skills/design/schemas/input.schema.json`（P1-003-R3-R2 定义）：

| 字段 | 必需 | 说明 |
|------|------|------|
| `requirements_ref` | 是 | Requirements Artifact 引用（path/version/sha256/type=requirements） |
| `analysis_ref` | 是 | Analysis Artifact 引用（path/version/sha256/type=analysis） |
| `complexity` | 是 | L1/L2/L3，由 Orchestration 提供；Design 不自行判定/降低；缺失时 `blocked`，非法枚举时 `failed`/`input_invalid` |
| `requirements` | 否 | 已解析的 Requirements `data.requirements`；复用 requirements-standard.md |
| `analysis` | 否 | 已解析的 Analysis `data.analysis`；复用 analysis-standard.md |
| `project_context` | 否 | 项目上下文摘要 |
| `constraints` | 否 | 调用方补充约束 |
| `existing_design` | 否 | 已有 Design Artifact 引用数组 |
| `evidence_refs` | 否 | 外部证据引用 |
| `change_context` | 否 | 变更原因、变更项、上一版引用 |
| `requested_scope` | 否 | 本次设计范围 |

**输入状态判断（按 P1-001 IO 契约区分，不得把所有问题都归为 `failed`）：**

1. **Schema 格式/类型错误**：字段类型错误、Artifact type 错误、SHA 格式错误、非法 enum、未知字段 → `failed` + `input_invalid`。
2. **必要信息缺失，需调用方/用户补充**：缺少 `requirements_ref`/`analysis_ref`，或缺少可向用户询问的设计选择信息 → `needs_input` + 最小 `questions`；若上游 Artifact 已声明但不可读取/不可达，则为 `blocked`。
3. **Orchestration 上下文缺失**：`complexity` 缺失 → `blocked` + `precondition_failed`；`complexity` 非法枚举 → `failed` + `input_invalid`。Design 不得自行推断或降低复杂度。
4. **权限、依赖或外部条件阻塞**：无读取权限、上游依赖未就绪、任务工作区/Artifact 路径不可用 → `blocked` + `precondition_failed`。
5. **上游业务阻塞**：Requirements blocking 未决项/未解决冲突，或 Analysis blocking unknown/open question → `needs_input`/`blocked`，不得输出完整可实施的 `ok`。
6. **内部执行错误**：设计生成过程异常且不可恢复 → `failed` + `internal_error`。
7. Requirements/Analysis 引用 type 错误属于第 1 类 → `failed`；不得通过"最新版本"隐式选取 Artifact。
8. 若同时提供已解析的 `requirements`/`analysis`，其来源必须与对应 Artifact 引用一致；Design 不创建第二套 Requirements/Analysis 身份。

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

`data.design` 主要包括：

| 字段 | 分类 | 说明 |
|------|------|------|
| `design_id` | Required | 设计标识 |
| `design_version` | Required | 设计内容版本（SemVer） |
| `created_at` | Required | 创建时间 |
| `source_requirements_ref` | Required | 来源 Requirements Artifact 引用 |
| `source_analysis_ref` | Required | 来源 Analysis Artifact 引用 |
| `source_refs` | Optional | 额外证据/上下文引用 |
| `design_summary` | Required | 设计范围、目标、非目标；引用上游，不重写需求 |
| `selected_solution` | Conditional Required | 选择结果；引用 Analysis candidate 或说明新方案 |
| `alternatives` | Conditional Required | 多候选/偏离推荐时必须有；L1 单方案可记录"无其他可行方案"理由 |
| `decisions` | Required | 设计决策列表 |
| `architecture_overview` | Required | 系统/组件/部署/运行视图的适用部分 |
| `components` | Conditional Required | 新模块/组件/跨模块变更时必需 |
| `modules` | Conditional Required | 模块划分与依赖 |
| `interfaces` | Conditional Required | API/事件/端口/契约变化时必需 |
| `data_models` | Conditional Required | 数据模型变化时必需 |
| `data_flows` | Conditional Required | 跨组件数据流/敏感数据流时必需 |
| `state_model` | Conditional Required | 有状态/生命周期变化时必需 |
| `failure_handling` | Conditional Required | 外部依赖/失败路径/重试/补偿/降级 |
| `security_design` | Conditional Required | 安全敏感/认证/授权/加密/信任边界 |
| `performance_scalability` | Conditional Required | 有性能/容量 NFR 或架构变化 |
| `migration_rollback` | Conditional Required | 数据/接口/生产架构变更 |
| `test_strategy` | Required | 验证方法、测试层级、AC 映射、环境/数据需求 |
| `requirements_traceability` | Required | FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/AC/non_goals/source_refs |
| `analysis_traceability` | Required | 候选/风险/unknowns/design_considerations 承接 |
| `risks` | Required | 设计级风险、缓解、残余、状态 |
| `assumptions` | Required（可空） | 设计假设 |
| `unknowns` | Required（可空） | 未知项 |
| `open_questions` | Required（可空） | 需用户/上游回答的问题 |
| `design_change_impact` | Conditional Required | 变更设计时记录下游影响 |
| `implementation_constraints` | Optional | 给 Coding 的约束/技术栈边界 |
| `coverage` | Recommended | 对各区域记录 designed/not_applicable/deferred + 理由 |

> **L1 说明：** L1 的 `architecture_overview` 可以只记录本次变更影响、受影响组件/接口/数据和依赖，不要求完整架构章节；但影响与 N/A 判断必须可审查。

**禁止字段：**

- `implementation_plan`、任务拆解、排期（属于 Planning/G3）；
- `design_approved`、`gate_approved`、`confirmation_ref`、`gate_decision`、`approval`；
- `code_review_approved`、`testing_approved`；
- 完整的 Requirements 副本（应引用 Requirements Artifact）；
- 测试执行结果（属于 Testing/G5）。

**`status=ok` 语义：**

- 设计达到最低完整度，无 blocking 未决项；
- **不表示 G2 已通过、设计已批准、用户已确认**；
- Required 字段完整，Conditional Required 字段要么有内容要么有 `not_applicable` 理由。

### 4.1 字段分层说明

| 分类 | 含义 | 处理规则 |
|------|------|----------|
| **Required** | 必须存在 | `ok` 时必须存在；标为“可空”的数组必须存在但允许为空 |
| **Conditional Required** | 条件必须 | 适用时有内容，不适用时记录 `not_applicable` + 理由 |
| **Optional** | 可选 | 有则提供，无则省略 |
| **Not Applicable** | 不适用 | 必须在 `coverage` 或对应字段记录理由，不得静默省略 |

---

## 5. Artifact 身份与版本

- Design 输出是独立 `type=design` Artifact，复用 ADR-005 定义，不新增 Artifact 类型。
- `source_requirements_ref` 必须引用 Requirements Artifact（path/version/sha256/type=requirements）。
- `source_analysis_ref` 必须引用 Analysis Artifact（path/version/sha256/type=analysis）。
- `design_version` 是设计内容版本（SemVer），与 Artifact `version`（ADR-005 整数版本）不混用。
- `source_requirements_ref`、`source_analysis_ref` 必须与输入一致；所有含 `data.design` 的状态都适用。
- `status=ok` 至少包含一个 `type=design` 的 Artifact；不得用 `source_refs` 替代。
- 上游 Requirements/Analysis 版本变化时，Design 应重新评估适用性；本阶段**不实现**自动失效 Runtime。
- 旧设计版本按 ADR-005 标记 `superseded`；本 Skill 不直接修改历史 Artifact。

---

## 6. 设计完整度等级

复杂度由 Orchestration 按 [task-classification-standard.md §4](./task-classification-standard.md) 判定，Design 不自行降低复杂度。

### 6.1 等级定义

| 等级 | 设计深度 | 最低要求 |
|------|----------|----------|
| **L1** | 轻量设计 | 设计摘要、受影响组件/接口/数据的 N/A 说明、至少一个设计决策（可为 lightweight）及理由、AC/验证方法、明确风险/unknown；可跳过完整架构章节 |
| **L2** | 标准设计 | L1 + 架构概览、组件职责、接口/数据模型（如变化）、失败处理、安全边界、测试策略、决策/备选、Requirements/Analysis 追踪 |
| **L3** | 完整设计 | L2 + 完整架构/组件/数据流、状态转换、安全/信任边界、性能/容量、迁移/回滚、运维/可观测性、偏离推荐的理由、变更影响、完整追踪 |

### 6.2 升级触发（至少建议）

- 系统/跨系统影响或架构变更；
- 数据模型/数据迁移/生产数据；
- 认证、授权、加密、敏感凭证；
- 新增外部服务/依赖/API；
- 不可逆或高风险变更；
- 需求/技术方案存在关键未知；
- 多模块、多 Agent、跨团队依赖。

### 6.3 降级条件

- 仅局部、可逆、无接口/数据/安全变化，且有验证证据；
- 降级必须由 Orchestration 基于证据决定并记录，Design 只能建议，不能自行降级。
- Design 发现 §6.2 升级触发条件时，应向 Orchestration 建议升级；不得以“设计简单”为由自行降低等级。

---

## 7. 设计决策规则

### 7.1 决策结构

每个设计决策至少记录：

- `decision_id`；
- `decision`（决定了什么）；
- `rationale`（理由/证据）；
- `alternatives_considered`（至少记录未选方案及不选原因）；
- `related_requirements`（FR/NFR/constraint ID）；
- `related_analysis`（候选/风险/unknown/design consideration ID）；
- `consequences`（对实现、测试、运维、安全、性能的影响）；
- `deviation_from_recommendation`（如偏离 Analysis 推荐，记录理由与证据）。

### 7.2 决策级别

| 级别 | 适用场景 | 记录要求 |
|------|----------|----------|
| **Key Decision** | 系统结构、长期影响、跨模块、数据模型、安全边界、性能架构 | 完整决策记录，含 alternatives、rationale、consequences |
| **Lightweight Decision** | 局部实现细节、临时方案、无长期影响 | 简化记录，含 decision + rationale 即可 |

**判断标准：** 涉及系统结构、长期影响、跨模块、数据模型变更、安全边界、性能架构的决策必须是 Key Decision；其他可记录为 Lightweight Decision。

### 7.3 偏离推荐的处理

- Analysis 推荐方案不是强制决定；
- Design 选择 Analysis 未列出的新方案时，必须提供 `new_solution_rationale` 和证据，或返回 `needs_input`；
- 偏离推荐时必须记录理由、证据和重新评估条件；
- 不得用 Design 决策字段写 G2 审批结果。

---

## 8. Requirements 追踪

Design 不得静默丢弃 Requirements 的关键信息。`requirements_traceability.items` 必须为上游关键条目建立处理关系：

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

- `designed`：已映射到组件/接口/数据/状态/安全/测试策略等设计元素；必须提供可解析的 `design_refs`；
- `mapped`：已映射到决策/风险/验证方法；必须提供 `design_refs`；
- `retained`：保留为设计假设/unknown/open question/非目标；必须能在实际 Design 输出中找到对应内容；
- `resolved`：已由设计决策/证据解决；必须提供 `resolution_evidence_refs`，且引用必须使用规范形式（同 Analysis R2 严格 SHA-256 引用规则）；
- `not_applicable` / `deferred`：不适用/延后；必须提供非空 `rationale`。

规则：

1. 不要求机械复制上游内容；只要求逐项建立处理关系。
2. 不适用/延后必须解释原因；不得静默删除。
3. `mapped` 的 `design_refs` 必须指向存在的设计元素。
4. `retained` 必须闭环到实际输出。
5. `resolved` 的证据只接受显式 evidence_refs，且必须使用规范引用；`source_requirements_ref`、普通 `source_refs` 登记、纯 path、`user_stated`/`assumption` 陈述均不得充当解决证据。
6. Requirements Artifact 不被修改；Design 不是第二个 Requirements 生产者。
7. 只做最小追踪，不引入新的全局 Artifact 类型或状态机。

---

## 9. Analysis 追踪

Design 必须承接 Analysis 的候选方案、风险、unknowns、open questions、design considerations：

| Analysis 内容 | Design 处理 |
|---------------|-------------|
| 候选方案 | 记录 selected_solution，偏离推荐时记录 deviation_rationale |
| 可行性评估 | 记录设计级可行性结论 |
| 风险清单 | 承接为 design.risks，说明设计控制措施 |
| unknowns | 承接为 design.unknowns，blocking 时不得 `ok` |
| open_questions | 承接为 design.open_questions |
| design_considerations | 记录为 design 输入，说明采纳/偏离理由 |
| 推荐方案 | 作为设计参考，非强制决定 |

`analysis_traceability` 覆盖候选、风险、unknowns、design considerations；Design 必须说明承接、偏离或拒绝理由。

`analysis_traceability.items` 建议使用：

| `source_type` | 说明 |
|---------------|------|
| `candidate` | Analysis 候选方案 |
| `risk` | Analysis 风险 |
| `unknown` | Analysis 未知项 |
| `open_question` | Analysis 未决问题 |
| `design_consideration` | Analysis 设计考虑 |

`disposition`：

- `adopted`：采纳到最终设计；必须有 `design_refs`；
- `adapted`：调整后采纳；必须说明调整及理由；
- `rejected`：未采纳；必须说明理由/证据，不得静默忽略；
- `retained`：保留为设计风险/unknown/open question；必须闭环到实际输出；
- `not_applicable` / `deferred`：不适用/延后；必须提供非空 `rationale`。

推荐方案被拒绝或替换时，必须记录 `deviation_from_recommendation`；Analysis 的 blocking unknown/open question 未闭环时不得输出 `ok`。

---

## 10. 架构、组件、模块与依赖

### 10.1 架构概览

必须包含：

- `architecture_overview`：系统/组件/部署/运行视图的适用部分；
- 系统边界、组件职责、依赖方向；
- 外部系统/服务/依赖。

### 10.2 组件与模块

- `components`：新模块/组件/跨模块变更时必需；
- `modules`：模块划分与依赖；
- 每个组件/模块记录：ID、职责、边界、依赖方向。

### 10.3 依赖管理

- 记录组件/模块间依赖方向；
- 检查循环依赖；
- 记录外部依赖及其版本/兼容性约束。

---

## 11. 接口与数据模型/数据流

### 11.1 接口契约

- `interfaces`：API/事件/端口/契约变化时必需；
- 每个接口记录：ID、输入/输出、错误处理、版本、兼容性、幂等/并发约束。

### 11.2 数据模型

- `data_models`：数据模型变化时必需；
- 实体/关系、生命周期、敏感数据、迁移策略。

### 11.3 数据流

- `data_flows`：跨组件数据流/敏感数据流时必需；
- 数据流向、转换、存储、访问控制。

---

## 12. 状态与状态转换

- `state_model`：有状态/生命周期变化时必需；
- 记录状态、事件、转换、非法转换、终态、持久化责任。

---

## 13. 错误、失败、重试、补偿与降级

- `failure_handling`：外部依赖/失败路径/重试/补偿/降级时必需；
- 失败分类、重试策略、补偿机制、降级方案、回滚路径。

---

## 14. 安全与信任边界

- `security_design`：安全敏感/认证/授权/加密/信任边界时必需；
- 参考 [security-architecture.md](../architecture/security-architecture.md) R0–R4/SA，不重定义；
- 记录信任边界、权限模型、数据保护、审计需求。

---

## 15. 性能与可扩展性

- `performance_scalability`：有性能/容量 NFR 或架构变化时必需；
- 性能目标、容量假设、扩展点、退化策略、验证方法。

---

## 16. 迁移、回滚与兼容性

- `migration_rollback`：数据/接口/生产架构变更时必需；
- 迁移步骤、回滚方案、兼容性策略、数据备份。

---

## 17. 测试策略与验收标准映射

- `test_strategy`：Required；
- 定义验证方法、测试层级、AC 映射、环境/数据需求；
- 每个 Acceptance Criterion 映射必须至少引用一个设计元素（`design_refs` 非空）；无法直接映射时必须引用明确记录受控例外的设计元素并说明 `exception.reason`，不得留空；
- **不是测试执行结果**；G5 由 Testing Skill 执行；
- 记录 Requirements AC → Design 验证方法 → Testing 用例的追踪。

---

## 18. 风险、假设、未知项、未决问题

- `risks`：Required；设计级风险、缓解、残余、状态；
- `assumptions`：Required（可空）；设计假设，不得伪装为事实；
- `unknowns`：Required（可空）；未知项，blocking 时不得 `ok`；
- `open_questions`：Required（可空）；需用户/上游回答的问题。

---

## 19. 设计变更影响

- `design_change_impact`：Conditional Required；
- 变更设计时记录下游影响、需重跑阶段；
- 上游 Requirements/Analysis 版本变化时，Design 应重新评估适用性。
- 影响分析至少覆盖：受影响的组件/接口/数据/状态/安全/测试/部署；是否需要新 Design 版本；Coding/Review/Testing 是否需重做。
- Design 新版本使 G2/G3 旧 decision 失效属于 **ADR-009 Proposed** 的规划方向，尚未成为已生效 Gate 规则；本阶段不实现自动失效，也不修改 ADR-006/P1-002。

---

## 20. Design → Planning 交接

- Design 输出 `type=design` Artifact，**不输出** `implementation_plan`；
- Planning 由 Orchestration 内部活动执行，消费 Requirements/Analysis/Design，生成 `type=plan` Artifact；
- G3 检查/批准 plan，不生成 plan；
- 当前 P1-002 `feature-development.yaml` 在 G2 后直接 G3，没有 plan 节点/生产者；该缺口**不在 R3 修改**，由 R4 处理；
- R3 只在 Design 标准中明确交接边界，不实现 Planning。

---

## 21. Design → Coding 交接

Design 应提供：

- 组件/模块 ID、职责、依赖方向；
- 接口契约（输入/输出/错误/版本/兼容性）；
- 数据模型/数据流/敏感数据；
- 状态与转换、失败/重试/补偿/降级；
- 安全/信任边界和 R0–R4/SA 约束；
- 性能/容量约束；
- AC → 验证方法；
- `implementation_constraints`（技术栈边界，不写完整实现）。

Coding 遇到设计缺失时必须反馈/返回 `needs_input`，不得自行做出重大架构决策。

---

## 22. Design → Code Review / Testing 边界

- Code Review 使用组件/接口/数据/决策/约束作为设计符合性基准；
- Testing 使用 `test_strategy` 和 AC 映射设计测试；
- Design 的 test strategy 不是测试结果，不产生 G5 证据；
- Design 不替代 G4/G5，不写 `code_review_approved`/`testing_approved`；
- Design 变更应说明对现有代码/测试/部署的下游影响。

---

## 23. G2 与 Builder Check 边界

### 23.1 当前规则

- G2 在 Design 完成之后、Planning/Coding 之前由 Orchestration 挂载；
- ADR-006 §4 是 G2 权威规则；
- `gate-orchestration-standard.md §3/§6` 定义挂载与 Builder Check；
- GateDecision Schema 通用 `subject_hash`；G2 PASSED 至少需要非空 subject_hash，但不强制 Design path/version/type；
- Approval Schema 只强制 G4/G5/G6 的 subject_hash；
- 没有 G2 专项示例或 Design 语义测试；
- ADR-009 Proposed 才要求 G2 绑定 Design Artifact path/version/sha256 和失效链。

### 23.2 R3 范围

- Design 输出可供 G2 审查的结构化设计；
- Checklist 覆盖 ADR-006 G2 自动检查：设计文档、架构影响、接口/数据模型、安全、备选方案、可测试性、回滚/迁移；
- 支持 Builder Check 独立审查所需证据：设计 Artifact hash、检查项、决策/备选、风险/异常场景；
- **不实现 G2 审批、GateDecision、Approval 或自动失效。**

**G2 检查项到 Design 输出的映射建议：**

| ADR-006 G2 检查项 | Design 输出依据 |
|-------------------|------------------|
| 设计文档 | `design_summary`、`architecture_overview` 与完整 `data.design` |
| 架构影响 | 架构/组件/模块、依赖方向、兼容性影响 |
| 接口/数据模型 | `interfaces`、`data_models`、`data_flows` |
| 安全考虑 | `security_design`、信任边界、R0–R4/SA 约束引用 |
| 备选方案 | `alternatives`、`decisions`、偏离推荐理由 |
| 可测试性 | `test_strategy`、Acceptance Criteria 映射 |
| 回滚/迁移 | `migration_rollback`、失败/降级方案 |
| 需求遗漏/设计矛盾 | `requirements_traceability`、`analysis_traceability`、风险与 unknown |

**Builder Check 独立性：** 审查者 ID 不得等于设计/执行作者 ID；Builder Check 的审查结果、审查者、检查项、时间、关联设计 Artifact hash 属于 G2 证据，不属于 Design Skill 输出。Design 不得在 `data.design` 中伪造 `approved/needs_revision/escalated`。

### 23.3 R4 范围

- 若 ADR-009 被接受，扩展 GateDecision/Approval 的 Design Artifact binding；
- 增加 G2 静态示例/测试；
- 处理 Design 新版本失效 G2/G3；
- 关闭 Planning/plan 生产者缺口。

---

## 24. Skill 状态语义

复用 P1-001 五状态，不新增状态机：

| 状态 | Design 语义 | 约束 |
|------|-------------|------|
| `ok` | 设计达到最低完整度，无 blocking 未决项 | **不等于 G2 通过/设计批准**；不得写 `design_approved` |
| `needs_input` | 缺少必要信息、需要调用方/用户补充、设计选择需用户确认、关键 unknown | 必须返回 `questions`；可带部分 design；不得把所有信息缺口都归为 `failed` |
| `needs_approval` | 设计决策触发安全/高风险审批，需显式批准后才能定稿 | 只能表示待确认，**不得表示 G2 已通过**；不得自批；不得把 G2 本身作为 Design 的审批请求，G2 由 Orchestration 在 Design 完成后执行 |
| `blocked` | 缺少 Orchestration complexity、上游 Artifact 不可读、权限/环境/外部依赖不满足 | 必须返回 `blocked_reason`；不得伪造完整设计 |
| `failed` | Schema 格式/类型错误、非法 enum、内部执行错误、无法恢复的处理异常 | 至少一个 error；不得把可补充的信息缺口伪装成 `failed` |

**三层状态分离：**

1. Skill `status`：本次执行结果；
2. Artifact `status`：draft/approved/superseded（ADR-005）；
3. Gate `status`：PENDING/PASSED/FAILED 等（ADR-006/P1-002）。

Design Skill 只负责第 1 层并输出第 2 层的引用；G2/Gate 由 Orchestration 负责。

---

## 25. 禁止行为

Design **不得**：

- 重写 Requirements；
- 输出 `implementation_plan`、任务拆解、排期；
- 伪造 G2/Approval/GateDecision；
- 输出 `design_approved`、`gate_approved`、`confirmation_ref`；
- 代替 Coding/Code Review/Testing；
- 自行降低任务复杂度；
- 重定义 R0–R4/SA 权限；
- 新建 Gate、Approval、Evidence 模型或状态机；
- 新建与 ADR-005 重复的 Artifact 类型；
- 复制 Requirements/Analysis 全文；
- 静默丢弃上游关键条目；
- 将假设/unknown 伪装为事实。

---

## 26. 完成条件

`status=ok` 必须满足：

1. Required 字段完整；
2. Conditional Required 字段要么有内容要么有 `not_applicable` 理由；
3. 无 blocking unknown/open question；
4. 每个设计决策有理由；
5. Requirements/Analysis 追踪完整；
6. 至少一个 `type=design` Artifact；
7. 无禁止字段。

---

## 27. 相关标准

- [skill-standard.md](./skill-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [requirements-standard.md](./requirements-standard.md)
- [analysis-standard.md](./analysis-standard.md)
- [task-classification-standard.md](./task-classification-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)
- [ADR-009](../decisions/ADR-009-predevelopment-artifact-binding.md)（Proposed）
- [system-architecture.md](../architecture/system-architecture.md)
- [module-architecture.md](../architecture/module-architecture.md)
- [security-architecture.md](../architecture/security-architecture.md)
- [testing-architecture.md](../architecture/testing-architecture.md)

---

**P1-003-R3 Draft 状态：** Design 标准 Draft；Runtime 未实现。
