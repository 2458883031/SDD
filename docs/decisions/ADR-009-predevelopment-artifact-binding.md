# ADR-009：前置研发 Artifact 的 Gate 绑定（Proposed）

**状态：** Proposed（P1-003-R1 提案，待 ChatGPT 审查；**不是 Accepted，未生效**）
**日期：** 2026-11-20
**决策范围：** G1/G2/G3 的 Artifact subject binding、上游变更失效、Planning 与 Design 边界

---

## 1. 背景

P1-001 已定义 Skill 统一 IO 契约，P1-002 已定义 Orchestration/Gate/Approval/Evidence，ADR-006 已定义 G1–G6。现有规则中：

- G4/G5 明确要求同一 code commit 或产物 hash；新版本使旧结果失效（ADR-006 §10.1）。
- G1/G2/G3 定义了触发、自动检查、人工审批和回退，但没有明确要求 GateDecision 绑定 requirements/analysis/design/plan artifact 的 version + sha256。

P1-003-R1 的 Requirements 标准需要一个可追溯的 G1 Artifact 绑定；ChatGPT 已给出方向：

- D1：Design 输出设计规格，不负责正式 implementation-plan；Planning 由 Orchestration 内部活动产生；G3 检查并批准 plan。
- D2：G1 绑定 Requirements Artifact；G2 绑定 Design Artifact；G3 绑定 Plan Artifact；上游变化使下游产物/门禁失效。

由于 D2 属于 ADR-006 门禁规则的扩展，必须先以 **Proposed ADR** 记录，不能直接修改 ADR-006。

---

## 2. 问题

如何在不改变 G1–G6 既有触发条件、人工审批条件和安全权限模型的前提下，使前置研发门禁能够证明“批准的是哪一个准确产物”，并在上游产物变化时失效下游结果？

需要回答：

1. G1/G2/G3 分别绑定什么 Artifact 类型？
2. GateDecision 如何记录 version/hash？
3. 上游 Artifact 变化后哪些下游产物和 Gate 失效？
4. GateDecision 与 Approval 如何关联？
5. 与 G4/G5 的代码版本绑定有何区别？
6. Planning 活动属于谁，Design 是否输出 implementation-plan？

---

## 3. 决策

### 3.1 G1/G2/G3 Artifact subject binding

| Gate | 绑定的 Artifact | 类型 | 版本/hash |
|------|------------------|------|-----------|
| G1 | Requirements Artifact | `requirements` | `version` + `sha256` |
| G2 | Design Artifact | `design` | `version` + `sha256` |
| G3 | Plan Artifact | `plan` | `version` + `sha256` |

- GateDecision 使用：
  - `subject_type=artifact`；
  - `subject_hash=<artifact sha256>`；
  - 记录 artifact `path`、`version`、`type`；
  - 通过/失败/阻塞均绑定同一 subject。
- GateDecision 不得只写“设计已确认”而不记录具体 Artifact。
- 具体 Schema 字段由后续 P1-003 标准和 GateDecision 扩展定义；本 ADR 不修改现有 Schema。

### 3.2 Approval 关联

- G1/G2/G3 需要人工审批时，Approval 必须绑定同一 Artifact `path/version/sha256` 和 task/workflow/node。
- Approval 通过后，GateDecision 记录 `approval_ref`；Approval 不得跨 Artifact 版本复用。
- 超时/拒绝/失效/已消费的 Approval 不得产生 PASSED GateDecision。
- 用户确认（尤其 G1）由 GateDecision/Approval 记录，不由 Requirements Skill 的 `status=ok` 表示。

### 3.3 上游变更与下游失效

| 上游变化 | 必须失效/重跑 |
|----------|----------------|
| Requirements 新版本（新 path/version/sha256） | G1 重新评估；Analysis/Design/Plan 旧产物标记 superseded；G2/G3 旧 decision 失效 |
| Analysis 新版本 | Design/Plan 旧产物 superseded；G2/G3 旧 decision 失效 |
| Design 新版本 | Plan 旧产物 superseded；G3 旧 decision 失效 |
| Plan 新版本 | G3 重新评估 |
| 仅文档/注释变化且 Artifact hash 不变 | 不自动失效 |
| Artifact hash 变化 | 依赖该 Artifact 的下游 Gate 失效 |

- 失效以 Artifact hash 为准确依据，不以时间或“最新版本”推断。
- 具体失效事件、重跑策略和 Orchestrator 实现在后续 Runtime 阶段实现；本 ADR 只定义规则。
- 旧 GateDecision 保留审计历史，不得改写；新增 decision 记录新一轮结果。

### 3.4 Planning 与 Design 边界

- Design Skill 输出设计规格（architecture/modules/interfaces/data/state/errors/security/performance/test strategy/tradeoffs/decisions）。
- Design **不输出正式 implementation-plan**。
- Planning 是 Orchestration 内部活动，不属于独立研发专业 Skill；它根据 Design/Requirements/Analysis 生成 plan artifact。
- G3 检查并批准该 plan artifact。
- 正式链路：`Requirements → G1 → Analysis → Design → G2 → Planning → G3 → Coding`。
- 不改变 G1/G2/G3 既有触发条件、人工审批条件或失败回退；本 ADR 只补充 Artifact subject binding 和 Planning 归属。

### 3.5 与 G4/G5 的区别

| 门禁 | 绑定对象 | 绑定粒度 | 版本变化 |
|------|----------|----------|----------|
| G1 | Requirements Artifact | artifact version+sha256 | 新需求版本使 G1/G2/G3 失效 |
| G2 | Design Artifact | artifact version+sha256 | 新设计版本使 G2/G3 失效 |
| G3 | Plan Artifact | artifact version+sha256 | 新计划版本使 G3 失效 |
| G4 | code commit/产物 hash | commit/artifact hash | 新代码版本使 G4 失效 |
| G5 | code commit/产物 hash | commit/artifact hash | 新代码版本使 G5 失效 |

- G4/G5 规则保持不变。
- G1/G2/G3 的 Artifact binding 不替代 G4/G5 的代码版本绑定。
- 质量门禁仍要求同一版本的 G4 AND G5；本 ADR 不改变该规则。

### 3.6 不改变的内容

本 ADR **不改变**：

- G1–G6 的触发条件；
- G1–G6 的人工审批条件；
- G6 仅实际生产部署触发；
- R0–R4、SA、G6 的职责分离；
- G4/G5 同一 commit/hash 绑定；
- Builder Check 独立性；
- 现有安全权限模型。

---

## 4. 理由

1. **可追溯**：GateDecision 能证明批准的是哪个具体 Artifact 版本。
2. **可失效**：上游产物变化时下游结果不会继续被误用。
3. **职责清晰**：Planning 归 Orchestration，Design 不越权输出正式 plan。
4. **兼容**：只扩展 G1/G2/G3 的 Artifact binding，不改变既有门禁触发/审批语义。
5. **可审计**：旧 decision 保留，新增 decision 记录新版本。

---

## 5. 兼容性与测试影响

### 5.1 兼容性

- 现有 P1-002 `GateDecision` Schema 已有 `subject_type`/`subject_hash` 字段；本 ADR 不要求立即修改现有 Schema。
- 现有 P1-002 G1/G2/G3 示例未强制 Artifact binding；在 ChatGPT 接受本 ADR 前，不改变既有示例语义。
- Requirements Skill 0.2.0 只输出 Artifact 引用和 `change_impact`；不实现自动失效 Runtime。
- 若后续正式实施需要修改 P1-002 标准/Schema，必须另行变更并接受审查。

### 5.2 测试影响

后续 P1-003 测试至少覆盖：

- G1/G2/G3 GateDecision 绑定 artifact version+sha256；
- Artifact 新版本使下游 Gate decision 失效；
- 旧 decision 不被改写；
- Approval 绑定同一 Artifact；
- G4/G5 原有绑定不回归；
- 纯操作审批不误用 Artifact binding；
- Runtime 未执行时不得声称自动失效已生效。

---

## 6. 后果

### 6.1 正面

- 前置研发门禁可审计、可失效、可追溯；
- Requirements/Analysis/Design/Planning 的版本链清晰；
- G3 的 plan 来源明确。

### 6.2 成本/风险

- Orchestrator 需要维护 Artifact 依赖图和失效事件（后续 Runtime）；
- 需要额外测试 Artifact hash/version 失效；
- 现有 G1/G2/G3 示例需要后续更新（本 ADR 不直接修改）；
- 若实现不当，可能出现“旧 decision 被继续使用”的风险。

---

## 7. 尚未实现

- Artifact 依赖图持久化；
- GateDecision 自动失效 Runtime；
- G1/G2/G3 自动 hash binding Runtime；
- Planning Runtime；
- Orchestrator 重跑策略；
- 任何平台适配实现。

`runtime_behavior = NOT_EXECUTED`。

---

## 8. 状态与生效

- 本 ADR 当前为 **Proposed**，不是 Accepted。
- 在 ChatGPT 明确接受前，本 ADR **不改变** ADR-006 或现有 G1–G6 的权威规则。
- 正式实施前必须再次审查 Schema/标准/测试变更。

---

## 9. 相关文档

- [ADR-005 任务上下文与产物管理](./ADR-005-task-context.md)
- [ADR-006 质量门禁与人工审批](./ADR-006-quality-gates.md)
- [requirements-standard.md](../standards/requirements-standard.md)
- [gate-orchestration-standard.md](../standards/gate-orchestration-standard.md)
- [approval-orchestration-standard.md](../standards/approval-orchestration-standard.md)
- [execution-evidence-standard.md](../standards/execution-evidence-standard.md)

---

**ADR-009 状态：** Proposed / NOT ACCEPTED。未生效。
