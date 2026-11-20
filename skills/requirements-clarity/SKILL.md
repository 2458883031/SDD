---
name: requirements-clarity
description: "Clarify an ambiguous software request into an explicit requirements baseline with goal, scope, constraints, acceptance criteria, non-goals and open questions."
requires:
  runtime: []
  tools: [file-read]
  permissions: [fs:read:project, fs:write:project]
---

# Requirements Clarity

## 目标与职责

把用户的原始软件需求转化为可评审的需求基线，明确目标、范围、约束、验收标准、非目标和待确认问题。该 Skill 只负责需求澄清，不负责技术设计、编码或 Workflow 调度。

## 适用场景

- 用户提出新功能、系统修改或重构请求，但范围/验收标准不清晰；
- 需要为后续 analysis/design/coding 提供稳定输入；
- 需要识别需求缺口、冲突和不可验证的表述。

## 不适用场景

- 需求已经明确且验收标准完整（可直接进入 analysis/design）；
- 纯技术咨询，不产生需求基线；
- 需要全局流程调度或 G 门禁审批的任务（由 Orchestration 负责）。

## 触发条件

- 用户说“帮我做……”“实现……”“增加……”“重构……”且缺少明确验收标准；
- 上游 Workflow 节点显式调用 `requirements-clarity`；
- 发现需求存在歧义、冲突或缺失非目标。

## 输入

遵循 `schemas/input.schema.json`：

- `request`（必需）：用户原始需求；
- `project_context`（可选）：项目上下文摘要；
- `constraints`（可选）：已知限制；
- `existing_requirements`（可选）：已有需求引用；允许字符串兼容旧输入，推荐 Artifact 引用（path/version/sha256/type）；
- `change_request`（可选）：变更原因、请求变更项、上一版需求 Artifact 引用。

输入中的文件引用遵循 ADR-005：路径 + 版本 + sha256。

## 前置条件

- 已获得用户原始请求；
- 有权读取项目上下文；
- 不需要修改生产数据或凭证；
- 若涉及安全敏感/外部依赖，标记并请求后续 G 门禁，不在本 Skill 内自行批准。

## 执行步骤

1. **复述请求**：用一句话说明理解的目标。
2. **识别范围**：列出本次包含的内容。
3. **识别非目标**：明确本次不包含的内容。
4. **拆分功能需求**：输出可编号的 FR（must/should/could）。
5. **拆分非功能需求**：输出可度量的 NFR（性能/可靠性/安全/兼容性等）。
6. **提取约束和依赖**：技术、业务、时间、安全、外部服务、数据依赖。
7. **区分事实与假设**：用户原话、证据支持、Agent 假设、未知项分别记录。
8. **发现缺口、模糊点和冲突**：形成 `open_questions`、`unknowns`、`ambiguities`、`conflicts`，不得静默丢弃。
9. **定义验收标准**：每条必须可观察/可验证，并尽量关联需求 ID。
10. **记录来源和变更**：填写 `source_refs`；变更场景填写 `change_impact`。
11. **检查冲突**：与 `existing_requirements`/`project_context` 比对。
12. **输出需求基线**：按输出契约返回结构化结果；`ok` 不代表 G1 已通过或用户已确认。

## 决策规则

- 若缺少目标或验收标准 → `status: needs_input`，返回 `questions`。
- 若需求与已有需求冲突 → `status: needs_input`，列出冲突项。
- 若存在 `blocking=true` 的 `open_questions`/`unknowns` 或未解决冲突 → `status: needs_input` 或 `blocked`，不得返回 `ok`。
- 用户明确表达的内容标记 `user_stated`；仓库文件/代码/文档可验证的信息标记 `evidence_backed` 并提供证据引用；Agent 推断只进入 `assumptions`（`unconfirmed`）；缺少证据的信息进入 `unknowns`。
- 未获得用户确认的假设不得升级为已确认需求；用户未回答的问题不得标记为已解决。
- `status: ok` 只表示 Skill 完成需求基线；G1 用户确认由 GateDecision/Approval 记录，Skill 不伪造 `confirmation_ref`。
- 若涉及安全敏感/外部依赖/生产变更 → 在输出中标记 `needs_approval` 建议，交由 Orchestration/G 门禁处理。
- 若范围无法在不猜测的情况下确定 → 不生成虚假验收标准，返回 `blocked` 或 `needs_input`。
- 不得用“尽快/友好/高性能”等不可验证词作为验收标准；必须转化为可观察条件。

## 输出

遵循 `schemas/output.schema.json` 的统一信封：

- `status`: `ok | needs_input | needs_approval | blocked | failed`
- `data`: 业务输出；`ok` 时包含完整 `requirements`，`needs_input` 时包含 `questions`（可含部分 `requirements`），`needs_approval` 时包含 `approval_request`，`blocked` 时包含 `blocked_reason`
- `requirements` 可包含：
  - `goal`、`scope`、`non_goals`、`constraints`；
  - `functional_requirements`（FR）、`non_functional_requirements`（NFR）；
  - `dependencies`、`assumptions`、`unknowns`、`open_questions`、`ambiguities`、`conflicts`；
  - `acceptance_criteria`（字符串或带 `verification` 的对象）；
  - `source_refs`、`change_impact`、`requirements_version`。
- `artifacts`: 需求文档产物引用（`path/version/sha256/type`）；文件写入通过 `artifact-port`（由 ContextPort 提供）
- `errors`: 标准错误对象；`failed` 时至少一个
- `evidence`: 测试/审查/命令/产物证据引用

不得使用已废弃的 `artifact_refs` 字段。不得在 Skill 输出中写 `confirmation_ref`、`gate_approved` 或伪造用户确认。

## 异常处理

| 情况 | 处理 |
|------|------|
| 输入为空 | 返回 `input_invalid` |
| 目标/验收标准缺失 | 返回 `needs_input` + questions |
| 需求冲突 | 返回 `needs_input` + 冲突项 |
| 存在阻塞性未知项/问题 | 返回 `needs_input` 或 `blocked`，不得返回 `ok` |
| 需求变更 | 输出新 Artifact version + `change_impact`，不得覆盖旧版本 |
| 需要安全审批 | 返回 `needs_approval` 建议，不自行批准 |
| 上下文读取失败 | 返回 `blocked` 或 `internal_error`，不得猜测 |
| 超时 | 由 Orchestration 处理；本 Skill 返回 `timeout` 错误 |

## 安全约束

- R0：读取允许的项目文件；R1：写入需求产物。
- 需求产物写入通过 `artifact-port`（由 ContextPort 提供），不直接写平台私有路径。
- 只调用 `file-read` 和受限写入；不调用 Shell、网络或生产工具。
- 不读取敏感凭证、其他项目或越界路径。
- 涉及安全敏感需求时标记 G2/G4/SA 建议，不自行批准。
- 不把用户输入拼入命令或路径。

## 验收标准

- [ ] 输出通过 `output.schema.json`；
- [ ] `goal/scope/non_goals/constraints/acceptance_criteria` 完整；
- [ ] FR/NFR 可编号、可分类；NFR 有可度量目标；
- [ ] 事实、证据支持、假设、未知项明确区分；
- [ ] 每条验收标准可观察/可验证；
- [ ] 缺口、冲突、模糊点和未决问题已列出，未静默丢弃；
- [ ] 未猜测缺失信息；`ok` 未被当作 G1 通过或用户确认；
- [ ] 未自行批准任何 G/SA；未伪造 confirmation_ref；
- [ ] Artifact 引用符合 ADR-005（path/version/sha256/source）。

## 相关参考资料

- [需求检查清单](references/requirements-checklist.md)
- [输入示例](examples/example-input.json)
- [变更输入示例](examples/example-input-change.json)
- [输出示例](examples/example-output.json)
- [结构化输出示例](examples/example-output-structured.json)
- [变更输出示例](examples/example-output-change.json)
- [测试用例](tests/cases.yaml)
- 通用规范：[skill-standard.md](../../docs/standards/skill-standard.md)
- 需求标准：[requirements-standard.md](../../docs/standards/requirements-standard.md)
- 输入输出契约：[skill-io-contract.md](../../docs/standards/skill-io-contract.md)
- 前置 Artifact 绑定提案：[ADR-009](../../docs/decisions/ADR-009-predevelopment-artifact-binding.md)

---

**版本：** 0.2.0（draft）
**平台元数据：** `platforms/openclaw/skill-metadata.yaml`
