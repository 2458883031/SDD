# ADR-002：Skill 标准与目录组织

**状态：** 已采纳  
**日期：** 2026-11-20

## 背景

不同平台和工具对 Skill 的定义各异。我们需要统一标准，同时保持跨平台兼容。

## 问题

如何设计 Skill 标准，使其：
- 在 OpenClaw、Claude Code、Codex 等平台通用
- 支持复杂的多步骤工作流
- 便于维护和扩展
- 有良好的发现机制

## 候选方案

### 方案 A：完全自定义格式

定义全新的 Skill 文件格式。

**优点：** 完全控制  
**缺点：** 与现有生态不兼容，移植成本高

### 方案 B：遵循 Anthropic Agent Skills 规范（选定）

参考 [anthropics/skills](https://github.com/anthropics/skills) 的 SKILL.md 格式。

**优点：**
- 已被多个工具支持
- 社区活跃，持续演进
- 明确的元数据和触发机制
- 支持条件激活

**缺点：**
- 部分平台可能有差异
- 需要适配层处理平台特定需求

### 方案 C：混合方案

结合 Superpowers 的流程编排 + Anthropic 的 Skill 格式。

**优点：** 兼顾两者优势  
**缺点：** 实现复杂，维护成本高

## 决策

采用**方案 B：遵循 Anthropic Agent Skills 规范**，并在编排层进行扩展。

核心标准：
```yaml
---
name: skill-name
description: "trigger scenario + core capability"
---
```

目录结构：
```
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

## 理由

1. **兼容性优先** — 采用广泛支持的格式可降低移植成本
2. **社区支持** — Anthropic 规范有明确的演进路径
3. **扩展空间** — 通过编排层补充平台特定需求，而非修改 Skill 格式
4. **学习成本低** — 参考项目已有大量实例

## 优缺点

### 优点
- 成熟的规范
- 工具链支持良好
- 文档丰富

### 缺点
- 需要适配层处理平台差异
- 复杂工作流可能需要额外机制

## 后续影响

- P1 阶段需定义 Schema 验证工具
- P7 阶段需验证各平台兼容性
- 平台适配层需维护兼容性矩阵

## P0-002 修订：通用规范与平台元数据分离

P0-002 明确 Skill 规范分为两层，核心规范不得依赖平台：

### A. 通用核心规范（`skills/**/SKILL.md`）

```yaml
---
name: skill-name
description: "用途、适用场景和触发条件"

# 可选：平台无关的能力需求声明（声明需求，不是授权）
requires:
  runtime: [node>=20]
  tools: [file-read, shell:exec:tests]
  permissions: [fs:read:project, fs:write:project]
---
```

- 只包含 `name`、`description` 和通用 `requires`。
- 不包含 `metadata.openclaw`、平台环境变量、平台 CLI 参数等平台专属字段。
- `requires.permissions` 只是需求声明，实际授予由安全模型决定（见 security-architecture.md）。

### B. 平台适配元数据（`platforms/<platform>/skill-metadata.yaml`）

- 负责发现路径、触发映射、bins/env、调用方式和审批模式。
- 只能影响发现、调用、环境准备和审批映射，不得改变核心 Skill 的输入/输出/验收语义。
- 平台不支持某字段时，适配层忽略并记录警告；必要时降级。
- 六个平台目录统一：Codex、Claude Code、Cursor、Gemini CLI、OpenCode、OpenClaw。

### 字段归属与处理

| 内容 | 归属 | 规则 |
|------|------|------|
| name / description | 核心 | 必需，跨平台 |
| requires.runtime / tools / permissions | 核心 | 平台无关的需求声明 |
| 发现路径 / 触发别名 / bins / env / 调用参数 | 平台元数据 | 不进入核心 |
| 平台扩展字段 | 平台元数据 | 不得改变核心语义 |

详细规则见 [skill-architecture.md](../architecture/skill-architecture.md) 与 [platform-architecture.md](../architecture/platform-architecture.md)。

## 修订记录

- **2026-11-20（P0-002）**：将通用 Skill 核心规范与平台适配元数据分离；核心规范移除平台专属字段；明确 `requires` 为需求声明而非授权。
