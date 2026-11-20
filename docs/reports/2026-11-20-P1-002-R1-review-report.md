# SDD P1-002-R1 独立复审整改报告

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-002-R1（含 R1-F2 补充整改） |
| 目标 PR | **#3** — https://github.com/2458883031/SDD/pull/3 |
| 分支 | `feature/p1-002-orchestration` |
| 基线 | `70b8549aff89fa8e1ce5caaf42bd413616d54c92`（main） |
| R1 实施提交 | `14cd1e0af6775f5dac5df75af24b8b60fa1c5ab7` |
| R1 报告文件所在提交 | `aa81252bfc1646adf938526e472d2281fc34047c` |
| R1-F2 实施提交 | `9bc493362609f36bf2eae4db45c15f0f2ce1487d` |
| R1-F2 报告提交 | 无法在文件内容中预写自身提交 SHA；由最终交付消息提供具体值 |
| 最终 PR Head | 由最终交付消息提供（报告提交后更新） |
| 执行/监督 | Claude Code |
| 当前状态 | **P1-002-R1-F2 Draft（整改已提交，待推送/复审）** |

> 本轮在 R1 基础上补充修复 Approval 安全绑定、路径符号链接、DAG 分支终止性、并行汇合、Task Context Schema 约束和报告元数据。不重新设计 P1-002，不修改 main，不创建新 PR，不合并。

---

## 一、执行前状态

| 检查项 | 实际值 | 结果 |
|--------|--------|------|
| 分支 | `feature/p1-002-orchestration` | ✅ |
| 本地 HEAD | `6e321c39fbf45114d3a99b8de9d84cabb6016abf` | ✅ |
| origin 分支 | `6e321c39fbf45114d3a99b8de9d84cabb6016abf` | ✅ |
| PR #3 Head | `6e321c39fbf45114d3a99b8de9d84cabb6016abf` | ✅ 未变化 |
| PR Base | `main` — `70b8549a` | ✅ |
| main / origin/main | `70b8549a` / `70b8549a` | ✅ 未修改 |
| 工作区 | clean | ✅ |

PR Head 未发生变化，按授权在原分支追加整改提交。

---

## 二、原始问题与整改对应表

| 编号 | 原始问题 | 整改结果 | 主要文件 |
|------|----------|----------|----------|
| R1-M1 | Approval 缺少单次消费状态与并发消费约束 | 增加 `CONSUMED`、`consumed_at`、`consumed_by`、`consumption_ref`、原子消费测试 | `approval.schema.json`、`approval-state-machine.json`、`approval-orchestration-standard.md`、`approval-g6-consumed.json`、校验器 |
| R1-M2 | Subworkflow 未固定版本，缺递归/深度/状态检查 | `workflow_ref` 改为 `{id, version}`；递归、深度 ≤3、引用存在/状态检查 | `workflow.schema.json`、`workflow-standard.md`、`release-composed.yaml`、校验器 |
| R1-M3 | GateDecision hash 约束可被 null/缺失绕过 | G4/G5 全状态必须有效 `subject_hash`；G6 增加 `deployment_target` | `gate-decision.schema.json`、`gate-orchestration-standard.md`、`gate-g6-blocked.json`、校验器 |
| R1-M4 | 状态机测试用自身 transitions 自证 | 独立期望转换集、全状态对负向测试、18 个 Guard 测试 | 校验器 |
| R1-M5 | 路径前缀校验不安全，Approval 绑定检查不足 | 路径规范化/目录边界/穿越/绝对路径/符号链接；Approval 全绑定字段 + 并发消费 | 校验器、`approval-orchestration-standard.md` |
| R1-m1 | Workflow DAG 校验不完整 | `on_success`/`on_failure` 引用、终止可达、parallel join、quorum、Subworkflow 全图 | 校验器 |
| R1-m2 | 最终报告统计不统一 | 本报告统一实施 HEAD、报告 SHA、PR Head、提交数、文件统计 | 本报告 |
| 专项 | Task Context 与 ADR-005 关系不清 | 增加 `context_scope`（root/node），明确根 Context 完成条件 | `task.schema.json`、`task-standard.md`、`orchestration-state-machine.md`、示例、校验器 |

---

## 三、R1-M1：Approval 单次消费

### 3.1 变更

- Approval 状态增加 `CONSUMED`。
- 增加字段：
  - `consumed_at`：消费时间；
  - `consumed_by`：消费执行者；
  - `consumption_ref`：消费对应执行/证据引用。
- 状态机增加 `APPROVED → CONSUMED`，`CONSUMED` 为终态。
- 标准明确：
  - 只能从 `APPROVED` 原子消费一次；
  - 并发消费只能一个成功，其余返回 `already_consumed`；
  - `CONSUMED` 不得恢复为 `APPROVED`；
  - `approval_usable()` 必须拒绝 `CONSUMED`。
- 示例新增 `approval-g6-consumed.json`。
- 校验器新增：
  - `CONSUMED` 缺 `consumed_at`/`consumed_by` 负向 Schema 测试；
  - `ApprovalStore` 原子消费；
  - 双线程并发消费，断言恰好一个成功；
  - 第二次消费失败；
  - 消费后不可用。

### 3.2 文件

- `schemas/orchestration/approval.schema.json`
- `schemas/orchestration/approval-state-machine.json`
- `docs/standards/approval-orchestration-standard.md`
- `docs/standards/orchestration-state-machine.md`
- `examples/orchestration/approvals/approval-g6-approved.json`
- `examples/orchestration/approvals/approval-g6-consumed.json`
- `tests/unit/orchestration/validate_orchestration.py`

---

## 四、R1-M2：Subworkflow 版本与递归

### 4.1 Schema 变化

```text
before: workflow_ref: string
after:  workflow_ref: { id: <workflow-id>, version: <SemVer> }
```

- `workflow_ref` 必须是对象，`id` + 固定 SemVer `version` 均必需。
- 不允许 `latest`、范围版本或缺失版本。

### 4.2 校验规则

1. 被引用 Workflow 的 `(id, version)` 必须存在。
2. 被引用 Workflow 的 `status` 必须为 `tested` 或 `published`。
3. 直接/间接递归/循环拒绝。
4. 组合深度 ≤3。
5. 递归校验被引用 Workflow 的完整 DAG。

### 4.3 示例与测试

- `release-composed.yaml` 使用：
  - `feature-development@0.1.0`
  - `deployment@0.1.0`
- 被引用 Workflow 示例状态为 `tested`。
- 新增负向测试：
  - 未知 Workflow ID；
  - 未知版本；
  - 被引用 Workflow 为 `draft`；
  - 间接循环 `A → B → A`；
  - 深度 >3 的链。

### 4.4 文件

- `schemas/orchestration/workflow.schema.json`
- `docs/standards/workflow-standard.md`
- `examples/orchestration/workflows/release-composed.yaml`
- `examples/orchestration/workflows/feature-development.yaml`
- `examples/orchestration/workflows/deployment.yaml`
- `tests/unit/orchestration/validate_orchestration.py`

---

## 五、R1-M3：GateDecision hash 约束

### 5.1 Schema 变化

- 新增 `deployment_target` 字段。
- G4/G5 条件：
  ```text
  if gate_id in [G4, G5]:
      subject_hash required, non-empty string (minLength 8)
  ```
  适用于 PENDING/EVALUATING/BLOCKED/PASSED/FAILED 等所有状态。
- G6 条件：
  ```text
  subject_hash required
  deployment_target required, non-empty
  ```
- 不允许 null/缺失绕过。

### 5.2 测试

新增负向：

- G4 `PENDING` 缺 `subject_hash`；
- G4 `BLOCKED` 缺 `subject_hash`；
- G4 `FAILED` 缺 `subject_hash`；
- G6 缺 `deployment_target`；
- G6 缺 `subject_hash`（此前已有）。

保留：

- G4/G5 `subject_hash` 必须相同；
- `current_subject_hash` 必须等于 G4/G5 hash；
- 新 commit 使旧 Gate 失效；
- 不用 Task SUCCEEDED 替代 GateDecision。

### 5.3 文件

- `schemas/orchestration/gate-decision.schema.json`
- `docs/standards/gate-orchestration-standard.md`
- `examples/orchestration/gates/gate-g6-blocked.json`
- `tests/unit/orchestration/validate_orchestration.py`

---

## 六、R1-M4：状态机测试独立性

### 6.1 变更

- 不再通过读取状态机自身 `transitions` 证明合法。
- 在测试代码中维护独立 `EXPECTED_TRANSITIONS`：
  - Task：18；
  - Workflow：14；
  - Node：19；
  - Gate：16；
  - Approval：10。
- 对每个状态机：
  - 合法转换逐项验证；
  - 所有未定义状态对（含非终态、终态、自转换）验证为非法；
  - 检查实际 transitions 与独立期望完全一致。
- 新增 18 个 Guard 条件测试，覆盖：
  - 依赖；
  - 权限/租约；
  - 审批；
  - 产物/证据/Gate；
  - 取消；
  - 恢复等待；
  - 阻塞解除；
  - 产物版本变化；
  - 原子消费。

### 6.2 统计

```text
transition_definitions=77
transition_tests=322
guard_cases=18
state_transitions_positive=77
state_transitions_negative=245
```

`transition_tests` = 77 个合法转换 + 245 个非法状态对。

---

## 七、R1-M5：安全测试

### 7.1 路径校验

替换字符串前缀判断，新增：

- `normalize_path()`：反斜杠规范化、`posixpath.normpath`、绝对路径拒绝、`..` 越界拒绝；
- `path_allowed()`：只允许 `artifacts/{task_id}/` 目录边界；
- 符号链接映射解析后再校验。

负向测试：

- `artifacts/{task}/../other/secret`；
- `/etc/passwd`；
- `C:\Windows\win.ini`；
- 其他 task 目录；
- 符号链接指向其他 task；
- 符号链接指向项目外。

### 7.2 Approval 绑定

`approval_usable()` 现在检查：

- `task_id`；
- `workflow_id`；
- `node_id`；
- `operation`；
- `target`；
- `environment`；
- `scope`；
- `subject_hash`；
- `expires_at`；
- `single_use`；
- `consumed_at`/`CONSUMED` 状态。

测试覆盖每个字段变化均拒绝，以及同一 Approval 重复消费/并发消费。

---

## 八、R1-m1：Workflow DAG 校验

新增/强化：

1. `on_success`/`on_failure` 目标必须存在；新增未知目标负向测试。
2. 从每个节点沿依赖和成功/失败边必须可达一个 `end`；新增不可终止分支负向测试。
3. `parallel_group` 必须有共同汇合后代；新增无汇合负向测试。
4. `join_policy=quorum` 时 `quorum` 必须在依赖数量范围内；无 `join_policy` 时不得出现 `quorum`；新增两个负向测试。
5. Subworkflow 递归校验完整 DAG、版本、状态、循环和深度。

DAG 测试统计：

```text
workflow_graph_positive=10
workflow_graph_negative=16
```

---

## 九、R1-m2：最终报告修订

本报告作为独立整改报告，不覆盖历史报告。统一后的统计：

| 项目 | 值 |
|------|-----|
| 基线 | `70b8549aff89fa8e1ce5caaf42bd413616d54c92` |
| R1 实施提交 / 最终实施 HEAD | `14cd1e0af6775f5dac5df75af24b8b60fa1c5ab7` |
| R1 报告文件所在提交 | `aa81252bfc1646adf938526e472d2281fc34047c` |
| R1-F2 实施提交 | `9bc493362609f36bf2eae4db45c15f0f2ce1487d` |
| R1-F2 报告提交 / 最终 HEAD | 由最终交付消息提供（无法预写自身提交 SHA） |
| PR | #3 |
| PR Base | `main` |
| PR Head（R1 实施后） | `14cd1e0af6775f5dac5df75af24b8b60fa1c5ab7` |
| PR 总提交数（R1 实施后） | 10 |
| 实施变更统计 | 46 files, +6408/−1 |
| 报告提交后最终 PR | 47 files, 11 commits（报告文件 +1） |

旧 `2026-11-20-P1-002-final-report.md` 保留为历史快照，不再作为最终统计来源。

---

## 十、Task Context 与 ADR-005 一致性

### 10.1 明确回答

1. **Workflow Run 是否拥有独立根 Task Context？**
   是。每个 Workflow Run 拥有一个根 Task Context；其 `task-status` 按 ADR-005 生命周期演进，代表整个 Run。
2. **节点级 Task 是否拥有独立 Task Context？**
   是。每个节点 Task 拥有 scoped Task Context，`parent_task_id` 指向根任务；它只记录节点输入/输出/执行状态。
3. **节点 Task SUCCEEDED 是否会错误把根 Context 设置为 completed？**
   不会。节点 SUCCEEDED 只更新节点本地状态和本地 `context_status`，不得写根 `task-status`。
4. **根 Context 何时才能 completed？**
   只有所有必需 Task 成功/允许跳过、必需 Gate 通过、Workflow 级验证完成后，根 Context 才能 `verifying → completed`。
5. **映射如何定义？**
   - `context_scope=root`：`context_status` 是权威 ADR-005 生命周期；`status` 是调度投影。
   - `context_scope=node`：`status` 是节点执行状态；`context_status` 只是本地投影。
   - 节点 `SUCCEEDED` 对应本地 `completed`，不改变根 `task-status`。

### 10.2 实现

- `task.schema.json` 新增 `context_scope`（`root`/`node`，必需）。
- 新增根任务示例 `task-root-running.json`；节点示例 `parent_task_id` 指向根任务。
- `task-standard.md`、`orchestration-state-machine.md`、`orchestration-standard.md`、`orchestration-architecture.md` §10 同步说明。
- 校验器新增 `task_context_cases=7`：
  - 根/节点作用域；
  - 节点父任务指向根；
  - 节点成功不改根；
  - 根仅在 Workflow 验证 + Gate 通过后 completed；
  - 缺 Gate 不完成；
  - 本地/根生命周期区分。

**未修改 ADR-005。** 该专项是 P1-002 对 ADR-005 的实现澄清，不改变 ADR-005 权威模型。

---

## 十一、Schema 修改前后差异

| Schema | 修改前 | 修改后 |
|--------|--------|--------|
| `approval.schema.json` | 状态无 CONSUMED；无消费字段 | 增加 `CONSUMED`、`consumed_at`、`consumed_by`、`consumption_ref`；CONSUMED 条件必需 |
| `workflow.schema.json` | `workflow_ref` 为 string | `workflow_ref` 为 `{id, version}`，version 固定 SemVer |
| `gate-decision.schema.json` | G4/G5 仅 PASSED 需要 hash；G6 无部署对象 | G4/G5 全状态 hash；G6 增加 `deployment_target` |
| `task.schema.json` | 无根/节点 Context 区分 | 增加 `context_scope` root/node |
| `approval-state-machine.json` | APPROVED 无消费终态 | 增加 `APPROVED → CONSUMED`，CONSUMED 终态 |

---

## 十二、状态机变化

| 状态机 | 变化 |
|--------|------|
| Approval | 新增 `CONSUMED` 状态；新增 `APPROVED → CONSUMED`；`CONSUMED` 终态；禁止恢复 |
| Task | 转换集合保持不变；增加根/节点 Context 完成规则；测试改为独立期望集 |
| Workflow | 转换集合保持不变；增加根 Context 完成条件 |
| Node | 转换集合保持不变 |
| Gate | 转换集合保持不变；G4/G5/G6 约束在 Schema/标准中强化 |

---

## 十三、新增测试数量与实际输出

### 13.1 测试数量

| 类别 | 数量 |
|------|------|
| Schema 正向 | 22 |
| Schema 负向 | 24 |
| Workflow DAG 正向 | 10 |
| Workflow DAG 负向 | 16 |
| 状态机合法转换 | 77 |
| 状态机非法状态对 | 245 |
| 状态转换实际测试 | 322 |
| Guard 条件 | 18 |
| 并行 | 19 |
| Task Context | 7 |
| Gate | 15 |
| 失败恢复 | 16 |
| 安全 | 35 |

### 13.2 实际输出

```text
ORCHESTRATION VALIDATION PASSED
schemas=5 state_machines=5
examples: workflows=10 tasks=4 gates=3 approvals=2 evidence=3
schema_positive=22 schema_negative=24
workflow_graph_positive=10 workflow_graph_negative=16
state_transitions_positive=77 state_transitions_negative=245
transition_definitions=77 transition_tests=322 guard_cases=18
parallel_cases=19 task_context_cases=7 gate_cases=15
failure_cases=16 security_cases=35
yaml_blocks_checked=9 registry_ids=7
runtime_behavior=NOT_EXECUTED
```

P1-001 参考 Skill 校验器：

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=1 examples_out=5
cases_input_validated=6 invalid_cases_rejected=3
semver_valid=6 semver_invalid=6
yaml_blocks_checked=9 metadata_examples=1 registry_ids=7
negative_metadata_cases_passed=5
optional_positive_cases_passed=2 optional_negative_cases_passed=9
runtime_behavior=NOT_EXECUTED platform_entries=1
```

其他检查：

- Markdown 链接：58 个文件 0 断链；
- 围栏：无未闭合；
- 全仓 JSON/YAML 解析：无错误；
- 重复键 Loader：生效；
- P0 ADR-001–008：未修改。

---

## 十四、修改文件清单

R1 实施提交 `14cd1e0`：24 files changed，+806/−127。

### 文档

- `docs/architecture/orchestration-architecture.md`
- `docs/standards/approval-orchestration-standard.md`
- `docs/standards/execution-evidence-standard.md`
- `docs/standards/gate-orchestration-standard.md`
- `docs/standards/orchestration-standard.md`
- `docs/standards/orchestration-state-machine.md`
- `docs/standards/task-standard.md`
- `docs/standards/workflow-standard.md`

### Schema

- `schemas/orchestration/approval.schema.json`
- `schemas/orchestration/approval-state-machine.json`
- `schemas/orchestration/gate-decision.schema.json`
- `schemas/orchestration/task.schema.json`
- `schemas/orchestration/workflow.schema.json`

### 示例

- `examples/orchestration/approvals/approval-g6-approved.json`
- `examples/orchestration/approvals/approval-g6-consumed.json`（新增）
- `examples/orchestration/gates/gate-g6-blocked.json`（新增）
- `examples/orchestration/tasks/task-failed.json`
- `examples/orchestration/tasks/task-root-running.json`（新增）
- `examples/orchestration/tasks/task-running.json`
- `examples/orchestration/tasks/task-succeeded.json`
- `examples/orchestration/workflows/deployment.yaml`
- `examples/orchestration/workflows/feature-development.yaml`
- `examples/orchestration/workflows/release-composed.yaml`

### 测试

- `tests/unit/orchestration/validate_orchestration.py`

### 本报告

- `docs/reports/2026-11-20-P1-002-R1-review-report.md`

---

## 十五、提交、PR、CI 与 Runtime

### 15.1 提交

| 提交 | SHA |
|------|-----|
| R1 实施提交 | `14cd1e0af6775f5dac5df75af24b8b60fa1c5ab7` |
| R1 报告文件所在提交 | `aa81252bfc1646adf938526e472d2281fc34047c` |
| R1-F2 实施提交 | `9bc493362609f36bf2eae4db45c15f0f2ce1487d` |
| R1-F2 报告提交 | 由最终交付消息提供（无法预写自身 SHA） |
| 原 PR Head | `6e321c39fbf45114d3a99b8de9d84cabb6016abf` |

R1 实施后 PR 总提交数：10；报告提交后：11。

### 15.2 PR

- PR #3：https://github.com/2458883031/SDD/pull/3
- Base：`main` — `70b8549a`
- 状态：open，未合并
- 未创建新 PR

### 15.3 CI / Checks

- 仓库无 CI 配置；
- GitHub Check Runs：`total_count = 0`；
- Combined Status：`pending`，`total_count = 0`；
- 不得描述为 CI 通过。

### 15.4 Runtime

`runtime_behavior = NOT_EXECUTED`。

本轮未实现 Orchestrator、WorkflowRunner、Scheduler、StateStore、GateController、ApprovalCoordinator、EvidenceRecorder 或 Adapter；未执行运行时权限/审批/产物写入/平台兼容性验证。

---

## 十六、剩余风险

| 风险 | 说明 |
|------|------|
| Runtime 未实现 | 所有规则仍为静态标准/Schema/测试 |
| 状态机独立测试 | 已用独立期望集，但仍非运行时执行 |
| Subworkflow 运行时 | 版本/递归/深度为静态校验 |
| Approval 消费 | 原子消费为测试实现，不等于生产存储实现 |
| 路径安全 | 符号链接测试为模拟映射，未做 OS 级沙箱 |
| CI | 无自动 Checks |
| 平台兼容性 | 六平台 SDD 语义未实测 |
| ADR-005 | 未修改；根/节点 Context 为实现澄清，需在 Runtime 阶段验证同步 |

---

## 十七、R1-F2 补充整改

### 17.1 问题与整改映射

| 编号 | 问题 | 整改 |
|------|------|------|
| F2-M5.1 | Approval `subject_hash` 可单边缺失通过 | 双向绑定：要求上下文绑定时 Approval 必须有非空 hash；一方缺失/为空即拒绝；纯 SA 允许双方均无 |
| F2-M5.2 | Scope 使用无约束子集匹配，空 Scope 可能被解释为无限授权 | 改为规范化完整 Scope 精确匹配；空 Scope 仅匹配空请求；高风险 SA/G6 必须非空；新增参数/资源/路径/范围扩大/缩小均拒绝 |
| F2-M5.3 | 过期为字符串比较 | 使用 `datetime.fromisoformat` 解析并统一 UTC；支持 `Z` 与偏移；`now >= expires_at` 即过期 |
| F2-M5.4 | `ApprovalStore.consume()` 未在临界区验证绑定/有效期 | 临界区内调用完整 `approval_usable()` 校验；并发只成功一次；本地锁不声称分布式保证 |
| F2-M5.5 | 路径符号链接只匹配完整路径 | 按路径组件逐级解析；相对目标按符号链接所在目录解析；多级/嵌套/循环/绝对/越界拒绝 |
| F2-m1.1 | DAG 将成功/失败边合并，无法证明每条分支终止 | 分开 success/failure 前向图；成功分支与失败分支分别检查终止；新增互相掩盖负向测试 |
| F2-m1.2 | 并行汇合只检查共同后代 | join 必须直接依赖全部成员，或明确 `join_policy=quorum` 且满足 quorum；新增缺成员/仅单分支/错误 quorum 负向测试 |
| F2-Task | Schema 未约束根/节点 Context | 增加 `context_scope`/`workflow_verified` 条件；root 不得有 parent，node 必须有合法 parent；root completed 必须 workflow_verified=true |
| F2-Report | 报告元数据不完整 | 补充 R1 报告提交 `aa81252`、F2 实施提交 `9bc4933`、PR 统计和最终交付说明 |

### 17.2 Approval 新规则

**subject_hash：**

1. 操作需要代码/产物绑定时，Approval 与上下文都必须有非空且完全一致的 `subject_hash`。
2. Approval 有 hash、上下文缺失/为空 → 拒绝。
3. 上下文有 hash、Approval 缺失/为空 → 拒绝。
4. 仅纯操作（明确不涉及代码/产物）允许双方均无 hash。
5. G4/G5/G6 相关 Approval 自动要求 hash，即使调用方未传 `subject_required`。

**Scope：**

- 完整 Scope 规范化后精确匹配（JSON 键排序）。
- 空 Scope 只匹配空请求，不是无限授权。
- 高风险 SA/G6 必须非空 Scope。
- 新增参数、资源变化、路径变化、范围扩大、范围缩小、超集/子集均拒绝，必须重新审批。

**时间与消费：**

- `expires_at`/`now` 解析为 UTC；临界时刻 `now == expires_at` 即过期。
- 消费临界区内验证全部绑定；并发消费只成功一次；第二次失败。
- 本地线程锁仅用于静态测试，不代表生产级分布式原子保证。

### 17.3 符号链接解析策略

`normalize_path()` 按路径组件逐级解析：

1. 拒绝绝对路径、Windows 盘符路径和初始 `..` 越界。
2. 遇到组件级符号链接时，目标相对于符号链接所在目录解析。
3. 替换后从当前位置继续解析，支持多级/嵌套符号链接。
4. 使用 seen 集合与最大跳数检测循环。
5. 最终规范化路径必须位于 `artifacts/{task_id}/`。
6. 覆盖目录本身、目录子文件、多级链、嵌套、循环、相对越界、绝对目标、其他 Task、项目外路径。

本阶段仍是静态安全模型，**不声称实现 OS 级沙箱或运行时文件系统安全**。

### 17.4 Workflow 分支与并行汇合规则

- 成功前向图：依赖边 + `on_success`。
- 失败前向图：依赖边 + `on_success` + `on_failure`。
- 每个 success-reachable 节点必须能沿成功边到达 `end`。
- 每个已声明 `on_failure` 目标必须能沿失败/后续边到达 `end`。
- 失败分支不能由成功分支的可达性掩盖，反之亦然。
- `parallel_group` 的 join 必须直接依赖全部成员；`join_policy=quorum` 时必须满足 quorum，且 quorum 不超过成员数。
- 仅存在共同后代、但 join 不等待全部成员，视为无效汇合。

### 17.5 Task Context Schema 差异

| 约束 | 规则 |
|------|------|
| root + parent_task_id | 必须为空/省略 |
| node + parent_task_id | 必须存在，格式 `task-YYYYMMDD-<id>` |
| node + context_status=verifying | 拒绝（verifying 属于 Workflow 级） |
| root + context_status=completed | 必须 `workflow_verified=true` |
| node SUCCEEDED | 只更新本地 completed，不改变 root executing/verifying |
| root completed | 仅在 Workflow 验证 + 必需 Gate 通过后 |

新增示例：`task-root-running.json`、`task-root-completed.json`、`approval-pure-sa.json`。

### 17.6 F2 测试统计

| 类别 | 数量 |
|------|------|
| Schema 正向 | 24 |
| Schema 负向 | 30 |
| Workflow DAG 正向 | 10 |
| Workflow DAG 负向 | 21 |
| 状态机合法转换 | 77 |
| 状态机非法状态对 | 245 |
| 状态转换实际测试 | 322 |
| Guard 条件 | 18 |
| Approval 用例 | 48 |
| Scope 用例 | 12 |
| 过期用例 | 6 |
| 路径安全用例 | 12 |
| DAG 分支用例 | 4 |
| 并行汇合用例 | 6 |
| Task Context 用例 | 11 |
| 并行用例 | 19 |
| Gate 用例 | 15 |
| 失败恢复用例 | 16 |
| 安全用例 | 71 |

### 17.7 F2 实际测试输出

```text
ORCHESTRATION VALIDATION PASSED
schemas=5 state_machines=5
examples: workflows=10 tasks=5 gates=3 approvals=3 evidence=3
schema_positive=24 schema_negative=30
workflow_graph_positive=10 workflow_graph_negative=21
state_transitions_positive=77 state_transitions_negative=245
transition_definitions=77 transition_tests=322 guard_cases=18
parallel_cases=19 task_context_cases=11 gate_cases=15
approval_cases=48 scope_cases=12 expiry_cases=6 path_cases=12
dag_branch_cases=4 parallel_join_cases=6
failure_cases=16 security_cases=71
yaml_blocks_checked=9 registry_ids=7
runtime_behavior=NOT_EXECUTED
```

P1-001 参考 Skill 校验器：

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=1 examples_out=5
cases_input_validated=6 invalid_cases_rejected=3
semver_valid=6 semver_invalid=6
yaml_blocks_checked=9 metadata_examples=1 registry_ids=7
negative_metadata_cases_passed=5
optional_positive_cases_passed=2 optional_negative_cases_passed=9
runtime_behavior=NOT_EXECUTED platform_entries=1
```

其他检查：

- Markdown 链接：59 个文件 0 断链；
- 围栏：无未闭合；
- 全仓 JSON/YAML 解析：无错误；
- 重复键 Loader：生效；
- P0 ADR-001–008：未修改。

### 17.8 F2 修改文件

R1-F2 实施提交 `9bc4933`：10 files changed，+737/−132。

- `docs/standards/approval-orchestration-standard.md`
- `docs/standards/orchestration-state-machine.md`
- `docs/standards/task-standard.md`
- `docs/standards/workflow-standard.md`
- `schemas/orchestration/approval.schema.json`
- `schemas/orchestration/task.schema.json`
- `examples/orchestration/approvals/approval-pure-sa.json`（新增）
- `examples/orchestration/tasks/task-root-running.json`
- `examples/orchestration/tasks/task-root-completed.json`（新增）
- `tests/unit/orchestration/validate_orchestration.py`

本报告文件由 R1-F2 报告提交追加。

### 17.9 报告元数据修订

| 项目 | 值 |
|------|-----|
| R1 实施提交 | `14cd1e0af6775f5dac5df75af24b8b60fa1c5ab7` |
| R1 报告文件所在提交 | `aa81252bfc1646adf938526e472d2281fc34047c` |
| R1-F2 实施提交 | `9bc493362609f36bf2eae4db45c15f0f2ce1487d` |
| F2 实施后累计 | 12 commits，49 files，+7516/−1 |
| F2 报告提交后累计 | 13 commits，50 files（报告 +1） |
| R1-F2 报告提交 SHA | 无法预写自身 SHA；由最终交付消息提供 |
| 最终 PR Head | 由最终交付消息提供（报告提交后更新） |

---

**P1-002-R1-F2 状态：** 整改提交已创建，待推送并等待 ChatGPT 独立复审。未合并 PR #3，未启动 P1-003。
