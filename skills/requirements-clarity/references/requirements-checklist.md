# 需求检查清单

用于 `requirements-clarity` 自检：

- [ ] 目标能用一句话复述；
- [ ] 范围（包含）已列出；
- [ ] 非目标（不包含）已列出；
- [ ] 约束已分类：业务/技术/时间/安全/兼容性；
- [ ] 功能需求已编号（FR-*），并标注 must/should/could；
- [ ] 非功能需求已分类并有可度量目标（NFR-*）；
- [ ] 依赖已列出（技术/业务/外部服务/数据）；
- [ ] 用户明确内容（user_stated）与证据支持内容（evidence_backed）已区分；
- [ ] Agent 推断只进入 assumptions（unconfirmed），未升级为用户事实；
- [ ] 未知项（unknowns）和未决问题（open_questions）已列出，阻塞性已标注；
- [ ] 模糊点和冲突已列出，未静默丢弃；
- [ ] 每条验收标准可观察、可验证；
- [ ] 没有“尽快/友好/高性能”等不可验证词；
- [ ] 与已有需求/上下文无冲突；
- [ ] 需求变更已记录 previous_ref、差异、原因、影响和 Gate 失效；
- [ ] 用户确认由 G1 GateDecision/Approval 记录，未伪造 confirmation_ref；
- [ ] 安全敏感项已标记 G/SA 建议；
- [ ] 未猜测缺失信息；
- [ ] 输出符合 Schema。

参考：[skill-io-contract.md](../../../docs/standards/skill-io-contract.md)、[requirements-standard.md](../../../docs/standards/requirements-standard.md)、[ADR-009](../../../docs/decisions/ADR-009-predevelopment-artifact-binding.md)
