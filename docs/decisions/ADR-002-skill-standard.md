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
