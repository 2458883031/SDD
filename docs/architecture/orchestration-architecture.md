# 编排引擎架构设计

## 概述

编排引擎是整个 SDD 体系的核心，负责任务识别、Skill 路由、流程控制和门禁管理。

## 核心组件

### 1. 任务识别器 (TaskIdentifier)

**职责：** 分析用户需求，确定任务类型和复杂度。

```yaml
# 任务类型分类
task_types:
  simple_change:
    description: "简单修改，如修改按钮样式"
    example_skills: [coding, testing]
    
  bug_fix:
    description: "Bug 修复，如修复接口异常"
    example_skills: [analysis, coding, testing, code-review]
    
  feature_development:
    description: "功能开发，如增加用户管理模块"
    example_skills: [requirements, analysis, design, coding, testing]
    
  system_refactoring:
    description: "系统重构，如重构整个前端架构"
    example_skills: [analysis, design, coding, code-review, testing]
    
  new_project:
    description: "从零开发业务系统"
    example_skills: [requirements, analysis, design, coding, testing, deployment]
    
  deployment_task:
    description: "部署任务，如 Docker 部署"
    example_skills: [analysis, deployment]
    
  technical_consultation:
    description: "技术咨询，如评估技术方案"
    example_skills: [analysis, design]

# 复杂度评估
complexity_levels:
  L1_simple:
    criteria:
      - 影响范围：单文件或单一模块
      - 风险：低
      - 依赖：无或单一依赖
      - 技术不确定性：无
    workflow: [coding, testing]
    
  L2_medium:
    criteria:
      - 影响范围：多个模块
      - 风险：中
      - 依赖：存在依赖关系
      - 技术不确定性：部分已知
    workflow: [analysis, coding, testing, code-review]
    
  L3_complex:
    criteria:
      - 影响范围：整个系统
      - 风险：高
      - 依赖：复杂依赖链
      - 技术不确定性：需要探索
    workflow: [requirements, analysis, design, coding, code-review, testing, deployment]
```

### 2. Skill 路由器 (SkillRouter)

**职责：** 根据任务类型和复杂度，选择需要调用的 Skill。

```yaml
# 路由规则示例
routing_rules:
  - name: "feature-development-L3"
    conditions:
      task_type: feature_development
      complexity: L3_complex
    skills:
      - name: requirements-clarity
        mode: sequential
      - name: analysis
        mode: sequential
      - name: design
        mode: sequential
        gate: G2
      - name: coding
        mode: parallel
        subagents: true
      - name: code-review
        mode: sequential
        gate: G4
      - name: testing
        mode: parallel
      - name: deployment
        mode: conditional
        condition: "user_confirms_production"
```

### 3. 门禁控制器 (GateController)

**职责：** 在关键节点执行人工审批。

#### HARD-GATE 设计

```yaml
gates:
  G1_requirements:
    name: "需求确认"
    stage: requirements-clarity
    check_items:
      - 需求边界清晰
      - 验收标准明确
      - 非目标已确认
    human_approval:
      required_for: [L2_medium, L3_complex]
      auto_skip_for: [L1_simple]
      
  G2_design:
    name: "设计确认"
    stage: design
    check_items:
      - 架构方案合理
      - 技术选型恰当
      - 安全风险已考虑
    human_approval:
      required_for: [L3_complex]
      builder_check: true
      
  G3_plan:
    name: "开发计划"
    stage: coding
    check_items:
      - 任务拆解完整
      - 依赖关系明确
      - 时间估算合理
    human_approval:
      required_for: [L3_complex]
      
  G4_code_review:
    name: "代码质量"
    stage: code-review
    check_items:
      - 无严重安全问题
      - 符合编码规范
      - 核心逻辑正确
    human_approval:
      required_for: [severe_issues]
      auto_pass: [minor_issues]
      
  G5_testing:
    name: "测试验收"
    stage: testing
    check_items:
      - 核心测试通过
      - 覆盖率达标
      - 边界case覆盖
    human_approval:
      required_for: [all]
      auto_fail: [core_tests_failed]
      
  G6_deployment:
    name: "部署授权"
    stage: deployment
    check_items:
      - 生产环境变更申请
      - 回滚方案准备
      - 监控配置确认
    human_approval:
      required_for: [production]
      audit_log: true
```

### 4. 产物管理器 (ArtifactManager)

**职责：** 统一管理任务上下文和输出产物。

```yaml
# 产物目录结构
artifacts:
  root: "artifacts/"
  structure:
    task-{id}/
      metadata.json      # 任务元信息
      requirements.md    # 需求文档
      analysis.md        # 分析报告
      design.md          # 设计文档
      implementation-plan.md  # 实施计划
      code/              # 源代码
      code-review.md     # 审查报告
      test-report.md     # 测试报告
      deployment-report.md  # 部署报告
      logs/              # 执行日志
```

## 工作流引擎

### 工作流定义格式

```yaml
# workflows/simple-task.yaml
name: simple-task
description: "简单任务工作流"
triggers:
  task_type: simple_change
  complexity: L1_simple
  
steps:
  - id: coding
    skill: coding
    timeout: 300
    retry: 2
    
  - id: testing
    skill: testing
    depends_on: [coding]
    timeout: 300
```

### 工作流执行状态

```yaml
workflow_states:
  pending: 等待执行
  running: 正在执行
  paused: 暂停（等待人工审批）
  completed: 已完成
  failed: 执行失败
  aborted: 已中止
  
step_states:
  queued: 已排队
  executing: 执行中
  succeeded: 成功
  failed: 失败
  skipped: 已跳过
  blocked: 被阻塞
```

## 子 Agent 协作

### 并行执行策略

```yaml
parallel_execution:
  max_concurrent: 5
  strategy: 
    - type: fork
      description: "拆分独立任务并行执行"
    - type: pipeline
      description: "流水线并行，上一步完成后立即启动下一步"
      
subagent_config:
  context_mode: isolated  # 或 fork
  model: default  # 可使用更便宜的模型
  timeout_seconds: 600
  announce: true  # 完成后通知父任务
```

### Builder Check 机制

借鉴 Superpowers 的设计审查思路：

```yaml
builder_check:
  trigger: [G2_design]
  role: independent-reviewer
  checklist:
    - 是否遗漏用户需求？
    - 是否存在设计矛盾？
    - 是否有过度设计？
    - 是否存在安全风险？
    - 是否有无法落地的技术方案？
    - 是否存在未考虑的异常场景？
    
  outcome_options:
    - approved: 继续执行
    - needs_revision: 返回上一阶段修改
    - escalated: 升级人工决策
```

## 当前状态

- [x] 组件设计完成
- [ ] Schema 定义（P1）
- [ ] 工作流引擎实现（P2）
- [ ] 平台适配验证（P7）
