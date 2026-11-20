# SDD Skill 输入输出契约与 Schema 标准

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** 所有带结构化输入/输出的 SDD Skill
**权威关系：** 本文件定义 IO 契约；核心 Skill 标准见 [skill-standard.md](./skill-standard.md)，产物管理见 [ADR-005](../decisions/ADR-005-task-context.md)。

---

## 1. 基本原则

1. **契约优先**：输入、输出、错误结果都必须有可验证的契约，不能只依赖自然语言描述。
2. **结构化**：机器可读数据使用 JSON；校验使用 JSON Schema。
3. **可追溯**：输入/输出引用必须带路径、版本和 hash（ADR-005）。
4. **平台无关**：核心 Schema 不包含平台专属字段。
5. **版本化**：契约变化必须遵循版本与兼容规则。

---

## 2. 契约组成

每个 Skill 的 IO 契约至少包括：

| 组成 | 位置 | 必需 |
|------|------|------|
| 输入 Schema | `schemas/input.schema.json` | 有结构化输入时必需 |
| 输出 Schema | `schemas/output.schema.json` | 有结构化输出时必需 |
| 错误 Schema | `schemas/error.schema.json` | 可选；建议统一错误结构 |
| 示例 | `examples/` | 推荐 |
| 文本说明 | `SKILL.md` 的“输入/输出”章节 | 必需 |
| Artifact 引用 | Task Context / runtime | 有文件产物时必需 |

---

## 3. JSON Schema 规范

- 版本：**JSON Schema Draft 2020-12**。
- `$schema`: `https://json-schema.org/draft/2020-12/schema`
- `$id`: 使用仓库内稳定 URI，例如 `https://sdd.local/skills/requirements-clarity/input.schema.json`，仅作为标识，不要求可访问。
- 文件编码 UTF-8，JSON 对象顶层必须是 schema。
- 必须声明 `title`、`type`、`required`、`properties`；对每个字段说明 `description`。
- 默认值使用 `default`；合法范围使用 `minimum`/`maximum`/`minLength`/`maxLength`/`enum`/`pattern` 等。
- 不允许使用自然语言“必填/可选”代替 `required`。
- 不允许依赖未声明的附加字段；默认 `additionalProperties: false`，确需扩展时显式声明。

### 3.1 输入 Schema 示例

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://sdd.local/skills/requirements-clarity/input.schema.json",
  "title": "RequirementsClarityInput",
  "type": "object",
  "additionalProperties": false,
  "required": ["request"],
  "properties": {
    "request": {
      "type": "string",
      "minLength": 1,
      "description": "用户原始需求"
    },
    "project_context": {
      "type": "object",
      "description": "项目上下文摘要",
      "additionalProperties": true
    },
    "constraints": {
      "type": "array",
      "items": { "type": "string" },
      "default": []
    }
  }
}
```

### 3.2 输出 Schema 示例

所有结构化 Skill 使用统一输出信封：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SkillOutputEnvelope",
  "type": "object",
  "additionalProperties": false,
  "required": ["status", "artifacts", "errors", "evidence"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["ok", "needs_input", "needs_approval", "blocked", "failed"]
    },
    "data": { "type": "object" },
    "artifacts": { "type": "array" },
    "errors": { "type": "array" },
    "evidence": { "type": "array" }
  }
}
```

- `data` 的具体结构由各 Skill 的 `output.schema.json` 通过状态条件约束（见 §5.3）。
- `artifacts` 是统一产物引用字段；不再使用 `artifact_refs`。
- 完整可执行 Schema 见 `skills/requirements-clarity/schemas/output.schema.json`。

---

## 4. 输入参数规则

每个参数必须定义：

- 名称：稳定、snake_case 或 camelCase 二选一；同一 Skill 内保持一致。
- 类型：JSON 类型或 `$ref`。
- 是否必填：`required`。
- 默认值：`default`（可选）。
- 合法范围/约束：`enum`、`pattern`、`minimum`、`maxLength` 等。
- 示例：`examples` 或 `examples/` 文件。
- 说明：`description`。

**禁止：**

- 仅用 Markdown 表格描述输入，而没有 Schema。
- 允许未声明字段并将它们当作隐式输入。
- 用平台专属字段作为核心输入。

---

## 5. 输出与错误结果

### 5.1 统一输出信封（权威定义）

**所有 Skill 必须使用以下输出信封；本文件是信封的权威定义。**

```json
{
  "status": "ok",
  "data": {},
  "artifacts": [],
  "errors": [],
  "evidence": []
}
```

| 字段 | 必需 | 说明 |
|------|------|------|
| `status` | 是 | `ok` / `needs_input` / `needs_approval` / `blocked` / `failed` |
| `data` | 视状态 | Skill 业务输出；结构由 `output.schema.json` 按状态约束 |
| `artifacts` | 是 | 本次产生的 Artifact 引用：`{path, version, sha256, type}` |
| `errors` | 是 | 标准错误对象数组；`failed` 时至少一个 |
| `evidence` | 是 | 证据引用：`{type, ref, sha256?, note?}` |

- `artifacts` 是**唯一**的产物字段；`artifact_refs` 已废弃，不得在新 Skill 中使用。
- `evidence` 用于引用测试/审查/命令/产物证据，不替代 `artifacts`；`type` 取 `test|review|command|artifact|other`。
- `data` 不是任意对象：各 Skill 必须通过 `output.schema.json` 给出状态相关结构。

### 5.2 状态与合法输出

| 状态 | `data` 要求 | `errors` 要求 | 说明 |
|------|-------------|----------------|------|
| `ok` | 必须包含完整业务输出（如 `requirements`） | 空 | 成功完成 |
| `needs_input` | 必须包含 `questions`（至少 1 条）；`requirements` 可为部分对象，**不得**强制伪造 `acceptance_criteria` | 可空 | 需要用户补充信息 |
| `needs_approval` | 必须包含 `approval_request`（`gate_or_sa`、`reason`、`impact`、`rollback`）；`requirements` 可为部分对象 | 可空 | 需要 G/SA 审批 |
| `blocked` | 必须包含 `blocked_reason`；`requirements` 可为部分对象 | 可空 | 缺少权限/上下文/依赖 |
| `failed` | 可省略或只含诊断信息 | 至少 1 个错误 | 执行失败；不得强制成功状态的 requirements |

`requirements` 的部分对象允许字段：`goal`、`scope`、`constraints`、`non_goals`；`acceptance_criteria` 仅在已能定义时出现。

### 5.3 错误对象

```json
{
  "code": "input_invalid",
  "message": "request 不能为空",
  "field": "request",
  "retryable": false,
  "details": {}
}
```

标准错误码：

| 错误码 | 含义 | 可重试 |
|--------|------|--------|
| `input_invalid` | 输入不符合 Schema | 否 |
| `precondition_failed` | 前置条件不满足 | 视情况 |
| `permission_denied` | 权限不足/未授权 | 否 |
| `needs_input` | 缺少必要信息 | 是（补充后） |
| `needs_approval` | 需要 G/SA 审批 | 是（批准后） |
| `timeout` | 节点/工具超时 | 视策略 |
| `tool_error` | ToolPort 调用失败 | 视情况 |
| `internal_error` | Skill 内部错误 | 视情况 |

---

## 6. Artifact 引用

遵循 [ADR-005](../decisions/ADR-005-task-context.md)：

```json
{
  "path": "artifacts/task-20261120-a1b2/requirements/requirements.md",
  "version": 1,
  "sha256": "...",
  "type": "requirements"
}
```

- 读取方必须校验 hash；不得隐式使用“最新版本”。
- 跨任务引用必须显式；不得遍历其他任务目录。
- 输出中的 `artifacts` 必须指向允许路径（项目根/artifacts）。

---

## 7. 校验时机

```text
加载时：校验 Schema 文件合法、字段/必需项完整
调用前：校验输入实例
执行后：校验输出实例
发布前：校验示例、测试用例与 Schema 一致
```

- 校验失败时不得继续执行；返回 `input_invalid`/`internal_error` 并记录。
- 平台适配器负责把平台输入映射到核心 Schema；不得跳过校验。
- 参考 Skill 的 Schema 与示例必须同时通过校验。

---

## 8. 兼容性规则

采用“语义化契约版本”：

- 增加可选字段、放宽约束：**Minor**，保持向后兼容。
- 新增必填字段、删除字段、改变类型/语义：**Major**，必须升级主版本。
- 修正描述/示例：**Patch**。
- 旧 Major 版本的契约在弃用窗口内保留；不得静默改变含义。
- 版本号与 Skill 版本（`skill.yaml`）同步遵循 [skill-versioning-standard.md](./skill-versioning-standard.md)。

---

## 9. 与质量门禁的关系

- Skill 的 IO 契约测试是 **Skill 级测试**，属于 [skill-standard.md](./skill-standard.md) 与测试标准。
- Skill 级测试通过不等于 Workflow 的 G4/G5 通过；G4/G5 仍由 ADR-006 定义。
- IO Schema 校验失败应阻止该 Skill 节点通过，不得由下游节点“猜测修复”。

---

## 10. 相关标准

- [skill-standard.md](./skill-standard.md)
- [skill-metadata-standard.md](./skill-metadata-standard.md)
- [skill-versioning-standard.md](./skill-versioning-standard.md)
- [ADR-005](../decisions/ADR-005-task-context.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)

---

**当前状态：** P1-001 设计产出，待 ChatGPT 评审。未实现运行时 Schema 校验器或 ArtifactManager。
