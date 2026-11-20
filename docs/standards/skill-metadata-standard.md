# SDD Skill 元数据标准

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** 所有 SDD Skill 的核心元数据、通用清单和平台扩展元数据
**权威关系：** 本文件定义元数据分层与字段归属；核心 Skill 标准见 [skill-standard.md](./skill-standard.md)，平台适配见 [platform-adapter-architecture.md](../architecture/platform-adapter-architecture.md)。

---

## 1. 三层元数据模型

| 层 | 位置 | 作用 | 是否跨平台 |
|----|------|------|------------|
| L1 核心元数据 | `SKILL.md` Frontmatter | 发现、路由、能力需求声明 | 是 |
| L2 通用清单 | `skill.yaml` | 版本、状态、依赖、兼容能力、维护信息 | 是 |
| L3 平台元数据 | `platforms/<platform>/skill-metadata.yaml` | 发现路径、平台字段映射、运行时依赖、调用/审批模式 | 否 |

**核心规则：**

- L1 只允许 `name`、`description`、`requires`。不得加入平台专属字段。
- L2 不包含平台专属配置；只描述跨平台的版本、依赖和能力要求。
- L3 不得改变核心输入/输出/验收语义；只负责映射。
- 平台字段缺失或未知时，由适配层降级或标记 `not_ready`，不得静默改变核心行为。

---

## 2. L1：核心元数据（SKILL.md Frontmatter）

```yaml
---
name: skill-name
description: "用途、适用场景和触发条件"
requires:
  runtime: [node>=20]
  tools: [file-read, shell:exec:tests]
  permissions: [fs:read:project, fs:write:project, shell:exec:test]
---
```

### 2.1 字段定义

| 字段 | 必需 | 类型 | 约束 |
|------|------|------|------|
| `name` | 是 | string | 小写字母/数字/连字符；1–64 字符；与目录名一致 |
| `description` | 是 | string | 1–1024 字符；说明用途、适用场景、触发条件；建议 ≤160 字符 |
| `requires` | 否 | object | 平台无关的能力需求声明 |
| `requires.runtime` | 否 | array[string] | 运行环境需求，如 `node>=20`、`python>=3.11` |
| `requires.tools` | 否 | array[string] | 需要的工具能力类别，如 `file-read`、`shell:exec:tests` |
| `requires.permissions` | 否 | array[string] | 需要的最小权限类别；声明需求，不是授权 |

### 2.2 约束

- `name` 必须与 Skill 目录名一致；不得使用大写或空格。
- `description` 必须覆盖“做什么 + 何时用”，用于发现和路由。
- `requires.permissions` 不是权限授予；实际授权由安全控制层按 R0–R4 和 SA 执行。
- 核心 Frontmatter 不包含 `version`、平台名、安装命令、环境变量名或平台工具名。版本在 `skill.yaml`，平台字段在 L3。
- 未知字段应被校验器拒绝或警告；不得静默忽略核心未知字段。

---

## 3. L2：通用清单（skill.yaml）

```yaml
schema_version: 1
name: skill-name
version: 0.1.0
status: draft            # draft | review | tested | published | deprecated | retired | archived
license: MIT
maintainers:
  - role: owner
    id: team-or-user
dependencies:
  skills: []
  tools: [file-read]
compatibility:
  requires_capabilities:
    - skill-discovery
    - skill-metadata
    - tool-invocation
    - context-port
    - artifact-port
    - result-port
  optional_capabilities:
    - approval-port
changelog: CHANGELOG.md
```

### 3.1 字段定义

| 字段 | 必需 | 说明 |
|------|------|------|
| `schema_version` | 是 | 清单格式版本；当前为 1 |
| `name` | 是 | 必须与 `SKILL.md` 一致 |
| `version` | 是 | SemVer 2.0.0，见版本标准 |
| `status` | 是 | 生命周期状态 |
| `license` | 推荐 | 许可证标识 |
| `maintainers` | 推荐 | 负责人/团队 |
| `dependencies.skills` | 否 | 依赖的 Skill 名称 + 兼容版本范围 |
| `dependencies.tools` | 否 | 通用工具能力类别 |
| `compatibility.requires_capabilities` | 否 | 需要的核心端口能力，不是平台名 |
| `compatibility.optional_capabilities` | 否 | 可选能力；缺失时可降级 |
| `changelog` | 否 | 变更记录路径 |

- `compatibility.requires_capabilities` 必须使用 [Capability Registry](../architecture/platform-adapter-architecture.md#21-capability-registry统一能力标识) 的唯一标识；不得自造别名。
- `artifact-port` 的 Artifact 读写由 ContextPort 提供，不新增端口。

**禁止：**

- 在 `skill.yaml` 中写平台专属配置（如安装命令、平台环境变量、平台工具名）。
- 用 `compatibility` 声明“某平台已验证”，除非有证据并注明证据来源。
- 用 `dependencies` 隐式依赖未声明的 Skill 或全局状态。

---

## 4. L3：平台元数据

### 4.1 路径与格式

每个平台维护一个目录：

```text
platforms/
├── common/
│   ├── compatibility.md
│   └── testing-guide.md
├── openclaw/
│   └── skill-metadata.yaml
├── claude-code/
│   └── skill-metadata.yaml
├── codex/
│   └── skill-metadata.yaml
├── cursor/
│   └── skill-metadata.yaml
├── gemini-cli/
│   └── skill-metadata.yaml
└── opencode/
    └── skill-metadata.yaml
```

`skill-metadata.yaml` 是**平台级 Skill 目录**，按 Skill 名称索引；一个文件可以包含多个 Skill 的平台映射。

```yaml
schema_version: 1
platform: openclaw
adapter_version: 0.1
skills:
  requirements-clarity:
    discovery:
      roots: [workspace/skills, workspace/.agents/skills]
    trigger:
      mode: description_match
      aliases: []
      auto_invoke: true
    requirements:
      bins: []
      env: []
      config: []
    invocation:
      mode: native
      tools: [read, write]
    capabilities:
      skill-discovery: true
      skill-metadata: true
      tool-invocation: true
      context-port: true
      artifact-port: true
      approval-port: false
    approval:
      mode: platform
    context:
      base_dir_token: "{baseDir}"
    limitations:
      - "SDD Skill 语义尚未实测"
```

### 4.2 字段归属

| 字段 | 归属 | 说明 |
|------|------|------|
| `discovery.roots` | 平台 | 平台扫描路径 |
| `trigger.mode` / `aliases` / `auto_invoke` | 平台 | 平台触发机制映射 |
| `requirements.bins` / `env` / `config` | 平台 | 平台运行时依赖 |
| `invocation.mode` / `tools` | 平台 | 平台调用和工具名映射；只列 Skill 可见的 ToolPort 工具，ContextPort 内部写工具不列 |
| `approval.mode` | 平台 | 平台审批交互映射 |
| `context.base_dir_token` | 平台 | 平台资源根目录占位符 |
| `limitations` | 平台 | 已知限制和降级说明 |

### 4.3 处理规则

1. **平台不支持某字段**：适配层忽略并记录警告；核心 Skill 仍按通用字段工作。
2. **未知字段**：平台元数据校验器拒绝或警告；不得静默生效。
3. **冲突**：以核心 `SKILL.md` 的输入/输出/验收契约为准；平台元数据不得覆盖。
4. **缺失必需映射**：该 Skill 在该平台标记为 `not_ready`，不得以不安全方式降级。
5. **隔离**：平台元数据不得写入核心 `SKILL.md`、`skill.yaml` 或 `references/`。
6. **证据**：平台能力状态必须引用证据（官方文档 URL、命令/结果、日期），见兼容性矩阵。

---

## 5. 加载与验证顺序

```text
1. 读取 SKILL.md 核心元数据（name/description/requires）
2. 读取 skill.yaml（版本/状态/依赖/兼容能力）
3. 选择平台适配器，读取 platforms/<platform>/skill-metadata.yaml
4. 校验核心字段 → 校验通用清单 → 校验平台字段
5. 解析 requires（runtime/tools/permissions）
6. 平台检查 runtime/tools/config；标记 ready/not_ready
7. 生成可用 Skill 清单（仅暴露 name/description + 平台触发信息）
8. 调用时加载 SKILL.md 正文和按需 references
```

任何一步失败都必须记录原因；不得把“未验证”显示为“可用”。

---

## 6. 上下文成本控制

- L1 元数据：约 100 词以内；只用于发现和路由。
- `SKILL.md` 正文：建议 <500 行；执行步骤和验收标准在内。
- `references/`：按需加载，不进入默认上下文；`SKILL.md` 提供索引。
- L3 平台元数据：不注入核心 Skill 上下文；仅适配层读取。
- 大型资料使用目录索引或分片文件；避免把整本手册塞进 `SKILL.md`。

---

## 7. 校验规则汇总

| 规则 | 级别 |
|------|------|
| `name` 合法且与目录一致 | 错误 |
| `description` 非空且说明触发场景 | 错误 |
| 核心 Frontmatter 无平台字段 | 错误 |
| `requires` 只含通用类别 | 错误 |
| `skill.yaml` name/version/status 有效 | 错误 |
| SemVer 格式有效 | 错误 |
| 平台元数据 schema_version/platform 有效 | 错误 |
| 平台字段不改变核心语义 | 错误 |
| 未知平台字段 | 警告/错误（按适配器策略） |
| 缺少平台必需映射 | `not_ready` |

---

## 8. 示例

- 核心元数据：见第 2 节。
- 通用清单：见第 3 节。
- OpenClaw 平台目录示例：`platforms/openclaw/skill-metadata.yaml`（P1-001 参考 Skill 使用）。
- 其他平台：字段结构相同，具体 `trigger.mode`、`requirements`、`invocation.tools` 由各平台适配器定义；在兼容性矩阵中标注证据来源。

---

## 9. 相关标准

- [skill-standard.md](./skill-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [skill-security-standard.md](./skill-security-standard.md)
- [skill-versioning-standard.md](./skill-versioning-standard.md)
- [platform-adapter-architecture.md](../architecture/platform-adapter-architecture.md)
- [platform-compatibility-matrix.md](../architecture/platform-compatibility-matrix.md)
- [ADR-002](../decisions/ADR-002-skill-standard.md)、[ADR-007](../decisions/ADR-007-skill-standard.md)

---

**当前状态：** P1-001 设计产出，待 ChatGPT 评审。平台字段为设计规范，不代表任何平台已完成 SDD 语义验证。
