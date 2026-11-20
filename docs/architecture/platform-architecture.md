# 平台适配架构设计

## 1. 概述

平台适配层（L6）把核心定义的统一契约映射到具体 Agent 平台。它是**适配边界**，不是普通意义上的核心向下层；依赖方向与原因见 [system-architecture.md §3](./system-architecture.md#3-架构分层与依赖方向)。

**核心原则：**

- 核心 Skill、Workflow、门禁和产物模型不依赖任何平台专属字段或能力。
- 平台适配层只负责发现、调用、元数据、审批和上下文的映射与降级。
- 未实测的能力必须标记为「设计假设」或「待验证」，不得写成已实现或完全兼容。

## 2. 适配层职责

### 2.1 核心职责

1. **Skill 发现适配** — 把平台的 Skill 扫描/发现机制映射到核心的 DiscoveryPort。
2. **元数据映射** — 把 `platforms/<platform>/skill-metadata.yaml` 映射到平台原生字段；核心 `SKILL.md` 不包含平台字段。
3. **触发语义映射** — 把核心 description/触发条件映射到平台原生触发机制。
4. **工具调用映射** — 实现 ToolPort，把统一工具接口映射到平台 API/CLI。
5. **审批交互适配** — 实现 ApprovalPort，把 G1–G6 的暂停/恢复映射到平台交互。
6. **上下文持久化** — 实现 ContextPort，按 ADR-005 读写 Task Context 与 Artifact。
7. **能力声明与降级** — 声明平台支持度；缺失能力时提供降级路径，不改变核心流程规则。

### 2.2 边界定义

| 层 | 职责 | 不包含 |
|----|------|--------|
| L3 研发能力层 | 业务逻辑、输入输出契约 | 平台特定实现 |
| L6 平台适配层 | 调用机制、API 映射、审批/上下文映射 | 研发流程、门禁规则、产物语义 |

## 3. 平台清单（六个，统一）

所有文档、目录和能力矩阵必须使用以下六个平台，不得遗漏或多出：

- Codex
- Claude Code
- Cursor
- Gemini CLI
- OpenCode
- OpenClaw

## 4. 平台能力矩阵（设计假设，未实测）

> **状态说明：** 下表是**设计假设矩阵**，不是验证结果。除第 5 节列出的 OpenClaw CLI 能力外，P0 阶段没有对任何平台进行 SDD 能力实测。P7 之前不得据此宣称任何平台「兼容」或「支持 SDD」。

| 能力 | Codex | Claude Code | Cursor | Gemini CLI | OpenCode | OpenClaw |
|------|-------|-------------|--------|------------|----------|----------|
| Skill 发现 | 预期原生 | 预期原生 | 预期适配 | 未评估 | 预期适配 | 未验证 |
| SKILL.md 元数据 | 预期原生 | 预期原生 | 预期适配 | 未评估 | 预期适配 | 未验证 |
| 自动触发 | 预期原生 | 预期原生 | 预期不支持 | 预期不支持 | 未评估 | 未验证 |
| 子 Agent | 预期不支持 | 预期适配 | 预期不支持 | 预期不支持 | 预期不支持 | 未验证 |
| 工具调用 | 预期原生 | 预期原生 | 预期原生 | 预期原生 | 预期原生 | 未验证 |
| 文件读写 | 预期原生 | 预期原生 | 预期原生 | 预期原生 | 预期原生 | 未验证 |
| 审批机制 | 预期适配 | 预期原生 | 预期适配 | 预期不支持 | 未评估 | 未验证 |
| 上下文传递 | 预期原生 | 预期原生 | 预期适配 | 预期适配 | 预期适配 | 未验证 |
| Workflow 执行 | 预期不支持 | 预期适配 | 预期不支持 | 预期不支持 | 预期不支持 | 未验证 |

**图例：**

- **预期原生** — 设计假设：平台可能原生提供该能力，未实测。
- **预期适配** — 设计假设：可能需要适配层映射，未实测。
- **预期不支持** — 设计假设：平台可能不提供，未实测。
- **未评估** — 尚未形成设计假设。
- **未验证** — 有候选能力，但未做 SDD 语义验证。

## 5. OpenClaw 已实测能力（证据范围）

以下能力在 2026-11-20、OpenClaw 2026.11.4 上实际验证；证据仅限所列命令和行为，**不能推断** OpenClaw 已完整支持 SDD 的 Agent、Workflow 或安全特性。

| 能力 | 验证方式 | 结果 |
|------|----------|------|
| 向既有会话投递消息 | `openclaw agent --session-key '<key>' --message-file '<file>'` | 成功，消息进入指定会话并返回回复 |
| 读取会话元数据 | `openclaw sessions --json` | 成功，返回会话 key、sessionId、状态、token |
| 读取执行轨迹 | `openclaw sessions tail --session-key '<key>'` | 成功 |
| 健康检查 | `openclaw health` / `openclaw status` | 成功 |
| 列出 Skills | `openclaw skills list` | 成功（平台自带 Skills，不代表 SDD Skill 规范已验证） |

**明确未验证：**

- SDD Skill 的发现、触发和元数据映射
- 子 Agent / `agents team` 的 SDD 协作语义
- Workflow 执行与门禁暂停/恢复
- 审批交互与审计记录
- 与 SDD 产物模型、权限模型的集成
- 任何跨平台兼容性结论

## 6. 适配层目录结构（设计规划）

```text
platforms/
├── common/
│   ├── compatibility.md         # 兼容性总览（与 ADR-004 一致）
│   ├── testing-guide.md         # 验证方法说明
│   └── ports.md                 # 核心端口说明（P1 规划）
├── codex/
│   ├── README.md
│   ├── skill-metadata.yaml
│   └── limitations.md
├── claude-code/
│   ├── README.md
│   ├── skill-metadata.yaml
│   └── limitations.md
├── cursor/
│   ├── README.md
│   ├── skill-metadata.yaml
│   └── limitations.md
├── gemini-cli/
│   ├── README.md
│   ├── skill-metadata.yaml
│   └── limitations.md
├── opencode/
│   ├── README.md
│   ├── skill-metadata.yaml
│   └── limitations.md
└── openclaw/
    ├── README.md
    ├── skill-metadata.yaml
    └── limitations.md
```

> P0 仅定义规划，不创建实际文件。六个平台目录必须保持一致；OpenClaw 不得遗漏。

## 7. 通用 Skill 与平台元数据分离

- 核心 `SKILL.md` 只包含 `name`、`description` 和平台无关的 `requires` 声明。
- 平台元数据只放在 `platforms/<platform>/skill-metadata.yaml`，示例与字段规则见 [skill-architecture.md §3](./skill-architecture.md#3-平台适配元数据)。
- 平台字段不能改变核心 Skill 的输入、输出、验收或权限语义。
- 平台缺少某能力时，由适配层降级并记录；核心流程不引入平台分支。

## 8. 兼容性验证方法

### 8.1 静态验证

1. **Schema 检查** — 核心 `SKILL.md` 符合通用规范。
2. **目录检查** — 平台要求的目录布局与发现路径。
3. **元数据检查** — 平台 `skill-metadata.yaml` 字段合法、无未知字段。
4. **隔离检查** — 核心目录不出现平台专属字段或平台 SDK 引用。

### 8.2 动态验证

1. **发现测试** — 平台能否发现并加载 Skill。
2. **触发测试** — description/触发条件是否正确触发。
3. **工具测试** — ToolPort 映射后的工具调用是否成功。
4. **上下文测试** — 产物是否按 ADR-005 传递。
5. **审批测试** — G1–G6 暂停/恢复是否正确。
6. **Workflow 测试** — DAG、并行、失败路径是否正确。

### 8.3 证据要求

每次验证必须记录：

- 平台名称与版本
- 验证日期
- 执行的命令/步骤
- 期望结果与实际结果
- 产物或日志路径
- 结论：已验证 / 部分验证 / 失败

没有上述证据的能力，只能标记为「设计假设」或「待验证」。

### 8.4 状态标签

| 标签 | 含义 |
|------|------|
| 已验证 | 有可复现证据，注明范围和版本 |
| 部分验证 | 只在受限场景验证 |
| 设计假设 | 基于公开资料或推断，未实测 |
| 待验证 | 计划验证，尚无结论 |
| 不支持 | 有证据表明平台无此能力 |

## 9. 核心原则

1. **不宣称完全兼容** — 明确标注支持程度与证据。
2. **降级策略** — 不支持的功能提供降级方案，不改变核心规则。
3. **文档先行** — 每个平台必须有 README、能力状态和限制说明。
4. **验证驱动** — 兼容性结论必须基于实测证据。
5. **隔离适配** — 平台特定代码和元数据不得进入 `core/` 或核心 `SKILL.md`。
6. **核心独立** — 新增平台只增加适配器与元数据，不修改核心流程。

## 10. 当前状态

- [x] 六平台清单统一（P0-002）
- [x] 平台目录规划包含 OpenClaw
- [x] 能力矩阵明确标注设计假设/未验证
- [x] OpenClaw 已实测能力范围说明
- [ ] 实际平台验证（P7）
- [ ] 各平台 README / 元数据编写（P7）

## 11. 风险与限制

1. **全部 SDD 平台能力未实测** — 矩阵仅为设计假设，P7 前不得作为兼容性结论。
2. **OpenClaw 仅验证 CLI 会话能力** — 不能推断其已支持 SDD 的 Skill、Workflow、审批与安全模型。
3. **平台差异** — 触发、审批、子 Agent 和上下文机制差异较大，可能需要降级。
4. **核心独立性** — 任何平台适配都不得反向要求核心引入平台专属字段。

---

*本文档与 [ADR-004](../decisions/ADR-004-cross-platform.md)、[skill-architecture.md](./skill-architecture.md) 配合使用。*
