# 系统架构设计

## 1. 概述与定位

SDD 采用「核心 + 平台适配边界」的架构，将研发能力、编排规则和工程基础设施放在平台无关的核心中，再由平台适配层把统一契约映射到具体 Agent 平台。

本文件是以下内容的**权威定义来源**：

- 六个核心概念：Agent、Orchestration、Workflow、Skill、Tool、Platform Adapter（第 2 节）
- 核心层与平台适配层的依赖方向（第 3、5 节）
- 平台无关原则（第 7 节）

其他文档引用本文件，不重复定义这些概念。

> **P0 状态：In Review。** 本文档描述的是设计，不代表已经实现。实现阶段见 P1–P7 路线图。

## 2. 核心概念（权威定义）

> 同一概念只能有一个权威定义。本节是六个概念的唯一定义来源；其他文档通过「见 system-architecture.md §2」引用。

| 概念 | 职责定义 | 不应该被理解成 |
|------|----------|----------------|
| **Agent** | 具有角色、任务边界、上下文和权限的智能执行主体。Agent 可以执行一个或多个 Skill，也可以参与一个或多个 Workflow。 | 不是一个平台，也不是一个 Skill。 |
| **Orchestration** | 负责任务识别、任务拆解、路由、协调、状态管理和结果汇总的运行时能力，通常由编排引擎实现。 | 不是 `orchestration` Skill 本身；Skill 只是可选入口。 |
| **Workflow** | 定义任务执行步骤、依赖关系、条件分支、并行组和门禁的流程定义。Workflow 通过 `depends_on` 引用 Skill 节点或 Tool 节点。 | 不是 Skill 的简单集合，也不是运行时引擎。 |
| **Skill** | 封装某项专业能力的知识、规范、步骤和验收要求的可复用能力包（`SKILL.md` + 资源）。 | 不直接拥有超出授权的系统权限；不定义全局流程。 |
| **Tool** | 提供文件、Shell、Git、浏览器、测试、网络等实际操作能力的原语。 | 不决定研发流程，也不绕过权限和审批。 |
| **Platform Adapter** | 将统一能力接口（工具调用、Skill 发现、元数据、审批交互、上下文持久化）映射到具体 Agent 平台。 | 不决定核心研发流程，不向核心反向注入平台语义。 |

### 2.1 概念之间的关系

```text
Agent
  ├── 执行一个或多个 Skill
  └── 参与一个或多个 Workflow

Orchestration Engine
  ├── 读取 Workflow 定义
  ├── 创建/维护 Task Context
  ├── 路由 Skill
  └── 调用 GateController / ArtifactManager

Workflow
  └── 引用 Skill 节点和 Tool 节点（通过 depends_on 组织 DAG）

Skill
  └── 通过 ToolPort 调用 Tool（受 R0–R4 权限与审批约束）

Platform Adapter
  └── 实现 ToolPort / DiscoveryPort / MetadataPort / ApprovalPort / ContextPort
```

### 2.2 必须明确的边界

1. **Orchestration 可以通过 Skill 作为入口，但编排引擎不等同于 Skill。**
   `skills/development/orchestration/SKILL.md` 只是帮助 Agent 识别任务并选择流程的入口能力；真正的任务拆解、路由、状态管理和结果汇总由编排引擎（L2）负责。
2. **Workflow 是流程定义，不是 Skill 的简单集合。**
   Workflow 描述节点、依赖、并行、条件、门禁和失败路径；Skill 是可被节点引用的能力包。
3. **Skill 可以调用 Tool，但不直接拥有超出授权范围的系统权限。**
   Skill 只声明需要什么能力；实际工具调用经过 ToolPort，并受 R0–R4 权限和审批控制。
4. **Agent 可以执行一个或多个 Skill，也可以参与多个 Workflow。**
   Agent 是执行主体；Skill 和 Workflow 是它使用的能力与流程。
5. **Platform Adapter 负责平台能力映射，不决定核心研发流程。**
   Adapter 只把统一契约翻译成平台调用；流程、门禁和产物规则仍在核心。
6. **核心架构不能依赖某个具体平台的专属功能才能成立。**
   核心只依赖抽象端口；平台缺能力时由 Adapter 降级，而不是让核心引入平台分支。

## 3. 架构分层与依赖方向

### 3.1 整体结构（组件关系图）

```text
┌────────────────────────────────────────────────────────────────────┐
│                          Agent / 用户                              │
└───────────────────────────────┬────────────────────────────────────┘
                                │ 任务、审批、结果
┌───────────────────────────────▼────────────────────────────────────┐
│ L1 交互层                                                          │
│ 需求输入 / 进度展示 / 审批交互 / 结果呈现                           │
└───────────────────────────────┬────────────────────────────────────┘
                                │
┌───────────────────────────────▼────────────────────────────────────┐
│ L2 编排层（Orchestration Engine）                                  │
│ TaskIdentifier / ComplexityEvaluator / SkillRouter                 │
│ GateController / ArtifactManager / Workflow Runner（P2 实现）       │
└───────────────┬───────────────────────────────┬────────────────────┘
                │ 路由 Skill                     │ 读写 Task Context
┌───────────────▼──────────────────┐   ┌────────▼───────────────────┐
│ L3 研发能力层（Development Skill）│   │ ADR-005 产物与上下文模型    │
│ requirements / analysis / design │   │ artifacts/{task-id}/...     │
│ coding / review / testing / ...  │   └────────────────────────────┘
└───────────────┬──────────────────┘
                │ 调用技术能力
┌───────────────▼──────────────────┐
│ L4 专业技术层（Technical Skill）  │
│ Vue / React / Java / Python / ...│
└───────────────┬──────────────────┘
                │ 使用
┌───────────────▼──────────────────┐
│ L5 工程基础设施层                 │
│ Scripts / Templates / References │
│ ToolPort / Git / 测试工具         │
└──────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ L6 平台适配边界（不是核心的向下层）                                │
│ codex / claude-code / cursor / gemini-cli / opencode / openclaw    │
│ 实现 ToolPort / DiscoveryPort / MetadataPort / ApprovalPort /       │
│ ContextPort，把核心契约映射到平台 SDK / CLI / API                   │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 依赖关系图（方向）

```text
        ┌───────────────┐
        │ L1 Interaction│
        └───────┬───────┘
                │ 调用
        ┌───────▼─────────────┐
        │ L2 Orchestration    │
        └───────┬─────────────┘
                │ 调用
        ┌───────▼─────────────┐
        │ L3 Development Skill│──────────┐
        └───────┬─────────────┘          │
                │ 调用                   │ 使用
        ┌───────▼─────────────┐  ┌───────▼────────────┐
        │ L4 Technical Skill  │  │ L5 Infrastructure  │
        └───────┬─────────────┘  └────────────────────┘
                │ 使用
        ┌───────▼─────────────┐
        │ L5 Infrastructure   │
        └─────────────────────┘

        L6 Platform Adapter ───────────────► 实现核心端口
                 │
                 └──────────────────────────► 平台 SDK / CLI / API

        核心 (L1–L5) ──X──► 不依赖 L6 的具体实现
```

**规则：**

1. 上层可以调用下层的**抽象接口**；下层不得反向依赖上层的具体实现。
2. L4 依赖 L5 提供的基础设施；L5 不依赖 L4。
3. L3 可以依赖 L4 和 L5；L4/L5 不依赖 L3 的具体 Skill。
4. L6 依赖核心定义的端口（ToolPort、DiscoveryPort、MetadataPort、ApprovalPort、ContextPort），核心不依赖 L6。
5. 核心代码不得 import 任何 `platforms/<platform>/` 的具体模块，也不得读取平台专属配置。
6. 平台能力缺失时，由 L6 提供降级实现；核心流程不因平台差异而分叉。

### 3.3 关于 L6 的说明

L6 保留编号是为了与 P0-001 的文档和目录保持连续，但它**不是普通意义上的向下分层**：

- 从源码依赖看：`L6 → Core Ports`，方向指向核心；
- 从部署装配看：Core 与 Adapter 由运行时组装，Adapter 是边界实现；
- 从流程控制看：Adapter 不决定流程、门禁或产物规则，只负责映射；
- 从演化看：新增平台只增加 Adapter 与平台元数据，不修改核心 Skill 语义。

因此，架构图把 L6 画成独立边界，而不是 L1–L5 之下的一层。

## 4. 各层职责

### L1 · 交互层

**职责：**
- 接收用户需求
- 展示执行进度
- 收集人工审批
- 呈现最终产物

**边界：**
- 不处理业务逻辑
- 不包含技术实现细节
- 与平台 UI 机制对接，但通过审批端口/上下文端口交互，不直接调用平台专属 API

### L2 · 编排层

**职责：**
- 任务类型识别
- 复杂度评估（L1/L2/L3）
- Skill 路由决策
- Workflow 选择与 DAG 执行跟踪
- 依赖关系管理
- 质量门禁控制（G1–G6，规则见 ADR-006）
- Task Context 创建、状态维护与结果汇总

**关键组件：**
- `task-identifier` — 任务识别器
- `complexity-evaluator` — 复杂度评估器
- `skill-router` — Skill 路由器
- `workflow-runner` — 工作流执行器（P2 实现）
- `gate-controller` — 门禁控制器
- `artifact-manager` — 产物管理器（与 ADR-005 一致）

**边界：** 编排层不实现具体研发能力；它只决定「何时、调用谁、如何验收」。

### L3 · 研发能力层

**职责：**
- 提供独立的研发阶段能力
- 定义每个阶段的输入/输出契约
- 支持渐进式披露
- 通过 ToolPort 使用工具，不直接持有系统权限

**Skill 列表：**

| Skill | 输入 | 输出 |
|-------|------|------|
| requirements-clarity | 用户原始需求 | 需求文档 |
| analysis | 需求文档 | 分析报告 |
| design | 分析报告 | 设计文档 |
| coding | 设计文档 | 代码 |
| code-review | 代码 | Review 报告 |
| testing | 代码 + 测试用例 | 测试报告 |
| deployment | 代码 + 部署配置 | 部署产物 |
| documentation | 代码 + 设计 | 技术文档 |
| feedback-loop | 上线反馈 | 改进建议 |

### L4 · 专业技术层

**职责：**
- 提供特定技术栈的实现能力
- 被 L3 的 Coding 等 Skill 调用
- 保持技术栈无关的上层接口

**分类：**
- 前端：Vue / React / TypeScript / 性能优化
- 后端：Java / Spring Boot / Python / API 开发
- 数据库：MySQL / PostgreSQL / SQL 优化
- AI：Agent / RAG / Prompt Engineering / Workflow
- 工程：Git / 重构 / 依赖管理

### L5 · 工程基础设施层

**职责：**
- 提供通用工具和脚本
- 管理模板和参考文档
- 提供 ToolPort 的标准实现或适配接口
- 维护测试框架

**内容：**
- `scripts/` — 可执行脚本
- `templates/` — 标准模板
- `references/` — 参考文档
- `tools/` — 验证和质量检查工具

### L6 · 平台适配边界

**职责：**
- 实现核心端口：工具调用、Skill 发现、元数据映射、审批交互、上下文持久化
- 管理平台特定的配置和降级策略
- 维护平台能力矩阵和验证状态

**不包含：**
- 不定义研发流程
- 不定义 G1–G6 规则
- 不定义 Task Context / Artifact 语义
- 不向核心注入平台专属字段

**平台清单（六个，统一）：**
- Codex
- Claude Code
- Cursor
- Gemini CLI
- OpenCode
- OpenClaw

## 5. 层间依赖规则

| 调用方 | 被调用方 | 允许方式 |
|--------|----------|----------|
| L1 | L2 | 通过任务/审批接口 |
| L2 | L3 | 通过 Skill 路由与 Workflow 节点 |
| L3 | L4、L5 | 通过能力接口与 ToolPort |
| L4 | L5 | 使用基础设施 |
| L6 | 核心端口 | 实现 ToolPort / DiscoveryPort / MetadataPort / ApprovalPort / ContextPort |
| 核心 | L6 | **禁止**直接依赖具体平台实现；只依赖端口 |

**禁止项：**

- 核心 Skill 中不得出现 `metadata.openclaw` 等平台专属字段。
- L3/L4 不得直接调用平台 CLI；必须通过 ToolPort。
- L5 不得反向依赖 L3/L4 的具体 Skill。
- L2 不得把某个平台的专属能力写死为流程前提。

## 6. 数据流

```text
用户输入
  → L1 接收
  → L2 识别任务类型/复杂度
  → L2 创建 Task Context（ADR-005）
  → L2 选择 Workflow（DAG 定义见 orchestration-architecture.md）
  → L3 Skill 按节点执行
  → L4 技术能力 / L5 基础设施 / ToolPort
  → 产物写入 artifacts/{task-id}/（ADR-005）
  → G1–G6 门禁（ADR-006）
  → 结果汇总
  → L1 展示 / 交付
```

## 7. 平台无关原则

- 核心 Skill 只使用通用字段与能力契约（见 `skill-architecture.md`）。
- 平台扩展元数据集中放在 `platforms/<platform>/`，不进入核心 `SKILL.md`。
- 平台适配器只做映射和降级，不改变核心 Skill 的语义。
- 六个平台的能力状态统一在 `platform-architecture.md` 维护；未实测能力必须标记为「设计假设」或「待验证」。
- 核心架构在任何单一平台上不可用时，仍应能通过最小 ToolPort 实现运行，或明确报告不可用原因。

## 8. 设计原则

1. **单一职责** — 每层只做一件事。
2. **低耦合** — 层间通过明确接口交互；核心只依赖端口。
3. **高内聚** — 层内组件紧密协作。
4. **渐进披露** — 按需加载资源。
5. **可测试** — 每层可独立验证。
6. **可扩展** — 新增平台或技术栈不影响核心。
7. **唯一权威** — 同一核心规则只在一个文档定义，其他文档引用。
8. **默认拒绝** — 权限和安全控制默认拒绝，按最小权限授予。
9. **设计不等于实现** — 未实现的能力必须标注为规划或待验证。

## 9. 当前状态

- [x] 核心概念与依赖方向收敛（P0-002）
- [x] 架构设计文档完成
- [ ] 各层详细设计（P1–P2）
- [ ] 平台适配验证（P7）
- [ ] 端到端集成测试（P7）

## 10. 权威定义索引

| 主题 | 权威文档 |
|------|----------|
| 六个核心概念 | 本文件 §2 |
| 层间依赖与平台无关原则 | 本文件 §3、§5、§7 |
| G1–G6 门禁 | [ADR-006](../decisions/ADR-006-quality-gates.md) |
| Task Context / Artifact | [ADR-005](../decisions/ADR-005-task-context.md) |
| Skill 通用规范与平台元数据 | [skill-architecture.md](./skill-architecture.md) + [ADR-002](../decisions/ADR-002-skill-standard.md) |
| Workflow DAG 与执行语义 | [orchestration-architecture.md](./orchestration-architecture.md) + [ADR-003](../decisions/ADR-003-orchestration.md) |
| 权限与审批 | [security-architecture.md](./security-architecture.md) |
| 平台能力与适配边界 | [platform-architecture.md](./platform-architecture.md) + [ADR-004](../decisions/ADR-004-cross-platform.md) |
