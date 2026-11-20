---
name: analysis
description: "Analyze a structured requirements baseline, technical context, candidate solutions, feasibility, risks, and trade-offs to produce an evidence-backed recommendation for Design."
requires:
  runtime: []
  tools: [file-read]
  permissions: [fs:read:project, fs:write:project]
---

# Analysis

## 目标与职责

将已结构化的 Requirements 转化为有证据、有边界、有风险判断的技术分析结果，为 Design 提供候选方案、可行性、风险、比较和推荐依据。Analysis 只提出推荐，不做最终设计。

## 适用场景

- 需求已结构化，需要评估技术可行性和方案；
- 需要分析现状、差距、影响、依赖、风险和候选技术路径；
- 需要为 Design 提供推荐和未解决事项；
- 需求变更后需要重新评估影响。

## 不适用场景

- Requirements 仍有 blocking 未决项：先返回 `needs_input`/`blocked`；
- 需要最终架构/接口/数据模型决策：由 Design 负责；
- 需要 implementation-plan/任务拆解：由 Orchestration Planning/G3 负责；
- 纯咨询且不需要技术分析：使用 consultation 流程。

## 输入

遵循 `schemas/input.schema.json`：

- `requirements_ref`（必需）：Requirements Artifact 引用（path/version/sha256/type=requirements）；
- `requirements`（可选）：已解析的 Requirements `data.requirements`；
- `project_context`、`technical_context`、`constraints`、`existing_analysis`、`evidence_refs`、`change_context`、`requested_scope`。

Requirements 内容由 `skills/requirements-clarity/schemas/output.schema.json` 校验；本 Skill 不复制第二套 Requirements Schema。

## 前置条件

- Requirements 已通过 G1 或明确说明为可分析状态；
- 有权读取项目上下文/证据；
- 不修改生产数据或凭证；
- 涉及安全/权限风险时标记并请求后续 G/SA，不自行批准。

## 执行步骤

1. 校验 Requirements 引用和输入状态；blocking 未决项存在时返回 `needs_input`/`blocked`。
2. 复述问题、目标、范围、非目标、约束和已知条件。
3. 描述技术上下文、系统结构、外部系统、依赖、数据/运行环境、限制和未知。
4. 识别候选方案；每个方案说明 approach、适用需求、优劣、复杂度、成本依据、影响、依赖、风险和证据。
5. 评估可行性领域（技术/资源/兼容/性能/安全/运维/迁移/外部依赖/交付）。
6. 建立风险清单；标注 likelihood/impact/severity/severity_basis/mitigation/residual/status。
7. 建立可解释的比较矩阵；加权时说明权重来源和方法。
8. 形成推荐、依据、权衡、未解决风险、条件、置信度。
9. 汇总事实、假设、未知、blocking/non-blocking 问题、所需证据、验证任务和设计考虑。
10. 输出统一信封；`ok` 只表示 Analysis 完成，不代表 Design 批准/G2 通过/用户确认。

## 决策规则

- 输入缺失/无效 → `failed`/`input_invalid`。
- Requirements 存在 blocking open question/unknown 或未解决冲突 → `needs_input`/`blocked`，不得输出可进入 Design 的 `ok`。
- 只有一个合理方案时，必须输出 `single_solution_rationale` 解释其他方案为何不适用/不可行；不得编造候选。
- 推荐方案必须存在于 `candidate_solutions`；未解决风险必须存在于 `risk_assessment`。
- 推荐不等于设计批准；不得输出 `design_approved`/`gate_approved`/`confirmation_ref`。
- 事实/证据/假设/未知严格区分；证据不足降低 confidence，不编造依据。
- 不得静默删除 Requirements 的约束、依赖、未知项或验收标准；发现问题回指上游，不修改需求。
- 不得输出正式 Design Artifact 或 implementation-plan。

## 输出

遵循 `schemas/output.schema.json` 的统一信封：

- `status`: `ok | needs_input | needs_approval | blocked | failed`
- `data.analysis`: 分析结果（problem/technical/candidates/feasibility/risks/comparison/recommendation/facts/assumptions/unknowns/requirements_traceability/next_steps）
- `artifacts`: Analysis Artifact 引用（path/version/sha256/type=analysis）；`status=ok` 至少一个 analysis Artifact
- `errors`: 标准错误对象；`failed` 时至少一个
- `evidence`: 证据引用

禁止字段：`implementation_plan`、`design_spec`、`design_approved`、`gate_approved`、`confirmation_ref`。

所有包含 `data.analysis` 的状态都必须满足 `source_requirements_ref == input.requirements_ref`。`requirements_traceability` 必须为上游 FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/acceptance_criteria/non_goals/source_refs 建立保留/分析/映射/不适用关系；`analyzed`/`mapped` 必须有可解析 `analysis_refs`，`retained` 必须闭环到实际输出（Acceptance Criterion 使用 `AC-<id>: <非空 consideration>`），`resolved` 只能引用 facts/candidate/risk 中的 evidence_refs，且每个引用必须完整匹配裸 `^[a-f0-9]{64}(?![\s\S])` 或版本化 `^(?!.*(?:^|/)\.\.?(?:/|@))(?!(?:.*[a-f0-9]{64}){2})(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+@(?:0|[1-9][0-9]*)#[a-f0-9]{64}(?![\s\S])`；路径仅 ASCII 字母/数字/`.`/`_`/`-` 段，版本为无前导零的十进制非负整数，SHA-256 小写、恰好一个、位于绝对末尾；不接受 `path#sha256`、多摘要、缺失/重复摘要、额外前后缀、换行/空白或大小写混用；不得使用 source_requirements_ref、普通 source_refs、纯 path 或 user_stated/assumption 陈述作为证据，相同规范 SHA 更换 path 仍视为同一 Artifact；不适用/延后必须说明原因。

## 异常处理

| 情况 | 处理 |
|------|------|
| Requirements ref 缺失/无效 | `failed`/`blocked` |
| 上游 blocking 未决项 | `needs_input`/`blocked` + 部分分析 |
| 无法形成候选/推荐 | `needs_input` 或 `no_recommendation`；不编造 |
| 推荐引用不存在 | `failed`/`needs_input` |
| 证据不足 | 标记 unknown/assumption，降低 confidence |
| 风险/成本无依据 | `unknown` + 依据/不确定性 |
| 需要 G/SA 审批 | 返回 `needs_approval` 建议，不自行批准 |
| 超时 | Orchestration 处理；本 Skill 返回 timeout 错误 |

## 安全约束

- R0 读取、R1 写分析产物；通过 `artifact-port`（ContextPort）写入，不直接写平台私有路径。
- 只调用 `file-read` 和受限写入；不执行 Shell/数据库/部署。
- 不读取生产凭证、敏感数据或其他项目私有内容。
- 安全/权限风险只记录建议，不重新定义 R0–R4/SA。
- 不得通过分析输出构造审批绕过路径。

## 验收标准

- [ ] 输出通过 `output.schema.json`；
- [ ] Requirements 来源引用和版本可追溯；所有含 analysis 的状态来源一致；
- [ ] `requirements_traceability` 覆盖上游关键条目，不适用/延后有理由；
- [ ] `status=ok` 至少包含一个 type=analysis 的 Artifact；
- [ ] 问题/技术上下文/候选方案/可行性/风险/比较/推荐/下一步完整；
- [ ] 事实、证据、假设、未知项严格区分；
- [ ] 推荐引用存在，推荐≠设计批准；
- [ ] 无 implementation_plan/design_spec/design_approved/confirmation_ref；
- [ ] 未静默删除上游约束/未决项；
- [ ] Artifact 引用符合 ADR-005。

## 相关参考资料

- [Analysis 标准](../../docs/standards/analysis-standard.md)
- [Requirements 标准](../../docs/standards/requirements-standard.md)
- [分析检查清单](references/analysis-checklist.md)
- [输入示例](examples/example-input.json)
- [多方案输出示例](examples/example-output.json)
- [单方案输出示例](examples/example-output-single-solution.json)
- [部分分析示例](examples/example-output-partial.json)
- [测试用例](tests/cases.yaml)
- [输入输出契约](../../docs/standards/skill-io-contract.md)
- [ADR-009](../../docs/decisions/ADR-009-predevelopment-artifact-binding.md)（Proposed）

---

**版本：** 0.1.0（draft）
**状态：** 静态规范与参考 Skill；Runtime 未实现。
