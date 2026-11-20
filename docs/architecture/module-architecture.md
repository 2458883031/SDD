# 模块架构设计

## 模块划分

### 核心模块

| 模块 | 路径 | 职责 | 依赖 |
|------|------|------|------|
| orchestration | `skills/development/orchestration/` | 流程总控 | 无 |
| requirements | `skills/development/requirements-clarity/` | 需求澄清 | orchestration |
| analysis | `skills/development/analysis/` | 技术分析 | requirements |
| design | `skills/development/design/` | 架构设计 | analysis |
| coding | `skills/development/coding/` | 代码实现 | design |
| code-review | `skills/development/code-review/` | 代码审查 | coding |
| testing | `skills/development/testing/` | 测试验证 | coding |
| deployment | `skills/development/deployment/` | 部署交付 | testing |
| documentation | `skills/development/documentation/` | 文档生成 | design, coding |
| feedback | `skills/development/feedback-loop/` | 反馈优化 | deployment |

### 技术模块

| 模块 | 路径 | 职责 | 所属 Skill |
|------|------|------|-----------|
| frontend-vue | `skills/development/coding/frontend/vue/` | Vue.js 开发 | coding |
| frontend-react | `skills/development/coding/frontend/react/` | React 开发 | coding |
| backend-java | `skills/development/coding/backend/java/` | Java 开发 | coding |
| backend-python | `skills/development/coding/backend/python/` | Python 开发 | coding |
| database-sql | `skills/development/coding/database/` | SQL 开发 | coding |
| devops-docker | `skills/development/deployment/docker/` | Docker 部署 | deployment |
| devops-k8s | `skills/development/deployment/kubernetes/` | K8s 部署 | deployment |

### 基础设施模块

| 模块 | 路径 | 职责 |
|------|------|------|
| standards | `core/standards/` | 规范文档 |
| schemas | `core/schemas/` | Schema 定义 |
| templates | `core/templates/` | 模板文件 |
| tools | `tools/` | 验证工具 |

## 依赖关系图

```
orchestration
    ↓
requirements-clarity
    ↓
analysis
    ↓
design
    ↓
coding ←→ technical-skills
    ↓
    ├── code-review
    └── testing
            ↓
        deployment
            ↓
        documentation
            ↓
        feedback-loop
```

## 模块接口定义

### 编排模块接口

```yaml
# input: task-context
type: object
properties:
  user_request: string
  project_context: object
  previous_artifacts: array

# output: workflow-plan
type: object
properties:
  task_type: enum[simple, bugfix, feature, refactor, new_project, deployment, consult]
  complexity: enum[L1, L2, L3]
  required_skills: array
  gates: array
  artifacts_path: string
```

### 需求模块接口

```yaml
# input: raw_request
type: string

# output: requirements-doc
type: object
properties:
  goal: string
  scope: object
  constraints: array
  acceptance_criteria: array
  non_goals: array
```

### 分析模块接口

```yaml
# input: requirements-doc
type: object

# output: analysis-report
type: object
properties:
  tech_stack_recommendation: object
  risk_assessment: object
  dependency_map: object
  complexity_factors: object
```

### 设计模块接口

```yaml
# input: analysis-report
type: object

# output: design-doc
type: object
properties:
  architecture: string
  module_structure: object
  api_definitions: array
  data_model: object
  security_considerations: array
```

## 模块间通信协议

### 产物传递

每个模块的输出作为下一个模块的输入，通过 `artifacts/` 目录传递：

```
artifacts/
└── task-{id}/
    ├── requirements.md
    ├── analysis.md
    ├── design.md
    ├── implementation-plan.md
    ├── code-review.md
    ├── test-report.md
    └── deployment-report.md
```

### 上下文共享

模块间共享以下上下文：
- `task-id` — 任务唯一标识
- `project-root` — 项目根目录
- `user-preferences` — 用户偏好设置
- `platform-config` — 平台配置

### 错误处理

模块失败时的处理策略：
1. **可恢复错误** — 记录日志，重试最多 3 次
2. **不可恢复错误** — 中止流程，返回错误详情
3. **人工介入** — 触发 HARD-GATE，等待用户决策

## 扩展点

### 新增 Skill

1. 在对应层级创建模块目录
2. 定义输入/输出 Schema
3. 在 orchestration 注册路由规则
4. 添加平台适配（如需要）

### 新增技术栈

1. 在 technical-skills 下创建模块
2. 实现标准接口
3. 在 coding/testing 中添加调用示例
4. 更新兼容性矩阵

### 新增平台支持

1. 在 platforms/ 下创建适配目录
2. 实现平台特定的 Skill 加载机制
3. 映射标准接口到平台 API
4. 更新兼容性测试

## 当前状态

- [x] 模块划分完成
- [x] 依赖关系确定
- [ ] 详细接口定义（P1）
- [ ] 模块实现（P2-P6）
