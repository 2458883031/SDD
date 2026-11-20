# 模块架构设计

## 模块划分

### 核心模块

| 模块 | 路径 | 职责 | 依赖 |
|------|------|------|------|
| orchestration-engine | `core/orchestration/`（P2 规划） | 任务识别、拆解、路由、状态管理、结果汇总 | 无（只依赖核心端口） |
| orchestration-skill | `skills/development/orchestration/` | 编排入口 Skill，辅助 Agent 选择流程 | 调用 orchestration-engine 的公开接口 |
| requirements | `skills/development/requirements-clarity/` | 需求澄清 | orchestration-engine |
| analysis | `skills/development/analysis/` | 技术分析 | requirements |
| design | `skills/development/design/` | 架构设计 | analysis |
| coding | `skills/development/coding/` | 代码实现 | design |
| code-review | `skills/development/code-review/` | 独立代码审查 | coding |
| testing | `skills/development/testing/` | 测试验证 | coding |
| deployment | `skills/development/deployment/` | 部署交付 | code-review、testing、G4/G5 |
| documentation | `skills/development/documentation/` | 文档生成 | design、coding |
| feedback | `skills/development/feedback-loop/` | 反馈优化 | deployment、testing |

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

> 模块依赖与 Workflow 节点的权威执行语义见 [orchestration-architecture.md](./orchestration-architecture.md) 与 ADR-003；G4/G5 门禁规则见 [ADR-006](../decisions/ADR-006-quality-gates.md)。

### 功能开发（L2/L3）

```text
requirements
    ↓
analysis
    ↓
design
    ↓
plan (G3)
    ↓
coding ────────────────┐
    │                   │
    ├── code-review ────┤
    │   (G4)            │
    └── testing ────────┤
        (G5)            │
                        ▼
                 quality gate
                 (G4 AND G5)
                        ↓
                 deployment (G6)
                        ↓
                 verification
                        ↓
                 documentation
                        ↓
                  feedback-loop
```

- `code-review` 与 `testing` 可以并行，但**不能互相替代**。
- 两者都必须通过 G4/G5，才允许进入 deployment。
- Review 发现严重问题时回到 coding；测试失败时按缺陷类型回到 coding 或 analysis。
- 文档与反馈可以并行，但不得绕过质量门禁。

### 简单修改（L1）

```text
coding → testing/automated checks → (G4/G5 简化) → end
```

简单修改允许省略 requirements/analysis/design，但仍需必要的代码检查与验证；不得跳过安全约束。

### Bug 修复（L2）

```text
analysis → coding → {code-review, testing} → quality gate → (deployment?) → verification
```

Bug 修复必须包含分析、编码、Review 和测试；是否部署由任务范围决定。

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

产物与上下文的权威模型见 [ADR-005](../decisions/ADR-005-task-context.md)。模块只通过 `artifacts/{task-id}/` 下的产物契约交互，不直接读取其他模块的内部状态。

```text
artifacts/{task-id}/
├── context.json
├── metadata.json
├── requirements/
├── analysis/
├── design/
├── implementation/
├── testing/
├── review/
└── reports/
```

### 上下文共享

模块间共享的 Task Context 字段（权威定义见 ADR-005）：

- `task-id` — 任务唯一标识
- `project-root` — 项目根目录
- `task-type` / `complexity`
- `task-status` / `current-stage`
- `user-preferences`
- `platform-config` — **平台配置引用**，不是平台配置本身
- `task-constraints`
- `artifact-references` — 产物引用（路径 + 版本 + hash）

`platform-config` 只保存适配器配置的引用/标识，不得把平台专属配置复制进任务上下文，也不得让核心 Skill 读取平台专属字段。

### 错误处理

模块失败时的处理策略：

1. **可恢复错误** — 记录日志，按 Workflow 重试策略重试（默认最多 3 次，指数退避）。
2. **不可恢复错误** — 中止当前节点，标记 Workflow 失败，保留已生成产物。
3. **质量门禁失败** — 按 ADR-006 的回退路径返回 coding / analysis / design，不得直接进入部署。
4. **人工介入** — 触发 G1–G6 中对应的审批点，暂停并等待用户决策；超时不得视为批准。

## 扩展点

### 新增 Skill

1. 在对应层级创建模块目录与 `SKILL.md`。
2. 定义输入/输出契约与所需 Tool/权限。
3. 在 Workflow 定义中注册节点（不是在编排引擎里硬编码）。
4. 如平台需要额外元数据，放入 `platforms/<platform>/`，不修改核心 Skill 语义。

### 新增技术栈

1. 在 technical-skills 下创建模块。
2. 实现标准接口。
3. 在 coding/testing 中添加调用示例。
4. 更新平台能力矩阵与验证计划。

### 新增平台支持

1. 在 `platforms/<platform>/` 下创建适配目录。
2. 实现核心端口（工具、发现、元数据、审批、上下文）。
3. 映射标准接口到平台 API。
4. 更新兼容性测试与验证状态。

## 当前状态

- [x] 模块划分完成
- [x] 依赖关系确定（Review/Testing 并行、Deployment 依赖双门禁）
- [x] Task Context / Artifact 统一引用 ADR-005
- [ ] 详细接口定义（P1）
- [ ] 模块实现（P2–P6）
