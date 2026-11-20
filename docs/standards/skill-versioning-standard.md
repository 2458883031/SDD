# SDD Skill 版本、依赖与生命周期标准

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** 所有 SDD Skill 的版本号、依赖、发布、废弃与归档
**权威关系：** 本文件定义版本与生命周期；Skill 结构见 [skill-standard.md](./skill-standard.md)，元数据见 [skill-metadata-standard.md](./skill-metadata-standard.md)。

---

## 1. 版本模型

采用 **Semantic Versioning 2.0.0**：

```text
MAJOR.MINOR.PATCH[-prerelease][+build]
```

| 变更类型 | 版本变化 | 示例 |
|----------|----------|------|
| 不兼容的输入/输出/行为变化 | MAJOR | `1.4.2 → 2.0.0` |
| 向后兼容的新能力/可选字段 | MINOR | `1.4.2 → 1.5.0` |
| 向后兼容的修复/文档/示例 | PATCH | `1.4.2 → 1.4.3` |
| 预发布 | prerelease | `2.0.0-rc.1` |
| 构建元数据 | build | `1.4.3+build.7` |

### 1.1 采用 SemVer 的理由

- 能明确区分破坏性变更与兼容变更；
- 便于 Workflow/Skill 依赖范围解析；
- 与开源生态和包管理器习惯一致；
- 支持预发布和构建元数据。

### 1.2 版本位置

- 版本号写在 `skill.yaml` 的 `version`；
- `SKILL.md` 核心 Frontmatter 不写版本（保持 P0 的 name/description/requires 约束）；
- 契约版本可单独记录在 `schemas/` 的 `$id` 或变更记录中，但必须与 Skill 版本语义一致；
- 平台元数据版本使用 `adapter_version`，与 Skill 版本独立。

---

## 2. 兼容性规则

1. **MAJOR**：删除/重命名字段、改变类型/语义、增加必填输入、改变验收标准、改变权限需求导致不兼容。
2. **MINOR**：增加可选输入、增加可选输出、增加新能力但保持旧行为、放宽合法范围。
3. **PATCH**：修复错误、改进描述/示例、性能优化且不改变契约。
4. 旧 MAJOR 在弃用窗口内保留；不得在同一 MAJOR 内静默改变语义。
5. 预发布版本不得被默认解析为稳定版本；生产 Workflow 不得依赖 prerelease，除非显式允许。

---

## 3. 依赖声明

```yaml
dependencies:
  skills:
    - name: requirements-clarity
      version: ">=1.2.0 <2.0.0"
  tools:
    - file-read
```

### 3.1 规则

- `dependencies.skills` 必须写名称 + SemVer 范围；不得依赖未声明的 Skill。
- `dependencies.tools` 只写通用工具能力类别；平台工具名由适配器映射。
- 依赖必须有向无环；禁止循环依赖。
- 依赖版本范围必须可解析；发布时锁定/记录实际解析结果。
- 核心 Skill 不得依赖某个平台专属实现；平台能力通过 `compatibility.requires_capabilities` 表达。

### 3.2 平台依赖

```yaml
compatibility:
  requires_capabilities:
    - skill-discovery
    - tool-port
    - artifact-port
  optional_capabilities:
    - approval-port
```

- 这是**能力依赖**，不是平台名单。
- 适配器负责判断平台是否具备能力；缺失时降级或 `not_ready`。
- 不得在核心规范中写“仅 OpenClaw 可用”之类的平台绑定。

---

## 4. 生命周期

```text
draft → review → tested → published → deprecated → retired → archived
```

| 状态 | 含义 | 允许的操作 |
|------|------|------------|
| draft | 开发中，契约可能变化 | 编辑、试验 |
| review | 等待独立设计/规范审查 | 只读审查、修改后重审 |
| tested | 通过结构/Schema/正常/异常/安全测试 | 准备发布 |
| published | 可用资产，版本固定 | 使用、引用 |
| deprecated | 不推荐新使用，兼容窗口内可用 | 迁移、修复 |
| retired | 不再接受新引用，保留历史产物可读 | 只读 |
| archived | 只读归档 | 审计、历史查阅 |

### 4.1 状态转换规则

- `draft → review`：提交设计、Schema、测试用例。
- `review → tested`：独立审查通过且测试通过。
- `tested → published`：版本号确定，产物/示例/变更记录完整。
- `published → deprecated`：发布弃用公告、替代方案、截止版本/日期。
- `deprecated → retired`：兼容窗口结束；不再新增引用。
- `retired → archived`：历史产物归档。

禁止从 `retired/archived` 直接恢复同一版本；需要重新发布时创建新版本。

---

## 5. 变更记录

每个发布 Skill 必须有 `CHANGELOG.md` 或在 `skill.yaml` 指定变更记录路径，至少包含：

- 版本号与日期；
- 新增/修改/修复/删除；
- 破坏性变更与迁移说明；
- 依赖变化；
- 平台适配变化；
- 未验证事项。

---

## 6. 废弃与替代

弃用必须提供：

1. 弃用原因；
2. 替代 Skill/版本；
3. 兼容截止版本或日期；
4. 迁移步骤；
5. 未迁移风险。

不得直接删除仍在兼容窗口内的 Skill 版本或历史产物。

---

## 7. 发布与资产规则

- 发布前必须有：`SKILL.md`、`skill.yaml`、Schema（如适用）、测试用例、示例、变更记录。
- 发布版本必须带完整版本号和来源；不得用“latest”作为唯一标识。
- 资产库应保存：名称、版本、状态、hash、依赖、平台能力要求、测试证据。
- 发布后版本不可原地修改；修复必须发新版本。
- 归档保留只读副本；不得覆盖历史。

---

## 8. 示例

```yaml
schema_version: 1
name: requirements-clarity
version: 0.1.0
status: draft
license: MIT
dependencies:
  skills: []
  tools: [file-read]
compatibility:
  requires_capabilities: [skill-discovery, tool-port, artifact-port]
changelog: CHANGELOG.md
```

---

## 9. 相关标准

- [skill-standard.md](./skill-standard.md)
- [skill-metadata-standard.md](./skill-metadata-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [ADR-005](../decisions/ADR-005-task-context.md)

---

**当前状态：** P1-001 设计产出，待 ChatGPT 评审。未实现资产库、发布系统或依赖解析器。
