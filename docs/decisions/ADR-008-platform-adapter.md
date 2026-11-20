# ADR-008：平台适配器与能力证据

**状态：** Proposed（P1-001 设计产出，待 ChatGPT 评审）
**日期：** 2026-11-20

## 背景

P0 已确定 L6 是平台适配边界：核心依赖抽象端口，适配器负责发现、元数据、工具、审批和上下文映射。P1 需要明确适配器接口、平台元数据位置和六平台证据规则。

## 问题

如何在不把平台能力假设为普遍能力的前提下，让同一套核心 Skill 运行在六个平台上，并明确：

- 适配器负责什么；
- 平台差异放在哪里；
- 能力缺失如何降级；
- 如何判定“兼容”。

## 候选方案

### 方案 A：核心内平台分支

在核心 Skill/流程中按平台写条件分支。

**优点：** 直接。
**缺点：** 污染核心、不可测试、违反 P0 平台无关原则。

### 方案 B：核心端口 + 平台适配器（选定）

定义 DiscoveryPort、MetadataPort、ToolPort、ContextPort、ApprovalPort、ResultPort；每个平台实现适配器；平台元数据放 `platforms/<platform>/skill-metadata.yaml`。

**优点：** 解耦、可替换、可降级、可逐平台验证。
**缺点：** 需要适配器实现和证据维护。

### 方案 C：每平台独立 Skill 仓库

各平台复制一套 Skill。

**优点：** 平台自由度最高。
**缺点：** 语义漂移、维护成本高、无法保证统一标准。

## 决策

采用**方案 B**：

1. 适配器实现六个核心端口。
2. 平台元数据独立于核心 `SKILL.md` 和 `skill.yaml`。
3. 平台能力缺失时 `not_ready`/降级，不得静默改变核心规则。
4. 每个平台能力状态必须带证据等级：Verified / Documented / Assumed / Unsupported / Unknown。
5. 未在 SDD 语义下实测的能力不得标记 Verified。
6. 六平台清单统一为 OpenClaw、Claude Code、Codex、Cursor、Gemini CLI、OpenCode。

## 理由

- 保持核心平台无关；
- 支持渐进式适配和降级；
- 让兼容性结论可审计；
- 与 ADR-004 的跨平台策略一致，但补充 P1 适配接口与证据规则。

## 影响

- P2/P7 需要实现各平台适配器；
- P7 需要按矩阵逐项实测并更新证据；
- 平台元数据校验器在 P2/P7 实现；
- 不改变 P0 的 L6 边界、R0–R4 或 G6 规则。

## 相关文档

- [platform-adapter-architecture.md](../architecture/platform-adapter-architecture.md)
- [platform-compatibility-matrix.md](../architecture/platform-compatibility-matrix.md)
- [platform-architecture.md](../architecture/platform-architecture.md)
- [ADR-004](./ADR-004-cross-platform.md)
- [ADR-007](./ADR-007-skill-standard.md)
