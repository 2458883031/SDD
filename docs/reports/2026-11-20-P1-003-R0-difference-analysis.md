# SDD P1-003-R0 Requirements / Analysis / Design 现状盘点与差异分析

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-003-R0 |
| 分支 | `feature/p1-003-requirements-analysis-design` |
| 基线 | `50df231d2de15b4dc33407798cce36f7d2178ee5`（main） |
| 执行/监督 | Claude Code |
| 架构决策/验收 | ChatGPT |
| 当前状态 | **P1-003-R0 COMPLETE；P1-003-R1 NOT STARTED** |

> 本报告只做现状盘点、差异分析和契约建议，不实现 Runtime，不批量创建 Skill，不修改 P0 ADR、P1-001/P1-002 已验收规范、现有 Schema 或校验器。

---

## 一、Git 基线证据

执行前检查：

```text
branch=feature/p1-003-requirements-analysis-design
HEAD=50df231d2de15b4dc33407798cce36f7d2178ee5
origin/main=50df231d2de15b4dc33407798cce36f7d2178ee5
main=50df231d2de15b4dc33407798cce36f7d2178ee5
status=## feature/p1-003-requirements-analysis-design
```

- main 与 origin/main 一致；
- 工作区 clean；
- 分支从 main 创建，未复用 P1-002 分支；
- 未修改任何已有架构规范或实现文件。

### 1.1 R0 变更范围

R0 只新增两份报告，不修改已跟踪文件：

```text
git status --short
?? docs/reports/2026-11-20-P1-003-R0-difference-analysis.md
?? docs/reports/2026-11-20-P1-003-R0-implementation-plan.md

git diff --stat
(empty)
```

---

## 二、已检查文件清单

### 2.1 P0 架构与决策

- `docs/architecture/system-architecture.md`
- `docs/architecture/orchestration-architecture.md`
- `docs/architecture/module-architecture.md`
- `docs/architecture/skill-architecture.md`
- `docs/architecture/platform-adapter-architecture.md`
- `docs/architecture/platform-compatibility-matrix.md`
- `docs/architecture/security-architecture.md`
- `docs/architecture/testing-architecture.md`
- `docs/decisions/ADR-001-overall-architecture.md` 至 `ADR-008-platform-adapter.md`

### 2.2 P1-001 标准与参考 Skill

- `docs/standards/skill-standard.md`
- `docs/standards/skill-metadata-standard.md`
- `docs/standards/skill-io-contract.md`
- `docs/standards/skill-security-standard.md`
- `docs/standards/skill-versioning-standard.md`
- `skills/requirements-clarity/SKILL.md`
- `skills/requirements-clarity/skill.yaml`
- `skills/requirements-clarity/schemas/input.schema.json`
- `skills/requirements-clarity/schemas/output.schema.json`
- `skills/requirements-clarity/examples/*`
- `skills/requirements-clarity/references/requirements-checklist.md`
- `skills/requirements-clarity/tests/cases.yaml`
- `skills/requirements-clarity/tests/invalid-cases.yaml`
- `tests/unit/requirements-clarity/validate_reference_skill.py`

### 2.3 P1-002 Orchestration 标准与资产

- `docs/standards/orchestration-standard.md`
- `docs/standards/task-classification-standard.md`
- `docs/standards/workflow-standard.md`
- `docs/standards/task-standard.md`
- `docs/standards/orchestration-state-machine.md`
- `docs/standards/gate-orchestration-standard.md`
- `docs/standards/approval-orchestration-standard.md`
- `docs/standards/failure-recovery-standard.md`
- `docs/standards/execution-evidence-standard.md`
- `schemas/orchestration/*`
- `examples/orchestration/*`
- `tests/unit/orchestration/validate_orchestration.py`

### 2.4 当前实际 Skill

```text
skills/
├── requirements-clarity/   # 有完整文件
└── development/            # 空目录，无文件
```

当前仓库**没有** `analysis` 或 `design` Skill 包、标准、Schema 或测试。

---

## 三、当前能力盘点

### 3.1 P0 架构基线

| 主题 | 现状 | 证据 |
|------|------|------|
| 六层架构 | L1 交互、L2 编排、L3 研发能力、L4 技术能力、L5 基础设施、L6 适配边界 | `system-architecture.md §3` |
| 六个核心概念 | Agent、Orchestration、Workflow、Skill、Tool、Platform Adapter | `system-architecture.md §2` |
| L1/L2/L3 复杂度 | 影响范围、风险、依赖、不确定性 | `orchestration-architecture.md §2`、`task-classification-standard.md §4` |
| G1–G6 | 唯一权威定义在 ADR-006 | `ADR-006` |
| R0–R4 / SA | 权限与审批分离；生产部署 R3+G6+SA | `security-architecture.md §2/§5` |
| Builder Check | G2 独立审查；审查者不能复用执行者自评 | `ADR-006 §12`、`orchestration-architecture.md §8` |
| Task Context / Artifact | ADR-005 定义路径、版本、hash、source、superseded | `ADR-005 §1/§2/§4` |
| G4/G5 版本绑定 | 同一 commit/产物 hash；新版本使旧结果失效 | `ADR-006 §10.1`、`gate-orchestration-standard.md §5` |
| L3 Skill 列表 | `system-architecture.md §4` 列出 requirements/analysis/design/coding/review/testing/... | `system-architecture.md` |
| 模块接口 | P0 module-architecture 给出 requirements/analysis/design 的初步接口 | `module-architecture.md §模块接口定义` |

**结论：** P0 只定义架构、职责和初步接口，不代表 Analysis/Design 已实现。

### 3.2 P1-001 Skill 规范

| 能力 | 现状 |
|------|------|
| 通用 Skill 结构、正文、生命周期 | 已定义（`skill-standard.md`、`skill-versioning-standard.md`） |
| 三层元数据 | 已定义（`skill-metadata-standard.md`） |
| 统一 IO 信封 | 已定义：`status/data/artifacts/errors/evidence`；五状态（`skill-io-contract.md §5`） |
| 安全边界 | 已定义 R0–R4/ToolPort/ContextPort/SA（`skill-security-standard.md`） |
| Requirements Clarity | 有参考 Skill、输入/输出 Schema、5 个输出示例、6 个 cases、3 个 invalid cases、校验器 |
| Analysis / Design | **没有实际 Skill 包、Schema 或标准** |

Requirements Clarity 的自动化验证是**静态校验**：结构、Schema、示例、cases、SemVer、元数据语义；不是运行时执行。

### 3.3 P1-002 Orchestration

| 能力 | 现状 |
|------|------|
| Orchestrator 职责 | 已定义（`orchestration-standard.md`） |
| 任务分类/复杂度 | 已定义 9 类任务（`task-classification-standard.md §2`） |
| Workflow 模型 | 已定义节点、DAG、组合、并行、动态阶段（`workflow-standard.md`） |
| Task 模型/状态机 | 已定义 8 状态及 ADR-005 映射（`task-standard.md`、`orchestration-state-machine.md`） |
| G1–G6 编排 | 已定义挂载、GateDecision、G4/G5 绑定（`gate-orchestration-standard.md`） |
| Approval | 已定义绑定、Scope、Fail-Closed 时间、原子消费（`approval-orchestration-standard.md`） |
| 失败/恢复 | 已定义分类、重试、补偿、恢复（`failure-recovery-standard.md`） |
| 证据/上下文 | 已定义上下文分层、Evidence、日志/事件/审计、指标（`execution-evidence-standard.md`） |
| Schema/示例/测试 | 5 个 Schema、5 个状态机、10 个 Workflow 示例、静态校验器 |
| Runtime | **未实现**；`runtime_behavior=NOT_EXECUTED` |

P1-002 的 Workflow 示例引用 `analysis`、`design` Skill 名称，但这些 Skill 当前不存在；示例仅用于静态 DAG/Schema 校验。

---

## 四、三个模块能力盘点

### 4.1 Requirements Clarity

| # | 能力 | 状态 | 证据/缺口 |
|---|------|------|-----------|
| 1 | 用户原始需求解析 | ✅ 部分 | `input.schema.json` 有 `request`；无需求来源/渠道字段 |
| 2 | 需求目标识别 | ✅ | `requirementsFull.goal` |
| 3 | 边界与非目标 | ✅ | `scope`、`non_goals` |
| 4 | 功能/非功能需求拆分 | ❌ 缺失 | 只有 `goal/scope/constraints/acceptance_criteria/non_goals`，无 FR/NFR 字段 |
| 5 | 约束、依赖和假设 | ⚠️ 部分 | `constraints` 存在；无 `dependencies`、`assumptions` 字段 |
| 6 | 模糊点/冲突识别 | ⚠️ 部分 | SKILL.md 决策规则与 cases 有冲突/缺口判断；输出无结构化 `ambiguities`/`conflicts` |
| 7 | 缺失信息判断 | ✅ 部分 | `needs_input` + `questions`；无 `unknowns` 列表/严重度 |
| 8 | 澄清问题生成 | ✅ | `questions` 至少 1 条 |
| 9 | 用户确认与需求冻结 | ⚠️ 委托 G1 | Skill 返回 `ok` 不等于用户确认；G1/Approval 记录确认；无 Skill 级 freeze 字段 |
| 10 | 验收标准/可测试条件 | ✅ | `acceptance_criteria` 必填 |
| 11 | 需求变更检测与影响 | ❌ 缺失 | 无变更检测、差异、影响标记字段 |
| 12 | 需求版本化与 Evidence | ⚠️ 部分 | Artifact 引用有 path/version/sha256；`existing_requirements` 只是字符串，不是结构化引用；无需求版本/变更记录字段 |

**关键风险：** 输出 Schema 允许 Agent 把推测写入 `goal/scope/constraints`，没有 `assumptions`/`unknowns` 与用户确认来源的结构化区分；必须依赖 SKILL.md 纪律和 G1，而不是 Schema 约束。

### 4.2 Analysis

| # | 能力 | 状态 | 证据/缺口 |
|---|------|------|-----------|
| 1 | 现状分析 | ❌ 无 Skill/标准 | P0 模块接口只有初步字段；无 Analysis Skill |
| 2 | 代码库/系统结构分析 | ❌ | 无 Schema/标准 |
| 3 | 需求与现有系统差异 | ❌ | 无 |
| 4 | 影响范围识别 | ❌ | 无 |
| 5 | 依赖分析 | ⚠️ P0 初步 | `module-architecture.md` 有 `dependency_map`；无正式契约 |
| 6 | 技术可行性 | ⚠️ P0 初步 | `tech_stack_recommendation`、`risk_assessment`；无标准 |
| 7 | 技术选型 | ⚠️ 与 Design 重叠 | P0 Analysis 接口含 `tech_stack_recommendation`；Design 也做架构/方案 |
| 8 | 风险分析 | ⚠️ P0 初步 | `risk_assessment`；无严重度/证据结构 |
| 9 | 安全与权限风险 | ❌ 无模块契约 | `security-architecture.md` 有全局要求；Analysis 无字段 |
| 10 | 性能/可靠性/可维护性 | ❌ | 无 |
| 11 | 多方案比较 | ❌ | 无 `options/tradeoffs` |
| 12 | 分析结论与证据 | ⚠️ 通用 Evidence | P1-002 Evidence 可复用；无 Analysis 专用 data schema |

**结论：** Analysis 目前只有 P0 的概念性接口和 Workflow 节点名，没有可执行规范、Schema、示例或测试。

### 4.3 Design

| # | 能力 | 状态 | 证据/缺口 |
|---|------|------|-----------|
| 1 | 系统架构设计 | ⚠️ P0 初步 | `module-architecture.md` `architecture` 字段；无 Design Skill |
| 2 | 模块划分/职责边界 | ⚠️ P0 初步 | `module_structure` |
| 3 | 组件设计 | ❌ | 无组件字段/契约 |
| 4 | 数据模型/接口 | ⚠️ P0 初步 | `data_model`、`api_definitions` |
| 5 | API 契约 | ⚠️ | 无正式 Schema/示例 |
| 6 | 状态与流程设计 | ❌ | 无 |
| 7 | 错误/异常路径 | ❌ | 无 |
| 8 | 安全/权限设计 | ⚠️ P0 初步 | `security_considerations`；无 R0–R4/SA 映射 |
| 9 | 性能/可扩展性 | ❌ | 无 |
| 10 | 测试策略/验收设计 | ❌ 无 Design 契约 | G5/Testing 有全局要求；Design 无 test strategy 字段 |
| 11 | 方案权衡 | ❌ | 无 tradeoffs/备选方案结构 |
| 12 | 设计版本/变更追踪 | ⚠️ 通用 Artifact | ADR-005 有 version/source/superseded；无 Design 专用字段 |

**结论：** Design 目前只有 P0 初步接口和 G2 检查清单，没有 Design Skill、Schema、示例或测试。

---

## 五、已有能力、缺失能力、重复能力

### 5.1 可直接复用

1. **统一输出信封**：`skill-io-contract.md §5` 的五状态和 `status/data/artifacts/errors/evidence` 可直接用于三个模块。
2. **Artifact 模型**：ADR-005 已有 `requirements/analysis/design/plan` 类型、path/version/sha256/source/status/superseded。
3. **Task/Workflow/Gate/Approval**：P1-002 已定义 Task 模型、状态机、GateDecision、Approval、Evidence。
4. **G1/G2/G3 规则**：ADR-006 已定义触发、自动检查、人工审批、失败回退。
5. **G4/G5 版本绑定**：同一 commit/产物 hash；新版本使旧结果失效。
6. **安全与版本标准**：R0–R4、ToolPort/ContextPort、SemVer、依赖声明。

### 5.2 缺失能力

1. Requirements 的 FR/NFR、assumptions、dependencies、change impact、confirmation/freeze、结构化 unknowns。
2. Analysis Skill、标准、Schema、示例、测试。
3. Design Skill、标准、Schema、示例、测试。
4. 三模块之间的版本/失效契约：需求版本变化如何使 Analysis/Design 和 G1/G2/G3 失效。
5. G1/G2/G3 的显式 Artifact hash 绑定（当前只有 G4/G5 明确）。
6. G3 的 plan 生产者和 plan artifact 归属。
7. 简单任务/咨询/Bug 修复的模块适用性矩阵。
8. 三模块的跨模块契约校验器。

### 5.3 重复/重叠风险

| 重叠 | 风险 | 处理建议 |
|------|------|----------|
| Requirements Skill 的缺口/冲突识别 vs G1 自动检查 | 两处都判断需求完整性 | Skill 产出结构化未知项；G1 做门禁/审批，不重复生成需求 |
| Analysis 的 `tech_stack_recommendation` vs Design 的技术选型 | 责任边界模糊 | Analysis 只给可行性/候选/依据；Design 做最终选择与规格 |
| Design 的 test strategy vs Testing Skill/G5 | 设计策略与测试执行混淆 | Design 定义策略/验收映射；Testing 执行并产出测试证据 |
| Design 的 security considerations vs Security Architecture | 可能自造权限规则 | Design 遵守 R0–R4/SA，不重新定义权限模型 |
| `technical_consultation` Workflow 的 analysis 节点 vs Analysis Skill | 咨询可能只需轻量分析 | 用同一 Analysis Skill 的可裁剪输出，不强制完整设计 |

---

## 六、架构冲突与歧义

### C1. G3 的 plan 生产者不一致（Major，需决策）

**证据：**

- P0 `docs/architecture/orchestration-architecture.md` §3.3（约 164–175 行）：
  - `design` 节点 `outputs: [design, implementation-plan]`
  - 后续 `plan` 节点 `type: gate`、`gate: G3`、`inputs: [implementation-plan]`
- P0 `docs/architecture/module-architecture.md` §设计模块接口（约 160–172 行）：
  - Design 输出仅 `architecture/module_structure/api_definitions/data_model/security_considerations`，没有 `implementation-plan`
- P1-002 `docs/standards/workflow-standard.md` §5.4（约 172 行）：
  - 阶段描述为 `... → G2 → plan → G3 → coding ...`
- P1-002 示例 `examples/orchestration/workflows/feature-development.yaml`（约 39–48 行）：
  - `g2` 后直接 `g3`，`coding` 依赖 `g3`；没有 plan 节点或 implementation-plan 输出
  - `new-project.yaml`、`refactoring.yaml` 同样只有 `gate: G3`，没有 plan producer
- ADR-006 §5（约 93–102 行）G3 自动检查包含“任务拆解、依赖关系、负责人、实施顺序、风险、回滚/验证计划”，但没有指定生产者。

**影响：** G3 的检查对象 `implementation-plan` 在 P0 示例中存在，在 P1-002 示例中没有生产者；G3 可能无实际输入。

**建议：** 由 ChatGPT 裁定以下之一：

- A. Design Skill 输出 design spec + implementation plan（与 P0 orchestration 示例一致）；或
- B. Design Skill 只输出 design spec，新增 Orchestration/Planner 的 plan 活动，G3 检查该 plan；或
- C. P1-002 示例修正为显式 plan 节点；Design 是否输出 plan 另行定义。

本报告不自行选择；R1–R3 需先解决此决策。

### C2. Analysis/Design Skill 名称已被 Workflow 引用，但没有实现

**证据：**

- `examples/orchestration/workflows/feature-development.yaml`：`skill: analysis`、`skill: design`
- `docs/architecture/system-architecture.md` L3 Skill 列表包含 analysis/design
- `skills/development/` 为空；`skills/` 下只有 `requirements-clarity`
- `docs/standards/` 无 analysis/design 标准
- `schemas/orchestration/` 只有 Orchestration Schema，无 Analysis/Design Skill Schema

**性质：** 实现缺口，不是架构冲突；Workflow 示例是静态设计，没有交叉校验 Skill 是否存在。

### C3. Requirements 输出 Schema 不足

**证据：**

- `skills/requirements-clarity/schemas/output.schema.json`：
  - `requirementsFull` 仅 `goal/scope/constraints/acceptance_criteria/non_goals`
  - 无 `functional_requirements`、`non_functional_requirements`、`dependencies`、`assumptions`、`unknowns`、`change_impact`、`confirmation_ref`
  - `okData` 的 `questions` 可选，但 `ok` 状态没有结构化未决项
- `input.schema.json` 的 `existing_requirements` 是 `array[string]`，不是 `{path,version,sha256}` 引用

**影响：** 无法仅靠 Schema 区分用户确认事实与 Agent 假设；无法稳定表达 NFR/依赖/变更影响；需求版本关联不足。

### C4. G1/G2/G3 没有显式 Artifact hash 绑定规则

**证据：**

- ADR-006 §10.1（约 222–229 行）只对 G4/G5 明确要求同一 commit/产物 hash。
- G1/G2/G3 描述了自动检查和回退，但没有要求 GateDecision 绑定 requirements/analysis/design artifact 的 version+sha256。
- P1-002 `gate-orchestration-standard.md §2` 的 GateDecision 有 `subject_hash` 字段（条件字段），§5.2 明确要求 G4/G5 在所有状态下绑定有效 `subject_hash`、G6 绑定 `subject_hash + deployment_target`；G1/G2/G3 未明确要求。

**影响：** 需求或设计产生新版本后，旧 G1/G2/G3 结果可能被继续使用；跨模块版本失效链不完整。

**建议：** P1-003 标准要求 G1/G2/G3 绑定对应 Artifact hash；如果 ChatGPT 认为这属于 ADR-006 门禁规则变更，则先提交 ADR-009 Proposed。

### C5. 用户确认与 Skill `ok` 的语义边界

**证据：**

- `requirements-clarity/SKILL.md` 决策规则要求不猜测；但 `status: ok` 只表示 Skill 完成需求基线。
- G1 才是需求确认门禁；G1 人工审批是用户确认。
- `output.schema.json` 没有 `confirmed` 字段或用户确认引用。

**性质：** 需要明确：Skill 不得把 `ok` 当作“用户已确认”；用户确认必须由 G1/Approval 记录。现有规范方向正确，但缺少显式字段/证据约定。

### C6. Analysis 与 Design 的技术选型重叠

**证据：**

- `module-architecture.md` 分析接口有 `tech_stack_recommendation`
- 设计接口有 `architecture`、`api_definitions`、`data_model`
- P1-002 Workflow 有 analysis → design，但没有规定谁做最终技术选型

**建议：** Analysis 输出候选方案、可行性、风险和依据；Design 做最终方案、接口/数据和决策记录。不要把“候选推荐”写成“最终设计”。

### C7. Design 与具体技术栈 Skill 的边界

**证据：**

- P0 L4 列举 Vue/React/Java/Python 等技术能力；L3 Design 是架构/设计。
- `skill-standard.md` 规定 Skill 不定义全局流程，`design` 不应替代 Coding 的技术实现。

**建议：** Design Skill 输出技术栈无关的设计规格；具体框架/库实现由 Coding/技术栈 Skill 决定。Design 可以声明约束和候选，但不能把实现细节写成唯一实现。

### C8. Design 输出与开发计划/Code Review 的边界

**证据：**

- ADR-006 G2 是设计确认，G4 是代码质量/Review；Builder Check 属 G2。
- P0 orchestration 示例中 Design 输出 `implementation-plan`，G3 检查 plan；P1-002 示例没有 plan。
- Testing/G5 是测试验收；Design 的 test strategy 不是 G5 执行结果。

**建议：** 明确 Design 输出 design spec、可选 implementation plan；G2 做设计/Build Check，G3 做计划，G4 做代码 Review，G5 做测试验收。不得用 Design 审查替代 G4。

### C9. 简单任务/咨询/Bug 修复的适用性

**证据：**

- P1-002 `workflow-standard.md §5.1` consultation：无代码门禁，G1/G2 按需。
- §5.2 simple-task：可跳过 G1/G2/G3，但 G4/G5 不得跳过。
- §5.3 bug-fix：analysis → coding → G4/G5；需求不清晰时增加 requirements/G1。
- §5.4 feature-development：完整 requirements/analysis/design/G1/G2/G3。

**现状：** 规则存在，但没有一张“Requirements/Analysis/Design 适用性矩阵”明确每个任务类型默认需要哪些模块、哪些可裁剪。

**建议：** P1-003 R4 增加适用性矩阵，不强制所有任务走完整链路。

### C10. 是否需要模块级状态机

**证据：**

- P1-002 已有 Task/Workflow/Node/Gate/Approval 状态机。
- ADR-005 已有 Artifact `draft/approved/superseded`。
- 三模块没有独立状态机。

**建议：** 不新增 Requirements/Analysis/Design 独立状态机；用 Task 执行状态 + GateDecision + Artifact status 表达。除非 R1–R5 证明存在无法表达的状态，否则不增加抽象。

### C11. 是否需要新 Artifact 类型

**证据：**

- ADR-005 Artifact type 已包含 `requirements`、`analysis`、`design`、`plan`。
- `requirements-clarity` 输出 artifact type 至少可为 `requirements`。
- P1-002 Task/Evidence 已有 Artifact 引用。

**建议：** 不新增 Artifact 类型；`plan` 已存在。Design 决策记录可放在 design artifact 的 `decisions` 数据内，或作为 `report`，无需新类型。

---

## 七、统一输入输出契约建议（未定案）

### 7.1 总体原则

1. **复用统一信封**：三模块都使用 `skill-io-contract.md §5` 的 `status/data/artifacts/errors/evidence`；不新增 Envelope。
2. **复用 Artifact 模型**：requirements/analysis/design/plan 类型已存在；path/version/sha256/source 使用 ADR-005。
3. **Skill 只做专业能力**：不调度 Workflow、不批准 G1/G2/G3、不修改根 Task Context。
4. **用户确认与 Agent 假设分离**：`ok` 不等于用户确认；用户确认由 G1/Approval 记录。
5. **版本链可追溯**：Analysis 引用 requirements version/hash；Design 引用 analysis version/hash；需求新版本使下游失效。

### 7.2 三模块契约表

| 项目 | Requirements | Analysis | Design |
|---|---|---|---|
| 输入 | 原始请求、项目上下文、已有需求引用、约束 | 已确认需求 Artifact（version/hash）、项目现状、约束 | Analysis Artifact（version/hash）、需求引用、约束 |
| 核心职责 | 澄清、结构化、验收标准、未决项 | 现状/差异/影响/依赖/可行性/方案依据/风险 | 架构/模块/接口/数据/状态/错误/安全/性能/测试策略/权衡 |
| 输出 | 结构化需求基线 + 未决项 + 假设 | 分析报告 + 事实/假设/未知 + 方案选项 + 风险 | 设计规格 + 决策记录 + 测试策略 + 实施约束 |
| 证据 | 需求来源、用户确认（G1/Approval） | 代码/文档引用、命令/检查、事实来源 | 设计决策、备选方案、G2/Builder Check 记录 |
| 下游 | Analysis | Design | Coding（经 G3 plan） |

### 7.3 建议的模块 data 字段（待 R1–R3 定稿）

**Requirements：**

```yaml
requirements:
  goal: string
  scope: [string]
  non_goals: [string]
  functional_requirements: [ {id, statement, priority} ]
  non_functional_requirements: [ {id, category, statement, measurable_target} ]
  constraints: [string]
  dependencies: [ {name, type, note} ]
  assumptions: [ {id, statement, source, needs_confirmation} ]
  open_questions: [ {id, question, blocking} ]
  acceptance_criteria: [ {id, criterion, verification} ]
  change_impact: {changed: bool, affected: [string], reason: string}
  source_refs: [artifactRef]
  confirmation_ref: string|null   # G1/Approval ID，不由 Skill 伪造
```

**Analysis：**

```yaml
analysis:
  requirement_refs: [artifactRef]
  analysis_type: current_state | gap | impact | feasibility | diagnosis | mixed
  current_state: object
  system_structure: object
  gap_analysis: [string]
  impact_scope: [string]
  dependencies: [object]
  feasibility: {verdict, evidence, unknowns}
  options: [ {id, option, pros, cons, risks, evidence} ]
  risks: [ {id, category, severity, evidence, mitigation} ]
  security_risks: [object]
  quality_attributes: {performance, reliability, maintainability}
  facts: [ {statement, evidence_ref} ]
  assumptions: [ {statement, basis} ]
  unknowns: [ {question, impact} ]
  recommendation: string
```

**Design：**

```yaml
design:
  analysis_refs: [artifactRef]
  requirement_refs: [artifactRef]
  architecture: object
  modules: [object]
  components: [object]
  data_model: object
  interfaces: [object]
  api_contracts: [object]
  state_flow: object
  error_paths: [object]
  security_design: object
  performance_scalability: object
  test_strategy: object
  tradeoffs: [object]
  decisions: [object]
  implementation_constraints: [string]
  design_version: string
```

> 这些字段是 R0 建议，不是已定案 Schema。R1–R3 需结合现有 `skill-io-contract.md`、ADR-005 和 P1-002 产出正式 Schema。

### 7.4 版本、Artifact 与 Evidence 关系建议

1. Requirements artifact：`type=requirements`，version+sha256；用户确认记录在 G1 GateDecision/Approval，不伪造在 Skill data。
2. Analysis artifact：`type=analysis`，`source` 引用 requirements artifact version+hash。
3. Design artifact：`type=design`，`source` 引用 analysis artifact version+hash；`plan` artifact 独立，`type=plan`。
4. 新 requirements version → Analysis/Design 旧版本标记 `superseded`；G1/G2/G3 GateDecision 应绑定对应 artifact hash 并失效。
5. G4/G5 继续绑定代码 commit/产物 hash；P1-003 不改变该规则。
6. 证据复用 P1-002 `execution-evidence-standard.md`；不新增 Evidence 模型；用户确认用 G1/Approval 记录，而不是 Skill `status=ok`。

### 7.5 G1/G2/G3 挂载建议

| Gate | 挂载位置 | 输入 | 责任边界 | 失败回退 |
|------|----------|------|----------|----------|
| G1 | Requirements 完成、Analysis 之前 | requirements artifact、G1 检查项、用户确认 | 需求范围/目标/约束/验收/歧义；用户确认；不由 Skill 自批 | 返回 requirements-clarity |
| G2 | Design 完成、Plan/Coding 之前 | design artifact、architecture/API/data/security/testability、Builder Check | 设计确认 + 独立 Builder Check；不是代码 Review | 返回 design/analysis/requirements |
| G3 | Plan 完成、Coding 之前 | plan artifact、任务拆解/依赖/顺序/风险/回滚 | 开发计划确认；需要明确 plan 生产者（C1） | 重新制定 plan，不得 coding |

### 7.6 是否独立状态机

建议**不新增**三模块独立状态机：

- Task Execution State 表达节点执行；
- GateDecision 表达 G1/G2/G3；
- ADR-005 Artifact `draft/approved/superseded` 表达产物生命周期；
- 需求变更通过新 Artifact version + source 链 + Gate invalidation 表达。

如果 R1–R5 发现无法表达的状态，再评估是否新增。

---

## 八、尚未解决的问题

1. **G3 plan 生产者**：Design 输出 plan、独立 Planning 步骤，还是 P1-002 示例补 plan 节点？（C1）
2. **G1/G2/G3 是否必须绑定 Artifact hash**：这是 P1-003 标准细化，还是 ADR-006 门禁规则变更？如属后者，需 Proposed ADR-009。
3. **Requirements Schema 扩展范围**：FR/NFR、assumptions、dependencies、change_impact 是否全部进入 0.2 Schema，还是先保留在 data 扩展？
4. **Analysis 的技术选型职责**：Analysis 只推荐候选，Design 最终选择；需要 ChatGPT 确认。
5. **用户确认的 Evidence 表达**：使用 G1 GateDecision/Approval，还是新增 `confirmation` 字段/类型？
6. **Design 与具体技术栈 Skill 的边界**：Design 输出技术栈无关规格，Coding/技术栈 Skill 负责实现；需在 R3 明确。
7. **简单任务/咨询/Bug 修复的适用性矩阵**：需 R4 定稿，不得强制全流程。
8. **是否需要 ADR-009**：若 G3/plan 或 G1-G3 binding 改变已验收门禁语义，需先 Proposed ADR，等待 ChatGPT 审查。
9. **Analysis/Design 参考 Skill 的发布状态**：R2/R3 创建后仍为 draft/tested，不宣称 published/runtime。
10. **现有 P1-002 Workflow 示例的 plan 缺口**：R0 不修改；R4 需决定是补 P1-003 契约还是提出 P1-002 修正。

---

## 九、R0 验证与 OpenClaw 检查

### 9.1 基线校验器

```text
python tests/unit/orchestration/validate_orchestration.py
ORCHESTRATION VALIDATION PASSED
schemas=5 state_machines=5
examples: workflows=10 tasks=5 gates=3 approvals=3 evidence=3
schema_positive=24 schema_negative=32
workflow_graph_positive=10 workflow_graph_negative=21
state_transitions_positive=77 state_transitions_negative=245
transition_definitions=77 transition_tests=322 guard_cases=18
parallel_cases=19 task_context_cases=11 gate_cases=15
approval_cases=111 scope_cases=15 expiry_cases=6 time_fail_closed_cases=15 path_cases=12
dag_branch_cases=4 parallel_join_cases=6
failure_cases=16 security_cases=134
yaml_blocks_checked=9 registry_ids=7
runtime_behavior=NOT_EXECUTED
```

```text
python tests/unit/requirements-clarity/validate_reference_skill.py
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=1 examples_out=5
cases_input_validated=6 invalid_cases_rejected=3
semver_valid=6 semver_invalid=6
yaml_blocks_checked=9 metadata_examples=1 registry_ids=7
negative_metadata_cases_passed=5
optional_positive_cases_passed=2 optional_negative_cases_passed=9
runtime_behavior=NOT_EXECUTED platform_entries=1
```

### 9.2 文档与解析检查

- Markdown 链接：**61 个文件，0 断链**；
- Markdown 代码围栏：无未闭合；
- 全仓 JSON/YAML 解析：无错误；
- YAML 重复键 Loader：生效；
- `git diff --stat`：空（未修改已跟踪文件）；
- `git status --short`：仅两份未跟踪 R0 报告。

### 9.3 OpenClaw 只读交叉检查

- 使用既有 SDD 会话，只读，不修改文件。
- 结论：**Blocker 0 / Major 0 / Minor 1**。
- Minor：C4 的 `subject_hash` 措辞可更精确；已改为“G4/G5 明确要求；G1/G2/G3 未明确要求”。
- OpenClaw 确认 C1 的 G3 plan 生产者不一致证据成立，且 R0 未修改 P0/P1-001/P1-002 文件。

---

## 十、结论

1. 现有 P0 架构、P1-001 Skill 标准、P1-002 Orchestration 标准足以承载 P1-003，不需要推翻六层架构或修改已验收 ADR。
2. Requirements Clarity 有可用参考实现和静态测试，但需求能力仍不完整；Analysis/Design 只有架构/Workflow 名称，没有实际 Skill/标准/Schema/测试。
3. 不存在阻断性六层架构冲突；存在一项需要 ChatGPT 裁定的 G3/plan 生产者不一致（C1），以及 G1/G2/G3 Artifact 绑定、Requirements Schema 扩展等需要定案的问题。
4. R0 不实现、不批量创建 Skill、不修改 P0/P1-001/P1-002；R1 起再按实施计划推进。

**P1-003-R0 COMPLETE；P1-003-R1 NOT STARTED。**
