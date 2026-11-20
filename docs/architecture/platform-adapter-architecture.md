# SDD 平台适配架构

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** 将 SDD 通用 Skill 映射到 OpenClaw、Claude Code、Codex、Cursor、Gemini CLI、OpenCode 等 Agent 平台
**权威关系：** 核心/适配边界见 [system-architecture.md](./system-architecture.md)，平台能力基线见 [platform-architecture.md](./platform-architecture.md)，证据状态见 [platform-compatibility-matrix.md](./platform-compatibility-matrix.md)。

---

## 1. 目标与边界

平台适配层（L6）负责把核心契约映射到平台，不负责定义研发流程。

**适配层负责：**

- Skill 发现与加载；
- 核心元数据与平台元数据转换；
- ToolPort 映射；
- 上下文/产物注入与结果回传；
- 权限与审批交互映射；
- 平台能力缺失时的降级与 `not_ready` 标记。

**适配层不负责：**

- 定义 Workflow/DAG；
- 定义 G1–G6 规则；
- 定义 R0–R4 权限等级；
- 修改核心 Skill 的输入/输出/验收语义；
- 把平台专属字段注入核心 `SKILL.md`。

---

## 2. 核心端口

| 端口 | 职责 | 关键操作 |
|------|------|----------|
| DiscoveryPort | 发现平台上的 Skill | `list()`, `resolve(name)` |
| MetadataPort | 读取/转换核心元数据与平台元数据 | `loadCore()`, `loadPlatform()`, `validate()` |
| ToolPort | 映射并调用平台工具 | `invoke(tool, args, context)` |
| ContextPort | 注入/读取 Task Context 与 Artifact | `readRef()`, `writeRef()` |
| ApprovalPort | 映射 G/SA 审批交互 | `request()`, `await()`, `record()` |
| ResultPort | 回传 Skill 结果与错误 | `return(result)`, `fail(error)` |

端口接口的权威语义在 [system-architecture.md §2–§3](./system-architecture.md)；本文件只定义适配层实现要求。

### 2.1 Capability Registry（统一能力标识）

Skill、`skill.yaml`、平台元数据和适配器必须使用以下唯一标识。不得为同一能力新增别名或新抽象端口。

| Capability ID | 映射端口 | 默认要求 | 缺失行为 |
|---------------|----------|----------|----------|
| `skill-discovery` | DiscoveryPort | required | `unsupported`/`not_ready` |
| `skill-metadata` | MetadataPort | required | `not_ready`；核心字段无法映射 |
| `tool-invocation` | ToolPort | required | 必需工具缺失 → `blocked`；不得用更高权限工具替代 |
| `context-port` | ContextPort | required | 无法注入 Task Context → `blocked` |
| `artifact-port` | ContextPort（Artifact 读写由 ContextPort 提供，不新增端口） | required | 无法读写产物 → `blocked`；只读降级需显式声明 |
| `approval-port` | ApprovalPort | optional（需要审批的 Skill 视为 required） | 需要审批的操作 → `blocked`，不得自动批准 |
| `result-port` | ResultPort | required | 无法回传结果 → `failed` |

- `artifact-port` **不是新端口**：Artifact 的读写沿用 ContextPort，并遵守 ADR-005。
- `skill.yaml` 的 `compatibility.requires_capabilities` 只能使用本表 ID。
- `requirements-clarity` 的文件写入通过 `artifact-port`（ContextPort）完成，不直接写平台私有路径。
- 平台元数据的 `capabilities` 块必须声明平台适配器是否提供每个能力；未声明视为 Unknown。
- 核心 `requires.tools` 表示工具类别，映射到 `tool-invocation`；`requires.permissions` 映射到安全控制，不是 capability。
- 缺失能力时禁止静默改变核心规则；按上表标记 `not_ready`/`blocked`/降级。

---

## 3. 适配器接口

每个平台适配器必须实现：

```text
loadSkill(skillRef) -> LoadedSkill
discoverSkills(root) -> SkillDescriptor[]
mapMetadata(core, platformMetadata) -> RuntimeMetadata
mapTool(coreTool) -> PlatformTool
injectContext(taskContext) -> RuntimeContext
returnResult(result) -> PlatformResult
checkPermission(required) -> PermissionDecision
requestApproval(gateOrSA, request) -> ApprovalDecision
capabilities() -> CapabilitySet
```

### 3.1 接口规则

- `loadSkill` 只接受核心 Skill 或通用 manifest；平台字段由 `mapMetadata` 注入。
- `mapMetadata` 不得改变 `name`、`description`、输入/输出/验收契约。
- `mapTool` 必须声明映射失败；未知工具返回 `not_ready`，不得猜测替代工具。
- `injectContext` 必须遵守 ADR-005 的路径、版本、hash 和权限边界。
- `checkPermission` 只能返回 `allowed | denied | needs_approval`；不得自行授予权限。
- `requestApproval` 只负责交互映射；审批规则来自 ADR-006/安全架构。
- `capabilities()` 必须返回可验证的能力声明；缺失能力由上层降级。

---

## 4. 平台元数据加载

```text
core SKILL.md + skill.yaml
        ↓
platforms/<platform>/skill-metadata.yaml
        ↓
MetadataPort.validate()
        ↓
RuntimeMetadata（只存在于适配器/运行时）
```

- 平台元数据是平台级目录，按 Skill 名称索引；字段规则见 [skill-metadata-standard.md](../standards/skill-metadata-standard.md)。
- 核心 Skill 不读取 L3 元数据；适配器读取后注入。
- 未知字段/缺失必需字段 → 警告或 `not_ready`；不得静默忽略。

---

## 5. 能力缺失与降级

| 缺失能力 | 处理 |
|----------|------|
| Skill 发现 | 该平台标记 `unsupported`；不声称兼容 |
| 元数据映射 | 使用最小映射；无法映射的核心字段标记 `not_ready` |
| 工具调用 | 映射失败 → `blocked`；不得用更高权限工具替代 |
| 子 Agent/并行 | 降级为串行，并记录降级 |
| 审批交互 | 无法交互 → 需要审批的操作 `blocked`，不得自动批准 |
| 上下文/产物 | 无法读写 → `blocked` 或只读降级 |
| 生命周期/安装 | 只支持手动安装；在矩阵标记 |

降级不得改变核心规则；不得把降级路径写成“完全兼容”。

---

## 6. 六平台适配基线

| 平台 | 适配重点 | 证据状态 |
|------|----------|----------|
| OpenClaw | workspace/`.agents` 发现、`metadata.openclaw` 映射、exec/tools、审批映射 | 部分 CLI 已实测；SDD 语义未验证 |
| Claude Code | `.claude/skills` 发现、SKILL.md、allowed-tools、上下文 | 官方文档；未实测 |
| Codex | `.agents/skills` 发现、SKILL.md、agents/openai.yaml、工具依赖 | 官方文档；未实测 |
| Cursor | Skills 与 Rules 双机制、`.cursor/skills`/rules、插件 | 官方文档；未实测 |
| Gemini CLI | `.gemini/skills`/`.agents/skills`、扩展 skills、激活同意 | 官方文档；未实测 |
| OpenCode | `.opencode/skills`/`.claude/skills`、permission allow/deny/ask | 官方文档；未实测 |

详细能力与证据见 [platform-compatibility-matrix.md](./platform-compatibility-matrix.md)。

---

## 7. 安全要求

- Adapter 不得绕过 R0–R4、SA、G6；
- 平台权限映射失败时默认拒绝；
- 平台专属凭证不进入核心 Skill 或 Task Context；
- 所有工具调用、审批、降级记录审计；
- 平台能力声明必须有证据；未验证能力标记 Documented/Assumed/Unknown。

---

## 8. 实现状态

- 端口接口和平台元数据规范为 P1 设计；
- 没有实现任何平台适配器、ToolPort、ApprovalPort；
- OpenClaw 仅有 CLI 会话/技能清单实测，不代表 SDD 适配完成。

---

## 9. 相关文档

- [platform-architecture.md](./platform-architecture.md)
- [platform-compatibility-matrix.md](./platform-compatibility-matrix.md)
- [skill-metadata-standard.md](../standards/skill-metadata-standard.md)
- [ADR-004](../decisions/ADR-004-cross-platform.md)
- [ADR-008](../decisions/ADR-008-platform-adapter.md)

---

**当前状态：** P1-001 设计产出，待 ChatGPT 评审。未实现任何平台适配器。
