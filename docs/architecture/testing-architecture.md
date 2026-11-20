# 测试架构设计

## 概述

SDD 测试架构覆盖从单元测试到端到端集成测试的完整测试层级，确保每个 Skill、工作流和平台适配的质量。

### 与门禁和 Workflow 的关系

- G1–G6 的触发条件、自动检查、人工审批、失败回退和审计要求，**唯一权威定义见 [ADR-006](../decisions/ADR-006-quality-gates.md)**。本文档只定义如何测试这些规则，不重复定义门禁规则。
- Workflow DAG、并行、失败路径的执行语义见 [orchestration-architecture.md](./orchestration-architecture.md)。本文档验证这些语义是否正确实现。
- **G4（代码质量/Review）与 G5（测试验收）是两道独立门禁**：测试通过不代表 Review 通过，Review 通过也不代表测试通过；两者可以并行，但必须共同满足质量门禁后才能进入部署。
- 测试产物按 [ADR-005](../decisions/ADR-005-task-context.md) 写入 `artifacts/{task-id}/testing/` 与 `reports/`，不得写到任务目录之外。

## 测试层级

> 命名说明：测试层级使用 **T1–T4**，避免与系统架构层 L1–L6 混淆。

```
┌─────────────────────────────────────────────────────────────┐
│                    T4 · 端到端测试                          │
│          Agent 全流程测试 / 平台兼容性测试                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    T3 · 集成测试                            │
│           Workflow 测试 / 跨 Skill 协作测试                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    T2 · 单元/组件测试                       │
│              Skill 单功能测试 / Schema 验证                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    T1 · 基础测试                            │
│               工具函数测试 / 安全测试                         │
└─────────────────────────────────────────────────────────────┘
```

## Skill 单元测试

### 测试范围

每个 Skill 必须测试：

1. **触发条件** — description 匹配是否正确
2. **输入验证** — 无效输入是否被拒绝
3. **执行流程** — 步骤是否按预期执行
4. **输出格式** — 产物是否符合 Schema
5. **边界情况** — 空输入、大输入、异常输入

### 测试用例设计

```yaml
# tests/unit/example-skill/evals.yaml
skill: example-skill
tests:
  - name: "valid-input"
    prompt: "帮我分析一下这段代码"
    expected:
      artifacts:
        - path: "artifacts/{task-id}/analysis.md"
          exists: true
      gates:
        - skipped: true  # 简单任务无需审批
    
  - name: "empty-input"
    prompt: ""
    expected:
      error: "input_required"
      gate: null
    
  - name: "complex-task"
    prompt: "帮我设计一个完整的电商系统"
    expected:
      complexity: "L3"
      gates:
        - name: "G2"
          required: true
```

### 测试执行（规划）

> 当前 OpenClaw CLI（2026.11.4）没有 `--skill` / `--test` 参数；以下为 P7 测试运行器的目标形态，现阶段不可直接执行。

```bash
# 目标形态（P7 实现 tools/skill-validator 后）
python tools/skill-validator/run_evals.py tests/unit/example-skill/evals.yaml

# 现阶段临时验证：用普通 agent turn 触发 Skill 描述
openclaw agent --session-key '<session-key>' --message "测试用例内容"
```

### 验收标准

- [ ] 所有测试用例通过
- [ ] 覆盖率 > 80%
- [ ] 边界情况测试覆盖
- [ ] 性能测试达标（< 30s 响应）

## Workflow 集成测试

### 测试范围

工作流集成测试验证多个 Skill 的协作：

1. **顺序执行** — Skill 按依赖顺序执行
2. **产物传递** — 上一 Skill 的输出成为下一 Skill 的输入
3. **门禁触发** — HARD-GATE 正确触发和等待
4. **错误处理** — 失败时的回退和重试
5. **并行执行** — 子 Agent 并行任务的正确性

### 测试用例设计

```yaml
# tests/workflow/feature-development.yaml
name: feature-development
description: "完整功能开发流程测试"
steps:
  - trigger: "帮我做一个用户管理功能"
    expected_skills:
      - requirements-clarity
      - analysis
      - design
      - coding
      - testing
    expected_gates:
      - name: "G1"
        required_for: L2/L3
      - name: "G2"
        required_for: L3
      - name: "G3"
        required_for: L3
      - name: "G4"
        required_for: 所有代码变更
      - name: "G5"
        required_for: 所有代码变更
    expected_artifacts:
      - requirements
      - analysis
      - design
      - implementation
      - review-report
      - test-report
    timeout: 300s
```

### 端到端测试

```yaml
# tests/workflow/bug-fix.yaml
name: bug-fix
description: "Bug 修复流程测试"
steps:
  - trigger: "接口返回 500 错误"
    expected_skills:
      - analysis
      - coding
      - testing
      - code-review
    expected_gates:
      - name: "G4"
        required_for: 所有代码变更
      - name: "G5"
        required_for: 所有代码变更
    expected_artifacts:
      - analysis
      - implementation
      - review-report
      - test-report
```

### Workflow DAG 测试

验证 DAG 执行语义（定义见 orchestration-architecture.md）：

1. **并行启动** — coding 完成后，code-review 与 testing 同时启动。
2. **屏障等待** — quality gate 必须等待两个节点都结束，不能先到先过。
3. **Review 失败阻断** — G4 严重问题必须阻止进入 deployment。
4. **Testing 失败回退** — G5 失败按缺陷类型回到 coding 或 analysis，不得进入 deployment。
5. **双门禁** — G4 与 G5 都通过才允许 G6；任何一方失败都不能被另一方替代。
6. **重试与超时** — 节点按 retry/timeout 规则执行；超时按失败处理。
7. **审批暂停/恢复** — 门禁节点进入 awaiting_approval，只有显式批准才恢复；超时不等于批准。
8. **产物引用** — 每个节点的输入/输出符合 ADR-005 的路径、版本和 hash 引用。

```yaml
# 规划示例：tests/workflow/dag-quality-gate.yaml
name: dag-quality-gate
steps:
  - given: "coding 成功"
    expect_parallel_start: [code-review, testing]
  - given: "code-review 有严重问题"
    expect: "quality gate blocked; deployment not started"
  - given: "testing 失败"
    expect: "return_to: coding_or_analysis; deployment not started"
  - given: "G4 和 G5 都通过"
    expect: "quality gate passed; deployment may start (G6)"
```

## Agent 端到端测试

### 测试范围

验证整个 Agent 系统在实际使用场景中的表现：

1. **需求理解** — 是否正确理解用户意图
2. **流程选择** — 是否选择合适的工作流
3. **质量门禁** — 是否严格执行审批
4. **错误恢复** — 失败后是否能恢复
5. **用户体验** — 交互是否顺畅

### 测试场景库

```yaml
# tests/e2e/scenarios/
scenarios:
  simple-change:
    description: "简单样式修改"
    trigger: "把按钮颜色改成蓝色"
    expected_duration: "< 30s"
    expected_gates: ["G4（简化）", "G5（简化）"]
    
  bug-investigation:
    description: "Bug 调查和修复"
    trigger: "用户登录失败"
    expected_duration: "< 5min"
    expected_gates: ["G4", "G5"]
    
  feature-development:
    description: "新功能开发"
    trigger: "实现搜索功能"
    expected_duration: "< 30min"
    expected_gates: ["G1", "G2", "G3", "G4", "G5"]
    
  system-refactor:
    description: "系统重构"
    trigger: "重构用户模块"
    expected_duration: "< 2h"
    expected_gates: ["G1", "G2", "G3", "G4", "G5"]
    
  production-deployment:
    description: "生产部署"
    trigger: "部署到生产环境"
    expected_duration: "< 30min"
    expected_gates: ["G5", "G6"]
```

### 测试执行

```bash
# 运行端到端测试
openclaw agent --session-key '<session-key>' \
  --message-file 'tests/e2e/scenarios/feature-development.md' \
  --timeout 1800
```

## 平台兼容性测试

### 测试矩阵

| 测试项 | Codex | Claude Code | Cursor | Gemini CLI | OpenCode | OpenClaw |
|--------|-------|-------------|--------|------------|----------|----------|
| Skill 触发 | 必测 | 必测 | 必测 | 必测 | 必测 | 必测 |
| 工具调用 | 必测 | 必测 | 必测 | 必测 | 必测 | 必测 |
| 文件读写 | 必测 | 必测 | 必测 | 必测 | 必测 | 必测 |
| 子 Agent | 按能力验证 | 按能力验证 | 按能力验证 | 按能力验证 | 按能力验证 | 按能力验证 |
| 审批交互 | 必测 | 必测 | 必测 | 必测 | 必测 | 必测 |
| 并行执行 | 按能力验证 | 按能力验证 | 按能力验证 | 按能力验证 | 按能力验证 | 按能力验证 |

> 六个平台的能力均未在 P0 实测；测试结果必须记录平台版本、命令、期望/实际结果和证据路径。未通过的能力标记为「不支持」或「降级」，不得写成通过。

### 兼容性测试用例

```yaml
# tests/compatibility/codex/basic-skill.yaml
platform: codex
skill: requirements-clarity
tests:
  - name: "trigger-match"
    input: "帮我写一个登录功能"
    expect_trigger: true
    
  - name: "output-format"
    expect_artifact: "requirements.md"
    validate_schema: true
    
  - name: "no-subagent"
    expect_parallel: false
    timeout: 120s
```

### 平台特定测试

每个平台 README 中必须包含：
- 兼容性测试结果
- 已知限制
-  workaround 方案
- 性能基准

## 安全测试

### 安全测试清单

```yaml
# tests/security/checklist.yaml
tests:
  - name: "input-injection"
    description: "测试输入注入攻击"
    payloads:
      - "../etc/passwd"
      - "$(rm -rf /)"
      - "'; DROP TABLE users;--"
    expect: "blocked or sanitized"
    
  - name: "path-traversal"
    description: "测试路径穿越"
    inputs:
      - "../../secret"
      - "/etc/shadow"
    expect: "access denied"
    
  - name: "sensitive-data-leak"
    description: "测试敏感信息泄漏"
    scenarios:
      - "API key in output"
      - "password in log"
    expect: "redacted"
    
  - name: "privilege-escalation"
    description: "测试权限提升"
    actions:
      - "低权限 Skill 执行高权限操作"
    expect: "permission denied"
```

### 安全测试执行（规划）

> 以下脚本 P7 才会实现，当前仓库中不存在。

```bash
# 运行安全测试（P7 待实现）
python tests/security/run_security_tests.py

# 生成安全报告（P7 待实现）
python tests/security/generate_report.py --output security-report.md
```

### 测试产物

测试报告、覆盖率、失败用例和重试记录按 [ADR-005](../decisions/ADR-005-task-context.md) 写入：

```text
artifacts/{task-id}/testing/
artifacts/{task-id}/reports/
```

测试产物必须记录：commit、环境、平台版本、测试命令、结果、证据路径和时间。

## 回归测试

### 回归测试策略

每次架构变更或 Skill 更新后，必须运行：

1. **全量单元测试** — 确保无破坏性变更
2. **核心工作流测试** — 关键路径回归
3. **安全测试** — 确认无安全回归
4. **兼容性测试** — 平台支持不变

### 回归测试套件

```yaml
# tests/regression/regression-suite.yaml
suite: regression
priority: high
tests:
  - path: "tests/unit/**/*"
    frequency: "每次变更"
  - path: "tests/workflow/feature-development.yaml"
    frequency: "每次架构变更"
  - path: "tests/security/**/*"
    frequency: "每次部署"
  - path: "tests/compatibility/**/*"
    frequency: "每月或平台更新"
```

## 验收标准

### 单元/组件测试

| 指标 | 目标值 | 当前状态 |
|------|--------|----------|
| 覆盖率 | > 80% | 0%（待实现） |
| 通过率 | 100% | N/A |
| 响应时间 | < 30s | N/A |

### 工作流测试

| 指标 | 目标值 | 当前状态 |
|------|--------|----------|
| 关键路径通过率 | 100% | N/A |
| 门禁正确触发 | 100% | N/A |
| 产物完整性 | 100% | N/A |

### 端到端测试

| 指标 | 目标值 | 当前状态 |
|------|--------|----------|
| 场景覆盖率 | > 90% | N/A |
| 用户满意度 | > 4/5 | N/A |
| 平均任务完成率 | > 95% | N/A |

### 平台兼容性测试

| 指标 | 目标值 | 当前状态 |
|------|--------|----------|
| 已验证平台数 | ≥ 2 | 0 |
| 兼容性通过率 | 100% | N/A |

## 测试基础设施

### 测试目录结构

```
tests/
├── unit/                    # 单元测试
│   └── skill-name/
│       ├── evals.yaml       # 测试用例
│       ├── expected/        # 期望输出
│       └── scripts/         # 测试脚本
├── integration/             # 集成测试
│   └── skill-combo/
├── workflow/                # 工作流测试
│   ├── simple-task.yaml
│   ├── bug-fix.yaml
│   └── feature-development.yaml
├── compatibility/           # 兼容性测试
│   └── platform-name/
├── security/                # 安全测试
│   ├── checklist.yaml
│   └── scripts/
└── e2e/                     # 端到端测试
    └── scenarios/
```

> 当前实际存在 `tests/unit/`、`tests/integration/`、`tests/workflow/`、`tests/compatibility/`；`tests/security/`、`tests/regression/`、`tests/e2e/` 为 P5–P7 规划目录，P0 不创建。

### 测试工具

```
tools/
├── skill-validator/         # Skill 验证器
│   └── validate_skill.py
├── workflow-validator/      # 工作流验证器
│   └── validate_workflow.py
├── compatibility-checker/   # 兼容性检查
│   └── check_compatibility.py
└── quality-checker/         # 质量检查
    └── check_quality.py
```

## 当前状态

- [x] 测试架构设计完成
- [ ] Skill 单元测试随各 Skill 在 P2–P6 阶段落地
- [ ] Workflow / 端到端 / 安全测试框架（P5–P7）
- [ ] 平台兼容性与回归测试（P7）

## 风险与限制

1. **测试覆盖延迟** — P0 阶段没有实现可测；单元测试应随 Skill 在 P2–P6 落地，端到端与兼容性测试在 P7
2. **平台差异** — 不同平台测试环境配置复杂
3. **测试数据** — 需要构造多样化的测试输入
4. **性能基准** — 长期性能追踪需要额外工具

---

*本文档应与 ADR-001、ADR-006 配合使用，定义整体测试策略。*
