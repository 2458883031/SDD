# ADR-003：Orchestration 调度策略

**状态：** 已采纳  
**日期：** 2026-11-20

## 背景

多 Skill 协同工作时，需要统一的调度机制来管理执行顺序、依赖关系和质量门禁。

## 问题

如何设计编排策略，使：
- 不同任务类型自动选择合适的工作流
- 复杂任务能拆分并行执行
- 关键节点有人工审批
- 错误能被正确处理

## 候选方案

### 方案 A：硬编码流程

在 orchestration Skill 中硬编码所有流程。

**优点：** 简单直接  
**缺点：** 无法适应新任务类型，扩展性差

### 方案 B：声明式工作流（选定）

使用 YAML 定义工作流，编排引擎解析并执行。

**优点：**
- 灵活可扩展
- 易于理解和维护
- 支持条件分支
- 可与版本控制集成

**缺点：**
- 需要定义 Schema
- 运行时解析有开销

### 方案 C：AI 动态编排

完全由 AI 决定执行顺序和流程。

**优点：** 最灵活  
**缺点：** 不可预测，难以调试，质量风险高

## 决策

采用**方案 B：声明式工作流**。

核心设计：
1. 预定义工作流模板（`workflows/*.yaml`）
2. 任务识别器选择匹配的工作流
3. 编排引擎按定义执行
4. HARD-GATE 作为人工干预点

## 理由

1. **可预测性** — 声明式流程行为可预期
2. **可测试性** — 工作流可独立测试
3. **可审计性** — YAML 文件可作为审计追踪
4. **灵活性** — 新增任务类型只需添加新工作流定义

## 关键设计

### 编排引擎与 orchestration Skill

| 对象 | 位置 | 职责 |
|------|------|------|
| Orchestration Engine | `core/orchestration/`（P2 规划） | 任务识别、拆解、路由、DAG 执行、状态、结果汇总 |
| orchestration Skill | `skills/development/orchestration/` | 可选入口：辅助 Agent 识别任务、选择 Workflow |

- 编排引擎不是 Skill；`SKILL.md` 不是引擎。
- orchestration Skill 可以调用引擎公开接口，但不得把全部编排逻辑写进一个 Skill。
- 引擎不依赖任何平台专属能力；平台差异由 L6 适配。

### 任务分类与路由

| 任务类型 | 复杂度 | 推荐工作流 | 必需门禁 |
|----------|--------|-----------|----------|
| simple_change | L1 | simple-task | G4（简化，独立 Review 不跳过）、G5（简化）；安全约束不跳过 |
| bug_fix | L2 | bug-fix | G4、G5 |
| feature_dev | L2/L3 | feature-development | G1、G2、G3、G4、G5（生产部署时 G6） |
| refactoring | L3 | refactoring | G1、G2、G3、G4、G5（生产部署时 G6） |
| new_project | L3 | new-project | G1、G2、G3、G4、G5；G6 仅计划生产部署 |
| deployment | L2 | deployment | 涉及代码/配置时 G4、G5；生产部署时 G6；非生产部署不触发 G6 |
| consultation | L1/L2 | consultation | 无代码门禁；输出分析/设计产物 |

> 门禁规则以 [ADR-006](./ADR-006-quality-gates.md) 为准；本表只表示任务类型到 Workflow 的映射，不重新定义门禁规则。

### Workflow DAG 依赖

```text
                 ┌── code-review (G4) ──┐
coding ──────────┤                      ├── quality gate (G4 AND G5) ── deployment (G6) ── verification
                 └── testing (G5) ──────┘
```

- Code Review 与 Testing 可以并行，但**不能互相替代**。
- 两者都必须通过 G4/G5，才允许进入 Deployment。
- Review 严重问题回到 coding；Testing 失败按缺陷类型回到 coding/analysis/requirements。
- Deployment 必须依赖质量门禁，不得绕过。

Workflow 节点字段、失败路径、重试、超时和审批暂停/恢复语义见 [orchestration-architecture.md](../architecture/orchestration-architecture.md)。本 ADR 只确定调度策略与依赖原则。

### HARD-GATE 设计

- G1–G6 的触发条件、自动检查、人工审批、跳过规则、失败回退和审计要求的**唯一权威定义见 [ADR-006](./ADR-006-quality-gates.md)**。
- 本 ADR 只规定门禁在 Workflow 中的挂载位置。
- AI 不能把用户未批准的操作当作已批准；超时、沉默不等于批准。

## 后续影响

- P2 阶段实现编排引擎
- 需定义工作流 Schema（core/schemas/workflow.schema.json）
- 需实现验证工具（tools/workflow-validator/）

## 修订记录

- **2026-11-20（P0-002）**：明确编排引擎与 orchestration Skill 的边界；将 Review/Testing 定义为并行且共同满足质量门禁；Deployment 必须依赖 G4/G5；门禁规则统一引用 ADR-006；Workflow DAG 语义独立定义。
- **2026-11-20（P0-003）**：简单修改 Workflow 增加独立 Code Review；G4 与 G5 并行且共同构成质量门禁；G6 在生产部署动作之前检查。
- **2026-11-20（P0-Final）**：任务表 G6 范围与 ADR-006 对齐；新项目仅计划生产部署时触发 G6，非生产部署不触发 G6；补注门禁规则以 ADR-006 为准。
