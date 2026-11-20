# SDD P1-003-R0 Requirements / Analysis / Design 实施计划

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-003-R0 |
| 分支 | `feature/p1-003-requirements-analysis-design` |
| 基线 | `50df231d2de15b4dc33407798cce36f7d2178ee5`（main） |
| 关联报告 | `docs/reports/2026-11-20-P1-003-R0-difference-analysis.md` |
| 当前状态 | **P1-003-R0 COMPLETE；P1-003-R1 NOT STARTED** |

> 本计划是 R0 建议，不是已定案架构。R1 开始前，ChatGPT 需先裁定差异分析报告 §八中的 G3/plan 生产者、G1/G2/G3 Artifact 绑定和 ADR 需求。

---

## 一、规划原则

1. **复用优先**：复用 P1-001 统一信封、ADR-005 Artifact、P1-002 Task/Gate/Approval/Evidence；不另建第二套通用规范。
2. **模块单一职责**：Requirements 只澄清需求；Analysis 只分析现状/影响/可行性；Design 只产出设计规格；不把 Coding/Testing/Workflow 调度塞进三个 Skill。
3. **按需适用**：简单修改、技术咨询、明确 Bug 修复可不走完整三模块链路；通过适用性矩阵裁剪。
4. **用户确认不伪造**：Skill 的 `ok` 不等于用户确认；G1/Approval 记录确认。
5. **版本可追溯**：requirements → analysis → design 通过 Artifact version+sha256+source 链关联；需求新版本使下游失效。
6. **静态优先**：R1–R5 只交付标准、Schema、示例和静态测试；不实现 Runtime。
7. **不扩大范围**：不实现 Coding/Testing/WorkflowRunner/Adapter；不批量创建 Skill；不修改 P0 ADR 或 P1-001/P1-002 已验收规则。

---

## 二、R1 开始前的决策门

| 决策 | 影响 | 处理 |
|------|------|------|
| D1 G3 plan 生产者 | Design 是否输出 implementation plan；G3 检查对象 | ChatGPT 在 R1/R3 前裁定；R4 前必须关闭 |
| D2 G1/G2/G3 Artifact hash 绑定 | 是否要求 GateDecision 绑定 artifact hash | 若视为 ADR-006 规则变更，先提交 ADR-009 Proposed |
| D3 Requirements Schema 扩展范围 | FR/NFR/assumptions/change_impact 是否进入 0.2 Schema | R1 前确认；未确认时先写入 data 扩展草案，不发布 |
| D4 Analysis 技术选型职责 | Analysis 候选推荐 vs Design 最终选择 | R2/R3 前确认 |
| D5 用户确认 Evidence | G1 GateDecision/Approval vs Skill 字段 | R1 前确认；默认使用 G1/Approval，不新增证据类型 |
| D6 是否需要 ADR-009 | G3/plan 或 G1-G3 binding 是否改变已验收语义 | 若需要，R4 前 Proposed，等待审查 |

---

## 三、阶段总览

| 阶段 | 目标 | 主要交付 | 依赖 |
|------|------|----------|------|
| R1 | Requirements 标准与参考 Skill 升级 | Requirements 标准、Schema、SKILL.md、示例、测试 | D3/D5 |
| R2 | Analysis 标准与参考 Skill | Analysis 标准、Schema、SKILL.md、示例、测试 | R1 契约 |
| R3 | Design 标准与参考 Skill | Design 标准、Schema、SKILL.md、示例、测试 | R2 契约、D1/D4 |
| R4 | 跨模块契约、版本、Evidence、G1-G3 集成 | 契约标准、版本/失效规则、适用性矩阵、G1-G3 绑定 | R1–R3、D1/D2/D6 |
| R5 | Schema/示例/校验器与全量回归 | 跨模块校验器、正负向用例、回归报告 | R1–R4 |
| R6 | 集成审查与 PR 准备 | 最终报告、OpenClaw 只读审查、PR | R5 |

每个阶段形成独立提交；阶段报告记录实施内容、修改文件、测试结果、未解决问题和下一阶段依赖。

---

## 四、R1：Requirements 标准与参考 Skill 升级

### 4.1 目标

把 `requirements-clarity` 从“基础需求基线”升级为可支撑 Analysis/Design 的需求契约，覆盖差异分析 §4.1 的 12 项能力；保持简单任务可按需裁剪。

### 4.2 预期文件

- `docs/standards/requirements-standard.md`（新）
- `skills/requirements-clarity/SKILL.md`（升级）
- `skills/requirements-clarity/skill.yaml`（版本、状态、依赖）
- `skills/requirements-clarity/schemas/input.schema.json`
- `skills/requirements-clarity/schemas/output.schema.json`
- `skills/requirements-clarity/examples/*`（新增/更新）
- `skills/requirements-clarity/references/requirements-checklist.md`
- `skills/requirements-clarity/tests/cases.yaml`
- `skills/requirements-clarity/tests/invalid-cases.yaml`
- `tests/unit/requirements-clarity/validate_reference_skill.py`
- `docs/reports/2026-11-20-P1-003-R1-report.md`

### 4.3 交付物

1. Requirements 标准：职责、适用/不适用、输入输出、G1 边界、Evidence、版本。
2. Schema 扩展建议：
   - `functional_requirements`、`non_functional_requirements`；
   - `dependencies`、`assumptions`、`open_questions`；
   - `acceptance_criteria` 的可验证结构；
   - `change_impact`；
   - `source_refs`/`confirmation_ref`（确认由 G1/Approval 记录）。
3. 明确 `ok` 不等于用户确认；`needs_input` 保留未决问题，不伪造确认。
4. 适用性矩阵：simple/consultation/bug-fix/feature/refactor/new-project/testing/documentation 对 Requirements 的默认需要。
5. 输入 `existing_requirements` 从字符串升级为结构化 Artifact 引用（或兼容字符串并标注）。
6. 测试：现有 6 cases + 新增 NFR/assumptions/change/confirmation/negative cases。

### 4.4 测试策略

- Schema 正向/负向：必填、未知字段、状态相关 data、artifact ref、版本/hash。
- 现有 cases/invalid cases 全部保留；新增 NFR、assumptions、open questions、change impact 用例。
- 不得把 `ok` 测试成用户确认；G1 确认另行测试/记录。
- 不执行 Runtime。

### 4.5 验收条件

- Requirements 标准与 P1-001 信封/安全/版本标准一致；
- 现有参考 Skill 回归通过；
- 简单/咨询/Bug 修复适用性明确；
- 无 Schema 伪造确认、无 Agent 假设升级为用户事实；
- 报告明确静态验证边界。

---

## 五、R2：Analysis 标准与参考 Skill

### 5.1 目标

建立 Analysis 的职责、输入输出和证据契约，覆盖现状、结构、差异、影响、依赖、可行性、方案依据、风险、安全、质量属性、多方案和结论。

### 5.2 预期文件

- `docs/standards/analysis-standard.md`（新）
- `skills/analysis/SKILL.md`（新，最小参考 Skill）
- `skills/analysis/skill.yaml`
- `skills/analysis/schemas/input.schema.json`
- `skills/analysis/schemas/output.schema.json`
- `skills/analysis/examples/*`
- `skills/analysis/tests/cases.yaml`
- `skills/analysis/tests/invalid-cases.yaml`
- `tests/unit/analysis/validate_analysis_skill.py`
- `docs/reports/2026-11-20-P1-003-R2-report.md`

### 5.3 交付物

1. Analysis 标准：职责、与 Requirements/Design/Coding 边界。
2. Schema 建议：
   - `requirement_refs`（version+sha256）；
   - `analysis_type`（current_state/gap/impact/feasibility/diagnosis/mixed）；
   - `current_state`、`system_structure`、`gap_analysis`、`impact_scope`、`dependencies`；
   - `feasibility`、`options`、`risks`、`security_risks`、`quality_attributes`；
   - `facts`、`assumptions`、`unknowns`、`recommendation`。
3. 明确 Analysis 只做候选方案/可行性/依据，不把候选写成最终 Design。
4. Evidence：代码/文档引用、命令/检查、事实来源；不伪造验证。
5. 测试：结构/Schema/正常/异常/未知项/安全风险/多方案。

### 5.4 测试策略

- Schema 正向/负向、必填/未知字段、状态相关 data。
- 需求引用版本/hash 必填（按 D2 裁定）。
- 事实/假设/未知分类测试。
- 安全/权限风险、性能/可靠性/可维护性字段测试。
- 现有 P1-001/P1-002 校验器回归不受影响。

### 5.5 验收条件

- Analysis 标准与 Requirements 契约一致；
- Analysis 不重新定义需求、不输出最终设计；
- 证据可追溯；
- 静态测试通过；
- 无 Runtime 声明。

---

## 六、R3：Design 标准与参考 Skill

### 6.1 目标

建立 Design 的职责、输入输出和审查契约，覆盖架构、模块/组件、数据/API、状态/错误、安全、性能、测试策略、权衡和版本。

### 6.2 预期文件

- `docs/standards/design-standard.md`（新）
- `skills/design/SKILL.md`（新，最小参考 Skill）
- `skills/design/skill.yaml`
- `skills/design/schemas/input.schema.json`
- `skills/design/schemas/output.schema.json`
- `skills/design/examples/*`
- `skills/design/tests/cases.yaml`
- `skills/design/tests/invalid-cases.yaml`
- `tests/unit/design/validate_design_skill.py`
- `docs/reports/2026-11-20-P1-003-R3-report.md`

### 6.3 交付物

1. Design 标准：职责、与 Analysis/Coding/技术栈 Skill/G2/G4 的边界。
2. Schema 建议：
   - `analysis_refs`/`requirement_refs`；
   - `architecture`、`modules`、`components`；
   - `data_model`、`interfaces`、`api_contracts`；
   - `state_flow`、`error_paths`；
   - `security_design`、`performance_scalability`；
   - `test_strategy`、`tradeoffs`、`decisions`、`implementation_constraints`；
   - `design_version`。
3. 明确 Design 输出技术栈无关规格；具体实现由 Coding/技术栈 Skill 负责。
4. 明确 Design 审查是 G2/Builder Check，不是 G4 Code Review。
5. 按 D1 决定是否输出 `implementation_plan`；未决定前不擅自定案。
6. 测试：结构/Schema/正常/异常/安全/接口/数据/测试策略/版本。

### 6.4 测试策略

- Schema 正向/负向、必填/未知字段、状态相关 data。
- 引用 Analysis version/hash；需求变更失效测试。
- G2 Builder Check 独立性测试（作者≠审查者）。
- 设计不替代 G4/G5 的边界测试。
- 不执行 Runtime。

### 6.5 验收条件

- Design 标准与 Requirements/Analysis 契约一致；
- G2/G3 边界明确；
- 不输出最终代码/不替代 Code Review；
- 静态测试通过；
- 无 Runtime 声明。

---

## 七、R4：跨模块契约、版本与 G1-G3 集成

### 7.1 目标

把三个模块组织成可追溯的 Requirements → Analysis → Design → Coding 链路，解决版本失效、Artifact/Evidence、G1/G2/G3 挂载和适用性矩阵。

### 7.2 预期文件

- `docs/standards/requirements-analysis-design-contract.md`（新，跨模块契约）
- `docs/standards/module-applicability-matrix.md`（或并入 contract）
- 可能新增 `schemas/p1-003/contract.schema.json`（仅在确有必要时）
- `tests/unit/p1-003/validate_contract.py`
- `docs/reports/2026-11-20-P1-003-R4-report.md`

### 7.3 交付物

1. 三模块输入/输出/证据/版本契约表。
2. Artifact 链：requirements → analysis → design → plan；source/version/sha256。
3. 需求变更失效规则：新 requirements version 使 Analysis/Design/plan 及 G1/G2/G3 失效。
4. G1/G2/G3 挂载与 Artifact hash 绑定；若 D2 需要 ADR，先 Proposed ADR-009。
5. G3 plan 生产者（D1）定案；P1-002 示例缺口处理建议（不自行修改 P1-002）。
6. 适用性矩阵：simple/consultation/bug-fix/feature/refactor/new-project/testing/documentation。
7. Evidence 映射：需求确认、代码/文档依据、设计决策、G2/Builder Check。
8. 不新增模块独立状态机（除非证明必要）。

### 7.4 测试策略

- 契约 Schema 正向/负向。
- 版本/hash 链、source 引用、superseded/失效测试。
- G1/G2/G3 GateDecision subject_hash 测试。
- 需求变更后 Analysis/Design 旧版本失效测试。
- 适用性矩阵正/负向（简单任务不被强制全流程）。
- P1-001/P1-002 全量回归。

### 7.5 验收条件

- 三模块契约闭环；
- 需求变更可追踪并失效下游；
- G1/G2/G3 责任明确；
- 简单任务适用性明确；
- 未修改 P0/P1-001/P1-002 已验收规则；如需修改，先 ADR/变更提案。

---

## 八、R5：Schema、示例与校验器完善

### 8.1 目标

补齐三模块和跨模块契约的 Schema、正负向示例、自动化校验器与全量回归。

### 8.2 预期文件

- 三模块 `schemas/*.json`（R1–R3 已创建，R5 完善）
- `examples/p1-003/` 或各 Skill `examples/`（按现有组织）
- `tests/unit/p1-003/validate_p1_003.py`
- `docs/reports/2026-11-20-P1-003-R5-report.md`

### 8.3 交付物

- Schema 正向/负向用例；
- 三模块正常/异常/未知项/安全/版本用例；
- 跨模块版本/失效/Gate 绑定用例；
- 全仓 JSON/YAML、链接、围栏、P1-001/P1-002 回归；
- 测试输出保持 `runtime_behavior=NOT_EXECUTED`。

---

## 九、R6：集成审查与 PR 准备

### 9.1 目标

完成最终集成、独立审查准备和 PR 创建；不合并。

### 9.2 交付物

- 最终报告（分支、基线、提交、文件、测试、PR、CI、Runtime 限制、风险）；
- OpenClaw 只读交叉审查；
- PR（Base main，Head P1-003 分支），不合并；
- 等待 ChatGPT 复审。

---

## 十、测试策略

| 层级 | 内容 | 是否运行时 |
|------|------|------------|
| Schema | 三模块输入/输出、契约、Artifact ref、状态 data | 否 |
| 正向 | 正常需求/分析/设计、完整链路、简单任务裁剪 | 否 |
| 负向 | 缺必填、未知字段、非法状态、错误 artifact ref、伪造确认、需求变更未失效、G1/G2/G3 绑定缺失 | 否 |
| 跨模块 | 版本/hash/source 链、superseded、失效、适用性矩阵 | 否 |
| 回归 | P1-001 参考 Skill 校验器、P1-002 Orchestration 校验器、链接、JSON/YAML、重复键 | 否 |
| Runtime | 不执行；`runtime_behavior=NOT_EXECUTED` | **否** |

不得把静态 Schema/测试描述为运行时验证。

---

## 十一、风险与缓解

| 风险 | 缓解 |
|------|------|
| 过度设计三模块，强迫所有任务全流程 | 适用性矩阵；简单/咨询/Bug 修复可裁剪 |
| 重复 P1-001 通用规范 | 只写模块特有职责/字段，引用通用标准 |
| Requirements Schema 变更破坏现有参考 Skill | 版本升级、保留旧示例/兼容测试、更新 CHANGELOG |
| G3 plan 归属不明 | R1 前 D1 决策；R3/R4 不得自行定案 |
| G1-G3 绑定被误解为修改 ADR-006 | 若属门禁规则变更，先 Proposed ADR-009 |
| Schema 过度膨胀 | 最小必填 + 明确扩展点；R5 校准 |
| 把设计审查与代码审查混淆 | G2/Builder Check vs G4 明确分离 |
| 平台/运行时能力被误标 | 保持 Documented/Assumed/Unknown；Runtime NOT_EXECUTED |
| P1-002 示例 plan 缺口被忽略 | R4 明确处理；不自行改 P1-002，提出变更建议 |

---

## 十二、是否需要新增 ADR

**R0 结论：暂不新增 ADR。**

- Requirements/Analysis/Design 的模块标准属于 P1-003 细化，可在现有 P1-001/P1-002 框架内完成。
- 如果 ChatGPT 认定以下事项改变已验收门禁语义，则先提交 **ADR-009 Proposed**：
  1. G1/G2/G3 必须绑定 Artifact hash；
  2. Design 输出 implementation plan 或新增独立 Planning 步骤；
  3. 任何需要修改 ADR-006 或 ADR-005 权威模型的变更。
- 未获审查前不得直接修改 ADR 或 P1-002 标准。

---

## 十三、阶段验收条件

| 阶段 | 验收条件 |
|------|----------|
| R1 | Requirements 标准/Schema/参考 Skill/测试通过；G1 边界明确；简单任务可裁剪 |
| R2 | Analysis 标准/Schema/参考 Skill/测试通过；不输出最终设计 |
| R3 | Design 标准/Schema/参考 Skill/测试通过；G2/G4 边界明确 |
| R4 | 三模块契约/版本/失效/G1-G3 集成通过；D1/D2/D6 已裁定 |
| R5 | 全量 Schema/用例/回归通过；无 Runtime 声明 |
| R6 | 报告完整、OpenClaw 只读审查、PR 创建未合并 |

---

## 十四、下一阶段建议

1. ChatGPT 先裁定 D1（G3 plan 生产者）、D2（G1-G3 Artifact 绑定）、D6（是否 ADR-009）。
2. 批准后从 **R1 Requirements** 开始；R1/R2 可按依赖顺序推进，R3 需 D1/D4。
3. R4 前不修改 P0 ADR、P1-001/P1-002 已验收规则。
4. 任何阶段发现需要改变权威模型，立即停止并提交 Proposed 决策，不得自行覆盖。

**P1-003-R0 COMPLETE；P1-003-R1 NOT STARTED。**
