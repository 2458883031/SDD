# 平台适配架构设计

## 概述

平台适配层（L6）负责将核心 Skill 能力适配到不同的 Agent 平台。本设计确保核心逻辑与平台差异分离，避免平台特定代码污染通用规范。

## 适配层职责

### 核心职责

1. **Skill 发现适配** — 不同平台的 Skill 扫描机制不同
2. **触发语义映射** — trigger 描述需转换为平台原生机制
3. **工具调用映射** — 标准工具接口映射到平台 API
4. **子 Agent 协作** — 并行执行能力各平台支持度不同
5. **审批交互适配** — 人工确认的 UI/UX 机制差异
6. **上下文传递** — 任务上下文在各平台的持久化方式

### 边界定义

| 层 | 职责 | 不包含 |
|----|------|--------|
| L3 研发能力层 | 业务逻辑、输入输出契约 | 平台特定实现 |
| L6 平台适配层 | 调用机制、API 映射 | 业务逻辑 |

## 平台能力差异分析

### Codex

| 能力 | 支持状态 | 备注 |
|------|----------|------|
| Skill 发现 | ✅ 原生支持 | 扫描 skills/ 目录 |
| SKILL.md 元数据 | ✅ 支持 | name + description |
| 自动触发 | ✅ 支持 | 基于 description 匹配 |
| 子 Agent | ❌ 不支持 | 无原生子 Agent 机制 |
| 工具调用 | ✅ 支持 | exec/read/write |
| 文件读写 | ✅ 支持 | 标准文件系统 |
| 审批机制 | ⚠️ 部分支持 | 需手动暂停等待 |
| 上下文传递 | ✅ 支持 | 通过文件系统 |
| 工作流执行 | ❌ 不支持 | 无原生工作流引擎 |

**适配策略：**
- 使用串行执行替代并行子 Agent
- 工作流通过 shell 脚本模拟
- 审批通过人工干预点

### Claude Code

| 能力 | 支持状态 | 备注 |
|------|----------|------|
| Skill 发现 | ✅ 原生支持 | 扫描 skills/ 目录 |
| SKILL.md 元数据 | ✅ 支持 | name + description |
| 自动触发 | ✅ 支持 | description 匹配 |
| 子 Agent | ✅ 支持 | sessions_spawn |
| 工具调用 | ✅ 支持 | 完整工具集 |
| 文件读写 | ✅ 支持 | 标准文件系统 |
| 审批机制 | ✅ 支持 | 内置交互 |
| 上下文传递 | ✅ 支持 | session 状态 |
| 工作流执行 | ✅ 支持 | 可编排 |

**适配策略：**
- 原生支持，无需额外适配
- 可直接使用 SDD 核心规范

### Cursor

| 能力 | 支持状态 | 备注 |
|------|----------|------|
| Skill 发现 | ⚠️ 部分支持 | 需配置 extension |
| SKILL.md 元数据 | ⚠️ 部分支持 | 自定义触发规则 |
| 自动触发 | ❌ 不支持 | 需手动调用 |
| 子 Agent | ❌ 不支持 | 无原生支持 |
| 工具调用 | ✅ 支持 | 基础工具 |
| 文件读写 | ✅ 支持 | 编辑器集成 |
| 审批机制 | ⚠️ 部分支持 | 通过 UI |
| 上下文传递 | ⚠️ 部分支持 | 编辑器状态 |
| 工作流执行 | ❌ 不支持 | 无原生支持 |

**适配策略：**
- 主要作为 IDE 辅助工具使用
- 工作流通过命令面板触发
- 限制适用场景

### OpenClaw

| 能力 | 支持状态 | 备注 |
|------|----------|------|
| Skill 发现 | ✅ 原生支持 | 多路径扫描 |
| SKILL.md 元数据 | ✅ 支持 | 完整规范 |
| 自动触发 | ⚠️ 部分支持 | description 匹配 |
| 子 Agent | ✅ 支持 | sessions_spawn |
| 工具调用 | ✅ 支持 | 完整工具集 |
| 文件读写 | ✅ 支持 | 标准文件系统 |
| 审批机制 | ✅ 支持 | 内置交互 |
| 上下文传递 | ✅ 支持 | session 状态 |
| 工作流执行 | ✅ 支持 | 可扩展 |

**适配策略：**
- 原生支持，可作为参考实现
- 支持所有 SDD 特性

### Gemini CLI

| 能力 | 支持状态 | 备注 |
|------|----------|------|
| Skill 发现 | ❓ 未验证 | 需实测 |
| SKILL.md 元数据 | ❓ 未验证 | 需实测 |
| 自动触发 | ❌ 不支持 | 无 Skill 机制 |
| 子 Agent | ❌ 不支持 | 无原生支持 |
| 工具调用 | ✅ 支持 | MCP 集成 |
| 文件读写 | ✅ 支持 | 标准文件系统 |
| 审批机制 | ❌ 不支持 | 无内置机制 |
| 上下文传递 | ⚠️ 部分支持 | 会话状态 |
| 工作流执行 | ❌ 不支持 | 无原生支持 |

**适配策略：**
- 暂不支持 SDD 工作流
- 仅支持基础工具调用
- 标记为"实验性支持"

### OpenCode

| 能力 | 支持状态 | 备注 |
|------|----------|------|
| Skill 发现 | ⚠️ 部分支持 | 社区实现 |
| SKILL.md 元数据 | ⚠️ 部分支持 | 自定义格式 |
| 自动触发 | ❓ 未验证 | 需实测 |
| 子 Agent | ❌ 不支持 | 无原生支持 |
| 工具调用 | ✅ 支持 | 基础工具 |
| 文件读写 | ✅ 支持 | 标准文件系统 |
| 审批机制 | ❓ 未验证 | 需实测 |
| 上下文传递 | ⚠️ 部分支持 | 会话状态 |
| 工作流执行 | ❌ 不支持 | 无原生支持 |

**适配策略：**
- 生态较新，支持度不确定
- P7 阶段专项验证

## 兼容性验证方法

### 静态验证

1. **Schema 检查** — 验证 SKILL.md 符合开放规范
2. **目录结构检查** — 验证平台要求的目录布局
3. **元数据检查** — 验证 name/description 格式

### 动态验证

1. **触发测试** — 验证描述匹配是否正确触发 Skill
2. **执行测试** — 验证工具调用是否成功
3. **上下文测试** — 验证产物传递是否正确
4. **审批测试** — 验证 HARD-GATE 交互是否正常

### 验证矩阵

| 平台 | Schema | 目录 | 触发 | 执行 | 上下文 | 审批 |
|------|--------|------|------|------|--------|------|
| Codex | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Claude Code | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cursor | ⚠️ | ⚠️ | ❌ | ✅ | ⚠️ | ⚠️ |
| OpenClaw | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Gemini CLI | ❓ | ❓ | ❌ | ✅ | ⚠️ | ❌ |
| OpenCode | ⚠️ | ⚠️ | ❓ | ✅ | ⚠️ | ❓ |

**图例：**
- ✅ 已通过验证
- ⚠️ 部分支持/需适配
- ❌ 不支持
- ❓ 未验证

## 适配层目录结构

```
platforms/
├── common/
│   ├── compatibility-matrix.md  # 兼容性总览
│   └── testing-guide.md         # 验证方法说明
├── codex/
│   ├── README.md                # 适配说明
│   ├── limitations.md           # 已知限制
│   └── workarounds.md           #  workaround 方案
├── claude-code/
│   └── README.md                # 原生支持说明
├── cursor/
│   ├── README.md
│   └── limitations.md
├── gemini-cli/
│   ├── README.md
│   └── limitations.md
└── opencode/
    ├── README.md
    └── limitations.md
```

## 平台特定配置

### Codex 配置示例

```yaml
# platforms/codex/config.yaml
adapter:
  skill_discovery: "filesystem_scan"
  trigger_mode: "description_match"
  parallel_execution: false  # 降级为串行
  approval_mode: "manual_pause"

workarounds:
  workflow: "shell_script_simulation"
  subagent: "sequential_tasks"
```

### Cursor 配置示例

```yaml
# platforms/cursor/config.yaml
adapter:
  skill_discovery: "extension_manifest"
  trigger_mode: "command_palette"
  parallel_execution: false
  approval_mode: "ui_dialog"

limitations:
  - "无自动触发"
  - "无原生子 Agent"
  - "工作流需手动编排"
```

## 核心原则

1. **不宣称完全兼容** — 明确标注支持程度
2. **降级策略** — 不支持的功能提供降级方案
3. **文档先行** — 每个平台必须有 README 说明
4. **验证驱动** — 兼容性结论必须基于实测
5. **隔离适配** — 平台特定代码不得进入 core/

## 当前状态

- [x] 平台能力分析完成
- [x] 兼容性矩阵初稿完成
- [ ] 实际验证（P7）
- [ ] 各平台 README 编写（P7）

## 风险与限制

1. **Gemini CLI 和 OpenCode 未实测** — 兼容性矩阵中的 "❓" 项需 P7 验证
2. **Cursor 自动触发不支持** — 可能需要用户手动调用
3. **子 Agent 协作受限** — Codex/Cursor/Gemini/OpenCode 不支持并行执行

---

*本文档应与 ADR-004 配合使用，提供更详细的平台适配指导。*
