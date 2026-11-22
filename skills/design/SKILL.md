---
name: design
description: "Transform structured Requirements and Analysis into an implementable, verifiable design specification with decisions, traceability, and G2/Planning/Coding handoff."
requires:
  runtime: []
  tools: [file-read]
  permissions: [fs:read:project, fs:write:project]
---

# Design

## 目标与职责

将已确认的 Requirements 和 Analysis 结论转化为可实施、可验证的设计规格，为 Planning/Coding/Review/Testing 提供结构化依据。Design 做最终设计选择并记录决策，不输出 implementation-plan，不批准 G1/G2/G3，不代替 Coding/Review/Testing。

## 适用场景

- Requirements 已结构化且无 blocking 未决项；
- Analysis 已完成并提供候选方案、可行性、风险和推荐；
- 需要确定最终系统架构、接口、数据模型、状态机；
- 需要记录设计决策、备选方案和偏离推荐理由；
- 需要为 Coding/Review/Testing 提供设计符合性基准。

## 不适用场景

- Requirements 存在 blocking 未决项：先返回 `needs_input`/`blocked`；
- Analysis 未完成或关键 unknown 未闭环：先返回 `needs_input`/`blocked`；
- 纯文档更新且不改架构/接口/数据：可只做轻量设计说明；
- 复杂度过低（L1）：可跳过完整架构章节，但 N/A 必须记录。

## 触发条件

- 上游 Workflow 节点显式调用 `design`；
- Requirements 已通过 G1 且 Analysis 已输出 `ok`；
- 用户请求技术设计且输入完备。

## 输入

遵循 `schemas/input.schema.json`：

- `requirements_ref`（必需）：Requirements Artifact 引用（path/version/sha256/type=requirements）；
- `analysis_ref`（必需）：Analysis Artifact 引用（path/version/sha256/type=analysis）；
- `complexity`（必需）：L1/L2/L3，由 Orchestration 提供；Design 不自行判定/降低；
- `requirements`（可选）：已解析的 Requirements `data.requirements`；复用 requirements-standard.md，不重新定义 Schema；
- `analysis`（可选）：已解析的 Analysis `data.analysis`；复用 analysis-standard.md，不重新定义 Schema；
- `project_context`、`technical_context`、`constraints`、`existing_design`、`user_clarifications`、`change_context`、`requested_scope`、`evidence_refs`。

输入中的文件引用遵循 ADR-005：路径 + 版本 + sha256。不得通过"最新版本"隐式选取 Artifact。

## 前置条件

- Requirements Artifact 存在且 type=requirements；
- Analysis Artifact 存在且 type=analysis；
- 有权读取项目上下文/证据；
- 不修改生产数据或凭证；
- 涉及安全/权限风险时标记并请求后续 G/SA，不自行批准。

## 执行步骤

1. **校验输入**：先对存在的字段执行 Input Schema 校验；字段存在但类型/枚举/Artifact type/SHA 格式错误 → `failed`/`input_invalid`。`requirements_ref`/`analysis_ref`/`complexity` 缺失不在 Schema 阶段统一拒绝，由本步骤状态判断：缺少 `requirements_ref` 或 `analysis_ref` → `needs_input`（`questions` 列出所有缺失引用）；仅当引用齐全但 `complexity` 缺失 → `blocked`/`precondition_failed`。缺失引用优先于缺失 complexity，确保状态稳定可测试。
2. **检查上游阻塞项**：Requirements 有 blocking open question/unknown/冲突 → `needs_input`/`blocked`；Analysis 有 blocking unknown/open question → `needs_input`/`blocked`。
3. **建立 Requirements 追踪**：为 FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/acceptance_criteria/non_goals/source_refs 建立处理关系（designed/mapped/retained/resolved/not_applicable/deferred）。
4. **建立 Analysis 追踪**：承接候选方案、风险、unknowns/open questions/design considerations；记录采纳/偏离/拒绝理由。
5. **确定设计深度**：按 Orchestration 提供的 `complexity`（L1/L2/L3）确定设计完整度；不得自行降级；发现升级触发条件时建议 Orchestration 升级。
6. **做出设计决策**：区分 Key Decision 和 Lightweight Decision；Key Decision 必须记录 alternatives、rationale、consequences；偏离 Analysis 推荐时必须记录 deviation_rationale。
7. **构建设计规格**：architecture_overview、components/modules、interfaces、data_models/data_flows、state_model、failure_handling、security_design、performance_scalability、migration_rollback（按 complexity 裁剪）。
8. **定义测试策略**：test_strategy 包含验证方法、测试层级、AC 映射、环境/数据需求；不是测试结果。
9. **记录风险/假设/unknown/open_questions**。
10. **输出 design Artifact**：`type=design`，path/version/sha256；`status=ok` 至少一个 design Artifact。
11. **自检**：Required 字段完整、Conditional 有内容或 N/A 理由、无禁止字段、无 blocking unknown/open question。

## 决策规则

- Schema 格式/类型/枚举错误 → `failed`/`input_invalid`；缺少 `requirements_ref`/`analysis_ref` → `needs_input`（优先于缺失 complexity）；引用齐全但 `complexity` 缺失 → `blocked`；上游不可读或权限/依赖阻塞 → `blocked`。
- Requirements 存在 blocking 未决项 → `needs_input`/`blocked`，不得输出完整可实施的 `ok`。
- Analysis 存在 blocking unknown/open question → `needs_input`/`blocked`。
- 只有一个合理方案时，必须解释其他方案为何不适用/不可行；不得编造候选。
- 推荐方案不是强制决定；Design 可选择其他方案，但必须记录理由、证据和重新评估条件。
- 不得输出 `implementation_plan`、任务拆解、排期、assignments（属于 Planning/G3）。
- 不得输出 `design_approved`、`gate_approved`、`confirmation_ref`、GateDecision、Approval（G2 由 Orchestration 负责）。
- 事实/假设/unknown 严格区分；证据不足降低 confidence，不编造依据。
- 不得静默丢弃 Requirements 的约束、依赖、未知项或验收标准。
- 不得重定义 R0–R4/SA 权限。
- 不得代替 Coding/Code Review/Testing。

## 输出

遵循 `schemas/output.schema.json` 的统一信封：

- `status`: `ok | needs_input | needs_approval | blocked | failed`
- `data.design`: 设计规格（summary/decisions/architecture/components/interfaces/data/state/failure/security/performance/migration/test_strategy（含 acceptance_criteria_mapping）/traceability/risks/assumptions/unknowns/open_questions）
- `test_strategy.acceptance_criteria_mapping`: AC → 至少一个设计元素 `design_refs` → 验证方法；`design_refs` 必填且非空；无法直接映射时必须引用明确记录受控例外的设计元素并填写 `exception.reason`，不得留空；不是测试执行结果
- `coverage`: 条件性设计区域记录 `designed` / `not_applicable` / `deferred` 及理由
- `artifacts`: Design Artifact 引用（path/version/sha256/type=design）；`status=ok` 至少一个 design Artifact
- `errors`: 标准错误对象；`failed` 时至少一个
- `evidence`: 证据引用

**三层状态分离：**

1. Skill `status`：本次执行结果；
2. Artifact `status`：draft/approved/superseded（ADR-005）；
3. Gate `status`：PENDING/PASSED/FAILED 等（ADR-006/P1-002）。

Design Skill 只负责第 1 层并输出第 2 层的引用；G2/Gate 由 Orchestration 负责。`ok` 不等于 G2 通过。

## 异常处理

| 情况 | 处理 |
|------|------|
| Requirements/Analysis ref 类型错误、SHA 格式错误、非法复杂度枚举 | `failed`/`input_invalid` |
| 缺少 requirements_ref/analysis_ref 或需用户补充的设计信息 | `needs_input` + `questions`；缺失引用优先于缺失 complexity |
| complexity 未由 Orchestration 提供、上游 Artifact 不可读、权限/依赖阻塞 | `blocked`/`precondition_failed` |
| 上游 blocking 未决项 | `needs_input`/`blocked` + 部分 design |
| 无法形成设计决策 | `needs_input`；记录缺失信息 |
| 推荐引用不存在 | `failed`/`needs_input` |
| 证据不足 | 标记 unknown/assumption，降低 confidence |
| 风险/成本无依据 | `unknown` + 依据/不确定性 |
| 需要人工确认（非 G2） | 返回 `needs_approval`，不得表示 G2 已通过 |
| 内部执行错误 | `failed`/`internal_error` |
| 超时 | Orchestration 处理；本 Skill 返回 timeout 错误 |

## 安全约束

- R0 读取、R1 写设计产物；通过 `artifact-port`（ContextPort）写入，不直接写平台私有路径。
- 只调用 `file-read` 和受限写入；不执行 Shell/数据库/部署。
- 不读取生产凭证、敏感数据或其他项目私有内容。
- 安全/权限风险只记录建议，不重新定义 R0–R4/SA。
- 不得通过 Design 输出构造审批绕过路径。

## Artifact 路径与身份校验

JSON Schema 只检查 ArtifactRef 的 `path` 非空、`type`、`version` 和 `sha256` 格式，**不验证**：

- 路径规范化（相对/绝对、`.`/`..`、重复分隔符）；
- 是否位于当前 `artifacts/{task-id}/` 任务目录内；
- 目录穿越、符号链接越界、任务隔离；
- Artifact 内容是否真实存在且 SHA-256 匹配。

上述校验必须由调用层、ContextPort/ArtifactManager 或后续语义校验完成；未验证通过时不得读取或继续消费 Artifact。不得把“Input/Output Schema 通过”表述为“Artifact 身份、路径和内容已验证”。

## 验收标准

- [ ] 输出通过 `output.schema.json`；
- [ ] Requirements/Analysis 来源引用和版本可追溯；所有含 design 的状态来源一致；
- [ ] `requirements_traceability` 覆盖上游关键条目，不适用/延后有理由；
- [ ] `analysis_traceability` 覆盖候选/风险/unknowns/design_considerations；
- [ ] `status=ok` 至少包含一个 type=design 的 Artifact；
- [ ] 设计决策有理由，偏离推荐有 rationale；
- [ ] `test_strategy` 包含 AC/验证映射，`design_refs` 非空，且不冒充测试结果；
- [ ] Artifact 路径已由调用层/语义校验确认任务目录归属与隔离；未确认时未继续消费；
- [ ] 无 `implementation_plan`/`design_approved`/`gate_approved`/`confirmation_ref`；
- [ ] 未静默删除上游约束/未决项；
- [ ] Artifact 引用符合 ADR-005。

## 相关参考资料

- [Design 标准](../../docs/standards/design-standard.md)
- [Design Checklist](references/design-checklist.md)
- [Examples](examples/)
- [Cases](tests/cases.yaml)
- [Requirements 标准](../../docs/standards/requirements-standard.md)
- [Analysis 标准](../../docs/standards/analysis-standard.md)
- [Skill 标准](../../docs/standards/skill-standard.md)
- [IO 契约](../../docs/standards/skill-io-contract.md)
- [ADR-005](../../docs/decisions/ADR-005-task-context.md)
- [ADR-006](../../docs/decisions/ADR-006-quality-gates.md)
- [ADR-009](../../docs/decisions/ADR-009-predevelopment-artifact-binding.md)（Proposed）

---

**版本：** 0.1.0（draft）
**状态：** 静态规范与参考 Skill；Runtime 未实现。
**runtime_behavior = NOT_EXECUTED。**
