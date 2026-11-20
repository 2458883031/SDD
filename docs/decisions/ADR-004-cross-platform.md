# ADR-004：跨平台兼容策略

**状态：** 已采纳  
**日期：** 2026-11-20

## 背景

SDD 需要支持多个 AI Agent 平台：Codex、Claude Code、Cursor、Gemini CLI、OpenCode 等。

## 问题

如何在保持核心 Skill 统一的同时，适配不同平台的能力差异？

## 候选方案

### 方案 A：单一平台优先

只支持一个平台（如 Claude Code），其他平台暂不考虑。

**优点：** 实现简单  
**缺点：** 锁定平台，丧失灵活性

### 方案 B：完全通用（选定）

核心 Skill 遵循开放规范，平台差异放在适配层。

**优点：**
- 核心能力跨平台
- 新增平台只需适配层
- 符合开放标准趋势

**缺点：**
- 需要定义兼容性边界
- 部分高级特性可能无法完全移植

### 方案 C：平台专属分支

为每个平台维护独立版本。

**优点：** 充分利用平台特性  
**缺点：** 维护成本高，代码重复

## 决策

采用**方案 B：完全通用**策略。

核心原则：
1. **核心 Skill 遵循 Agent Skills 开放规范**
2. **平台差异通过 `platforms/` 目录适配**
3. **不宣称完全兼容，标注实际支持状态**

## 兼容性矩阵

| 能力 | Codex | Claude Code | Cursor | Gemini CLI | OpenCode | OpenClaw |
|------|-------|-------------|--------|------------|----------|----------|
| Skill 发现 | ✅ | ✅ | ⚠️ | ❓ | ⚠️ | ❓ |
| SKILL.md 元数据 | ✅ | ✅ | ⚠️ | ❓ | ⚠️ | ❓ |
| 自动触发 | ✅ | ✅ | ❌ | ❌ | ❓ | ❓ |
| 子 Agent | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❓ |
| 工具调用 | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| 文件读写 | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ |
| 审批机制 | ⚠️ | ✅ | ⚠️ | ❌ | ❓ | ❓ |
| 上下文传递 | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ❓ |
| 工作流执行 | ❌ | ✅ | ❌ | ❌ | ❌ | ❓ |

**图例：**
- ✅ 预期原生支持（P0 未实测）
- ⚠️ 预期通过适配支持
- ❌ 预期不支持
- ❓ 未评估 / 未验证

> 注：本矩阵是**设计假设矩阵**，与 [platform-architecture.md](../architecture/platform-architecture.md) 的平台能力表对齐，P0 未做任何 SDD 平台实测。OpenClaw 的 SDD 能力全部标记为未验证；仅其 CLI 会话投递/读取能力有实测证据（见 platform-architecture.md §5）。P7 实测前不得作为兼容性结论。

## 适配层设计

```
platforms/
├── common/
│   └── compatibility.md    # 兼容性总览
├── codex/
│   ├── README.md           # Codex 适配说明
│   └── skill-metadata.yaml
├── claude-code/
│   ├── README.md           # Claude Code 适配说明
│   └── skill-metadata.yaml
├── cursor/
│   ├── README.md           # Cursor 适配说明
│   └── skill-metadata.yaml
├── gemini-cli/
│   ├── README.md           # Gemini CLI 适配说明
│   └── skill-metadata.yaml
├── opencode/
│   ├── README.md           # OpenCode 适配说明
│   └── skill-metadata.yaml
└── openclaw/
    ├── README.md           # OpenClaw 适配说明
    └── skill-metadata.yaml
```

每个平台 README 包含：
1. 支持的能力清单
2. 已知限制
3. 使用建议
4. 测试状态

## 理由

1. **开放标准** — 遵循社区规范而非私有协议
2. **长期维护** — 单一核心 + 多适配层比多分支更易维护
3. **渐进验证** — 未验证的能力标注为「尚未验证」，避免误导

## 风险

1. **部分能力无法移植** — 如子 Agent 在某些平台不可用
2. **触发语义差异** — 不同平台的 trigger 机制可能不同
3. **审批交互差异** — 人工确认的 UI/UX 在各平台不同

## 后续影响

- P7 阶段需进行实际跨平台测试
- 需要建立兼容性验证工具
- 平台 README 需随版本更新

## 相关文档

- [平台适配架构](../architecture/platform-architecture.md)

## 修订记录

- **2026-11-20（P0-002）**：统一六个平台清单（含 OpenClaw）与平台目录；将 OpenClaw 的 SDD 能力标记为未验证；能力矩阵明确为设计假设；补充平台元数据文件规划。
