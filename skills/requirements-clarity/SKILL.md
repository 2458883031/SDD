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
- `existing_requirements`（可选）：已有需求引用。

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
4. **提取约束**：技术、业务、时间、安全、兼容性限制。
5. **定义验收标准**：每条必须可观察/可验证。
6. **发现缺口**：列出必须由用户回答的问题。
7. **检查冲突**：与 `existing_requirements`/`project_context` 比对。
8. **输出需求基线**：按输出契约返回结构化结果。

## 决策规则

- 若缺少目标或验收标准 → `status: needs_input`，返回 `questions`。
- 若需求与已有需求冲突 → `status: needs_input`，列出冲突项。
- 若涉及安全敏感/外部依赖/生产变更 → 在输出中标记 `needs_approval` 建议，交由 Orchestration/G 门禁处理。
- 若范围无法在不猜测的情况下确定 → 不生成虚假验收标准，返回 `blocked` 或 `needs_input`。
- 不得用“尽快/友好/高性能”等不可验证词作为验收标准；必须转化为可观察条件。

## 输出

遵循 `schemas/output.schema.json`：

- `status`: `ok | needs_input | needs_approval | blocked | failed`
- `requirements`: `goal/scope/constraints/acceptance_criteria/non_goals`
- `questions`: 待确认问题
- `artifact_refs`: 需求文档产物引用（如生成）
- `errors`: 标准错误对象

## 异常处理

| 情况 | 处理 |
|------|------|
| 输入为空 | 返回 `input_invalid` |
| 目标/验收标准缺失 | 返回 `needs_input` + questions |
| 需求冲突 | 返回 `needs_input` + 冲突项 |
| 需要安全审批 | 返回 `needs_approval` 建议，不自行批准 |
| 上下文读取失败 | 返回 `blocked` 或 `internal_error`，不得猜测 |
| 超时 | 由 Orchestration 处理；本 Skill 返回 `timeout` 错误 |

## 安全约束

- R0：读取允许的项目文件；R1：写入需求产物。
- 只调用 `file-read` 和受限写入；不调用 Shell、网络或生产工具。
- 不读取敏感凭证、其他项目或越界路径。
- 涉及安全敏感需求时标记 G2/G4/SA 建议，不自行批准。
- 不把用户输入拼入命令或路径。

## 验收标准

- [ ] 输出通过 `output.schema.json`；
- [ ] `goal/scope/non_goals/acceptance_criteria` 完整；
- [ ] 每条验收标准可观察/可验证；
- [ ] 缺口和冲突已列出；
- [ ] 未猜测缺失信息；
- [ ] 未自行批准任何 G/SA；
- [ ] Artifact 引用符合 ADR-005。

## 相关参考资料

- [需求检查清单](references/requirements-checklist.md)
- [输入示例](examples/example-input.json)
- [输出示例](examples/example-output.json)
- [测试用例](tests/cases.yaml)
- 通用规范：[skill-standard.md](../../docs/standards/skill-standard.md)
- 输入输出契约：[skill-io-contract.md](../../docs/standards/skill-io-contract.md)

---

**版本：** 0.1.0（draft）
**平台元数据：** `platforms/openclaw/skill-metadata.yaml`
