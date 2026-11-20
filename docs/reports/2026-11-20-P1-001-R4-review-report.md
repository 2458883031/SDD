# SDD P1-001-R4 Optional Capability 校验边界修复报告

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-001-R4 |
| 原始分支 | `feature/p1-001-skill-standard` |
| 原始 HEAD | `fe18b3fbf811e0efe1018948ee0779cd6b173ad0` |
| R4 实施提交 | `4a377c86fbcc4268dd2917c7de67ed76f49e0bcb` |
| 报告提交 | 见最终交付说明（报告内容无法包含自身提交哈希） |
| main | `63be04dfa91ffbae8b53232b84a292978288b08f`（未修改） |
| 执行/监督 | Claude Code |
| 当前状态 | **P1-001-R4 Draft（待 ChatGPT 复审）** |

> 本轮只修复 optional capability 校验边界和小范围测试，不重新设计 P1-001；未修改 main，未创建 PR，未合并，未启动 P1-002，未实现运行时或 Adapter。

---

## 一、执行前 Git 状态

| 检查项 | 实际值 | 预期 | 结果 |
|--------|--------|------|------|
| 当前分支 | `feature/p1-001-skill-standard` | 同左 | ✅ |
| 本地 HEAD | `fe18b3fbf811e0efe1018948ee0779cd6b173ad0` | 同左 | ✅ |
| main | `63be04dfa91ffbae8b53232b84a292978288b08f` | 同左 | ✅ |
| origin/main | `63be04dfa91ffbae8b53232b84a292978288b08f` | 同左 | ✅ |
| origin/feature/p1-001-skill-standard | `fe18b3fbf811e0efe1018948ee0779cd6b173ad0` | 与本地同步 | ✅ |
| 工作区 | `git status --short` 为空 | 干净 | ✅ |

未执行 reset、rebase、强制推送或历史重写。

---

## 二、原缺陷及修复方式

### 2.1 原缺陷

修复前，`skill.yaml` 的 optional capability 检查为：

```python
check(set(opt_caps) <= REGISTRY, "skill.yaml: unknown optional capability")
```

该检查只验证 ID 是否存在于 7-ID Registry，没有验证 ID 是否属于 optional 集合。由于所有 required capability 也都在 Registry 中，以下错误声明会被错误接受：

```yaml
optional_capabilities:
  - skill-discovery
```

`skill-discovery` 属于 Registry，但它是 required capability，不应出现在 optional 列表中。同样，该旧检查也无法拒绝重复 ID 和非列表类型。

### 2.2 修复方式

在 `tests/unit/requirements-clarity/validate_reference_skill.py` 新增 `validate_optional_caps(value)`，并让 `skill.yaml` 校验实际调用它：

```python
opt_errors = validate_optional_caps(opt_caps)
check(not opt_errors, "skill.yaml: invalid optional_capabilities: " + "; ".join(opt_errors))
```

同时为 `requires_capabilities` 增加列表类型保护，避免类型错误导致 traceback，而不是明确的校验失败。

修复范围仅限校验器；未修改 `skill.yaml`、Registry、标准文档、平台 metadata 或历史报告。

---

## 三、OPTIONAL_CAPS 的实际校验逻辑

`OPTIONAL_CAPS` 现状：

```python
OPTIONAL_CAPS = {"approval-port"}
```

`validate_optional_caps()` 的实际规则：

1. 值必须是 `list`，否则返回 `optional_capabilities must be a list`。
2. 列表元素必须全部是字符串，否则返回 `optional_capabilities must contain only strings`。
3. 重复 ID 返回 `optional_capabilities contains duplicate IDs: [...]`。
4. 未知 ID 返回 `optional_capabilities contains unknown IDs: [...]`。
5. required capability 出现在 optional 列表，返回 `optional_capabilities must not contain required capabilities: [...]`。
6. 任何不在 `OPTIONAL_CAPS` 中的 ID，返回 `optional_capabilities must only contain registered optional IDs: [...]`。
7. 空列表允许通过；字段缺失时默认空列表，也允许通过。
8. `OPTIONAL_CAPS` 仍只有 `approval-port`；未新增 Capability ID，未改变 Registry。

关键代码位于 `tests/unit/requirements-clarity/validate_reference_skill.py:60`；`skill.yaml` 调用位于同文件 `:189`。

---

## 四、正向测试结果

| 用例 | 输入 | 结果 |
|------|------|------|
| optional 空列表 | `[]` | ✅ 通过 |
| 合法 optional | `["approval-port"]` | ✅ 通过 |
| 当前参考 Skill manifest | `optional_capabilities: [approval-port]` | ✅ 通过 |

输出计数：

```text
optional_positive_cases_passed=2
```

---

## 五、负向测试结果及失败断言证据

测试真实调用 `validate_optional_caps()`，并检查返回错误中包含指定关键字，不是只检查测试代码是否存在。

| # | 用例 | 输入 | 实际失败断言 |
|---|------|------|--------------|
| 1 | `skill-discovery` 声明为 optional | `["skill-discovery"]` | `must not contain required capabilities: ['skill-discovery']`；`must only contain registered optional IDs: ['skill-discovery']` |
| 2 | `skill-metadata` 声明为 optional | `["skill-metadata"]` | `must not contain required capabilities: ['skill-metadata']`；`must only contain registered optional IDs: ['skill-metadata']` |
| 3 | `tool-invocation` 声明为 optional | `["tool-invocation"]` | `must not contain required capabilities: ['tool-invocation']`；`must only contain registered optional IDs: ['tool-invocation']` |
| 4 | `context-port` 声明为 optional | `["context-port"]` | `must not contain required capabilities: ['context-port']`；`must only contain registered optional IDs: ['context-port']` |
| 5 | `artifact-port` 声明为 optional | `["artifact-port"]` | `must not contain required capabilities: ['artifact-port']`；`must only contain registered optional IDs: ['artifact-port']` |
| 6 | `result-port` 声明为 optional | `["result-port"]` | `must not contain required capabilities: ['result-port']`；`must only contain registered optional IDs: ['result-port']` |
| 7 | 未知 ID | `["unknown-cap"]` | `contains unknown IDs: ['unknown-cap']`；`must only contain registered optional IDs: ['unknown-cap']` |
| 8 | 列表类型错误 | `"approval-port"`（字符串） | `must be a list` |
| 9 | 重复 ID | `["approval-port", "approval-port"]` | `contains duplicate IDs: ['approval-port']` |

输出计数：

```text
optional_negative_cases_passed=9
```

旧逻辑与新逻辑对比：

```text
old check set(['skill-discovery']) <= REGISTRY -> True
new check errors -> ["optional_capabilities must not contain required capabilities: ['skill-discovery']", "optional_capabilities must only contain registered optional IDs: ['skill-discovery']"]
```

旧检查确实会错误接受 required-as-optional；新检查明确失败。

---

## 六、全部回归测试的实际命令和结果

### 6.1 参考 Skill 校验器

```bash
python tests/unit/requirements-clarity/validate_reference_skill.py
```

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=1 examples_out=5
cases_input_validated=6 invalid_cases_rejected=3
semver_valid=6 semver_invalid=6
yaml_blocks_checked=8 metadata_examples=1 registry_ids=7
negative_metadata_cases_passed=5
optional_positive_cases_passed=2 optional_negative_cases_passed=9
runtime_behavior=NOT_EXECUTED platform_entries=1
```

### 6.2 Markdown 链接检查

```bash
node D:\ai_project\claude-assistant\tmp\md-link-check.mjs D:\openclaw\sdd
```

```text
markdown files: 45, broken links (outside code fences): 0
```

### 6.3 JSON/YAML 全量解析与围栏检查

```bash
python -X utf8 - <<'PY'
# 遍历仓库（排除 .git），解析全部 .json/.yaml/.yml；
# 使用重复键 Loader；统计 Markdown 未闭合围栏。
PY
```

```text
json/yaml parse errors: none
fence_imbalance: none
```

### 6.4 Git diff 检查

```text
git diff --check            -> 无空白错误
git diff --name-only        -> 仅 tests/unit/requirements-clarity/validate_reference_skill.py
git diff --stat             -> 1 file changed, 57 insertions(+), 2 deletions(-)
```

### 6.5 16 项回归映射

| # | 回归项 | 实际结果 |
|---|--------|----------|
| 1 | 参考 Skill 结构检查 | ✅ `structure=passed` |
| 2 | JSON Schema Draft 2020-12 | ✅ `schema=Draft202012` |
| 3 | 输入输出示例 | ✅ `examples_in=1 examples_out=5` |
| 4 | 六个 case 输入 | ✅ `cases_input_validated=6` |
| 5 | 三个非法输入拒绝 | ✅ `invalid_cases_rejected=3` |
| 6 | SemVer 正向/反向 | ✅ `semver_valid=6 semver_invalid=6` |
| 7 | YAML 解析与重复键 | ✅ 8 个代码块全部解析；重复键 Loader 生效 |
| 8 | 7 个 Capability ID Registry | ✅ `registry_ids=7` |
| 9 | required / optional 分类 | ✅ `optional_positive_cases_passed=2 optional_negative_cases_passed=9` |
| 10 | Metadata 示例语义 | ✅ `metadata_examples=1`，`negative_metadata_cases_passed=5` |
| 11 | OpenClaw 平台工具映射 | ✅ `invocation.tools == ["read"]`，无 write |
| 12 | Markdown 链接 | ✅ 45 个文件 0 断链 |
| 13 | Markdown 围栏 | ✅ 无未闭合 |
| 14 | JSON/YAML 全量解析 | ✅ 无解析错误 |
| 15 | Git diff | ✅ 仅 1 个校验器文件 |
| 16 | P0 ADR、R1、R2、R3 一致性 | ✅ P0 文件未修改；R1/R2/R3 规则与历史提交保留 |

---

## 七、Claude Code Review 结果

Claude Code 对自身 diff 做了独立复核：

- 旧检查确实只做 Registry 成员判断，`skill-discovery` 会被错误接受；新检查会拒绝。
- `OPTIONAL_CAPS` 已成为实际校验依据，而不是未使用常量。
- 覆盖空列表、合法 optional、6 个 required-as-optional、未知 ID、类型错误、重复 ID。
- 负向测试真实调用 `validate_optional_caps()` 并断言错误信息，不是字符串存在性检查。
- 未引入新依赖、新端口或新 Capability ID；`REGISTRY` 仍为 7 个 ID。
- 未修改 `skill.yaml`、Registry、标准文档、平台 metadata、P0 决策或历史报告。
- 未实现 Adapter、运行时组件或 P1-002。
- 本轮按要求未启用 OpenClaw 大范围架构审查；未将 Claude Code 自审作为 ChatGPT 独立验收。

**结论：** 未发现 Blocker / Major / Minor 级问题；符合 R4-M1/R4-M2。

---

## 八、修改文件清单及 Git diff 统计

### 8.1 R4 实施提交

| 文件 | 修改 |
|------|------|
| `tests/unit/requirements-clarity/validate_reference_skill.py` | 新增 `validate_optional_caps()`、manifest 实际调用、2 个正向 + 9 个负向测试、输出计数 |

```text
1 file changed, 57 insertions(+), 2 deletions(-)
```

### 8.2 报告提交

| 文件 | 修改 |
|------|------|
| `docs/reports/2026-11-20-P1-001-R4-review-report.md` | 新增本报告 |

未修改其他文件。

---

## 九、新实施提交 SHA

```text
4a377c86fbcc4268dd2917c7de67ed76f49e0bcb
```

父提交为 `fe18b3fbf811e0efe1018948ee0779cd6b173ad0`（R3 报告提交）。

---

## 十、报告提交 SHA

报告提交 SHA 由最终交付说明给出。报告内容无法在自身提交前写入自身提交哈希；提交后本地 `HEAD` 与远程分支 SHA 一致。

---

## 十一、远程分支 SHA

- 分支：`feature/p1-001-skill-standard`
- 推送方式：普通 `git push origin feature/p1-001-skill-standard`（非强制）
- 推送后远程 SHA：与报告提交 SHA 相同，最终值见交付说明和 `git ls-remote origin refs/heads/feature/p1-001-skill-standard`。

---

## 十二、main 是否保持不变

| 检查项 | 值 |
|--------|-----|
| 本地 main | `63be04dfa91ffbae8b53232b84a292978288b08f` |
| origin/main | `63be04dfa91ffbae8b53232b84a292978288b08f` |
| PR | 未创建 |
| 合并 | 未执行 |
| P1-002 | 未启动 |

**main 保持不变。**

---

## 十三、剩余风险和运行时测试状态

| 风险 | 状态 |
|------|------|
| 六平台 SDD 语义未实测 | 后续阶段（P2/P7） |
| Adapter 未实现 | 后续阶段 |
| 参考 Skill 未运行时加载、触发和执行 | 未执行 |
| Optional capability 校验仅为静态校验器逻辑 | 未做运行时权限验证 |
| 未来新增 optional ID 需同步 Registry 与 `OPTIONAL_CAPS` | 设计约束 |
| 校验器对参考 Skill 的平台工具映射仍是显式断言 | 新增平台时需扩展 |
| 测试依赖 `jsonschema==4.25.1`、`PyYAML==6.0.3` | 已固定 |

**运行时测试状态：未执行。** `runtime_behavior=NOT_EXECUTED`。本轮没有加载、触发或执行任何 Skill，也没有实现或调用 Adapter、Workflow Runner、GateController 或 ArtifactManager。所有“通过”仅指静态结构、JSON Schema、SemVer、YAML 语义和文档一致性检查通过。

---

**P1-001-R4 状态：** Draft，待 ChatGPT 独立复审。未自行宣布 P1-001 通过，未创建 PR，未合并 main，未启动 P1-002。
