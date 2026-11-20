# ADR-005：任务上下文与产物管理

**状态：** 已采纳  
**日期：** 2026-11-20

## 背景

多个 Skill 协作完成一个任务时，需要统一的方式传递上下文和共享产物。

## 问题

如何解决：
- 每个 Skill 重复理解需求？
- 产物散落各处难以追踪？
- 上下文丢失导致后续步骤出错？

## 候选方案

### 方案 A：全局变量

使用全局变量存储上下文。

**优点：** 访问简单  
**缺点：** 状态混乱，难以追踪，并发不安全

### 方案 B：文件系统统一存储（选定）

通过 `artifacts/` 目录统一管理所有产物和上下文。

**优点：**
- 持久化，可追溯
- 独立于执行环境
- 易于版本控制
- 支持并行访问

**缺点：**
- 需要约定目录结构
- 大文件可能影响性能

### 方案 C：内存对象传递

通过函数参数传递上下文对象。

**优点：** 类型安全  
**缺点：** 跨 Skill 传递复杂，持久化困难

## 决策

采用**方案 B：文件系统统一存储**。

核心设计：
```
artifacts/
└── task-{uuid}/
    ├── metadata.json         # 任务元信息
    ├── requirements.md       # 需求文档（来自 requirements-clarity）
    ├── analysis.md           # 分析报告（来自 analysis）
    ├── design.md             # 设计文档（来自 design）
    ├── implementation-plan.md  # 实施计划
    ├── code/                 # 源代码（来自 coding）
    ├── code-review.md        # 审查报告（来自 code-review）
    ├── test-report.md        # 测试报告（来自 testing）
    ├── deployment-report.md  # 部署报告（来自 deployment）
    └── logs/                 # 执行日志
```

## 上下文契约

每个 Skill 定义：
1. **Input Contract** — 需要什么输入文件
2. **Output Contract** — 产生什么输出文件
3. **Prerequisite** — 前置条件（哪些文件必须存在）

示例（requirements-clarity Skill）：
```yaml
# input
prerequisites:
  - 用户已提供需求描述

# output
artifacts:
  - path: artifacts/{task-id}/requirements.md
    format: markdown
    required_fields: [goal, scope, constraints, acceptance_criteria]
```

## 理由

1. **可追溯性** — 每个产物的创建时间、来源可查
2. **独立性** — Skill 间通过文件解耦
3. **调试友好** — 可检查中间产物定位问题
4. **复用性** — 相同输入产生相同输出

## 注意事项

1. **原子写入** — 使用临时文件 + 重命名避免部分写入
2. **冲突检测** — 相同 task-id 下的产物覆盖需明确策略
3. **清理策略** — 已完成任务的产物保留期限

## 后续影响

- P2 阶段实现 ArtifactManager
- 需定义 metadata.json 的 Schema
- 各 Skill 需遵守契约
