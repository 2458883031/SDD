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

### 任务分类与路由

| 任务类型 | 复杂度 | 推荐工作流 | 强制门禁 |
|----------|--------|-----------|----------|
| simple_change | L1 | coding → testing | 无 |
| bug_fix | L2 | analysis → coding → testing → review | G4 |
| feature_dev | L2/L3 | req → analysis → design → coding → test | G1, G2, G4, G5 |
| refactoring | L3 | analysis → design → coding → review → test | G2, G4, G5 |
| new_project | L3 | req → analysis → design → coding → test → deploy | G1, G2, G4, G5, G6 |
| deployment | L2 | analysis → deployment | G6 |

### HARD-GATE 设计

借鉴 Superpowers 的 HARD-GATE 机制：
- 门禁前必须暂停等待人工确认
- AI 不能假设用户已同意
- 每个门禁有明确的检查清单

## 后续影响

- P2 阶段实现编排引擎
- 需定义工作流 Schema（core/schemas/workflow.schema.json）
- 需实现验证工具（tools/workflow-validator/）
