# ADR-007：Skill 核心规范与分层元数据

**状态：** Proposed（P1-001 设计产出，待 ChatGPT 评审）
**日期：** 2026-11-20

## 背景

P0 已确定 Skill 是专业能力单元，核心 `SKILL.md` 只保留通用字段 `name`、`description`、`requires`，平台字段必须分离。P1 需要把该原则落成可执行规范，支持版本、依赖、IO 契约、测试和发布。

## 问题

如何在不重新设计 P0 架构的前提下，建立一套可指导后续批量 Skill 建设的标准，同时避免：

- 把所有内容塞进一个巨大的 `SKILL.md`；
- 把平台字段重新注入核心规范；
- 只用自然语言描述输入输出；
- 版本、依赖和生命周期无规则。

## 候选方案

### 方案 A：单文件 Skill

所有元数据、执行步骤、IO、测试和平台配置都写入 `SKILL.md`。

**优点：** 简单。
**缺点：** 上下文成本高、平台污染、无法稳定校验、无法版本化。

### 方案 B：核心 + 通用清单 + 平台目录（选定）

- 核心 `SKILL.md`：`name`、`description`、`requires` + 正文执行规范。
- `skill.yaml`：版本、状态、依赖、兼容能力。
- `platforms/<platform>/skill-metadata.yaml`：平台映射。
- `schemas/` + `tests/`：IO 契约与测试。

**优点：** 分层清晰、平台解耦、可校验、可版本化。
**缺点：** 文件较多，需要校验工具（P2/P7）。

### 方案 C：平台分支

每个平台维护独立 Skill 副本。

**优点：** 可充分利用平台特性。
**缺点：** 重复维护、语义漂移，违反 P0 平台无关原则。

## 决策

采用**方案 B**：

1. 核心 `SKILL.md` 只含通用元数据和正文规范。
2. 通用清单 `skill.yaml` 管理版本/依赖/生命周期。
3. 平台元数据独立在 `platforms/<platform>/skill-metadata.yaml`。
4. IO 使用 JSON Schema Draft 2020-12。
5. 版本使用 SemVer 2.0.0。
6. 发布前必须有测试、示例和变更记录。

## 理由

- 与 P0 的「六个核心概念」「平台无关原则」「G4/G5 版本绑定」一致；
- 允许平台差异，但不让平台字段改变核心语义；
- 可被静态校验、测试和审计；
- 为 P2/P7 的编排、适配和验证提供稳定契约。

## 影响

- P1 后续 Skill 必须遵循 `docs/standards/`。
- P2 需要实现 Schema/元数据校验器和 ArtifactManager 对接。
- P7 需要逐平台验证适配器能力。
- 不改变 P0 已验收的六层架构、R0–R4、G1–G6 或 Task Context 决策。

## 相关文档

- [skill-standard.md](../standards/skill-standard.md)
- [skill-metadata-standard.md](../standards/skill-metadata-standard.md)
- [skill-io-contract.md](../standards/skill-io-contract.md)
- [skill-versioning-standard.md](../standards/skill-versioning-standard.md)
- [ADR-002](./ADR-002-skill-standard.md)
- [skill-architecture.md](../architecture/skill-architecture.md)
