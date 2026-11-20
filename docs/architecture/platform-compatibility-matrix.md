# SDD 六平台兼容性矩阵与证据

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** OpenClaw、Claude Code、Codex、Cursor、Gemini CLI、OpenCode
**权威关系：** 适配职责见 [platform-adapter-architecture.md](./platform-adapter-architecture.md)，P0 设计假设见 [platform-architecture.md](./platform-architecture.md)。

> 本文件是 P1 证据台账，不是“完全兼容”声明。除明确标注 Verified 的项目外，所有能力均未在 SDD 语义下实测。

---

## 1. 证据等级

| 等级 | 含义 |
|------|------|
| **Verified** | 有实际运行测试证据（命令、时间、版本、结果） |
| **Documented** | 官方文档明确支持，但未在 SDD 语义下实测 |
| **Assumed** | 根据资料/相邻能力推断，未验证 |
| **Unsupported** | 官方明确不支持或不存在该机制 |
| **Unknown** | 没有足够证据 |

**禁止：** 将 Documented、Assumed 或 Unknown 写成 Verified。

---

## 2. 能力矩阵

### 2.1 核心 Skill 能力

| 能力 | OpenClaw | Claude Code | Codex | Cursor | Gemini CLI | OpenCode |
|------|----------|-------------|-------|--------|------------|----------|
| SKILL.md 格式 | Documented | Documented | Documented | Documented | Documented | Documented |
| Skill 发现 | Documented | Documented | Documented | Documented | Documented | Documented |
| `name` / `description` 原生 Frontmatter | Documented | Documented | Documented | Documented | Documented | Documented |
| `requires` 原生 Frontmatter | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| SDD Adapter 解析 `requires`（设计） | Assumed | Assumed | Assumed | Assumed | Assumed | Assumed |
| 平台原生 metadata 扩展 | Documented | Documented | Documented | Documented | Documented | Documented |
| SDD 平台 metadata 映射（设计） | Assumed | Assumed | Assumed | Assumed | Assumed | Assumed |
| references/ 按需加载 | Documented | Documented | Documented | Documented | Documented | Unknown |
| scripts/ 辅助脚本 | Documented | Documented | Documented | Documented | Documented | Unknown |
| Tool 调用 | Documented | Documented | Documented | Documented | Documented | Documented |
| 权限控制 | Assumed | Documented | Unknown | Unknown | Unknown | Documented |
| 人工审批/激活同意 | Assumed | Assumed | Unknown | Unknown | Documented | Documented |
| 上下文/产物传递 | Documented | Documented | Documented | Unknown | Unknown | Unknown |
| 生命周期/安装 | Documented | Documented | Documented | Documented | Documented | Documented |
| 运行环境限制 | Documented | Documented | Unknown | Unknown | Unknown | Unknown |
| SDD 全栈语义验证 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |

> **关键区分：**
>
> - **平台原生 Frontmatter**：各平台官方文档定义的 `name`/`description` 等字段。
> - **平台原生 metadata 扩展**：OpenClaw `metadata.openclaw`、Claude Code `allowed-tools`、Codex `agents/openai.yaml`、Cursor Rules/插件、Gemini 扩展、OpenCode metadata/permission 等。
> - **SDD Adapter 解析**：当前**未实现**的适配器设计能力；标记 Assumed，不代表平台原生支持。
> - `requires` 是 SDD 核心字段；没有平台官方文档明确把顶层 `requires` 作为原生 Frontmatter。OpenClaw 使用 `metadata.openclaw` 做 gating，不等于顶层 `requires` 原生支持。
> - SDD 全栈语义仍为 Unknown；不得因为平台支持 `SKILL.md` 就写成 Verified。

### 2.2 说明

- **OpenClaw**：官方文档定义 SKILL.md、`metadata.openclaw`、发现顺序、工具和安装；顶层 `requires` 不是官方原生字段；gating 使用 `metadata.openclaw`。`openclaw skills list` 实际运行成功；SDD 触发语义/映射/审批/Workflow 未实测。
- **Claude Code**：官方文档定义 `.claude/skills`、SKILL.md、`allowed-tools`、渐进披露；`allowed-tools` 是平台原生扩展，不是 SDD 核心 `requires`；未在 SDD 语义下实测。
- **Codex**：官方文档定义 `.agents/skills`、SKILL.md、`agents/openai.yaml`、技能发现和工具依赖；`agents/openai.yaml` 是平台扩展；SDD `requires` 解析未实现。
- **Cursor**：官方文档同时定义 Skills 与 Rules；Skills 支持 SKILL.md、发现路径、插件；权限/审批未验证。
- **Gemini CLI**：官方文档定义 skills、扩展内 skills、发现层级和激活同意；扩展 metadata 是平台原生机制；SDD `requires` 解析未实现。
- **OpenCode**：官方文档定义 `.opencode/skills`、`.claude/skills`、`.agents/skills`、frontmatter 和 `permission` allow/deny/ask；references/scripts/上下文证据不足。
- **SDD Adapter 解析**：所有平台的 Adapter 解析标记为 Assumed，因为 P1-001 未实现任何适配器；不得把该设计能力写成平台原生能力。

> **状态来源：** Documented 均来自 §4 对应平台官方文档；Assumed 为 Adapter 设计推断；Unknown 表示没有足够证据；Verified 仅用于 §3 的 OpenClaw CLI 实测项。

---

## 3. OpenClaw 实测证据

| 能力 | 证据 | 结果 |
|------|------|------|
| CLI 技能清单 | `openclaw skills list`（2026-11-20，OpenClaw 2026.11.4） | 成功返回可用 Skills 清单 |
| 会话投递 | `openclaw agent --session-key '<key>' --message-file '<file>'` | 成功进入既有会话并返回回复 |
| 会话读取 | `openclaw sessions --json` / `sessions tail` | 成功 |
| 健康检查 | `openclaw health` / `status` | 成功 |
| SDD Skill 语义 | 未执行 | **Unknown** |
| SDD 平台元数据映射 | 未执行 | **Unknown** |
| SDD 审批/Workflow | 未执行 | **Unknown** |

> OpenClaw CLI 会话/清单能力已实测，不代表 SDD Skill 体系已在 OpenClaw 兼容。

---

## 4. 官方证据来源

| 平台 | 来源 | 用途 |
|------|------|------|
| OpenClaw | https://docs.openclaw.ai/clawhub/skill-format | SKILL.md、metadata、发现 |
| OpenClaw | https://docs.openclaw.ai/tools/skills | 加载顺序、gating |
| OpenClaw | 本地 `openclaw` 2026.11.4 CLI | 清单/会话实测 |
| Claude Code | https://code.claude.com/docs/en/agent-sdk/slash-commands | Skills、发现、frontmatter |
| Codex | https://developers.openai.com/codex/skills | SKILL.md、discovery、metadata |
| Codex | https://developers.openai.com/plugins/build/skills | agents/openai.yaml、工具依赖 |
| Cursor | https://cursor.com/docs/skills | Skills、发现、结构 |
| Cursor | https://cursor.com/docs/rules | Rules 机制 |
| Gemini CLI | https://geminicli.com/docs/cli/skills/ | Skills、发现、激活 |
| Gemini CLI | https://geminicli.com/docs/cli/creating-skills/ | 创建、扩展内 skills |
| OpenCode | https://opencode.ai/docs/skills/ | SKILL.md、发现、frontmatter、permission |
| 通用 | https://agentskills.io/specification | Agent Skills 开放规范 |
| JSON Schema | https://json-schema.org/draft/2020-12 | IO Schema 版本 |
| SemVer | https://semver.org/ | 版本规则 |

**检索日期：** 2026-11-20。官方文档可能变化；发布或 P7 实测前必须重新核对。

---

## 5. 兼容性判定方法

一个平台只有在以下证据齐备时，才能标记某能力为 Verified：

1. 明确平台版本和运行环境；
2. 执行命令/步骤；
3. 记录期望/实际结果；
4. 保留产物/日志路径；
5. 在 SDD 语义下（不是仅平台自带 Skill）验证；
6. 记录日期和证据来源。

仅有官方文档 → Documented；仅推断 → Assumed；无资料 → Unknown。未验证能力不得写成“支持 SDD”或“完全兼容”。

---

## 6. 当前结论

- 六个平台均支持类似 `SKILL.md` 的 Agent Skills 机制（Documented），但字段、发现路径、审批、权限和上下文机制不同。
- 没有任何平台完成 SDD 全栈兼容性验证。
- OpenClaw 仅 CLI 会话/清单能力 Verified；SDD 语义 Unknown。
- P1-001 的平台适配设计必须按能力降级，不得假设平台能力一致。
- P7 必须逐平台实测并更新本矩阵。

---

## 7. 相关文档

- [platform-adapter-architecture.md](./platform-adapter-architecture.md)
- [platform-architecture.md](./platform-architecture.md)
- [skill-metadata-standard.md](../standards/skill-metadata-standard.md)
- [ADR-004](../decisions/ADR-004-cross-platform.md)
- [ADR-008](../decisions/ADR-008-platform-adapter.md)

---

**当前状态：** P1-001 研究产出，待 ChatGPT 评审。未完成任何平台的 SDD 全栈实测。
