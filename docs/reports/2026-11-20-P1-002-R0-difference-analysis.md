# SDD P1-002 R0 差异分析报告

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-002 |
| 阶段 | R0 — 现状盘点与差异分析 |
| 分支 | `feature/p1-002-orchestration` |
| 基线 | `70b8549aff89fa8e1ce5caaf42bd413616d54c92`（main） |
| 执行/监督 | Claude Code |
| 架构决策/验收 | ChatGPT |
| 当前状态 | **R0 完成，未发现阻断性架构冲突；可进入 R1–R6** |

> 本报告只做现状盘点和差距分析，不修改 P0/P1-001 已验收规则，不实现 Orchestration Runtime。

---

## 1. 执行前 Git 基线

| 检查项 | 实际值 | 预期 | 结果 |
|--------|--------|------|------|
| 当前分支 | `main` → 新建 `feature/p1-002-orchestration` | 从 main 新建 | ✅ |
| 基线 HEAD | `70b8549aff89fa8e1ce5caaf42bd413616d54c92` | 同左 | ✅ |
| 本地 main | `70b8549aff89fa8e1ce5caaf42bd413616d54c92` | 同左 | ✅ |
| origin/main | `70b8549aff89fa8e1ce5caaf42bd413616d54c92` | 同左 | ✅ |
| 工作区 | clean | clean | ✅ |
| 未处理用户修改 | 无 | 无 | ✅ |
| P1-002 既有分支 | 无 | 无 | ✅ |

已从基线创建独立分支 `feature/p1-002-orchestration`，未在 main 上修改。

---

## 2. 已完整检查的现有文档

### 2.1 P0 架构与决策

- `docs/architecture/system-architecture.md`
- `docs/architecture/orchestration-architecture.md`
- `docs/architecture/module-architecture.md`
- `docs/architecture/skill-architecture.md`
- `docs/architecture/platform-architecture.md`
- `docs/architecture/platform-adapter-architecture.md`
- `docs/architecture/platform-compatibility-matrix.md`
- `docs/architecture/security-architecture.md`
- `docs/architecture/testing-architecture.md`
- `docs/decisions/ADR-001-overall-architecture.md`
- `docs/decisions/ADR-002-skill-standard.md`
- `docs/decisions/ADR-003-orchestration.md`
- `docs/decisions/ADR-004-cross-platform.md`
- `docs/decisions/ADR-005-task-context.md`
- `docs/decisions/ADR-006-quality-gates.md`
- `docs/decisions/ADR-007-skill-standard.md`
- `docs/decisions/ADR-008-platform-adapter.md`

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
- `skills/requirements-clarity/tests/cases.yaml`
- `skills/requirements-clarity/tests/invalid-cases.yaml`
- `tests/unit/requirements-clarity/validate_reference_skill.py`

### 2.3 关键确认结果

| 确认项 | 结论 |
|--------|------|
| P0 六层架构 | L1 交互、L2 编排、L3 研发能力、L4 专业技术、L5 基础设施、L6 平台适配边界；核心 L1–L5 不依赖 L6 具体实现 |
| 六个核心概念 | Agent、Orchestration、Workflow、Skill、Tool、Platform Adapter；权威定义在 `system-architecture.md §2` |
| G1–G6 | 唯一权威定义在 ADR-006；G6 仅在实际生产部署动作之前触发 |
| R0–R4 | 权限等级与审批分离；生产部署 = R3 + G6 + SA；生产数据库破坏性操作 = R4 + SA（涉及生产部署时再加 G6） |
| SA | 单次高风险操作显式人工授权；不得被 G6、自动检查或 Agent 自批替代 |
| Builder Check | G2 的独立审查；审查者不能复用执行者自我评价 |
| G4/G5 版本绑定 | 必须针对同一 commit 或产物 hash；Coding 新版本使旧 G4/G5 失效 |
| Skill / Agent / Workflow / Tool / Adapter | 边界已在 `system-architecture.md §2`、`skill-standard.md`、`platform-adapter-architecture.md` 明确 |
| ToolPort / ContextPort / ResultPort | 端口职责与 Capability Registry 已定义；`artifact-port` 由 ContextPort 提供，不新增端口 |
| P0 已明确的流程/复杂度 | 7 类任务、L1/L2/L3、Workflow DAG 字段、节点/Workflow 状态、G1–G6 挂载点 |

---

## 3. 现有 Orchestration 设计摘要

### 3.1 已有职责边界

| 对象 | 已有定义 |
|------|----------|
| Orchestration Engine | L2 运行时能力：任务识别、拆解、路由、DAG 执行、状态管理、结果汇总 |
| orchestration Skill | 可选入口，帮助 Agent 识别任务和选择 Workflow；不是引擎 |
| Workflow | 声明式流程定义，通过 `depends_on` 组织 DAG，引用 Skill/Tool/Gate 节点 |
| Task Context | ADR-005 定义任务上下文、Artifact 引用、生命周期状态机 |
| GateController | 在 Workflow 指定节点执行 G1–G6；规则引用 ADR-006 |
| ArtifactManager | 按 ADR-005 创建、读写、版本化 Task Context 与 Artifact |
| Platform Adapter | 实现 ToolPort / DiscoveryPort / MetadataPort / ApprovalPort / ContextPort，不定义流程 |

### 3.2 已有 Workflow 语义

- 节点字段：`id`、`type`、`skill`/`tool`、`depends_on`、`mode`、`condition`、`parallel_group`、`inputs`、`outputs`、`on_success`、`on_failure`、`retry`、`timeout_seconds`、`approval`、`gate`、`artifacts`。
- 节点类型：`skill` / `tool` / `gate` / `parallel` / `check` / `end`。
- Workflow 状态：`pending`、`running`、`awaiting_approval`、`paused`、`completed`、`failed`、`aborted`。
- 节点状态：`queued`、`executing`、`succeeded`、`failed`、`skipped`、`blocked`、`awaiting_approval`。
- 已有功能开发、Bug 修复、简单修改示例；Code Review 与 Testing 并行且共同满足 G4 AND G5。
- 失败/重试/超时/审批暂停/恢复已有原则，但缺少统一对象模型和可验证 Schema。

### 3.3 已有安全与门禁语义

- G4/G5 独立、可并行、共同构成质量门禁；同一 commit/产物 hash 绑定。
- G6 只在实际生产部署动作之前触发；非生产部署、生产非部署变更不触发 G6。
- R3/R4/SA/G6 互不替代；生产数据库普通迁移 R3，破坏性操作 R4 + SA。
- 高风险操作按实际影响范围定级；Shell 不因形式自动判为 R4。
- Builder Check 独立审查；审批记录可追溯、追加写入、敏感字段脱敏。

### 3.4 已有 Skill 标准

- Skill 是专业能力单元，不承担 Workflow 调度。
- Skill 通过 ToolPort 调用 Tool，声明 `requires.tools` / `requires.permissions`，不自行授权。
- Skill 输出统一信封：`status` / `data` / `artifacts` / `errors` / `evidence`；五状态 `ok` / `needs_input` / `needs_approval` / `blocked` / `failed`。
- `needs_approval` 只提出请求，不自行批准 G/SA。
- Skill 级测试不等同于 Workflow 的 G4/G5。

---

## 4. P1-002 差异矩阵

| 领域 | 已有基线 | 当前缺口 | P1-002 需要交付 | 冲突判断 |
|------|----------|----------|------------------|----------|
| A. Orchestration 架构 | L2 职责、组件、边界、DAG 执行语义 | 缺少正式 Orchestrator 运行时契约、组件交互、生命周期和权威索引 | Orchestration 标准、组件边界、运行时模型、生命周期 | 无阻断冲突；P0 定义需被引用而非重写 |
| B. 任务分类/复杂度 | 7 类任务、L1/L2/L3 因素 | 缺 testing/documentation 类型；缺信息不足、无法判断、用户要求简化、高风险升级规则 | 任务分类标准、复杂度判定、澄清与升级策略 | 扩展，不冲突 |
| C. Workflow 编排 | 7 个 Workflow 方向、节点字段、条件/并行/失败路径 | 缺 testing/documentation Workflow；缺动态选择/组合/跳过/追加/终止/恢复的正式规则与 Schema | Workflow 标准、9 类流程、组合规则、Schema | 扩展，不冲突；需保留 P0 现有流程语义 |
| D. Task 模型与依赖调度 | ADR-005 Task Context；节点/Workflow 状态 | 缺统一 Task 数据模型、8 状态调度模型、依赖/队列/超时/取消/恢复规则 | Task 标准、Task Schema、状态机 | 术语需映射；不改变 ADR-005 语义 |
| E. 并行执行 | G4/G5 并行、并行组、最大并发、上下文隔离 | 缺同一版本绑定在编排层的操作规则、结果汇总、共享文件冲突、兄弟任务失败处理 | 并行调度标准、聚合规则、失败传播 | 无冲突；强化 ADR-006 版本绑定 |
| F. Gate/Approval | ADR-006 全量规则；Workflow `approval` 字段 | 缺 GateDecision / Approval 对象、生命周期、绑定、过期、失效、拒绝处理 | Gate 编排标准、Approval 标准、对象 Schema | 无冲突；不得重定义 G1–G6 |
| G. 失败/恢复 | 重试、超时、失败回退原则 | 缺错误分类、幂等、补偿、不可逆操作防重试、上下文丢失、产物损坏、中断恢复 | 失败恢复标准、错误分类、重试/补偿策略 | 无冲突；不得把不可逆操作设计为自动重试 |
| H. 上下文/证据 | ADR-005 Task Context/Artifact；安全审计 | 缺上下文分层边界、Evidence 模型、证据引用、观测指标、日志/事件/审计关系 | 上下文与证据标准、观测指标、脱敏规则 | 无冲突；复用 ADR-005，不另建上下文模型 |
| I. Schema/示例/测试 | P0 仅有设计示例 YAML，明确非可执行 Schema | 缺 Workflow/Task/Gate/Approval/Evidence Schema、示例和自动测试 | `schemas/orchestration/`、`examples/orchestration/`、`tests/unit/orchestration/` | 无冲突；P0 明确把 Workflow Schema 留给 P1 |

---

## 5. 术语与状态映射

P1-002 任务书建议的 Task 状态（PENDING、READY、RUNNING、WAITING、BLOCKED、SUCCEEDED、FAILED、CANCELLED）与 ADR-005 的 Task Context 生命周期状态（created、planned、executing、awaiting_approval、verifying、completed、failed、aborted）不是同一层概念。

**处理原则：**

1. ADR-005 仍是 Task Context 持久化生命周期的权威定义，不修改。
2. P1-002 定义 **Task Execution State**，用于调度器/运行时投影；Task 模型同时保留 `context_status`，用于记录 ADR-005 生命周期。
3. 两者通过明确映射表同步，不互相替代。

建议映射：

| Task Execution State | ADR-005 `task-status` 投影 |
|----------------------|----------------------------|
| PENDING | `created`（尚未完成计划）或 `planned` |
| READY | `planned` |
| RUNNING | `executing` |
| WAITING | `executing`（依赖/退避等待，任务未终止） |
| BLOCKED | `awaiting_approval`（审批原因）；其他阻塞记录 `blocked_reason`，不改变持久化状态 |
| SUCCEEDED | `completed`（Workflow 验证完成后） |
| FAILED | `failed` |
| CANCELLED | `aborted` |

P0 Workflow/节点状态到 P1-002 运行状态的映射也将在 R2 状态机标准中明确；不改变 P0 既有状态语义。

---

## 6. 潜在冲突与裁定

### 6.1 未发现阻断性冲突

以下 P0/P1-001 规则与 P1-002 目标一致，不需要修改：

- 六层架构与 L6 适配边界；
- Orchestration 与 Skill 的职责分离；
- G1–G6 唯一权威定义；
- G4/G5 独立、并行、同一 commit/产物 hash 绑定；
- G6 仅实际生产部署触发；
- R0–R4、SA、G6 互不替代；
- 生产数据库普通迁移 R3、破坏性操作 R4 + SA；
- Builder Check 独立性；
- Task Context / Artifact 的 ADR-005 模型；
- Skill IO 五状态与 `needs_approval` 边界；
- Capability Registry 7 个 ID。

### 6.2 非阻断差异

| 差异 | 性质 | 处理 |
|------|------|------|
| Task 状态命名不同 | 术语层级差异 | 定义执行状态投影 + `context_status` 映射，不改 ADR-005 |
| Workflow/节点状态命名与建议状态不同 | 术语差异 | R2 定义映射表和合法转换，不改 P0 语义 |
| 任务类型缺 testing/documentation | 覆盖缺口 | 在 P1-002 增加类型与 Workflow，保留 P0 类型 ID |
| Workflow 节点类型缺组合/审批节点 | 扩展缺口 | 以新增节点类型或 `workflow_ref` 扩展，明确不改变 P0 节点语义 |
| 现有 `approval` 字段过于简化 | 细化缺口 | R3 定义完整 Approval 对象；不重定义 G1–G6 |
| 缺少 Evidence/观测模型 | 细化缺口 | R4 定义；复用安全审计与 ADR-005 |
| P0 示例标注“非可执行 Schema” | 交付缺口 | R5 提供 Draft 2020-12 Schema 与示例 |

### 6.3 架构决策处理

现有 ADR-003（声明式 Workflow）、ADR-005（Task Context/Artifact）、ADR-006（G1–G6）足以承载 P1-002。本轮不修改 ADR-001–008，不新增 ADR。

如果 R1–R6 出现需要改变已验收架构的决策，将先提交 ADR-009 Proposed 并停止，等待 ChatGPT 审查。

---

## 7. R1–R6 实施计划

| 阶段 | 内容 | 主要交付 | 验证 |
|------|------|----------|------|
| R1 | Orchestration 架构与任务分类 | `orchestration-architecture.md` P1-002 落地节；`orchestration-standard.md`；`task-classification-standard.md` | 文档一致性、链接 |
| R2 | Workflow / Task / 状态机 | `workflow-standard.md`、`task-standard.md`、`orchestration-state-machine.md` | 状态转换、DAG 规则 |
| R3 | Gate / Approval / 并行 | `gate-orchestration-standard.md`、`approval-orchestration-standard.md`；并行规则 | G6/R3/R4/SA、G4/G5 绑定 |
| R4 | 失败恢复 / 上下文 / 证据 | 失败恢复节、`execution-evidence-standard.md`、观测指标 | 重试/幂等/不可逆/脱敏 |
| R5 | Schema / 示例 / 测试 | `schemas/orchestration/`、`examples/orchestration/`、`tests/unit/orchestration/` | Draft 2020-12、正/负向测试 |
| R6 | 集成与独立审查 | 最终报告、PR、OpenClaw 只读审查 | 全量回归、Git 历史、CI 状态 |

每个阶段形成独立提交；阶段报告记录实施内容、修改文件、测试结果、未解决问题和下一阶段依赖。

---

## 8. 风险与限制

| 风险 | 处理 |
|------|------|
| Task 状态与 ADR-005 术语混淆 | 明确“执行状态投影”与 `context_status` 映射；文档和测试同时校验 |
| Workflow 动态组合导致规则膨胀 | 只定义选择、组合、跳过、追加、终止、恢复的边界；不实现运行时 |
| Schema 过严导致合法流程无法表达 | 采用最小必填 + 明确扩展点；示例覆盖 9 类 Workflow |
| 静态 Schema/测试被误认为运行时验证 | 所有报告保持 `runtime_behavior = NOT_EXECUTED` |
| 平台能力被误标为已验证 | 沿用 Verified/Documented/Assumed/Unsupported/Unknown；不新增平台结论 |
| 仓库无 CI | 明确说明无 CI/Checks，不把本地测试称为 CI 通过 |
| OpenClaw 协作产出偏差 | Claude Code 独立检查 diff、运行测试、修正后再提交 |

---

## 9. 结论

1. 现有 P0 架构、ADR-003/005/006 与 P1-001 标准能够承载 P1-002，不需要修改已验收架构。
2. 未发现阻断性架构冲突；存在术语映射和覆盖缺口，可在 R1–R6 内解决。
3. 不新增 ADR；若出现新的架构决策变更，先提交 ADR-009 Proposed 并停止。
4. 进入 R1–R6 实施，最终只创建 PR，不合并，不启动 P1-003。

**R0 状态：** 完成，允许进入 R1。
