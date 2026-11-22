# Design Checklist

用于 `design` Skill 自检和 G2/Builder Check 参考。

每项标注适用等级（L1/L2/L3）和强制级别（Required/Conditional Required/Optional/Not Applicable/Deferred）。

**使用规则：**

- **Required**：所有适用设计必须满足；不因 L1 省略。
- **Conditional Required**：当前变更涉及对应领域时必须满足；不适用时必须在 `coverage` 记录 N/A 理由。
- **Optional**：按项目需要提供，不影响 `ok` 的最低完整度。
- **Not Applicable**：必须记录理由，不得静默省略。
- **Deferred**：必须记录原因、影响和后续处理条件；不得用 Deferred 逃避必要的安全、接口或数据设计。

---

## 1. 输入完整性

**[Required | L1/L2/L3]** — 见 [design-standard.md §3](../../../docs/standards/design-standard.md#3-输入契约)

- [ ] `requirements_ref` 存在且 type=requirements；引用格式为 path/version/sha256
- [ ] `analysis_ref` 存在且 type=analysis；引用格式为 path/version/sha256
- [ ] `complexity` 存在且为 L1/L2/L3 之一
- [ ] 不得通过"最新版本"隐式选取 Artifact
- [ ] 若提供 `requirements`/`analysis` 解析内容，其 `source_requirements_ref` 必须与 `requirements_ref` 一致

---

## 2. Requirements/Analysis 引用

**[Required | L1/L2/L3]** — 见 [design-standard.md §5](../../../docs/standards/design-standard.md#5-artifact-身份与版本)

- [ ] `source_requirements_ref` 与输入 `requirements_ref` 完全一致
- [ ] `source_analysis_ref` 与输入 `analysis_ref` 完全一致
- [ ] 所有含 `data.design` 的状态来源一致

---

## 3. Artifact 版本/SHA

**[Required | L1/L2/L3]** — 见 [design-standard.md §5](../../../docs/standards/design-standard.md#5-artifact-身份与版本)

- [ ] 输出 `artifacts` 包含至少一个 `type=design` 的 Artifact（`status=ok` 时）
- [ ] Artifact 格式：path/version/sha256/type
- [ ] SHA-256 为 64 位小写十六进制
- [ ] 不得用 `source_refs` 替代 `artifacts`

---

## 4. 复杂度/设计深度

**[Required | L1/L2/L3]** — 见 [design-standard.md §6](../../../docs/standards/design-standard.md#6-设计完整度等级)

- [ ] 按 Orchestration 提供的 `complexity` 确定设计深度，不自行降低
- [ ] L1：设计摘要、N/A 说明、至少一个决策、AC 映射、风险/unknown
- [ ] L2：L1 + 架构概览、组件职责、接口/数据模型、失败处理、安全边界、测试策略
- [ ] L3：L2 + 完整架构/数据流/状态转换、安全/信任边界、性能/容量、迁移/回滚
- [ ] 发现升级触发条件时向 Orchestration 建议升级

---

## 5. Requirements 追踪

**[Required | L1/L2/L3]** — 见 [design-standard.md §8](../../../docs/standards/design-standard.md#8-requirements-追踪)

- [ ] 覆盖 FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/AC/non_goals/source_refs
- [ ] `designed`/`mapped` 条目有非空 `design_refs`
- [ ] `resolved` 条目有规范 `resolution_evidence_refs`
- [ ] `not_applicable`/`deferred` 条目有非空 `rationale`
- [ ] `retained` 条目闭环到实际输出
- [ ] 不得静默丢弃上游关键条目

---

## 6. Analysis 追踪

**[Required | L1/L2/L3]** — 见 [design-standard.md §9](../../../docs/standards/design-standard.md#9-analysis-追踪)

- [ ] 覆盖候选方案、风险、unknowns/open questions/design considerations
- [ ] `adopted`/`adapted` 条目有 `design_refs`
- [ ] `rejected`/`retained`/`not_applicable`/`deferred` 条目有 `rationale`
- [ ] 偏离推荐时有 `deviation_from_recommendation`

---

## 7. Key/Lightweight 决策

**[Required | L1/L2/L3]** — 见 [design-standard.md §7](../../../docs/standards/design-standard.md#7-设计决策规则)

- [ ] 每个决策有 `decision_id`、`decision`、`rationale`、`decision_level`
- [ ] Key Decision 有 `alternatives_considered`（minItems 1）、`consequences`、`related_requirements`
- [ ] Lightweight Decision 可简化，但必须有 `decision` + `rationale`
- [ ] 偏离 Analysis 推荐时有 `deviation_from_recommendation`

---

## 8. 架构/模块边界

**[Conditional Required | L2/L3]** — 见 [design-standard.md §10](../../../docs/standards/design-standard.md#10-架构组件模块与依赖)

- [ ] L2+ 有 `architecture_overview`
- [ ] 新模块/组件时 `components`/`modules` 非空
- [ ] 模块/组件记录 ID、职责、依赖方向
- [ ] L1 可省略完整架构章节，但需在 `coverage` 中记录 N/A 理由

---

## 9. 接口/数据模型

**[Conditional Required | L2/L3]** — 见 [design-standard.md §11](../../../docs/standards/design-standard.md#11-接口与数据模型数据流)

- [ ] 接口变化时 `interfaces` 非空
- [ ] 数据模型变化时 `data_models` 非空
- [ ] 每个接口记录 ID、输入/输出、错误处理
- [ ] L1 可省略，但需在 `coverage` 中记录 N/A 理由

---

## 10. 数据流/状态

**[Conditional Required | L3]** — 见 [design-standard.md §11-12](../../../docs/standards/design-standard.md#11-接口与数据模型数据流)

- [ ] 跨组件数据流时 `data_flows` 非空
- [ ] 有状态变化时 `state_model` 非空
- [ ] L1/L2 可省略，但需在 `coverage` 中记录 N/A 理由

---

## 11. 失败处理

**[Conditional Required | L2/L3]** — 见 [design-standard.md §13](../../../docs/standards/design-standard.md#13-错误失败重试补偿与降级)

- [ ] 外部依赖/失败路径时 `failure_handling` 非空
- [ ] 记录失败分类、重试策略、补偿/降级方案
- [ ] L1 可省略，但需在 `coverage` 中记录 N/A 理由

---

## 12. 安全设计

**[Conditional Required | L2/L3]** — 见 [design-standard.md §14](../../../docs/standards/design-standard.md#14-安全与信任边界)

- [ ] 安全敏感/认证/授权/加密/信任边界时 `security_design` 非空
- [ ] 引用 R0–R4/SA，不重定义
- [ ] 不得为规避而将安全标记为 N/A
- [ ] L1 若无安全影响需在 `coverage` 中记录 N/A 理由

---

## 13. 性能/容量

**[Conditional Required | L2/L3]** — 见 [design-standard.md §15](../../../docs/standards/design-standard.md#15-性能与可扩展性)

- [ ] 有性能/容量 NFR 或架构变化时 `performance_scalability` 非空
- [ ] 记录性能目标、容量假设、扩展点
- [ ] L1 可省略，但需在 `coverage` 中记录 N/A 理由

---

## 14. 迁移/回滚

**[Conditional Required | L3]** — 见 [design-standard.md §16](../../../docs/standards/design-standard.md#16-迁移回滚与兼容性)

- [ ] 数据/接口/生产架构变更时 `migration_rollback` 非空
- [ ] 记录迁移步骤、回滚方案、兼容性策略
- [ ] L1/L2 可省略，但需在 `coverage` 中记录 N/A 理由

---

## 15. 测试策略

**[Required | L1/L2/L3]** — 见 [design-standard.md §17](../../../docs/standards/design-standard.md#17-测试策略与验收标准映射)

- [ ] `test_strategy` 存在且非空
- [ ] `approach`、`levels`、`verification_methods` 非空
- [ ] `acceptance_criteria_mapping` 非空（minItems 1）
- [ ] 不是测试执行结果

---

## 16. AC 映射

**[Required | L1/L2/L3]** — 见 [design-standard.md §17](../../../docs/standards/design-standard.md#17-测试策略与验收标准映射)

- [ ] 每条 AC 有 `criterion_ref`、非空 `design_refs`、`verification_method`
- [ ] `design_refs` 指向实际存在的设计元素 ID
- [ ] 无法直接映射时记录 `exception.reason`

---

## 17. 风险/假设/Unknown/Open Questions

**[Required | L1/L2/L3]** — 见 [design-standard.md §18](../../../docs/standards/design-standard.md#18-风险假设未知项未决问题)

- [ ] `risks` 存在（可为空数组）
- [ ] `assumptions` 存在（可为空数组）
- [ ] `unknowns` 存在（可为空数组）
- [ ] `open_questions` 存在（可为空数组）
- [ ] 无 blocking unknown/open question 时才可 `ok`
- [ ] assumption 状态为 `unconfirmed`，unknown 状态为 `unknown`

---

## 18. 条件性/N-A/Deferred

**[Required | L1/L2/L3]** — 见 [design-standard.md §4.1](../../../docs/standards/design-standard.md#41-字段分层说明)

- [ ] `coverage` 记录各区域状态（designed/not_applicable/deferred）
- [ ] N/A 条目有非空 `rationale`
- [ ] Deferred 条目有 `rationale` 和后续条件
- [ ] 不得静默省略条件性字段

---

## 19. Design Artifact 完整性

**[Required | L1/L2/L3]** — 见 [design-standard.md §5](../../../docs/standards/design-standard.md#5-artifact-身份与版本)

- [ ] `status=ok` 时 `artifacts` 至少一个 `type=design`
- [ ] `design_version` 为有效 SemVer
- [ ] `created_at` 为有效 date-time

---

## 20. G2/Builder Check/Planning 边界

**[Required | L1/L2/L3]** — 见 [design-standard.md §23](../../../docs/standards/design-standard.md#23-g2-与-builder-check-边界)

- [ ] 不输出 `implementation_plan`
- [ ] 不输出 `design_approved`/`gate_approved`/`confirmation_ref`
- [ ] 不输出 GateDecision/Approval
- [ ] `needs_approval` 的 `gate_or_sa` 不为 G2
- [ ] 不声称 G2 binding 已生效

---

## 21. 禁止输出字段

**[Required | L1/L2/L3]** — 见 [design-standard.md §25](../../../docs/standards/design-standard.md#25-禁止行为)

- [ ] 无 `implementation_plan`
- [ ] 无 `design_approved`/`gate_approved`/`confirmation_ref`
- [ ] 无 `gate_decision`/`approval`
- [ ] 无 `code_review_approved`/`testing_approved`
- [ ] 无任务拆解/排期/assignments

---

## 22. 最终状态/完成条件

**[Required | L1/L2/L3]** — 见 [design-standard.md §26](../../../docs/standards/design-standard.md#26-完成条件)

- [ ] `status=ok` 时 Required 字段完整
- [ ] Conditional Required 字段有内容或 N/A 理由
- [ ] 无 blocking unknown/open question
- [ ] 每个设计决策有理由
- [ ] Requirements/Analysis 追踪完整
- [ ] 无禁止字段
