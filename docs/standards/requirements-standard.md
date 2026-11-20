# SDD Requirements 标准

**状态：** P1-003-R1 Draft（待 ChatGPT 评审）
**适用范围：** Requirements Clarity 的职责、输入输出、需求事实/假设、变更、G1 边界和 Artifact/Evidence
**权威关系：** 通用 Skill 结构与 IO 信封见 [skill-standard.md](./skill-standard.md) 与 [skill-io-contract.md](./skill-io-contract.md)；Task Context/Artifact 见 [ADR-005](../decisions/ADR-005-task-context.md)；G1 见 [ADR-006](../decisions/ADR-006-quality-gates.md)；前置 Artifact 绑定提案见 [ADR-009](../decisions/ADR-009-predevelopment-artifact-binding.md)（**Proposed，未生效**）。

---

## 1. 职责与非职责

### 1.1 职责

Requirements Skill 负责把用户请求转化为**可评审、可追溯、可验证的需求基线**：

- 解析用户原始请求；
- 识别目标、范围、非目标；
- 拆分功能需求（FR）与非功能需求（NFR）；
- 识别约束、依赖、假设、未知项；
- 识别模糊点、冲突点并生成澄清问题；
- 生成可验证的验收标准；
- 记录需求来源、版本和变更影响；
- 为 Analysis 提供稳定输入。

### 1.2 非职责

Requirements Skill **不负责**：

- 技术方案、架构设计、技术选型；
- 影响范围/可行性/风险的完整技术分析（属于 Analysis）；
- 最终设计、接口/数据模型、测试策略（属于 Design）；
- 开发计划和任务拆解（属于 Orchestration Planning/G3）；
- 批准 G1、G2、G3 或 SA；
- 修改 Workflow、Task Context 状态或 Artifact 全局状态；
- 把 Agent 推断冒充为用户确认。

**权威边界：** Skill 只输出需求专业结果；G1 由 GateController/Approval 执行，见 [ADR-006 §3](../decisions/ADR-006-quality-gates.md)。

---

## 2. 适用场景与不适用场景

### 2.1 适用

- 新功能、系统修改、重构请求，且需求/验收标准不完全明确；
- 需求存在冲突、歧义、缺失非目标或非功能要求；
- 需要为 Analysis/Design 提供结构化需求基线；
- 需求变更需要记录差异和影响；
- 上游 Workflow 节点显式调用。

### 2.2 不适用/可裁剪

| 场景 | 处理 |
|------|------|
| 需求已明确且验收标准完整 | 可直接进入 Analysis；不强制完整澄清 |
| 简单局部修改（L1） | 可按 P1-002 simple-task 跳过 G1/G2/G3；仍需确认影响和测试 |
| 技术咨询、不产生需求基线 | 使用 consultation；不强制本 Skill |
| 明确 Bug 修复 | 可只做轻量需求确认/分析；需求不清晰时再调用本 Skill |
| 纯文档/纯测试任务 | 按 P1-002 任务类型裁剪；不强制 FR/NFR 全套 |

**不得**因为任务简单而伪造需求或跳过安全约束。

---

## 3. 输入契约

遵循 `skills/requirements-clarity/schemas/input.schema.json`：

| 字段 | 必需 | 说明 |
|------|------|------|
| `request` | 是 | 用户原始请求 |
| `project_context` | 否 | 项目上下文摘要；不得含凭证 |
| `constraints` | 否 | 已知业务/技术/时间/安全约束 |
| `existing_requirements` | 否 | 已有需求；字符串兼容旧输入，推荐 Artifact 引用 |
| `change_request` | 否 | 变更原因、请求变更项、上一版需求 Artifact 引用 |

- Artifact 引用使用 `{path, version, sha256, type}`（ADR-005）。
- 不得把平台专属配置、凭证或其它项目私有内容作为输入。
- 输入引用必须可追溯；不得隐式使用“最新版本”。

---

## 4. 输出契约

遵循 `skill-io-contract.md §5` 的统一信封：

```json
{
  "status": "ok | needs_input | needs_approval | blocked | failed",
  "data": {},
  "artifacts": [],
  "errors": [],
  "evidence": []
}
```

`data.requirements` 可包含：

| 字段 | 说明 |
|------|------|
| `goal` | 目标（必需） |
| `scope` | 范围（必需） |
| `non_goals` | 非目标（必需） |
| `constraints` | 约束（必需） |
| `functional_requirements` | FR 数组 |
| `non_functional_requirements` | NFR 数组 |
| `dependencies` | 依赖数组 |
| `assumptions` | Agent 假设（未确认） |
| `unknowns` | 未知项 |
| `open_questions` | 待用户回答的问题 |
| `ambiguities` | 模糊点 |
| `conflicts` | 冲突点 |
| `acceptance_criteria` | 验收标准（字符串或带 verification 的对象） |
| `source_refs` | 需求来源 Artifact 引用 |
| `change_impact` | 变更影响（仅变更场景） |
| `requirements_version` | 需求版本（SemVer；可选但推荐） |

**禁止：**

- `status=ok` 时存在 `blocking=true` 的 `open_questions`/`unknowns` 或未解决冲突；
- 在 Skill 输出中写 `confirmation_ref`、`gate_approved`、`confirmed_by` 或伪造用户确认；
- 用 `artifact_refs` 替代 `artifacts`；
- 静默丢弃未知项/未决问题。

---

## 5. 功能需求（FR）

每条 FR：

```yaml
- id: FR-1
  statement: "用户可以按一个或多个订单状态筛选列表"
  priority: must   # must | should | could
  source_type: user_stated   # user_stated | evidence_backed
  evidence_refs: []          # evidence_backed 时至少一项
```

规则：

1. FR 必须可编号、可验证、可追踪。
2. `priority` 使用 must/should/could，不使用模糊等级。
3. `user_stated` 表示用户明确表达；`evidence_backed` 表示仓库代码/文档可验证，必须有 `evidence_refs`。
4. Agent 推断不得写入 FR；只能进入 `assumptions`。
5. 缺少证据的信息不得伪装成 evidence-backed。

---

## 6. 非功能需求（NFR）

每条 NFR：

```yaml
- id: NFR-1
  category: performance
  statement: "筛选请求保持可用响应时间"
  measurable_target: "p95 < 500ms（10 万订单测试集）"
  source_type: user_stated
  evidence_refs: []
```

- `category`：performance / reliability / security / usability / compatibility / maintainability / observability / other。
- `measurable_target` 必须可度量；不得写“尽快/高性能/友好”等不可验证词。
- 安全/权限 NFR 只声明需求，不重新定义 R0–R4/SA。
- NFR 与验收标准应可映射；无可行验证方式时必须进入 `unknowns` 或 `open_questions`。

---

## 7. 约束和依赖

### 7.1 约束

`constraints` 记录业务、技术、时间、安全、兼容性限制；约束是需求边界，不是授权。

### 7.2 依赖

`dependencies` 记录：

| 字段 | 说明 |
|------|------|
| `id` | DEP-* |
| `name` | 依赖名称 |
| `type` | technical/business/external/service/data/other |
| `description` | 影响/前提 |
| `source_refs` | 证据/引用 |

- 外部依赖、服务、数据依赖必须显式列出；不得隐藏为“实现细节”。
- 依赖需要审批时，标记 G/SA 建议，由 Gate/Approval 处理。

---

## 8. 假设和未知项

### 8.1 事实来源

| 类型 | 含义 | 处理 |
|------|------|------|
| `user_stated` | 用户明确表达 | 可进入 FR/NFR/需求基线 |
| `evidence_backed` | 仓库代码/文档可验证 | 必须提供 `evidence_refs` |
| `assumption` | Agent 推断 | 只能进入 `assumptions`，状态 `unconfirmed` |
| `unknown` | 缺少证据 | 进入 `unknowns`，标注 `blocking` |

### 8.2 规则

1. 未获得用户确认的假设不能自动转为已确认需求。
2. 用户没有回答的问题不能伪造为已解决。
3. `assumptions[].status` 只允许 `unconfirmed`；不得写 confirmed/approved。
4. 阻塞性 unknown/open question 必须使 `status=needs_input` 或 `blocked`，不得 `ok`。
5. 非阻塞未知项可以保留在 `ok` 输出，但不得静默删除。

---

## 9. 模糊点、冲突点及澄清问题

- `ambiguities`：描述不清晰、不可判定之处；`status=open|resolved`。
- `conflicts`：与已有需求/上下文冲突；`status=open|resolved|accepted_risk`。
- `open_questions`：需要用户/上游回答的问题；`blocking` 表示是否阻止进入 Analysis。
- `questions`（`needs_input` 信封字段）用于直接向用户提问；应与 `open_questions` 保持一致。

规则：

- 未解决的 ambiguity/conflict 或 blocking question 不得返回 `ok`。
- 冲突不得由 Agent 自行选择一方；必须列为问题或 accepted_risk（需用户接受）。
- 澄清问题应尽量关联需求 ID，避免泛泛而问。

---

## 10. 验收标准

- 每条验收标准必须可观察/可验证。
- 推荐使用对象形式：`{id, criterion, verification, related_requirement_ids}`。
- 字符串形式保留兼容；字符串也必须可验证，不得使用模糊词。
- 无可行验证方式时，不得伪造验收标准；应列入 `unknowns`/`open_questions`。
- 验收标准是 Analysis/Design/Testing 的输入，不等于 G5 测试结果。

---

## 11. 用户确认与 G1 边界

1. `status=ok` 只代表 Skill 成功完成需求基线，**不代表用户已确认**。
2. 用户确认由 **G1 GateDecision / Approval** 记录；见 [ADR-006 §3](../decisions/ADR-006-quality-gates.md)。
3. Skill 不得生成 `confirmation_ref`、`gate_approved` 或任何伪造确认字段。
4. G1 人工审批条件、跳过规则、失败回退保持 ADR-006 原样；本文件不重新定义。
5. G1 的 Artifact 版本/hash 绑定见 ADR-009 **Proposed**；在 ChatGPT 接受前，不得声称运行时已生效。

---

## 12. Requirements Artifact 版本与 Evidence

- 需求产物使用 ADR-005 Artifact：
  - `type=requirements`；
  - `path` 在 `artifacts/{task-id}/requirements/`；
  - `version` 递增；
  - `sha256` 内容哈希；
  - `source` 引用输入 Artifact。
- `source_refs` 记录需求来源（用户输入/已有需求/上下文引用）。
- 需求变更生成新 version，旧版本标记 `superseded`，不得静默覆盖。
- 用户确认记录在 G1 GateDecision/Approval，不写入 Skill 的 `artifacts` 作为确认事实。
- ADR-009 Proposed 建议 G1 绑定 requirements artifact version+sha256；实际运行时未实现。

---

## 13. 需求变更检测与影响记录

变更输出必须包含 `change_impact`：

```yaml
change_impact:
  previous_ref: {path, version, sha256, type}
  change_reason: "..."
  changed_items: ["FR-1", "AC-1"]
  affected_requirement_ids: ["FR-1", "AC-1"]
  downstream_impact:
    analysis: true
    design: true
    plan: true
  gate_invalidation: [G1, G2, G3]
```

规则：

1. 新版本必须保留原始需求 Artifact 引用和新版本 Artifact。
2. 变更差异、原因、受影响需求条目必须记录。
3. 变更应标记对 Analysis/Design/Plan 的潜在影响。
4. 变更应标记对 G1/G2/G3 既有决策的失效影响。
5. 本阶段只定义静态契约；自动失效 Runtime 未实现。

---

## 14. 安全和权限限制

- Requirements Skill 默认 R0 读取、R1 写需求产物；不访问生产数据/凭证。
- `requires.permissions` 只是声明，不是授权；实际授权按 security-architecture R0–R4/SA。
- 需求涉及安全敏感/外部依赖/生产变更时，标记 G2/G4/SA 建议；不自批。
- 需求文本不得包含原始凭证、密钥、Token 或其它项目私有内容。
- 不得通过需求文档绕过权限、Artifact 路径限制或审计。

---

## 15. 异常处理

| 情况 | 处理 |
|------|------|
| 输入为空/非法 | `failed` + `input_invalid` |
| 目标/验收标准缺失 | `needs_input` + questions |
| 需求冲突 | `needs_input` + conflicts/questions |
| 阻塞性未知项 | `needs_input`/`blocked`，不得 `ok` |
| 需要安全审批 | `needs_approval` 建议，不自行批准 |
| 上下文读取失败 | `blocked`/`internal_error`，不得猜测 |
| 变更输入无法对应旧版本 | `needs_input`，要求提供 previous_ref |
| 超时 | Orchestration 处理；Skill 返回 timeout 错误 |

---

## 16. 验收标准和测试要求

Requirements R1 至少验证：

1. 结构/Schema：输入输出 Draft 2020-12；必填/未知字段/状态 data。
2. FR/NFR 正向/负向：编号、priority、category、measurable_target、source_type、evidence_refs。
3. 事实/假设分离：assumption 只能 unconfirmed；evidence-backed 必须有证据；不得伪造 confirmation。
4. unknown/open_questions：blocking 语义；`ok` 不得含 blocking 未决项。
5. dependencies：类型/来源。
6. acceptance criteria：verification；模糊词拒绝。
7. source_refs/Artifact version/hash。
8. change_impact：previous_ref、差异、原因、下游影响、G1/G2/G3 失效。
9. 需求变更版本：新 version、旧版本 superseded（静态模型）。
10. 旧版本兼容：旧字符串输入/验收标准/6 个既有用例仍通过。
11. `ok` 不等于 G1 通过：测试确认无 confirmation/gate_approved 字段。
12. 全量回归：P1-001/P1-002 校验器、链接、JSON/YAML、重复键。

**运行时状态：** `runtime_behavior = NOT_EXECUTED`。本文件是标准与静态 Schema 契约，不代表 Requirements Runtime 已实现。

---

## 17. 相关标准

- [skill-standard.md](./skill-standard.md)
- [skill-metadata-standard.md](./skill-metadata-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [skill-security-standard.md](./skill-security-standard.md)
- [skill-versioning-standard.md](./skill-versioning-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)
- [ADR-009](../decisions/ADR-009-predevelopment-artifact-binding.md)（Proposed）

---

**P1-003-R1 状态：** Requirements 标准 Draft；Runtime 未实现。
