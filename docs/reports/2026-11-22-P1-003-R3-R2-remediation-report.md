# SDD P1-003-R3-R2 契约整改报告（R2-F1 至 R2-F4）

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-003-R3-R2 remediation |
| 分支 | `feature/p1-003-r2-analysis` |
| 整改基线 | `37d3e211cb3cc793830ed26e2a88072ed96251bc` |
| 整改实施提交 | `2260fd48028c8045d89542232b1db31c9f8a33c4` |
| 整改报告提交 / 当前 HEAD | 由最终交付消息提供（报告无法预写自身 SHA） |
| 远程分支 SHA | 由最终交付消息提供 |
| main / origin/main | `50df231d2de15b4dc33407798cce36f7d2178ee5`（未修改） |
| 工作区 | 报告提交后 clean |
| 验收状态 | **P1-003-R3-R2 暂未通过；R2-F1–R2-F4 完成整改，等待独立复审** |
| 后续阶段 | **R3/R4/R5/R6 NOT STARTED；ADR-009 PROPOSED / NOT ACCEPTED；PR NOT CREATED；MAIN UNMODIFIED** |

> 本轮只整改独立审查发现的四项契约问题，不启动 R3，不创建 Examples/Checklist/Cases/Validator/Runtime，不修改既有 Requirements、Analysis、Orchestration 或 ADR。

---

## 一、Git 证据

| 项目 | 值 |
|------|-----|
| 分支 | `feature/p1-003-r2-analysis` |
| 整改基线 | `37d3e211cb3cc793830ed26e2a88072ed96251bc` |
| 原 R2 实施提交（保留） | `d923e9270fd3ee19f92372e8c5c84e6b941faded`、`f1b464f791a95a87616b2b4b220f5a8552ac9e72` |
| 原 R2 报告提交（保留） | `37d3e211cb3cc793830ed26e2a88072ed96251bc` |
| 整改实施提交 | `2260fd48028c8045d89542232b1db31c9f8a33c4` |
| 整改报告提交 / 当前 HEAD | 由最终交付消息提供 |
| 远程分支 SHA | 由最终交付消息提供 |
| main / origin/main | `50df231d2de15b4dc33407798cce36f7d2178ee5`（未修改） |
| 工作区 | 报告提交后 clean |
| PR / R3–R6 | 未创建 / 未启动 |

整改实施提交：**3 files changed，+51/−19**。

变更文件：

- `docs/standards/design-standard.md`
- `skills/design/SKILL.md`
- `skills/design/schemas/output.schema.json`
- `docs/reports/2026-11-22-P1-003-R3-R2-remediation-report.md`（本报告）

未修改 `skills/design/skill.yaml`、`skills/design/schemas/input.schema.json`、Requirements R1、Analysis R2、P1-001/P1-002、P0、ADR-005/006/009。

---

## 二、R2-F1：AC 映射设计元素约束

### 修改

`skills/design/schemas/output.schema.json` 的 `testStrategy.acceptance_criteria_mapping.items`：

- `criterion_ref`：必填；
- `design_refs`：**必填且 `minItems: 1`**；
- `verification_method`：必填；
- 可选 `exception` 对象：`reason` 必填，`evidence_refs` 可选。

受控例外规则：

- 不允许缺失或空 `design_refs`；
- 无法直接映射时，必须引用一个明确记录该例外的设计元素，并填写 `exception.reason`；不得用空列表或伪数据绕过。

同时更新：

- `docs/standards/design-standard.md §17`：明确每个 AC 映射至少一个设计元素，受控例外必须说明理由；
- `skills/design/SKILL.md` 输出和验收标准：`design_refs` 必填非空。

### 针对性 Schema 测试

使用实际 Output Schema 和 `jsonschema` Draft 2020-12：

```text
valid-ac-mapping: PASS (accepted)
missing-ac-design-refs: PASS (rejected)
empty-ac-design-refs: PASS (rejected)
exception-with-design-refs: PASS (accepted)
exception-empty: PASS (rejected)
```

结论：缺失/空 `design_refs` 已被 Schema 拒绝；受控例外仍必须有设计元素引用和理由。

---

## 三、R2-F2：Complexity 必填口径统一

### 修改

`docs/standards/design-standard.md §3` 输入表：

- `complexity` 由“否”改为 **“是”**；
- 明确由 Orchestration 提供；
- Design 不得自行判定或降低；
- 缺失时 `blocked`；
- 非法枚举时 `failed`/`input_invalid`。

R2 Skill 和 Input Schema 原本已要求 `complexity` 必填，本轮使 Design Standard 与实现口径一致。

---

## 四、R2-F3：输入错误状态规则

### 修改

`docs/standards/design-standard.md §3` 和 `skills/design/SKILL.md` 执行步骤/决策规则/异常表，明确区分：

| 情况 | 处理 |
|------|------|
| Schema 格式/类型错误、Artifact type 错误、SHA 格式错误、非法 enum、未知字段 | `failed` + `input_invalid` |
| 缺少 `requirements_ref`/`analysis_ref`，或需调用方/用户补充的信息 | `needs_input` + `questions` |
| `complexity` 未由 Orchestration 提供 | `blocked` + `precondition_failed` |
| 上游 Artifact 不可读、权限/依赖/外部条件不满足 | `blocked` + `precondition_failed` |
| Requirements/Analysis blocking 业务未决项 | `needs_input`/`blocked` |
| 内部执行异常且不可恢复 | `failed` + `internal_error` |

因此不再把所有“输入缺失/无效”统一归为 `failed`；可补充的信息缺口走 `needs_input`，上游/权限/环境条件走 `blocked`。

---

## 五、R2-F4：Artifact 路径校验责任

`skills/design/SKILL.md` 新增 **“Artifact 路径与身份校验”** 节，明确：

- JSON Schema 只检查 `path` 非空、`type`、`version`、`sha256` 格式；
- Schema 不验证路径规范化、`artifacts/{task-id}/` 目录归属、目录穿越、符号链接越界、任务隔离或内容 SHA 匹配；
- 上述检查必须由调用层、ContextPort/ArtifactManager 或后续语义校验完成；
- 未验证通过的 Artifact 不得读取或继续消费；
- 不得把“Schema 通过”描述为“Artifact 身份、路径和内容已验证”。

---

## 六、验证结果

### 6.1 Schema

```text
input: JSON parse OK, Draft2020-12 OK
output: JSON parse OK, Draft2020-12 OK
```

AC 映射针对性测试见 §二。

### 6.2 P1-001 Reference Skill / Requirements R1

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=2 examples_out=7
cases_input_validated=8 invalid_cases_rejected=6
semver_valid=6 semver_invalid=6
yaml_blocks_checked=12 metadata_examples=1 registry_ids=7
negative_metadata_cases_passed=5
optional_positive_cases_passed=2 optional_negative_cases_passed=9
requirements_semantic_positive=7 requirements_schema_negative=13 requirements_semantic_negative=6
runtime_behavior=NOT_EXECUTED platform_entries=1
```

> 该 Validator 仍只覆盖 requirements-clarity 参考 Skill，不支持 Design；未擅自创建/扩展 Design Validator。

### 6.3 Analysis R2

```text
ANALYSIS VALIDATION PASSED
schemas=2 input_examples=3 output_examples=3
input_positive=3 output_positive=3 cases=3 invalid_cases=4
schema_negative=19 semantic_negative=22
f1_negative=8 f1_positive=1 f2_cases=8 f3_cases=2
trace_negative=6 trace_positive=2
resolved_negative=42 resolved_positive=4
f7_negative=16 f7_negative_passed=16
f7_vectors=30 f7_vectors_passed=30 f7_identity_positive=4
acceptance_retained_negative=6 acceptance_retained_positive=1
runtime_behavior=NOT_EXECUTED
```

### 6.4 P1-002 Orchestration

```text
ORCHESTRATION VALIDATION PASSED
schemas=5 state_machines=5
examples: workflows=10 tasks=5 gates=3 approvals=3 evidence=3
schema_positive=24 schema_negative=32
workflow_graph_positive=10 workflow_graph_negative=21
state_transitions_positive=77 state_transitions_negative=245
transition_definitions=77 transition_tests=322 guard_cases=18
parallel_cases=19 task_context_cases=11 gate_cases=15
approval_cases=111 scope_cases=15 expiry_cases=6 time_fail_closed_cases=15 path_cases=12
dag_branch_cases=4 parallel_join_cases=6
failure_cases=16 security_cases=134
yaml_blocks_checked=12 registry_ids=7
runtime_behavior=NOT_EXECUTED
```

### 6.5 Static

```text
STATIC VALIDATION PASSED json=45 yaml=18 markdown=83
duplicate_json_yaml_keys=checked markdown_links=ok markdown_fences=ok
```

- `git diff --check`：无错误；
- `git show --check`：整改实施提交无错误；
- Markdown 链接/围栏：通过。

---

## 七、验证层次

| 层次 | 结果 |
|------|------|
| Static Validation | 通过 |
| Schema Validation | 通过（Draft 2020-12 + 针对性正/负向实例） |
| Semantic Validation | **未实现**（无 Design Semantic Validator） |
| Runtime | **未执行** |
| Platform Compatibility | **未验证** |

未把静态 Schema 检查描述为 Runtime 或完整 Design 质量验证。

---

## 八、遗留事项

- R2 整体暂未通过独立验收；本报告只证明 F1–F4 整改完成，等待 ChatGPT 重新审查。
- 无 Design Examples / Checklist / Cases / Invalid Cases / 正式 Validator（后续阶段）。
- Design 语义校验、Artifact 路径/内容校验、复杂度实际映射检查尚未实现。
- G2 Artifact binding 仍为 ADR-009 Proposed，未生效。
- P1-002 G3/plan 生产者缺口未关闭，留待 R4/R5。
- `runtime_behavior = NOT_EXECUTED`。

---

## 九、最终状态

**R2-F1–R2-F4 COMPLETE（等待复审）**

**P1-003-R3-R2 暂未通过独立验收**

**R3 NOT STARTED**

**R4 NOT STARTED**

**R5 NOT STARTED**

**R6 NOT STARTED**

**ADR-009 PROPOSED / NOT ACCEPTED**

**PR NOT CREATED**

**MAIN UNMODIFIED**

已停止，等待 ChatGPT 独立复审。
