# 编排引擎架构设计

## 1. 概述

编排引擎（Orchestration Engine，L2）是整个 SDD 体系的运行时核心，负责任务识别、任务拆解、Skill 路由、Workflow 执行、状态管理和结果汇总。

> 六个核心概念的权威定义见 [system-architecture.md §2](./system-architecture.md#2-核心概念权威定义)。本文件只定义编排与 Workflow 的执行语义，不重复定义概念。

### 1.1 编排引擎与 orchestration Skill 的边界

| 对象 | 位置 | 职责 | 是否运行时引擎 |
|------|------|------|----------------|
| Orchestration Engine | `core/orchestration/`（P2 规划） | 任务识别、拆解、路由、DAG 执行、状态、结果汇总 | 是 |
| orchestration Skill | `skills/development/orchestration/` | 面向 Agent 的入口能力：帮助识别任务、选择 Workflow、解释下一步 | 否 |

- orchestration Skill 可以调用 Orchestration Engine 的公开接口，但它本身不是引擎。
- 不允许把全部编排逻辑写进一个 `SKILL.md`，也不允许让引擎依赖某个平台的专属能力。
- P0 阶段两者都只有设计，没有实现。

## 2. 核心组件

### 2.1 TaskIdentifier（任务识别器）

**职责：** 分析用户需求，确定任务类型和复杂度。

```yaml
task_types:
  simple_change:
    description: "简单修改，如修改按钮样式"
    default_workflow: simple-task
  bug_fix:
    description: "Bug 修复，如修复接口异常"
    default_workflow: bug-fix
  feature_development:
    description: "功能开发，如增加用户管理模块"
    default_workflow: feature-development
  system_refactoring:
    description: "系统重构，如重构整个前端架构"
    default_workflow: refactoring
  new_project:
    description: "从零开发业务系统"
    default_workflow: new-project
  deployment_task:
    description: "部署任务，如 Docker 部署"
    default_workflow: deployment
  technical_consultation:
    description: "技术咨询，如评估技术方案"
    default_workflow: consultation

complexity_levels:
  L1_simple:
    criteria:
      - 影响范围：单文件或单一模块
      - 风险：低
      - 依赖：无或单一依赖
      - 技术不确定性：无
  L2_medium:
    criteria:
      - 影响范围：多个模块
      - 风险：中
      - 依赖：存在依赖关系
      - 技术不确定性：部分已知
  L3_complex:
    criteria:
      - 影响范围：整个系统
      - 风险：高
      - 依赖：复杂依赖链
      - 技术不确定性：需要探索
```

### 2.2 ComplexityEvaluator（复杂度评估器）

复杂度由影响范围、风险、依赖数量、技术不确定性共同决定，不只按代码行数。评估结果写入 Task Context（见 ADR-005），用于选择 Workflow 与门禁级别。

### 2.3 SkillRouter（Skill 路由器）

**职责：** 根据 Workflow 节点和当前上下文选择 Skill，不硬编码业务流程。

```yaml
routing_rules:
  - name: "feature-development-L3"
    match:
      task_type: feature_development
      complexity: L3_complex
    workflow: feature-development
```

路由规则只决定「选择哪个 Workflow / 哪个 Skill」，门禁规则由 ADR-006 定义。

### 2.4 WorkflowRunner（工作流执行器）

**职责：** 解析 Workflow DAG，按依赖、并行、条件、重试、超时和审批暂停语义执行节点；不实现具体 Skill。

### 2.5 GateController（门禁控制器）

**职责：** 在 Workflow 指定的节点执行 G1–G6 检查；门禁规则的唯一权威定义见 [ADR-006](../decisions/ADR-006-quality-gates.md)。本文件只描述门禁在流程中的挂载位置。

### 2.6 ArtifactManager（产物管理器）

**职责：** 按 [ADR-005](../decisions/ADR-005-task-context.md) 创建、读写、版本化 Task Context 与 Artifact；不定义流程。

## 3. Workflow DAG 执行语义

> Workflow 是流程定义，不是 Skill 的简单集合。节点通过 `depends_on` 组织 DAG；Skill 只是节点的一种类型。

### 3.1 节点字段

| 字段 | 说明 |
|------|------|
| `id` | 节点唯一标识（Workflow 内唯一） |
| `type` | `skill` / `tool` / `gate` / `parallel` / `check` / `end` |
| `skill` / `tool` | 节点引用的能力名称（`type=skill/tool` 时） |
| `depends_on` | 前置节点 ID 列表；空表示入口 |
| `mode` | `sequential` / `parallel` / `conditional` |
| `condition` | 条件表达式（`mode=conditional` 时） |
| `parallel_group` | 并行组标识；同组节点可同时执行 |
| `inputs` | 输入产物引用（路径 + 版本 + hash） |
| `outputs` | 输出产物引用（写入 Task Context） |
| `on_success` | 成功后的下一个节点/结束 |
| `on_failure` | 失败后的回退节点或失败处理 |
| `retry` | `{max, backoff}`；默认最多 3 次，指数退避 |
| `timeout_seconds` | 节点超时；超时按失败处理 |
| `approval` | `{gate, pause, resume}`；`gate` 取 G1–G6，暂停等待显式批准 |
| `gate` | 节点关联门禁（G1–G6）；G1–G5 在节点产出后检查，G6 在生产部署动作前检查；语义见 ADR-006 |
| `artifacts` | 该节点必须产出的产物清单 |

### 3.2 基础 DAG（功能开发）

```text
                 ┌── code-review (G4) ──┐
coding ──────────┤                      ├── quality gate (G4 AND G5) ── deployment (G6) ── verification ── documentation
                 └── testing (G5) ──────┘                                      │
                                                                                └── feedback-loop
```

- `code-review` 与 `testing` 并行，但必须**共同**满足质量门禁。
- 任一失败都不得进入 deployment。
- 两者不是替代关系：测试通过不代表 Review 通过，Review 通过也不代表测试通过。
- 未请求部署时，质量门禁通过后直接进入 documentation/feedback。

### 3.3 功能开发 Workflow 示例

```yaml
# workflows/feature-development.yaml（设计示例，非可执行 Schema）
name: feature-development
version: "0.1"
trigger:
  task_type: feature_development
  complexity: [L2_medium, L3_complex]

nodes:
  - id: requirements
    type: skill
    skill: requirements-clarity
    gate: G1
    outputs: [requirements]

  - id: analysis
    type: skill
    skill: analysis
    depends_on: [requirements]
    outputs: [analysis]

  - id: design
    type: skill
    skill: design
    depends_on: [analysis]
    gate: G2
    outputs: [design, implementation-plan]

  - id: plan
    type: gate
    gate: G3
    depends_on: [design]
    inputs: [implementation-plan]

  - id: coding
    type: skill
    skill: coding
    depends_on: [plan]
    outputs: [implementation]

  - id: code_review
    type: skill
    skill: code-review
    depends_on: [coding]
    gate: G4
    parallel_group: quality
    outputs: [review-report]

  - id: testing
    type: skill
    skill: testing
    depends_on: [coding]
    gate: G5
    parallel_group: quality
    outputs: [test-report]

  - id: quality_gate
    type: gate
    depends_on: [code_review, testing]
    requires: [G4, G5]
    on_failure:
      review_severe: coding
      testing_code_defect: coding
      testing_analysis_defect: analysis
      requirement_defect: requirements
    on_success:
      deployment_requested: deployment
      otherwise: documentation

  - id: deployment
    type: skill
    skill: deployment
    depends_on: [quality_gate]
    gate: G6                 # G6 在部署动作前检查；不是部署后验证
    condition: "deployment_requested == true"
    on_success: verification
    on_failure: rollback

  - id: verification
    type: check
    depends_on: [deployment]
    checks: [health-check, smoke-test, acceptance-checklist]
    on_success: documentation
    on_failure: rollback

  - id: documentation
    type: skill
    skill: documentation
    depends_on: [quality_gate]
    inputs: [design, implementation, implementation-plan]
    outputs: [technical-docs]

  - id: feedback
    type: skill
    skill: feedback-loop
    depends_on: [testing, documentation]
    outputs: [feedback-report]

  - id: rollback
    type: tool
    tool: rollback
    depends_on: [deployment, verification]
    on_success: failed
```

- 未请求部署时，`quality_gate` 通过后直接进入 `documentation`，跳过 deployment/verification。
- 请求部署时，`deployment` → `verification` → `documentation`；验证失败则进入 rollback。
- `documentation` 不依赖 deployment 是否发生，因此以质量门禁为入口。

### 3.4 Bug 修复 Workflow 示例

```yaml
name: bug-fix
version: "0.1"
trigger:
  task_type: bug_fix
  complexity: [L2_medium, L3_complex]

nodes:
  - id: analysis
    type: skill
    skill: analysis
    outputs: [analysis]

  - id: coding
    type: skill
    skill: coding
    depends_on: [analysis]
    outputs: [implementation]

  - id: code_review
    type: skill
    skill: code-review
    depends_on: [coding]
    gate: G4
    parallel_group: quality
    outputs: [review-report]

  - id: testing
    type: skill
    skill: testing
    depends_on: [coding]
    gate: G5
    parallel_group: quality
    outputs: [test-report]

  - id: quality_gate
    type: gate
    depends_on: [code_review, testing]
    requires: [G4, G5]
    on_failure:
      review_severe: coding
      testing_failed: coding_or_analysis
    on_success: end

  - id: end
    type: end
```

### 3.5 简单修改 Workflow 示例

```yaml
name: simple-task
version: "0.1"
trigger:
  task_type: simple_change
  complexity: [L1_simple]

nodes:
  - id: coding
    type: skill
    skill: coding
    outputs: [implementation]

  - id: code_review
    type: skill
    skill: code-review
    depends_on: [coding]
    gate: G4
    parallel_group: quality
    outputs: [review-report]

  - id: testing
    type: skill
    skill: testing
    depends_on: [coding]
    gate: G5
    parallel_group: quality
    outputs: [test-report]

  - id: quality_gate
    type: gate
    depends_on: [code_review, testing]
    requires: [G4, G5]
    on_failure:
      review_severe: coding
      review_minor: coding
      testing_failed: coding
    on_success: end

  - id: end
    type: end
```

简单修改允许省略需求/分析/设计，但必须包含：

- **独立 Code Review（简化 G4）**：Reviewer 必须与代码作者独立；作者自审、Lint、Typecheck 均不能替代独立 Review。
- **必要测试（简化 G5）**：至少执行与变更相关的聚焦测试/检查。
- 两者可以并行，但质量门禁必须是 **G4 AND G5**；Review 失败返回 coding 修复后重新 Review。
- 纯文档变更可将 G4 标记为 N/A；任何代码变更不得跳过 G4。
- 不得因为任务简单而绕过安全约束。

### 3.6 失败、重试、超时与审批

| 场景 | 处理 |
|------|------|
| 节点可恢复失败 | 按 `retry` 重试；超过次数进入 `on_failure` |
| 节点不可恢复失败 | Workflow 标记 `failed`，保留已生成产物 |
| Review 严重问题 | 回到 coding；不得进入 quality gate |
| 测试失败 | 缺陷类型为代码 → coding；需求/设计缺陷 → requirements/analysis/design |
| G6 失败 | 中止部署；如已部分执行，执行回滚并记录事件 |
| 节点超时 | 按失败处理；不得把超时当作成功或批准 |
| 审批暂停 | 节点进入 `awaiting_approval`，只有显式批准才恢复；超时不等于批准 |
| 恢复执行 | 从暂停节点继续，不重跑已成功且产物未变更的节点 |

### 3.7 Workflow 状态

```yaml
workflow_states:
  pending: 等待执行
  running: 正在执行
  awaiting_approval: 等待人工审批
  paused: 暂停（非审批原因）
  completed: 已完成
  failed: 执行失败
  aborted: 已中止

node_states:
  queued: 已排队
  executing: 执行中
  succeeded: 成功
  failed: 失败
  skipped: 已跳过
  blocked: 被阻塞
  awaiting_approval: 等待审批
```

## 4. 门禁挂载点

> G1–G6 的触发条件、自动检查、人工审批、跳过规则、失败回退和审计要求的唯一权威定义见 [ADR-006](../decisions/ADR-006-quality-gates.md)。下表只说明挂载位置。

| 门禁 | 挂载位置 | 作用 |
|------|----------|------|
| G1 | requirements-clarity 之后 | 需求确认 |
| G2 | design 之后 | 设计确认 + Builder Check |
| G3 | coding 之前 | 开发计划确认 |
| G4 | code-review 之后 | 代码质量 |
| G5 | testing 之后 | 测试验收 |
| G6 | 生产部署动作之前 | 部署授权（不含部署后验证） |

> **G6 位置：** G6 必须在生产部署动作发生**之前**通过。部署后的健康检查/冒烟/验收属于 **Deployment Verification**，不是 G6，也不能替代 G6。非生产环境是否需要审批按权限模型决定，不使用 G6。

## 5. 任务类型与流程

| 任务类型 | 复杂度 | 推荐 Workflow | 必需门禁 |
|----------|--------|---------------|----------|
| simple_change | L1 | simple-task | G4（简化，独立 Review 不跳过）、G5（简化）；安全约束不跳过 |
| bug_fix | L2 | bug-fix | G4、G5 |
| feature_dev | L2/L3 | feature-development | G1、G2、G3、G4、G5（生产部署时 G6） |
| refactoring | L3 | refactoring | G1、G2、G3、G4、G5（生产部署时 G6） |
| new_project | L3 | new-project | G1、G2、G3、G4、G5；G6 仅计划生产部署 |
| deployment_task | L2 | deployment | 涉及代码/配置时 G4、G5；生产部署时 G6；非生产部署不触发 G6 |
| technical_consultation | L1/L2 | consultation | 无需代码门禁；输出设计/分析产物 |

> 门禁规则以 [ADR-006](../decisions/ADR-006-quality-gates.md) 为准；本表只表示任务类型到 Workflow 的映射，不重新定义门禁规则。

## 6. Task Context 与产物

- 创建者：Orchestration Engine 在任务入口创建 `task-id`；无编排引擎时由执行的 Agent 创建并记录 `created_by`。
- 维护者：Orchestration Engine 维护状态；ArtifactManager 维护产物索引。
- 状态机：正常 `created → planned → executing → verifying → completed`；审批 `executing → awaiting_approval → approved → executing`，`rejected/timeout → aborted`；异常 `executing/verifying → failed/aborted`。权威定义见 [ADR-005](../decisions/ADR-005-task-context.md)。
- 终止状态（`completed/failed/aborted`）不可恢复执行；重试需创建新 `task-id`，并通过 `parent-task-id` 指向原任务。
- 路径、归属、版本、并发、归档规则：见 [ADR-005](../decisions/ADR-005-task-context.md)。
- 本文件中的 `inputs` / `outputs` 均使用 ADR-005 的 Artifact 引用格式（路径 + 版本 + hash）。

## 7. 子 Agent 协作

场景中的「子 Agent」是 Agent（见 system-architecture.md §2），不是 Skill。

```yaml
parallel_execution:
  max_concurrent: 5
  strategy:
    - fork: 拆分独立任务并行执行
    - pipeline: 上一步完成后立即启动下一步

subagent_config:
  context_mode: isolated
  timeout_seconds: 600
  announce: true
  permissions: 继承父 Agent 的子集，不得提权
```

- 子 Agent 不得获得超过父 Agent 的权限。
- 并行节点写入不同产物路径；共享产物只读。
- 子 Agent 失败按节点失败处理，不静默忽略。

## 8. Builder Check 机制

Builder Check 是 G2 的独立审查环节，规则见 ADR-006。

```yaml
builder_check:
  trigger: [G2]
  role: independent-reviewer
  checklist:
    - 是否遗漏用户需求？
    - 是否存在设计矛盾？
    - 是否有过度设计？
    - 是否存在安全风险？
    - 是否有无法落地的技术方案？
    - 是否存在未考虑的异常场景？
  outcomes:
    approved: 继续执行
    needs_revision: 返回设计阶段修改
    escalated: 升级人工决策
```

## 9. 当前状态

- [x] 组件设计完成
- [x] 编排引擎与 orchestration Skill 边界明确
- [x] Workflow DAG 执行语义与失败路径明确
- [x] 门禁规则统一引用 ADR-006
- [x] P1-002 标准、Schema 与示例落地（见第 10 节；Runtime 未实现）
- [ ] 编排引擎实现（P2）
- [ ] 平台适配验证（P7）

## 10. P1-002 规范落地

> P1-002 在保留 §1–§9 P0 语义的前提下，把 Orchestration 的职责、Workflow/Task 模型、状态机、Gate/Approval、失败恢复和证据要求拆成可验证标准。本节只做索引与边界说明，不重复定义规则。

### 10.1 权威文档索引

| 主题 | 权威文档 |
|------|----------|
| Orchestrator 职责、组件、运行时模型 | [orchestration-standard.md](../standards/orchestration-standard.md) |
| 任务类型、复杂度、澄清与升级 | [task-classification-standard.md](../standards/task-classification-standard.md) |
| Workflow 模型、选择、组合、动态阶段、并行 | [workflow-standard.md](../standards/workflow-standard.md) |
| Task 数据模型、调度、依赖、重试、取消、恢复 | [task-standard.md](../standards/task-standard.md) |
| Task/Workflow/Node/Gate/Approval 状态与转换 | [orchestration-state-machine.md](../standards/orchestration-state-machine.md) |
| G1–G6 在编排中的挂载、质量门禁和 G4/G5 绑定 | [gate-orchestration-standard.md](../standards/gate-orchestration-standard.md) |
| Approval 对象、生命周期、绑定、过期和失效 | [approval-orchestration-standard.md](../standards/approval-orchestration-standard.md) |
| 上下文分层、Evidence、日志/事件/审计、观测指标 | [execution-evidence-standard.md](../standards/execution-evidence-standard.md) |
| Workflow/Task/Gate/Approval/Evidence Schema | `schemas/orchestration/` |
| 可验证示例 | `examples/orchestration/` |
| 静态校验器与测试 | `tests/unit/orchestration/` |

### 10.2 Task 执行状态与 ADR-005

P1-002 引入的 Task Execution State（PENDING/READY/RUNNING/WAITING/BLOCKED/SUCCEEDED/FAILED/CANCELLED）是调度器的工作状态，不是对 ADR-005 `task-status` 的替代：

- ADR-005 仍是 Task Context 持久化生命周期和终止状态的权威定义。
- Task 模型同时记录 `status`（执行状态）和 `context_status`（ADR-005 投影）。
- 两者映射和同步规则见 [orchestration-state-machine.md](../standards/orchestration-state-machine.md)。
- 不新增或修改 ADR-005 的 `created/planned/executing/awaiting_approval/verifying/completed/failed/aborted` 语义。

### 10.3 不改变的 P0 规则

1. Orchestration 与 orchestration Skill 的边界不变：引擎负责调度，Skill 只是可选入口。
2. G1–G6 的唯一权威定义仍是 ADR-006；P1-002 只定义编排挂载和 GateDecision 记录。
3. R0–R4、SA、G6 的职责分离不变：G6 不是权限检查，R4 不等于 G6，SA 不替代权限检查。
4. G4/G5 必须针对同一 commit/产物 hash；Coding 新版本使旧结果失效。
5. 生产部署才触发 G6；非生产部署和生产环境非部署变更不触发 G6。
6. 失败、审批暂停和恢复不得把超时/沉默当作批准。
7. 本阶段只交付静态标准、Schema、示例和测试；`runtime_behavior = NOT_EXECUTED`。

---

**P1-002 状态：** 规范与静态 Schema 产出，待 ChatGPT 评审。未实现编排引擎、WorkflowRunner、GateController 或 ArtifactManager。
