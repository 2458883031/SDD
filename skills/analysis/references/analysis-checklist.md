# Analysis 检查清单

用于 `analysis` 自检：

- [ ] `requirements_ref` 存在且 type=requirements；Requirements 内容通过 R1 Schema；
- [ ] 上游 Requirements 没有 blocking 未决项/未解决冲突，或已返回 `needs_input`/`blocked`；
- [ ] 所有含 `data.analysis` 的状态，`source_requirements_ref` 与输入 `requirements_ref` 完全一致；
- [ ] `requirements_traceability` 覆盖 FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/acceptance_criteria/non_goals/source_refs；`analyzed`/`mapped` 有可解析 refs，`retained` 闭环到实际输出（AC 使用 `AC-<id>: <非空 consideration>`），`resolved` 只用 facts/candidate/risk 中的 evidence_refs，且引用完整匹配裸 `[a-f0-9]{64}` 或 `path@version#[a-f0-9]{64}`；SHA 小写、恰好一个且在末尾；多摘要/缺失/重复/额外前后缀/大小写混用/`path#sha256` 均拒绝；Requirements/source_refs/纯 path/陈述/假设和相同规范 SHA 换 path 均不得作为解决证据；不适用/延后有理由；
- [ ] `status=ok` 至少包含一个 type=analysis 的 Artifact；不得用 source_refs 替代 artifacts；
- [ ] Problem Statement 覆盖问题、目标、范围、非目标、约束、已知条件；
- [ ] Technical Context 覆盖技术栈、结构、外部系统、依赖、数据/运行环境、限制、unknown；
- [ ] 至少一个候选方案；单方案时解释其他方案为何不适用/不可行；
- [ ] 每个候选包含 approach、适用需求、优劣、复杂度、成本依据、影响、依赖、风险、证据；
- [ ] 成本/性能/复杂度估计说明依据和置信度，不伪装成精确事实；
- [ ] 可行性覆盖技术/兼容/性能/安全/运维等适用领域；
- [ ] 风险包含 likelihood/impact/severity/severity_basis/mitigation/residual/status；
- [ ] 比较矩阵可解释；加权时有权重来源和方法；
- [ ] 推荐方案存在于候选中；未解决风险存在于风险清单；
- [ ] 推荐不等于 Design 批准；无 design_approved/gate_approved/confirmation_ref；
- [ ] 事实/证据/假设/未知严格区分；evidence_backed 有证据；assumption 仅 unconfirmed；unknown 不得 verified；
- [ ] 未静默删除 Requirements 的关键约束、依赖、未知项或验收标准；
- [ ] 未输出 implementation_plan/design_spec；
- [ ] Artifact 引用符合 ADR-005（path/version/sha256/type/source）；
- [ ] 输出符合 `schemas/output.schema.json`。

参考：[analysis-standard.md](../../../docs/standards/analysis-standard.md)、[requirements-standard.md](../../../docs/standards/requirements-standard.md)、[ADR-009](../../../docs/decisions/ADR-009-predevelopment-artifact-binding.md)（Proposed）
