# SDD 通用 Skill 标准

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** 所有 SDD Skill 的设计、开发、测试、发布与维护
**权威关系：** 本文件是 P1 Skill 核心规范的权威来源；元数据、IO、安全、版本分别由 `skill-metadata-standard.md`、`skill-io-contract.md`、`skill-security-standard.md`、`skill-versioning-standard.md` 定义。

---

## 1. Skill 的定义与定位

**SDD Skill 是一个可复用的专业能力单元。**

它封装：

- 某项专业能力的知识、方法和判断规则；
- 明确的输入、输出与验收标准；
- 在给定权限和工具范围内可执行的步骤；
- 失败、异常和需要人工介入时的处理约定。

Skill **不是**：

- 一个完整的智能体（Agent）；
- 一条完整的业务工作流（Workflow）；
- 一个运行时编排引擎（Orchestration Engine）；
- 一个工具（Tool）本身；
- 一个平台专属插件。

六个核心概念的权威定义见 [system-architecture.md §2](../architecture/system-architecture.md#2-核心概念权威定义)。本文件只定义 Skill 层面的标准。

## 2. Skill 与其它组件的关系

| 组件 | 与 Skill 的关系 |
|------|-----------------|
| Agent | Agent 执行一个或多个 Skill；Skill 不拥有 Agent 的身份、全局上下文或最终决策权。 |
| Orchestration | 编排引擎决定何时、按什么依赖调用 Skill；Skill 不负责整个 Workflow 的调度。 |
| Workflow | Workflow 通过节点引用 Skill；Skill 是节点的一种能力实现，不是 Workflow 的集合。 |
| Tool | Skill 通过 ToolPort 调用 Tool；Skill 只声明需要的工具和权限，不能自行授予权限。 |
| 其他 Skill | Skill 可以通过明确的产物契约或 `dependencies.skills` 组合；不得隐式依赖其他 Skill 的内部状态。 |
| Platform Adapter | Adapter 负责发现、调用、元数据和审批映射；核心 Skill 不包含平台专属字段。 |

## 3. 职责边界

### 3.1 Skill 自身负责

- 校验输入契约与前置条件；
- 按标准步骤完成专业能力；
- 产出符合输出契约的结构化结果；
- 在安全约束内调用已授权的 Tool；
- 报告成功、失败、需要补充输入或需要审批；
- 记录必要的执行证据（输入引用、输出、错误、所用工具）。

### 3.2 Skill 不负责

- 决定整个任务的 Workflow 或 DAG；
- 自行批准 G1–G6、SA 或 R3/R4 高风险操作；
- 直接绕过 Orchestration 修改全局任务状态；
- 自行创建、删除或改写其他 Skill；
- 持有超出声明的系统权限；
- 将平台专属配置写入核心 `SKILL.md`。

### 3.3 与 Orchestration 的责任分界

| 事项 | Skill | Orchestration |
|------|-------|---------------|
| 输入/输出契约 | 定义并校验 | 传递 Artifact 引用 |
| 单节点执行 | 执行 | 调度与监控 |
| 重试 | 声明可重试条件；执行有限重试 | 按 Workflow 策略决定全局重试 |
| 超时 | 声明建议超时 | 强制执行节点超时 |
| 审批暂停 | 提出审批请求 | 进入 awaiting_approval，等待显式批准 |
| 失败回退 | 返回失败类型与建议 | 决定回退到哪个 Workflow 节点 |
| 任务状态 | 报告节点结果 | 维护 Task Context 状态机 |

## 4. 适用与不适用场景

**适用：**

- 有明确边界、可重复执行的专业能力；
- 需要结构化输入/输出和质量检查的能力；
- 可被多个 Workflow 或 Agent 复用的能力；
- 需要声明权限、工具依赖或平台适配的能力。

**不适用：**

- 需要全局调度、分支决策和跨阶段协调的完整流程（应使用 Workflow）；
- 只包含一个普通工具调用、没有专业知识或验收要求的操作（应使用 Tool）；
- 平台专属的安装、发现或 UI 配置（应使用 Platform Adapter）；
- 无法定义输入、输出或验收标准的模糊任务（应先由需求澄清或设计 Skill 处理）。

## 5. 标准目录结构

```text
skill-name/
├── SKILL.md              # 必需：核心能力说明与执行规范
├── skill.yaml            # 发布/版本化必需：版本、依赖、生命周期
├── references/           # 可选：按需加载的参考资料
├── scripts/              # 可选：可执行辅助脚本
├── assets/               # 可选：输出模板、静态资源
├── tests/                # 发布必需：测试用例与验收样例
├── schemas/              # 有结构化 IO 时必需：输入/输出 JSON Schema
└── examples/             # 推荐：最小输入/输出示例
```

### 5.1 文件与目录规则

| 内容 | 最低要求 |
|------|----------|
| `SKILL.md` | 所有 Skill 必需 |
| `skill.yaml` | 发布、版本化、依赖管理时必需；草稿可暂缺 |
| `schemas/` | 有结构化输入或输出时必需 |
| `tests/` | 发布前必需；至少包含正常、异常、边界用例 |
| `references/` | 仅在确有按需资料时创建 |
| `scripts/` | 仅在确需脚本时创建；脚本必须声明运行时和权限 |
| `assets/` | 仅在需要模板/静态资源时创建 |
| `examples/` | 推荐；至少一个最小示例 |

- 不得为了“目录完整”创建空目录或无意义文件。
- 目录结构必须与平台无关；平台差异放入 `platforms/<platform>/`。
- 较大参考资料拆分到 `references/` 并在 `SKILL.md` 中建立索引；正文只保留执行所需内容。
- 上下文成本原则见 [skill-metadata-standard.md](./skill-metadata-standard.md) 与 [skill-architecture.md](../architecture/skill-architecture.md)。

## 6. SKILL.md 标准

### 6.1 机器可解析元数据

`SKILL.md` 的 YAML Frontmatter **只允许通用字段**：

```yaml
---
name: skill-name
description: "用途、适用场景和触发条件"
requires:
  runtime: []
  tools: []
  permissions: []
---
```

- `name`、`description` 必需；`requires` 可选。
- 详细字段规则见 [skill-metadata-standard.md](./skill-metadata-standard.md)。
- 不得在核心 `SKILL.md` 写入平台专属字段（如 `metadata.openclaw`）。
- 不得把所有执行细节塞进 Frontmatter；正文负责 Agent 可读的执行规范。

### 6.2 Markdown 正文结构

正文必须包含以下章节；简单 Skill 可以精简内容，但不得省略边界：

1. **目标与职责** — 这个 Skill 解决什么问题。
2. **适用场景** — 什么时候使用。
3. **不适用场景** — 什么时候不要使用。
4. **触发条件** — 用户请求或上下文特征。
5. **输入** — 输入契约与引用。
6. **前置条件** — 必需的文件、环境、权限或审批。
7. **执行步骤** — 有序步骤，说明每步目的。
8. **决策规则** — 分支、优先级、升级人工的条件。
9. **输出** — 输出契约、产物路径和格式。
10. **异常处理** — 失败、超时、重试、需补充输入、需审批。
11. **安全约束** — R 级别、Tool、文件/Shell/网络边界；只声明需求，不授予权限。
12. **验收标准** — 可检查的完成条件。
13. **相关参考资料** — references 索引或相关 Skill/Tool。

## 7. 执行模型

Skill 的执行遵循：

```text
接收输入
  → 校验输入/前置条件
  → 解析引用与权限
  → 执行步骤（调用 Tool/读取 references）
  → 产出结构化结果
  → 自检/验收
  → 返回 status + output + evidence
```

- 执行前必须校验输入契约和权限声明；不满足时返回 `needs_input` 或 `blocked`，不得静默降级。
- 中间结果必须可被 Task Context 引用，遵循 [ADR-005](../decisions/ADR-005-task-context.md)。
- 完成条件由 Skill 的验收标准与 Workflow 节点契约共同决定；Skill 只报告自身结果。
- 超时、重试、审批暂停由 Orchestration/平台适配层执行；Skill 提供建议和失败类型。
- 需要人工介入时，Skill 返回 `needs_approval` 并说明所需 G 门禁/SA；Skill 不自行批准。

## 8. Skill 组合

允许的组合方式：

1. **产物组合** — 一个 Skill 读取另一个 Skill 产出的 Artifact（通过路径 + 版本 + hash）。
2. **依赖声明** — 在 `skill.yaml` 的 `dependencies.skills` 中声明，由 Workflow 保证顺序。
3. **嵌套调用** — 由 Orchestration 或 Agent 显式调用，不依赖隐式全局状态。

禁止：

- 读取其他 Skill 的内部实现或私有文件；
- 依赖未声明的 Skill；
- 在 Skill 内实现完整 Workflow 调度；
- 通过平台专属机制绕过核心契约。

## 9. 生命周期

```text
draft → review → tested → published → deprecated → retired → archived
```

- `draft`：开发中，不保证契约稳定。
- `review`：等待独立设计/规范审查。
- `tested`：通过结构、Schema、正常/异常/安全测试。
- `published`：进入可用资产库，版本固定。
- `deprecated`：不再推荐使用，保留兼容窗口。
- `retired`：不再接受新使用，保留历史产物可读。
- `archived`：只读归档，不可重新发布同一版本。

详细规则见 [skill-versioning-standard.md](./skill-versioning-standard.md)。

## 10. 质量原则

1. **单一职责** — 一个 Skill 只解决一类专业问题。
2. **契约优先** — 输入、输出、错误和验收必须可验证。
3. **权限最小化** — 只声明完成任务所需的权限。
4. **平台无关** — 核心规范不依赖任何平台字段。
5. **可组合** — 通过 Artifact 契约组合，不共享内部状态。
6. **可测试** — 有正常、异常、边界和安全用例。
7. **解释 WHY** — 规则要说明原因，而不只是 MUST/NEVER。
8. **不把规划写成已实现** — 未验证能力标记为 Assumed/Unknown。

## 11. 相关标准

- [skill-metadata-standard.md](./skill-metadata-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [skill-security-standard.md](./skill-security-standard.md)
- [skill-versioning-standard.md](./skill-versioning-standard.md)
- [skill-architecture.md](../architecture/skill-architecture.md)
- [platform-adapter-architecture.md](../architecture/platform-adapter-architecture.md)
- [platform-compatibility-matrix.md](../architecture/platform-compatibility-matrix.md)

---

**当前状态：** P1-001 设计产出，待 ChatGPT 评审。未实现 Orchestration/Workflow Runner/GateController/ArtifactManager。
