# SDD P1-003-R3-R0 Design 现状盘点与差异分析

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-003-R3-R0 |
| 分支 | `feature/p1-003-r2-analysis` |
| 授权基线 | `7c57ecbc1d970f1f2757427e3b115d9338ad849c` |
| main / origin/main | `50df231d2de15b4dc33407798cce36f7d2178ee5` |
| 当前 HEAD | `7c57ecbc1d970f1f2757427e3b115d9338ad849c` |
| 工作区 | clean |
| 日期 | 2026-11-21 |
| 本轮性质 | 只读盘点、差异分析、实施规划；**不实施 Design Skill** |
| 当前状态 | **P1-003-R3-R0 COMPLETE；P1-003-R3 Design 实施 NOT STARTED；ADR-009 PROPOSED / NOT ACCEPTED** |

> 本报告基于仓库实际文件、章节、Schema、示例、测试和 Git 历史，不把目录存在当作模块完成。未执行任何 Runtime 行为。

---

## 一、盘点范围与 Git 基线

### 1.1 盘点范围

已检查：

- `docs/architecture/`
- `docs/standards/`
- `docs/decisions/`
- `docs/roadmap/`
- `skills/`
- `schemas/`
- `examples/`
- `tests/`
- 根目录目录骨架（`core/`、`tools/`、`platforms/`、`workflows/`）
- Git 分支、提交历史与路径历史

重点检索词包括 `Design`、`设计`、`design_spec`、`design_version`、`design_approved`、`G2`、`Builder Check`、`implementation-plan`、`Planning`。

### 1.2 基线事实

| 事实 | 证据 |
|------|------|
| 当前分支为 `feature/p1-003-r2-analysis` | `git branch --show-current` |
| HEAD 等于授权基线 `7c57ecb` | `git rev-parse HEAD` |
| 工作区 clean | `git status --short` 无输出 |
| main 与 origin/main 均为 `50df231` | `git rev-parse main` / `git rev-parse origin/main` |
| main 是当前分支祖先 | `git merge-base --is-ancestor main HEAD` 返回成功 |
| 当前分支比 main 多 19 个提交 | `git rev-list --count main..HEAD` |
| R1 Requirements、R2 Analysis 在授权分支上完成，但尚未合并 main | Git 图显示 R1/R2 提交位于 `50df231` 之后 |
| 没有 Design Skill 实现提交 | `git log --all --oneline -- skills/design skills/development/design` 无输出 |

**重要边界：** 本报告讨论的“已完成 R1/R2”指授权分支 `feature/p1-003-r2-analysis` 上的状态；`main` 仍停留在 P1-002 合并提交 `50df231`。R0 不改变这一事实，也不把未合并内容写成 main 已验收。

---

## 二、当前 Design 实际内容

### 2.1 文件级盘点

| 位置 | 实际内容 | 性质 | 是否能支撑 Design Skill |
|------|----------|------|--------------------------|
| `docs/architecture/module-architecture.md` §设计模块接口（约 160–174 行） | 输入 `analysis-report`；输出 `design-doc`，仅含 `architecture`、`module_structure`、`api_definitions`、`data_model`、`security_considerations` | P0 初步接口示意，非 Schema | 否；字段远不完整，且未要求 Requirements 输入 |
| `docs/architecture/system-architecture.md` L3 Skill 表（211–214 行） | `design` 输入“分析报告”，输出“设计文档” | 架构概念 | 否；只有一行职责 |
| `docs/architecture/orchestration-architecture.md` §3.3（164–176 行） | design 节点输出 `design, implementation-plan`，G3 输入 `implementation-plan` | P0 Workflow 设计示例 | 否；与 ADR-009 Proposed 的 Design/Planning 边界冲突 |
| `docs/decisions/ADR-005-task-context.md` §2（139–161 行） | Artifact 类型含 `design`；记录 path/version/sha256/source/status/references | 已接受的通用 Artifact 规则 | 部分；只提供通用身份，不提供 Design 内容 |
| `docs/decisions/ADR-006-quality-gates.md` §4（82–91 行） | G2 触发、自动检查、人工审批、回退、`design_approved`、审计 | G2 权威规则 | 部分；是门禁规则，不是 Design 产出契约 |
| `docs/standards/gate-orchestration-standard.md` §3/§6（52–59、143–152 行） | G2 挂在 design 之后；Builder Check 独立审查、检查清单、结果和证据 | P1-002 静态规则 | 部分；非 Design Skill 标准 |
| `docs/decisions/ADR-009-predevelopment-artifact-binding.md` §3.1/§3.4（42–87 行） | G2 绑定 Design Artifact version+sha256；Design 输出设计规格；Design 不输出正式 implementation-plan；Planning 属于 Orchestration | **Proposed，未生效** | 只能作为方向，不能视为已生效规则 |
| `docs/standards/analysis-standard.md` §1.3（42–52 行） | Analysis 推荐方案，Design 确定最终设计方案并输出设计规格；两者都不产生 implementation-plan | 已完成的 R2 上游边界 | 部分；只定义 Analysis 侧边界 |
| `docs/standards/requirements-standard.md` §1.2（24–36 行） | Design 负责最终设计、接口/数据模型、测试策略；Requirements 不做这些 | 已完成的 R1 上游边界 | 部分；只定义 Requirements 侧边界 |
| `docs/roadmap/roadmap.md` P3（146–163 行） | “实现架构设计 Skill”仍未勾选；交付路径写 `skills/development/design/` | 旧路线图 | 否；路径与当前 P1 实际目录不一致 |
| `skills/development/design/` | 空目录，无文件 | 目录骨架 | 否 |
| `skills/design/` | 不存在 | — | 否 |
| `skills/design/{SKILL.md,skill.yaml,schemas,examples,tests}` | 不存在 | — | 否 |
| `docs/standards/design-standard.md` | 不存在 | — | 否 |
| `tests/unit/design/` | 不存在 | — | 否 |
| `schemas/` | 只有 `schemas/orchestration/`，无 Design Schema | 通用编排 Schema | 否 |

### 2.2 能力证据矩阵

| 能力 | 已有正式标准 | 已有 Skill 实现 | 已有 Schema | 已有 IO 契约 | 已有示例 | 已有校验器/测试 | 仅概念性文档 | 尚未实现 |
|------|--------------|-----------------|-------------|--------------|----------|------------------|--------------|----------|
| Design 职责与流程 | 否 | 否 | 否 | 否 | 否 | 否 | 是 | 是 |
| Design 输入 | 否 | 否 | 否 | 否 | 否 | 否 | 是（P0 一行接口） | 是 |
| Design 输出/设计规格 | 否 | 否 | 否 | 否 | 否 | 否 | 是（ADR-009 字段清单） | 是 |
| 设计决策与备选方案 | 否 | 否 | 否 | 否 | 否 | 否 | 部分（ADR-006 G2 检查项） | 是 |
| 架构/组件/接口/数据 | 否 | 否 | 否 | 否 | 否 | 否 | 部分（P0 初步字段） | 是 |
| 状态/异常/安全/性能 | 否 | 否 | 否 | 否 | 否 | 否 | 部分（ADR-009 名称） | 是 |
| 测试策略 | 否 | 否 | 否 | 否 | 否 | 否 | 部分（Requirements 标准提及 Design 负责） | 是 |
| 需求/Analysis 追踪 | 否 | 否 | 否 | 否 | 否 | 否 | 否 | 是 |
| G2 设计审查依据 | 部分（ADR-006 + P1-002） | 否 | 部分（通用 GateDecision） | 否 | 否 | 部分（通用静态测试） | 是 | 是 |
| Design Artifact 身份 | 通用规则（ADR-005） | 否 | 通用 artifactRef | 否 | 否 | 否 | 是 | 是 |
| Design → Planning 契约 | 否 | 否 | 否 | 否 | 否 | 否 | 部分（ADR-009 Proposed） | 是 |
| Design → Coding/Review/Testing | 否 | 否 | 否 | 否 | 否 | 否 | 部分（模块关系） | 是 |

**结论：** Design 目前只有 P0 概念接口、G2 门禁规则和 ADR-009 Proposed 方向，没有可执行的 Design Skill、标准、Schema、输入输出契约、示例、校验器或测试。`skills/development/design/` 是空目录，不能据此判断模块完成。

### 2.3 已完成与未完成

**已完成（可复用基础）：**

- P1-001 统一 Skill 结构、元数据、IO 信封、错误、安全和版本规则；
- ADR-005 Artifact `design` 类型、path/version/sha256/source/status/references；
- ADR-006 G2 门禁规则；
- P1-002 GateDecision、Approval、Evidence、Workflow、Builder Check 静态规则与 Schema；
- P1-003-R1 Requirements 标准与 Skill；
- P1-003-R2 Analysis 标准与 Skill；
- Analysis 输出中的候选方案、可行性、风险、比较、推荐、unknowns、design considerations；
- 复杂度 L1/L2/L3 分类规则；
- 测试架构 T1–T4 与 G4/G5 分离规则。

**未完成（Design 模块本体）：**

- `docs/standards/design-standard.md`；
- `skills/design/`（或统一后的等价路径）；
- Design Input Schema；
- Design Output Schema；
- Design Artifact 内容契约；
- Design 示例、Checklist、测试用例、invalid cases；
- Design 校验器；
- Design 对 Requirements/Analysis 的追踪契约；
- Design → Planning 的正式交接契约；
- G2 对 Design Artifact version+sha256 的正式绑定（ADR-009 仍 Proposed）；
- Design 的 Runtime 行为（未计划在 R3 实现）。

---

## 三、Design 职责边界逐项核查

| # | 能力 | 当前证据 | 缺口 |
|---|------|----------|------|
| 1 | 输入 Requirements Artifact | Requirements 标准定义 `source_refs`/`requirements_version`；Analysis 输入要求 `requirements_ref`；Design 无输入 Schema | 未要求 Design 显式引用 Requirements Artifact；P0 接口只写 `analysis-report` |
| 2 | 输入 Analysis Artifact | ADR-009 Proposed 说 Design 根据 Analysis/Requirements；P0 模块接口输入 `analysis-report` | 无正式输入契约、无 version/sha256 要求、无两者一致性校验 |
| 3 | 上游版本与 SHA-256 引用 | ADR-005 通用 artifactRef；Analysis output 已有 `source_requirements_ref` | Design 无 Input/Output Schema；G2 绑定仍 Proposed |
| 4 | 设计决策及选择理由 | ADR-006 G2 检查“备选方案”；ADR-009 提到 decisions/tradeoffs | 无 decision 结构、无 rationale 字段、无偏离 Analysis 推荐的记录规则 |
| 5 | 系统架构与组件职责 | P0 `architecture` 字符串；`module_structure` 对象 | 无架构视图、组件职责、边界、部署/运行视图契约 |
| 6 | 模块划分与依赖 | P0 `module_structure` | 无模块 ID、职责、依赖方向、外部依赖、循环依赖检查 |
| 7 | 接口契约 | P0 `api_definitions` 数组 | 无输入/输出、错误、版本、兼容性、幂等/并发契约 |
| 8 | 数据模型与数据流 | P0 `data_model` 对象 | 无实体/关系、迁移、数据流、敏感数据、生命周期 |
| 9 | 状态管理与状态转换 | ADR-009 仅列 `state` 名称 | 无状态、事件、转换、非法转换、终态、持久化责任 |
| 10 | 异常处理与失败路径 | ADR-009 仅列 `errors` 名称 | 无失败分类、重试/补偿/降级/回滚契约 |
| 11 | 安全、权限及信任边界 | P0 `security_considerations`；安全架构定义 R0–R4/SA | 无 Design 安全字段、无信任边界、无 R0–R4/SA 映射；不得由 Design 重定义权限 |
| 12 | 性能、可扩展性与约束 | ADR-009 列 `performance`；Requirements 有 NFR | 无性能目标、容量假设、扩展点、退化策略、验证方法 |
| 13 | 测试策略 | Requirements 标准说测试策略属于 Design；测试架构定义 T1–T4/G4/G5 | 无 Design test strategy 结构，未区分策略与 G5 执行结果 |
| 14 | 验收标准与设计可验证性 | Requirements 有 AC；G2 自动检查“可测试性” | 无 Requirements AC → Design 验证方法的追踪 |
| 15 | 技术方案选择及备选方案 | Analysis 有候选、比较、推荐；ADR-006 G2 检查备选方案 | 无 Design 最终选择、偏离推荐理由、重新评估条件 |
| 16 | 风险与未决问题 | Analysis 有 risk/unknowns/open questions；G2 检查设计风险 | 无 Design 风险、假设、unknown、open question 的承接和闭环 |
| 17 | 设计变更影响分析 | ADR-005 版本/superseded；ADR-009 Proposed 失效链；Requirements 有 `change_impact` | Design 无 `design_change_impact`，无变更后下游影响说明 |
| 18 | 设计 Artifact 版本与身份 | ADR-005 定义 `design` 类型、version/sha256 | Design Skill 无 artifact 输出契约；无 `design_version`/ID 规则 |
| 19 | G2 审查依据 | ADR-006 §4；Gate 标准 §6 Builder Check | 无 Design 标准/Checklist 与 G2 检查项的逐项映射 |
| 20 | 与 Planning 的交接契约 | ADR-009 Proposed D1；Workflow 标准阶段为 `design → G2 → plan → G3` | P1-002 `feature-development.yaml` 在 G2 后直接 G3，无 plan 节点/生产者；旧 P0 示例又让 Design 输出 implementation-plan，冲突未在已接受规则中关闭 |

---

## 四、上下游契约调查

### 4.1 Requirements → Design

**现有基础：**

- Requirements Skill 输出 `type=requirements` Artifact，包含 `goal/scope/non_goals/constraints/FR/NFR/dependencies/assumptions/unknowns/open_questions/acceptance_criteria/source_refs/requirements_version`（`requirements-standard.md §4`）。
- `source_refs` 使用 ADR-005 artifactRef。
- blocking open question/unknown/conflict 不得 `ok`（`requirements-standard.md §8/§9`）。
- `change_impact` 记录 downstream impact 和 `gate_invalidation`（G1/G2/G3）。

**缺口：**

1. Design 没有正式输入契约要求 `requirements_ref`（type=requirements、version、sha256）；P0 接口只接收 analysis-report。
2. 没有 FR/NFR → 设计约束/组件/接口/验证方法的追踪规则。
3. 没有 Constraints/Dependencies/Assumptions/Open Questions/Acceptance Criteria 在 Design 中的 disposition（承接/映射/不适用/延后）规则。
4. 没有“上游 blocking 未决项不得输出 Design `ok`”的规则。
5. 没有防止需求遗漏或无依据新增设计目标的检查。
6. 需求新版本导致 Design 旧版本 `superseded`/G2 失效的规则只在 ADR-009 Proposed，不是已生效规则。

**R3 应补充：**

- Input Schema 要求 `requirements_ref`；
- Design 输出 `requirements_traceability`，覆盖 FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/acceptance_criteria/non_goals/source_refs；
- `ok` 前检查 blocking 未决项；
- 设计目标必须来自 Requirements/Analysis 或明确说明新增理由并回指；
- `design_change_impact` 条件字段和上游变化处理规则。

### 4.2 Analysis → Design

**现有基础：**

- Analysis 输出 `source_requirements_ref`、候选方案、可行性、风险、比较矩阵、推荐、facts/assumptions/unknowns、requirements_traceability、next_steps（含 design_considerations）。
- Analysis 明确“推荐方案不是设计批准”，最终设计选择由 Design 完成（`analysis-standard.md §1.2/§1.3`）。
- Analysis 输出 `type=analysis` Artifact（ok 时 required）。

**缺口：**

1. Design 没有 `analysis_ref` 输入 Schema，也没有校验 type=analysis、version、sha256。
2. 没有“推荐方案不是强制设计决定”的正式规则；Design 可能把 `recommended_solution_id` 当作唯一答案。
3. 没有偏离推荐方案时必须记录理由、证据和重新评估条件的规则。
4. 没有 Analysis 的 risks/unknowns/open questions/assumptions/design_considerations 在 Design 中的承接规则。
5. 没有 Analysis 新版本导致 Design/G2 失效的已生效规则（仅 ADR-009 Proposed）。
6. 没有 Design 选择 Analysis 未列出的新方案时的处理规则（需要 evidence/rationale 或 `needs_input`）。

**R3 应补充：**

- Input Schema 要求 `analysis_ref`，并要求 Analysis `source_requirements_ref` 与输入的 `requirements_ref` 一致；
- Design `selected_solution` 引用 Analysis candidate（如适用），或记录 `new_solution_rationale`；
- `analysis_alignment`/`deviation_rationale`；
- `analysis_traceability` 覆盖候选、风险、unknowns、design considerations；
- 推荐不等于批准，Design 可以基于证据选择其他方案，但必须记录理由；
- `ok` 不得绕过 Analysis 的 blocking unknown/open question。

### 4.3 Design → Planning

**正式方向（ADR-009 Proposed）：**

- Design 输出设计规格；
- Design **不输出正式 implementation-plan**；
- Planning 是 Orchestration 内部活动，不是独立研发专业 Skill；
- Planning 根据 Design/Requirements/Analysis 生成 `plan` artifact；
- G3 检查并批准 plan，不负责生成 plan；
- 正式链路：`Requirements → G1 → Analysis → Design → G2 → Planning → G3 → Coding`。

**当前实现状态：**

- `workflow-standard.md §5.4` 描述 `design → G2 → plan → G3`；
- `examples/orchestration/workflows/feature-development.yaml` 实际节点为 `design → g2 → g3 → coding`，没有 `plan` 节点、没有 plan 输出、没有 Planning 活动；
- `docs/architecture/orchestration-architecture.md §3.3` 仍写 design 节点输出 `design, implementation-plan`，G3 输入 implementation-plan；
- 因此当前仓库同时存在三种口径：
  1. P0 旧示例：Design 输出 implementation-plan；
  2. P1-002 Workflow 标准：有 plan 阶段；
  3. P1-002 实际示例：无 plan 节点；
  4. ADR-009 Proposed：Design 不输出 plan，Planning 属于 Orchestration。

**结论：** Design → Planning 的语义方向已由 ADR-009 Proposed 给出，但**不是已生效规则**，且 P1-002 示例没有 plan 生产者。R3 只能定义 Design 输出和交接契约，不能自行决定 Planning 实现或修改 P1-002；该冲突必须在 R4 跨模块集成阶段由 ChatGPT 裁定后处理。

### 4.4 Design → Coding

**已有基础：**

- 模块架构声明 `design → coding`（`module-architecture.md` 依赖图）。
- ADR-009 Proposed 要求设计规格包含 architecture/modules/interfaces/data/state/errors/security/performance/test strategy/tradeoffs/decisions。

**缺口：**

- Coding Skill 尚未实现（`skills/development/coding/` 是空目录结构，`skills/coding/` 不存在）。
- 没有“Coding 需要哪些设计字段才能开始”的正式交接契约。
- 没有“设计不完整时 Coding 必须反馈而不是自行填补重大决策”的规则。
- 没有组件/接口/数据结构的稳定 ID 和可引用契约。
- 没有设计约束（依赖、兼容性、性能、安全）到实现约束的映射。

**R3 应补充：**

- Design 输出可供 Coding 引用的组件 ID、接口 ID、数据模型 ID、约束 ID；
- Design `implementation_constraints`/`coding_handoff`；
- 明确 Coding 不得自行决定架构/接口/数据模型；设计缺失时应返回 `needs_input`/反馈节点；
- 具体 Coding Skill 仍属后续阶段，不在 R3 实施。

### 4.5 Design → Review / Testing

**已有基础：**

- ADR-006：G4 代码质量/独立 Review；G5 测试验收；G4/G5 独立且绑定同一 commit/产物 hash。
- 测试架构：T1–T4；Skill 单元测试、Workflow 集成测试、E2E；G4/G5 分离。
- G2 Builder Check：独立审查设计，检查需求遗漏、设计矛盾、过度设计、安全风险、不可落地方案、异常场景（`gate-orchestration-standard.md §6`）。

**缺口：**

- 没有 Design 标准/Checklist，无法把 G2 检查项逐项映射到设计字段。
- 没有 Requirements AC → Design 验证方法 → Testing 用例的追踪契约。
- 没有 Design 决策/接口/数据模型与代码 Review 的符合性基准。
- 没有 Design 变更后 G4/G5 是否受影响的说明（G4/G5 绑定代码，不直接绑定设计；设计变更可能导致代码重做）。
- 没有防止 Design 输出被误当作 G4/G5 证据的规则。

**R3 应补充：**

- Design Checklist 与 G2 自动检查项一一对应；
- `test_strategy` 只定义策略/验证方法和 AC 映射，不写测试执行结果；G5 由 Testing 执行；
- `design_compliance_refs`/可审查的设计 ID，供 G4 检查代码符合性；
- 明确 Design 不替代 G4/G5，不产生 `testing_approved`/`code_review_approved`。

---

## 五、G2 现状与要求

### 5.1 当前正式规则（ADR-006）

`ADR-006 §4` 定义：

- 触发：design 节点完成；L2/L3；安全敏感任务；
- 自动检查：设计文档；架构影响；接口/数据模型；安全考虑；备选方案；可测试性；回滚/迁移方案；
- 人工审批：L3、跨模块、安全敏感、新增依赖/外部服务、用户要求；
- 允许跳过：L1 局部修改且无接口/数据模型/安全/外部依赖变化；
- 不允许跳过：新服务/新模块、数据模型变更、认证/授权/加密、外部 API、生产架构变更；
- 失败回退：design；方案不可行时回退 analysis/requirements；
- 通过状态：`design_approved`；
- 审计：Builder Check 结果 + 人工审批记录。

### 5.2 已实现的静态规则（P1-002）

- `gate-orchestration-standard.md §3`：G2 挂在 design 之后，控制技术方案、架构影响、Builder Check；人工审批条件与 ADR-006 一致。
- `§6` Builder Check：审查者独立；高风险任务独立 Agent/人类；检查需求遗漏、设计矛盾、过度设计、安全风险、不可落地方案、异常场景；结果 `approved/needs_revision/escalated`；证据包含设计产物 hash。
- `schemas/orchestration/gate-decision.schema.json`：GateDecision 通用 `subject_type`/`subject_hash`；`status=PASSED` 时要求非空 `subject_hash`；但 G1/G2/G3 没有专门的 artifact path/version/type 绑定。
- `schemas/orchestration/approval.schema.json`：仅 G4/G5/G6 相关 Approval 强制 `subject_hash`；G2 的人工审批不强制 Artifact hash。
- `examples/orchestration/gates/` 只有 G4、G5、G6 示例，没有 G2 示例。
- `tests/unit/orchestration/validate_orchestration.py` 对 GateDecision 做通用静态校验，没有 Design/G2 专项语义测试。

### 5.3 ADR-009 Proposed 规则

- G2 绑定 Design Artifact（`type=design`、version、sha256）；
- GateDecision 记录 subject_type=artifact、subject_hash、path/version/type；
- Approval 绑定同一 Artifact；
- Design 新版本使 G2/G3 旧 decision 失效；
- Design 不输出 implementation-plan，Planning 属于 Orchestration；
- 旧 decision 保留审计历史。

**状态：Proposed / NOT ACCEPTED。** 本 R0 不得把上述规则写成已生效，也不得修改 ADR-009。

### 5.4 尚未实现的 Runtime

- GateController / GateDecision 持久化；
- G1/G2/G3 自动 Artifact binding；
- Approval 与 Design Artifact 的运行时绑定；
- 上游版本变化自动失效；
- Builder Check 运行时独立性验证；
- G2 的 Workflow 执行与回退。

### 5.5 R3 与 R4 的分工建议

**R3（Design 模块本体）应补齐：**

- Design 标准、Skill、Input/Output Schema；
- Design Artifact 内容与 `design_version`；
- Requirements/Analysis 追踪；
- 设计决策、备选方案、风险、unknowns；
- G2 检查项到 Design 字段的静态映射；
- Builder Check 所需的设计证据字段；
- Design 不伪造 G2/Approval 的约束。

**R4（跨模块集成）才应处理：**

- G2 对 Design Artifact path/version/sha256 的 GateDecision 绑定；
- G3 Plan 生产者与 Planning 活动；
- Requirements/Analysis/Design/Plan 失效链 Runtime 表达；
- P1-002 Workflow 示例的 plan 节点缺口；
- ADR-009 是否接受及其对 ADR-006/P1-002 的影响；
- 跨模块 applicability matrix。

R3 可以设计输出字段以兼容 ADR-009 Proposed，但不得实施 GateController 或修改 P1-002。

---

## 六、Artifact 与 Schema 缺口

### 6.1 现有 Artifact 基础

- ADR-005 已定义 `type=design`，无需新增 Artifact 类型。
- Artifact 引用为 `{path, version, sha256, type}`；`source` 记录输入引用；`status` 为 draft/approved/superseded。
- Design Artifact 应由 Design Skill 输出，并在 `artifacts` 数组中引用；不能在 `data` 内伪造第二套 Artifact 身份。

### 6.2 建议的 Design Artifact 字段分类

| 字段/能力 | 分类 | 说明 |
|-----------|------|------|
| `design_id` | Required | 稳定 ID；建议 `DESIGN-*` |
| `design_version` | Required | SemVer；Artifact version 仍为 ADR-005 整数 version，两者不混用 |
| `created_at` | Required | 时间戳 |
| `source_requirements_ref` | Required | type=requirements；version+sha256 |
| `source_analysis_ref` | Required | type=analysis；version+sha256 |
| `source_refs` | Optional | 额外证据/上下文引用 |
| `design_summary` | Required | 设计范围、目标、非目标；引用上游，不重写需求 |
| `selected_solution` | Required（有方案选择时） | 选择结果；引用 Analysis candidate 或说明新方案 |
| `alternatives` | Conditional Required | 多候选/偏离推荐时必须有；L1 单方案可记录“无其他可行方案”理由 |
| `decisions` | Required | 决策 ID、内容、理由、备选、后果、关联需求/分析 |
| `architecture_overview` | Required | 系统/组件/部署/运行视图的适用部分 |
| `components` | Conditional Required | 新模块/组件/跨模块变更时必需 |
| `modules` | Conditional Required | 模块划分与依赖 |
| `interfaces` | Conditional Required | API/事件/端口/契约变化时必需 |
| `data_models` | Conditional Required | 数据模型变化时必需 |
| `data_flows` | Conditional Required | 跨组件数据流/敏感数据流时必需 |
| `state_model` | Conditional Required | 有状态/生命周期变化时必需 |
| `failure_handling` | Conditional Required | 外部依赖/失败路径/重试/补偿/降级 |
| `security_design` | Conditional Required | 安全敏感/认证/授权/加密/信任边界；否则记录 N/A 理由 |
| `performance_scalability` | Conditional Required | 有性能/容量 NFR 或架构变化 |
| `migration_rollback` | Conditional Required | 数据/接口/生产架构变更 |
| `test_strategy` | Required | 验证方法、测试层级、AC 映射、环境/数据需求；不是测试结果 |
| `requirements_traceability` | Required | FR/NFR/constraints/dependencies/assumptions/unknowns/open_questions/AC/non_goals/source_refs 的承接/映射/不适用/延后 |
| `analysis_traceability` | Conditional Required | 候选/风险/unknowns/design_considerations 的承接；有 Analysis 时必需 |
| `risks` | Required | 设计级风险、缓解、残余、状态；可引用 Analysis 风险并说明设计控制 |
| `assumptions` | Required（可空） | 设计假设；不得伪装为事实 |
| `unknowns` | Required（可空） | 未知项；blocking 时不得 `ok` |
| `open_questions` | Required（可空） | 需要用户/上游回答的问题 |
| `design_change_impact` | Conditional Required | 变更设计时记录下游影响、需重跑阶段 |
| `implementation_constraints` | Optional | 给 Coding 的约束/技术栈边界；不写完整实现 |
| `coverage` | Recommended | 对接口/数据/状态/安全/性能等区域记录 `designed/not_applicable/deferred` + 理由，防止静默遗漏 |
| 图表、ADR 链接、运行手册 | Optional | 可放 references/assets，不作为核心必填 |

**不应进入 Design data 的字段：**

- `implementation_plan`、任务拆解、排期（属于 Planning/G3）；
- `design_approved`、`gate_approved`、`confirmation_ref`、GateDecision/Approval；
- `code_review_approved`、`testing_approved`；
- 完整的 Requirements 副本（应引用 Requirements Artifact）；
- 测试执行结果（属于 Testing/G5）。

### 6.3 是否需要各 Schema/配套

| 交付物 | 建议 | 理由 |
|--------|------|------|
| `design-standard.md` | 必需 | 定义职责、输入输出、完整度、G2/Planning/Coding 边界 |
| `skills/design/SKILL.md` | 必需 | 参考 Skill 的执行规范 |
| `skills/design/skill.yaml` | 必需 | 版本、状态、依赖（requirements/analysis 契约） |
| `schemas/input.schema.json` | 必需 | 强制 Requirements/Analysis Artifact 引用与类型 |
| `schemas/output.schema.json` | 必需 | 统一信封 + 状态相关 data + 禁止字段 |
| `examples/` | 必需/推荐 | 至少 L2 完整、L1 轻量、needs_input/blocked 部分输出 |
| `references/design-checklist.md` | 必需 | G2/Builder Check 可操作检查项 |
| `tests/cases.yaml` | 必需 | 正向/边界/状态用例 |
| `tests/invalid-cases.yaml` | 必需 | 缺输入、错引用、伪造 G2、无理由决策等 |
| `tests/unit/design/validate_design_skill.py` | 必需 | Schema/语义/回归校验器 |
| 新 Artifact 类型 | 不建议 | ADR-005 已有 `design` |
| 新状态机 | 不建议 | 复用 Skill 五状态 + Task/Gate/Approval |

---

## 七、Design 状态语义建议

复用 P1-001 五状态，不新增状态机：

| 状态 | Design 语义 | 约束 |
|------|-------------|------|
| `ok` | 设计达到最低完整度，无 blocking 未决项 | **不等于 G2 通过/设计批准**；不得写 `design_approved` |
| `needs_input` | 缺少需求/分析信息、设计选择需用户确认、关键 unknown | 必须返回 `questions`；可带部分 design |
| `needs_approval` | 设计决策触发安全/高风险审批，需显式批准后才能定稿 | 只能表示待确认，**不得表示 G2 已通过**；不得自批 |
| `blocked` | 缺少上游 Artifact/权限/环境/外部依赖，无法继续 | 必须返回 `blocked_reason`；不得伪造完整设计 |
| `failed` | 输入无效、内部错误、无法生成设计 | 至少一个 error；不得伪装 `ok` |

补充规则：

- `ok` 要求 Required 字段完整、Conditional Required 字段要么有内容要么有 `not_applicable` 理由、无 blocking unknown/open question、决策有理由。
- `needs_approval` 不应被 Design 用来“请求 G2”；G2 是 Orchestration 在 Design 完成后执行的 Gate。Design 只可请求具体设计决策/安全事项的人工确认。
- Design 不得直接写 GateDecision/Approval，不得输出 `design_approved`、`gate_approved`、`confirmation_ref`。
- Skill `status`、Artifact `status`（draft/approved/superseded）和 Gate `status`（PASSED 等）是三层不同语义，不得混用。

---

## 八、复杂度与设计深度建议

复杂度由 Orchestration 按 P1-002 `task-classification-standard.md §4` 判定，不能仅按代码行数；Design 不应自行降低复杂度。

| 等级 | 最低设计要求 |
|------|--------------|
| **L1** | 设计摘要、受影响组件/接口/数据的 N/A 说明、至少一个关键决策及理由、AC/验证方法、明确风险/unknown；可跳过完整架构章节 |
| **L2** | 架构概览、组件职责、接口/数据模型（如变化）、失败处理、安全边界、测试策略、决策/备选、Requirements/Analysis 追踪 |
| **L3** | L2 + 完整架构/组件/数据流、状态转换、安全/信任边界、性能/容量、迁移/回滚、运维/可观测性、偏离推荐的理由、变更影响、完整追踪 |

**升级触发（至少建议）：**

- 系统/跨系统影响或架构变更；
- 数据模型/数据迁移/生产数据；
- 认证、授权、加密、敏感凭证；
- 新增外部服务/依赖/API；
- 不可逆或高风险变更；
- 需求/技术方案存在关键未知；
- 多模块、多 Agent、跨团队依赖。

**降低条件：**

- 仅局部、可逆、无接口/数据/安全变化，且有验证证据；
- 降级必须由 Orchestration 基于证据决定并记录，Design 只能建议，不能自行降级。

**不适用项：** 必须在 `coverage`/对应字段记录 `not_applicable` + 理由，不得静默省略。

---

## 九、兼容性与重复建设分析

### 9.1 应优先复用

| 现有资产 | 复用方式 |
|----------|----------|
| P1-001 Skill Standard / IO Contract | Design 的目录、SKILL.md、五状态信封、错误、Artifact/Evidence 字段 |
| ADR-005 Artifact | `type=design`、path/version/sha256/source/status/references；不新增 Artifact 类型 |
| Requirements Artifact | 作为唯一需求基线；Design 只引用/追踪，不复制或改写 |
| Analysis Artifact | 作为候选/可行性/风险/推荐来源；Design 做最终选择并记录偏离 |
| P1-002 Task/Workflow/Gate/Approval/Evidence | Design 不新建并行状态机、Gate 或 Approval；G2 由 Orchestration 执行 |
| ADR-006 G2 | Design 输出满足 G2 检查项，但不能自行批准 |
| Task Classification L1/L2/L3 | Design 深度由 Orchestration 分类驱动 |
| Security Architecture R0–R4/SA | Design 只声明安全约束和审批需求，不重定义权限 |
| Testing Architecture T1–T4 | Design 定义测试策略/AC 映射；Testing 执行 G5 |

### 9.2 兼容性问题

1. **路径不一致**：P0 模块架构/路线图写 `skills/development/design/`，实际 P1 Skill 位于 `skills/requirements-clarity/`、`skills/analysis/`；`skills/development/design/` 为空，`skills/design/` 不存在。R3 需先裁定统一路径（建议 `skills/design/`），但不得在 R0 修改 P0 文档。
2. **Design 输入不一致**：P0 接口只接收 `analysis-report`；正式方向要求同时引用 Requirements 和 Analysis。
3. **Planning 冲突**：P0 orchestration 示例让 Design 输出 implementation-plan；P1-002 实际 Workflow 没有 plan 节点；ADR-009 Proposed 规定 Design 不输出 plan。R0 记录，R4 关闭。
4. **G2 绑定未生效**：GateDecision Schema 的 PASSED 要求 subject_hash，但不要求 Design Artifact path/version/type；Approval Schema 不强制 G2 subject_hash；ADR-009 Proposed 未接受。
5. **字段重复风险**：Design 不应复制 Requirements 的 `goal/scope/non_goals/FR/NFR/AC` 全文；应引用和追踪。Design 不应复制 Analysis 的候选/比较全文；应引用并记录最终决策。
6. **证据重复风险**：Design 不能输出测试执行结果、Code Review 结果或 G2 审批记录；只能输出设计证据和 G2 审查对象。
7. **状态重复风险**：不新增 `design_state` 状态机；复用五状态信封 + ADR-005 Artifact status + GateDecision。
8. **目录骨架误导风险**：`skills/development/*` 大量空目录只是 P0 规划，不能作为 Skill 已存在证据。

---

## 十、发现的风险

| 风险 | 影响 | 建议 |
|------|------|------|
| G3/Plan 生产者未关闭 | Design 可能被重新塞入 implementation-plan，或 G3 无审查对象 | R4 前由 ChatGPT 裁定；R3 明确 Design 不输出 plan |
| ADR-009 仍 Proposed | 不能声称 G2 Artifact binding 已生效 | R3 设计兼容字段，但不实施 Gate binding；R4 处理生效问题 |
| G2 无专项示例/测试 | Design 输出可能不满足 Builder Check | R3 建 checklist；R4 加 G2 静态示例/测试 |
| Design 过宽/过度设计 | 输出膨胀、重复 Requirements/Analysis | 按复杂度裁剪；Required/Conditional/Optional/N/A 区分 |
| Design 越权定技术栈实现 | 与 Coding/技术栈 Skill 冲突 | Design 输出技术栈无关规格和约束；实现细节留给 Coding |
| 测试策略与 G5 混淆 | Design 被误当作测试通过证据 | 明确 test strategy ≠ test result；G5 由 Testing |
| 设计安全字段重定义 R0–R4/SA | 安全规则冲突 | 只引用安全架构，不重定义权限/审批 |
| 下游 Coding/Testing Skill 未实现 | Design→Coding/Testing 契约无法端到端验证 | R3 只做静态契约；端到端留待后续阶段 |
| 路径/目录骨架误导 | 误判 Design 已实现 | R3 前统一路径；R0 记录空目录事实 |
| 复杂度被 Design 自行降低 | 高风险任务设计不足 | Orchestration 拥有分类权；Design 只能建议升级 |

---

## 十一、结论

1. **Design 当前没有可执行实现。** 只有 P0 初步接口、G2 门禁规则和 ADR-009 Proposed 方向；没有标准、Skill、Schema、示例、校验器或测试。
2. **基础足够。** P1-001、ADR-005、ADR-006、P1-002、R1 Requirements、R2 Analysis 已提供可复用的 Skill/IO、Artifact、Gate、Approval、Evidence 和上游契约。
3. **Design 的核心缺口是“设计规格 + 决策 + 追踪 + G2 审查对象”契约**，不是再建一套工作流、状态机或审批系统。
4. **Design 不得输出 implementation-plan。** Planning 属于 Orchestration；G3 检查/批准 plan，不生成 plan。当前 P1-002 示例的 plan 生产者缺口必须在 R4 处理。
5. **G2 Artifact binding 仍为 Proposed。** R3 可以设计兼容字段和静态检查，但不能宣布 G2 binding 已生效，也不能修改 ADR-006/ADR-009/P1-002。
6. **建议进入 R3-R1（Design Standard）前，ChatGPT 先确认**：统一 Skill 路径、Design 输入双引用、Design 不输出 plan、G2/ADR-009 的 R3/R4 分工、复杂度裁剪原则。
7. **Runtime 未执行。** 本报告的所有结论均为静态文档/代码/测试盘点，不代表 Design Runtime、GateController 或自动失效已实现。

---

**P1-003-R3-R0 COMPLETE（本报告）**

**P1-003-R3 Design 实施 NOT STARTED**

**ADR-009 PROPOSED / NOT ACCEPTED**

**PR NOT CREATED**

**MAIN UNMODIFIED**
