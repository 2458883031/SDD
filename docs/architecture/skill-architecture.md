# Skill 架构设计

> **P1-001-R1 文档状态：** §1–§10 是 P0 历史设计基线，保留用于追溯；其中示例/兼容性表不再作为当前有效规范。当前有效规则见 §11 与 `docs/standards/`；平台证据见 [platform-compatibility-matrix.md](./platform-compatibility-matrix.md)。

## 1. 概述

本文件定义 SDD 体系中 Skill 的标准结构、加载机制和编写原则。Skill 的职责边界见 [system-architecture.md §2](./system-architecture.md#2-核心概念权威定义)。

Skill 规范分为两层：

| 层次 | 内容 | 位置 | 是否跨平台 |
|------|------|------|------------|
| **A. 通用 Skill 核心规范** | 名称、描述、通用能力需求声明、正文结构、输入输出契约 | `skills/**/SKILL.md` | 是 |
| **B. 平台适配元数据** | 平台发现路径、触发映射、二进制/环境变量、调用方式 | `platforms/<platform>/skill-metadata.yaml` | 否，由适配层处理 |

**核心规则：核心 SKILL.md 不得包含任何平台专属字段；平台差异不得改变核心 Skill 的语义。**

## 2. Skill 标准结构

### 2.1 目录布局

```text
skill-name/
├── SKILL.md              # 必需：Skill 主文件
├── scripts/              # 可选：可执行脚本
├── references/           # 可选：参考文档
├── assets/               # 可选：输出模板
└── examples/             # 可选：示例用例
```

### 2.2 通用核心元数据（平台无关）

```yaml
---
name: skill-name
description: "Skill 的用途、适用场景和触发条件（建议 160 字符内）"

# 可选：平台无关的能力需求声明（声明需求，不是授权）
requires:
  runtime: [node>=20]                 # 或 python>=3.11 等
  tools: [file-read, shell:exec:tests, git]
  permissions: [fs:read:project, fs:write:project, shell:exec:test]
---
```

**字段归属：**

| 字段 | 归属 | 说明 |
|------|------|------|
| `name` | 核心 | 必需，稳定标识 |
| `description` | 核心 | 必需，用于发现与路由 |
| `requires.runtime` | 核心 | 运行环境需求（平台无关描述） |
| `requires.tools` | 核心 | 需要的工具能力类别 |
| `requires.permissions` | 核心 | 需要的最小权限类别，实际授予由安全模型决定 |
| 平台发现路径 / 触发别名 / bins / env / primaryEnv / 调用参数 | 平台适配层 | 只能出现在 `platforms/<platform>/skill-metadata.yaml` |

**禁止：**

- 在核心 `SKILL.md` 中写 `metadata.openclaw`、平台专属环境变量或平台 CLI 参数。
- 用平台元数据改变核心 Skill 的输入、输出或验收语义。
- 把 `requires.permissions` 当作已授权；它只是需求声明，实际授权见 [security-architecture.md](./security-architecture.md)。

### 2.3 SKILL.md 正文结构

```markdown
# Skill 名称

## 目标与职责
[描述这个 Skill 做什么，解决什么问题]

## 适用场景
- 场景 1
- 场景 2

## 触发条件
- 用户说「XXX」时触发
- 当检测到「YYY」特征时自动触发

## 输入要求
[明确输入格式和必需字段]

## 前置条件
- [ ] 条件 1
- [ ] 条件 2

## 执行步骤
1. 第一步：做什么，为什么
2. 第二步：做什么，为什么
3. ...

## 输出规范
[定义输出格式、文件路径、内容要求]

## 质量检查
- [ ] 检查项 1
- [ ] 检查项 2

## 异常处理
- 异常情况 1：处理方式
- 异常情况 2：处理方式

## 禁止事项
- 禁止做 X
- 禁止做 Y

## 相关 Skill
- [skill-a](../skill-a/SKILL.md)
- [skill-b](../skill-b/SKILL.md)
```

## 3. 平台适配元数据

### 3.1 目录规划

```text
platforms/
├── common/
│   └── compatibility.md
├── codex/
│   └── skill-metadata.yaml
├── claude-code/
│   └── skill-metadata.yaml
├── cursor/
│   └── skill-metadata.yaml
├── gemini-cli/
│   └── skill-metadata.yaml
├── opencode/
│   └── skill-metadata.yaml
└── openclaw/
    └── skill-metadata.yaml
```

> 以上为 P0 设计规划，本阶段不创建实际文件。六个平台清单与目录必须保持一致：Codex、Claude Code、Cursor、Gemini CLI、OpenCode、OpenClaw。

### 3.2 平台元数据示例（P0 历史示例，已由 P1 标准取代）

> 以下示例仅保留 P0 设计历史，不是当前字段定义。当前字段、未知字段处理、缺失能力/降级规则见 [skill-metadata-standard.md](../standards/skill-metadata-standard.md) 与 [Capability Registry](./platform-adapter-architecture.md#21-capability-registry统一能力标识)。

```yaml
# platforms/openclaw/skill-metadata.yaml
skill: skill-name

discovery:
  paths: [skills/]

trigger:
  mode: description_match
  aliases: ["..."]
  auto_invoke: true

requirements:
  bins: []
  env: []
  primaryEnv: ""

invocation:
  adapter: openclaw
  approval_mode: interactive
```

### 3.3 平台字段处理规则

> 以下是 P0 的通用原则；当前字段归属、未知字段、缺失能力和降级处理以 P1 metadata standard 与 Capability Registry 为准。

1. **平台不支持某字段** — 适配层忽略并记录警告；核心 Skill 仍按通用字段工作。
2. **平台扩展字段** — 只能影响发现、调用、环境准备和审批映射，不得改变核心语义。
3. **冲突处理** — 以核心 `SKILL.md` 的输入/输出/验收契约为准；平台元数据不能覆盖。
4. **校验** — P1 的 Skill 校验器同时校验核心字段和平台元数据；平台元数据缺少必需映射时，标记该平台为「不可用/降级」。
5. **降级** — 平台缺失某能力时，由适配层提供降级路径（如串行替代并行），并在平台能力矩阵中标注。

## 4. Skill 如何声明运行环境、依赖和权限

- **运行环境**：`requires.runtime` 使用平台无关的版本约束（如 `node>=20`、`python>=3.11`）。
- **依赖**：`requires.tools` 声明工具类别（如 `shell:exec:tests`），由适配层映射到平台实际工具。
- **权限**：`requires.permissions` 声明最小权限需求，实际授予按 [security-architecture.md](./security-architecture.md) 的 R0–R4、默认拒绝和审批规则执行。
- **就绪检查**：平台适配层在执行前检查 runtime/tools/env；不满足时 Skill 标记为 `not_ready`，不得静默降级为不安全操作。

## 5. 渐进式披露机制

### 5.1 三层加载

| 层级 | 内容 | 加载时机 | 大小限制 |
|------|------|----------|----------|
| L1 | Metadata | 始终 | ~100 词 |
| L2 | SKILL.md body | 触发时 | <500 行 |
| L3 | Bundled resources | 按需 | 无限制 |

### 5.2 使用原则

1. **Metadata 是路由关键** — 描述要全面，覆盖各种触发场景。
2. **SKILL.md 保持精简** — 核心逻辑在内，细节放 references。
3. **按需加载 References** — 大文件用目录索引，避免全量加载。

```markdown
## 参考文档
- [详细规范](references/detailed-spec.md) — 仅当需要完整规范时阅读
- 平台适配说明 — 见 `platforms/<platform>/README.md`
- [故障排查](references/troubleshooting.md) — 常见问题解决方案
```

> 平台专属配置应放在 `platforms/<platform>/`，references 中只保留说明性内容。

## 6. Domain Organization

当 Skill 支持多种技术栈时，按 variant 组织：

```text
deployment/
├── SKILL.md              # 能力入口 + 选择逻辑
└── references/
    ├── docker.md         # Docker 部署
    ├── kubernetes.md     # K8s 部署
    ├── aws.md            # AWS 部署
    └── gcp.md            # GCP 部署
```

> **历史说明：** 原示例中的 `SKILL.md # 工作流 + 选择逻辑` 已修正为“能力入口 + 选择逻辑”。Skill 不实现 Workflow；Workflow 由编排层定义并通过节点引用 Skill。

调用规则：Agent 根据任务上下文决定读取哪个 reference 文件。例如检测到 Dockerfile → 读取 `docker.md`。

## 7. Skill 编写原则

### 7.1 单一职责

每个 Skill 只做一件事，做好一件事。

### 7.2 明确边界

- 输入什么 → 输出什么
- 什么情况触发 → 什么情况不触发
- 能做什么 → 不能做什么
- 需要什么权限 → 不默认拥有权限

### 7.3 解释 WHY

不要只写 MUST/NEVER，要解释为什么重要。

```markdown
# 不好的写法
ALWAYS validate input first!

# 好的写法
Validate input first to prevent cascading failures.
If input is invalid, early rejection saves time and avoids confusing errors later.
```

### 7.4 渐进增强

简单情况走快速路径，复杂情况走完整流程。

```markdown
## 快速路径
如果需求已明确且影响范围小（单文件修改），直接执行编码。

## 完整路径
如果需要分析影响范围或设计新架构，先执行 requirements-clarity。
```

## 8. 平台适配策略

### 8.1 核心 vs 适配

| 内容 | 位置 | 说明 |
|------|------|------|
| 通用逻辑 | `skills/development/*/SKILL.md` | 所有平台通用 |
| 平台元数据 | `platforms/<platform>/skill-metadata.yaml` | 平台专属，不进入核心 |
| 兼容性总览 | `platforms/common/compatibility.md` | 与 `platform-architecture.md` 一致 |

### 8.2 兼容性状态

> **历史摘要：** 以下 P0 状态表不再作为当前证据。当前六平台证据等级与来源见 [platform-compatibility-matrix.md](./platform-compatibility-matrix.md)。

平台能力状态统一在 [platform-architecture.md](./platform-architecture.md) 维护。未实测能力必须标记为「设计假设」或「待验证」，不得写「完全兼容」。

## 9. 测试与验证

### 9.1 CLI 示例标注规则

文档中的 CLI 示例必须标注状态：

- **已验证**：注明验证日期与 OpenClaw 版本。
- **伪代码**：说明不是实际可执行命令。
- **规划示例**：说明对应能力尚未实现。

### 9.2 当前可用的 OpenClaw 命令

| 示例 | 状态 | 说明 |
|------|------|------|
| `openclaw skills list` | 已验证（2026-11-20，2026.11.4） | 列出可用 Skills |
| `openclaw skills info <name>` | 命令存在，未逐项实测 | 查看 Skill 详情 |
| `openclaw agent --session-key '<key>' --message-file '<file>'` | 已验证（2026-11-20，2026.11.4） | 向既有会话投递任务 |
| `openclaw agent --message "..." --skill <name>` | **无效** | 当前 CLI 没有 `--skill` 参数，禁止使用 |
| `/skill <name>` | 伪代码 | 平台 UI 交互示意，未验证 |

### 9.3 集成测试

集成测试用例属于 P5–P7 规划；当前仓库没有可执行测试。

```yaml
# 规划示例：tests/workflow/feature-development.yaml（P5–P7 实现）
name: feature-development
description: "完整功能开发流程测试"
steps:
  - trigger: "帮我做一个用户管理功能"
    expected_skills: [requirements-clarity, analysis, design, coding, testing]
    expected_gates: [G1, G2, G3, G4, G5]
    expected_artifacts: [requirements, analysis, design, implementation, test-report]
```

## 10. 当前状态

- [x] 通用 Skill 规范与平台元数据分离（P0-002）
- [x] 结构规范定义
- [x] CLI 示例状态标注
- [x] P1-001 规范落地（见第 11 节）
- [ ] 模板文件与批量 Skill（P1 后续）
- [ ] 平台适配验证（P7）

## 11. P1-001 规范落地

P1-001 在保留 P0 架构关系的前提下，把 Skill 规范拆成可执行的标准文件：

| 主题 | 权威文档 |
|------|----------|
| Skill 定义、边界、目录、SKILL.md 正文 | [skill-standard.md](../standards/skill-standard.md) |
| 核心/通用/平台元数据分层 | [skill-metadata-standard.md](../standards/skill-metadata-standard.md) |
| 输入输出与 JSON Schema | [skill-io-contract.md](../standards/skill-io-contract.md) |
| 权限、Tool、SA/G6 | [skill-security-standard.md](../standards/skill-security-standard.md) |
| 版本、依赖、生命周期 | [skill-versioning-standard.md](../standards/skill-versioning-standard.md) |
| 平台适配接口 | [platform-adapter-architecture.md](./platform-adapter-architecture.md) |
| 六平台证据矩阵 | [platform-compatibility-matrix.md](./platform-compatibility-matrix.md) |

### 11.1 关键补充

1. **核心 Frontmatter 仍只含 name/description/requires**；版本进入 `skill.yaml`，平台字段进入 `platforms/<platform>/skill-metadata.yaml`。
2. **Skill 不承担 Workflow 调度**：超时、重试、门禁暂停和状态机由 Orchestration 负责；Skill 返回 `ok/needs_input/needs_approval/blocked/failed`。
3. **输入输出必须可验证**：结构化 IO 使用 JSON Schema Draft 2020-12；Artifact 引用遵循 ADR-005。
4. **安全只声明不授权**：`requires.permissions` 是需求；R0–R4/SA/G6 的实际执行由安全控制层负责。
5. **测试分级**：Skill 级测试（元数据/Schema/触发/IO/异常/安全）不等同于 Workflow 的 G4/G5。
6. **版本与依赖**：SemVer 2.0.0；依赖 Skill/Tool/通用能力，依赖平台名不得进入核心。
7. **参考 Skill**：`skills/requirements-clarity/` 作为 P1-001 最小可执行样例，用于验证标准。

### 11.2 与 P0 的关系

- 不改变 P0 的六概念、L6 适配边界、R0–R4、G1–G6 或 Task Context 决策。
- P0 `skill-architecture.md` 继续定义 Skill 的架构关系；P1 standards 提供字段/契约/测试细节。
- 平台能力状态以 [platform-compatibility-matrix.md](./platform-compatibility-matrix.md) 的证据等级为准；未实测能力不得写成 Verified。

### 11.3 历史口径

- §1–§10 的 P0 示例、兼容性摘要和平台字段示例是历史基线，不是当前可复制标准。
- 任何与 P1 `docs/standards/` 冲突的旧示例，以 P1 标准为准，并在后续任务中清理。
- `platforms/<platform>/skill-metadata.yaml` 的当前字段结构以 [skill-metadata-standard.md](../standards/skill-metadata-standard.md) 为准；`artifact-port` 由 ContextPort 提供。
- Capability IDs 以 [Capability Registry](./platform-adapter-architecture.md#21-capability-registry统一能力标识) 为准。

---

**P1-001 状态：** 设计产出，待 ChatGPT 评审。未实现运行时校验器、编排引擎或平台适配器。
