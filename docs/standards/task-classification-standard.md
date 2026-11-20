# SDD 任务分类与复杂度标准

**状态：** P1-002 Draft（待 ChatGPT 评审）
**适用范围：** 用户请求进入 Orchestration 后的任务类型识别、复杂度判断、风险升级和信息澄清
**权威关系：** Orchestration 职责见 [orchestration-standard.md](./orchestration-standard.md)；Workflow 定义见 [workflow-standard.md](./workflow-standard.md)；G1–G6 见 [ADR-006](../decisions/ADR-006-quality-gates.md)。

---

## 1. 目标

任务分类是 Orchestration 的第一道决策，回答：

1. 这是哪类研发任务？
2. 需要多复杂的流程？
3. 风险是否要求升级？
4. 信息是否足够开始？
5. 用户要求简化时，哪些不能简化？

**分类不是执行。** 分类结果必须写入 Task Context / 分类证据，供 Workflow 选择和审计。

---

## 2. 任务类型

### 2.1 规范任务类型

| 任务类型 ID | 名称 | 典型输入 | 默认 Workflow | 最低质量要求 |
|-------------|------|----------|---------------|--------------|
| `technical_consultation` | 技术咨询 | 问题、方案比较、代码片段 | `consultation` | 结论有依据；不虚构运行结果 |
| `simple_change` | 简单代码修改 | 明确的局部修改 | `simple-task` | G4（独立 Review，不跳过）、G5（简化） |
| `bug_fix` | Bug 修复 | 故障现象、日志、复现步骤 | `bug-fix` | G4、G5 |
| `feature_development` | 功能开发 | 新功能需求 | `feature-development` | G1、G2、G3、G4、G5；生产部署时 G6 |
| `system_refactoring` | 系统重构 | 重构目标、现状约束 | `refactoring` | G1、G2、G3、G4、G5；生产部署时 G6 |
| `new_project` | 新项目开发 | 从零构建的业务/系统需求 | `new-project` | G1、G2、G3、G4、G5；仅计划生产部署时 G6 |
| `testing_task` | 测试任务 | 测试目标、范围、已有实现 | `testing` | G5；修改测试代码时 G4；生产发布前按 G5 |
| `deployment_task` | 部署任务 | 部署目标、环境、产物 | `deployment` | 代码/配置变更时 G4/G5；生产部署 G6 + R3 + SA |
| `documentation_task` | 文档任务 | 需要编写/修订的文档 | `documentation` | 文档一致性检查；涉及代码示例/代码变更时 G4/G5 |

### 2.2 类型选择规则

1. 一次请求只选择一个**主任务类型**；可附加子任务类型（如 feature + documentation）。
2. 同时包含代码与部署时，主类型为 `deployment_task`，但必须保留代码变更的 G4/G5。
3. 同时包含 Bug 修复与功能开发时，若无法拆分，按更高风险的 `feature_development` 或 `system_refactoring` 处理。
4. 仅分析、不修改代码的请求归 `technical_consultation`；需要产出可执行测试时归 `testing_task`。
5. 分类不确定时，选择更保守的类型，并记录备选类型与原因。

---

## 3. 分类输入

分类器至少读取：

- 用户原始请求；
- 项目上下文摘要；
- 已声明的约束（时间、技术栈、环境、合规）；
- 已有 Artifact 引用；
- 目标环境（dev/test/staging/prod）；
- 是否涉及代码、数据、认证/授权、外部依赖、生产部署；
- 用户是否明确要求简化流程或跳过阶段。

不得仅凭关键词分类；必须结合上下文和风险信号。

---

## 4. 复杂度等级

### 4.1 L1 / L2 / L3

| 等级 | 定义 | 典型特征 |
|------|------|----------|
| **L1 简单** | 影响局限、风险低、依赖少、方案明确 | 单文件/单模块；无数据模型/接口/安全变化；无新依赖；可快速验证 |
| **L2 中等** | 跨多个模块或存在已知依赖，需要设计与协调 | 多模块；有接口/数据变化；存在依赖链；需要测试计划；风险可控 |
| **L3 复杂** | 系统级影响、高不确定性或高风险 | 跨系统/跨团队；架构变更；生产数据/安全影响；新项目；技术方案需探索 |

### 4.2 判断因素

| 因素 | 低 | 中 | 高 |
|------|----|----|----|
| 影响范围 | 单文件/单模块 | 多模块 | 系统/跨系统 |
| 技术风险 | 成熟方案 | 已知但有不确定性 | 未验证/高风险 |
| 依赖数量 | 0–1 | 2–4 | 5+ 或复杂依赖链 |
| 不确定性 | 需求/方案明确 | 部分未知 | 需探索/研究 |
| 跨模块程度 | 无 | 有限 | 广泛 |
| 数据与安全影响 | 无 | 有限/可控 | 认证、授权、加密、生产数据 |
| 生产环境 | 不涉及 | 非生产部署 | 生产部署/生产数据 |

### 4.3 判定规则

1. **不得按代码行数判定复杂度。** 行数只能作为辅助信号，不能单独决定等级。
2. 任意两个“高”因素 → 至少 L3。
3. 涉及生产数据破坏性操作、认证/授权/加密变更、生产部署 → 至少 L3，并触发相应 G/SA 评估。
4. 需求、技术方案或依赖存在关键未知 → 至少 L2；若未知涉及安全/生产/数据 → L3。
5. 只涉及文档且无代码/配置变化 → 默认 L1，但仍需文档一致性检查。
6. 无法判断 → 采用 L3（保守），并请求人工确认；不得默认 L1。

---

## 5. 风险等级

风险等级用于选择审批和证据强度，不等同于 R0–R4 权限等级。

| 风险等级 | 含义 | 典型处理 |
|----------|------|----------|
| `low` | 局部、可逆、无敏感数据 | 简化流程；仍保留必要的 G4/G5 |
| `medium` | 多模块、可回滚、有限外部依赖 | 标准流程；关键节点审批 |
| `high` | 安全/数据/生产相关，或不可逆风险较高 | 更严格流程；G2/G4/G6/SA 按规则 |
| `critical` | 生产破坏性、敏感凭证、不可逆高危 | 必须人工决策；R4 + SA；适用时 G6 |

**规则：**

- 风险等级不得低于权限等级所暗示的风险；R4 操作至少 `critical`。
- 风险等级提升时，必须重新评估 Workflow 和 Gate；不得沿用低风险审批。
- 风险等级降低需要新证据和人工确认，不得由 Agent 自行降级。

---

## 6. 分类输出

分类结果至少包含：

```yaml
task_type: feature_development
complexity: L2
risk_level: medium
confidence: 0.82
workflow_candidate: feature-development
required_gates: [G1, G2, G3, G4, G5]
clarification_questions: []
classification_evidence:
  - signal: "multiple modules"
    value: "api + ui"
  - signal: "no production deployment"
    value: true
unknowns: []
```

- `confidence` 低（建议 < 0.6）时不得自动进入高影响 Workflow；先澄清或人工确认。
- `required_gates` 是候选，最终以 ADR-006 和实际变更内容为准。
- 分类证据必须可追溯到请求片段或上下文引用，不得只写结论。

---

## 7. 信息不足与澄清

### 7.1 必须澄清的情况

- 目标或验收标准缺失；
- 影响范围无法确定；
- 是否涉及生产环境/生产数据不明确；
- 是否存在安全/合规/权限约束不明确；
- 用户要求的“简化”与强制门禁冲突；
- 任务类型存在两个以上合理解释且流程差异显著。

### 7.2 澄清策略

1. 返回 `needs_input`，列出最少必要问题（建议 ≤5 个）。
2. 优先询问会影响任务类型、复杂度、风险或门禁的问题。
3. 不猜测缺失信息；不伪造验收标准。
4. 可以在信息不足时先进入 `consultation` 做范围澄清，但不得进入编码或部署。
5. 用户拒绝提供关键信息时，按最高合理风险处理或阻止执行，并记录原因。

---

## 8. 用户要求简化流程

用户可以用显式指令简化流程，但边界如下：

**允许简化：**

- 跳过 G1/G2/G3 中不适用的阶段（需记录理由）；
- 将 L2 流程压缩为简化流程；
- 减少非关键文档和报告；
- 合并独立的小任务。

**不允许简化：**

- 任何代码变更的 G4（独立 Review）；
- 任何代码变更的 G5（测试）；
- 生产部署的 G6 + R3 + SA；
- 生产数据库破坏性操作的 R4 + SA；
- 敏感凭证读取的 R4 + SA；
- 安全审查、权限检查、路径限制、审计和脱敏；
- 独立审查原则（作者自审不能替代独立 Review）。

用户要求简化时，必须：

1. 说明哪些阶段被简化、哪些不能简化；
2. 将用户指令和简化理由写入 Task Context / 证据；
3. 在 Workflow 结果中标注简化范围；
4. 不得把“用户同意简化”当作绕过安全控制的授权。

---

## 9. 高风险升级

以下情况必须升级：

| 触发 | 升级动作 |
|------|----------|
| 生产部署 | L3；G6 + R3 + SA；生产部署前人工授权 |
| 生产数据库破坏性操作 | L3；R4 + SA；涉及生产部署时再加 G6 |
| 认证/授权/加密变更 | 至少 L2；G2/G4 + 显式安全审查；适用 SA |
| 敏感凭证读取 | L3；R4 + SA；禁止凭证进入日志/上下文 |
| 新增外部依赖/外部 API | 至少 L2；安全/依赖审查；必要时 G2 |
| 跨系统/跨团队 | L3；G3；多 Agent 并行需独立性审查 |
| 复杂度或风险无法判断 | L3 + 人工确认 |
| 分类置信度低且影响高 | 人工确认后再选择 Workflow |

升级不得只改标签；必须同步调整 Workflow、Gate、审批和证据要求。

---

## 10. 重新分类

1. 新信息出现时，TaskIdentifier/ComplexityEvaluator 必须重新评估。
2. 复杂度或风险上升：停止受影响 Task，重新规划；已通过的 Gate 如 subject hash 变化则失效。
3. 复杂度或风险下降：只有在新证据充分且经授权确认后才能降级；不得由 Agent 自行降级。
4. 任务类型变化：创建新的 Workflow Run 或明确的分支；不得在同一 Run 中静默改变语义。
5. 重新分类必须记录旧值、新值、原因、证据和影响。

---

## 11. 分类与门禁的关系

- 任务分类只提出候选 Gate；G1–G6 的最终规则以 ADR-006 为准。
- 分类不得因为“任务简单”而跳过 G4/G5 或安全控制。
- 分类不得把 G6 加到非生产部署上，也不得因生产相关就自动触发 G6。
- 分类不得把 R4 等同于 G6，或把 SA 等同于权限检查。

---

## 12. 实现状态

| 能力 | 状态 |
|------|------|
| TaskIdentifier | 未实现（P2） |
| ComplexityEvaluator | 未实现（P2） |
| 分类 Schema | 本轮提供 Task Schema 的 `task_type` / `complexity` 枚举，不是 Runtime |
| 自动澄清 | 未实现；依赖 Agent/Skill 交互 |

**`runtime_behavior = NOT_EXECUTED`。**

---

## 13. 相关标准

- [orchestration-standard.md](./orchestration-standard.md)
- [workflow-standard.md](./workflow-standard.md)
- [task-standard.md](./task-standard.md)
- [gate-orchestration-standard.md](./gate-orchestration-standard.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)
- [security-architecture.md](../architecture/security-architecture.md)

---

**P1-002 状态：** Draft，待 ChatGPT 评审。未实现分类器或复杂度评估器。
