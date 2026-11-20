# SDD P1-001-R1 Skill 标准一致性整改报告

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-001-R1 |
| 原始提交 | `bac9d81d57541198037fcca89580be0813a22f3a` |
| 原始基线 | `63be04dfa91ffbae8b53232b84a292978288b08f` |
| 分支 | `feature/p1-001-skill-standard` |
| R1 实施提交 | `d96dc5ae4a6462b470c7fb61f7380621f8bc6dd6` |
| 报告提交 | 见最终交付结果（本报告随报告提交入库） |
| 执行/监督 | Claude Code |
| OpenClaw 角色 | 既有 SDD 会话，只读交叉审查 |
| 当前状态 | **P1-001-R1 Draft（待 ChatGPT 复审）** |

> 本轮在原分支新增整改提交，保留 `bac9d81`；未修改 `main`，未创建 PR，未合并，未启动 P1-002。

---

## 一、原始评审问题

| 编号 | 问题 | 级别 |
|------|------|------|
| R1-M1 | 输出契约在 `skill-io-contract.md`、`SKILL.md`、`output.schema.json`、示例、报告中不一致 | Major |
| R1-M2 | 六平台 `requires` 兼容性证据混淆平台原生能力与 SDD Adapter | Major |
| R1-M3 | Capability 标识不统一（tool-port/context-port/artifact-port 等混用） | Major |
| R1-M4 | `skill-architecture.md` 历史口径与当前 P1 标准混杂 | Major |
| R1-m1 | Schema 测试未使用真正的 Draft 2020-12 校验库，未校验 Schema 本身 | Minor |
| R1-m2 | SemVer 校验不够严格 | Minor |

---

## 二、逐项修正

### R1-M1：统一输出契约

**权威定义：** `docs/standards/skill-io-contract.md §5.1`。

统一输出信封：

```json
{
  "status": "ok|needs_input|needs_approval|blocked|failed",
  "data": {},
  "artifacts": [],
  "errors": [],
  "evidence": []
}
```

- `artifacts` 是唯一产物字段；`artifact_refs` 已废弃。
- `evidence` 结构：`{type, ref, sha256?, note?}`，type 取 `test|review|command|artifact|other`。
- 状态合法输出：
  - `ok`：`data.requirements` 完整（goal/scope/constraints/acceptance_criteria/non_goals）。
  - `needs_input`：`data.questions` 至少 1 条；`data.requirements` 可为部分对象，不强制 `acceptance_criteria`。
  - `needs_approval`：`data.approval_request` 必需（gate_or_sa/reason/impact/rollback）。
  - `blocked`：`data.blocked_reason` 必需。
  - `failed`：`errors` 至少 1 个；不要求成功状态的 `requirements`。
- `skills/requirements-clarity/SKILL.md`、`schemas/output.schema.json`、5 个输出示例与 P1 报告均按此对齐。
- `output.schema.json` 使用 `allOf` + `if/then` 按状态约束 `data`；`requirementsPartial` 不强制 acceptance_criteria；failed 不要求 data。

### R1-M2：平台 requires 证据

**修改：** `docs/architecture/platform-compatibility-matrix.md`

- 拆分：
  - `name/description` 原生 Frontmatter；
  - `requires` 原生 Frontmatter；
  - SDD Adapter 解析 `requires`（设计）；
  - 平台原生 metadata 扩展；
  - SDD 平台 metadata 映射（设计）；
  - SDD 全栈语义验证。
- `requires` 原生 Frontmatter 在六平台均为 **Unknown**；未把 SDD Adapter 设计写成平台原生。
- OpenClaw 明确区分顶层 `requires` 与 `metadata.openclaw`。
- Claude Code `allowed-tools`、Codex `agents/openai.yaml`、Cursor Rules/插件、Gemini 扩展、OpenCode metadata/permission 分别作为平台原生扩展说明。
- SDD Adapter 解析统一标记 **Assumed**（未实现），并注明状态来源规则。
- 保留所有 SDD 语义 **Unknown**。

### R1-M3：统一 Capability Registry

**权威定义：** `docs/architecture/platform-adapter-architecture.md §2.1`。

| Capability ID | 映射端口 | 默认要求 | 缺失行为 |
|---------------|----------|----------|----------|
| `skill-discovery` | DiscoveryPort | required | unsupported/not_ready |
| `skill-metadata` | MetadataPort | required | not_ready |
| `tool-invocation` | ToolPort | required | blocked |
| `context-port` | ContextPort | required | blocked |
| `artifact-port` | ContextPort（Artifact 读写，不新增端口） | required | blocked/只读降级 |
| `approval-port` | ApprovalPort | optional（需要审批时 required） | blocked |
| `result-port` | ResultPort | required | failed |

- `artifact-port` 由 ContextPort 提供，不新增抽象端口。
- `requirements-clarity` 的文件写入通过 `artifact-port`（ContextPort）完成，已在 SKILL.md 安全约束中说明。
- `skill.yaml` 的 `requires_capabilities`：`skill-discovery`、`skill-metadata`、`tool-invocation`、`context-port`、`artifact-port`；optional：`approval-port`。
- `platforms/openclaw/skill-metadata.yaml` 增加 `capabilities` 块，与 `invocation.tools` 对齐。
- 元数据标准与版本标准改为引用统一 Registry。

### R1-M4：清理历史口径

**修改：** `docs/architecture/skill-architecture.md`

- 顶部增加 P1-001-R1 文档状态：§1–§10 为 P0 历史基线，§11 与 P1 standards 为当前有效规则。
- §3.2 平台元数据示例标记为 P0 历史示例，当前字段指向 metadata standard 与 Capability Registry。
- §3.3 字段处理规则增加当前 P1 指向。
- §8.2 兼容性状态标记为历史摘要，当前证据指向 platform-compatibility-matrix。
- Domain Organization 的 `SKILL.md # 工作流 + 选择逻辑` 修正为“能力入口 + 选择逻辑”，并说明 Skill 不实现 Workflow。
- 新增 §11.3 历史口径，明确旧示例不可复制、当前规则以 P1 为准。

### R1-m1：Schema 测试可信度

**修改：** `tests/unit/requirements-clarity/validate_reference_skill.py`、`requirements.txt`

- 使用 `jsonschema==4.25.1` 的 `Draft202012Validator`。
- 执行 `Draft202012Validator.check_schema()` 校验 Schema 本身。
- 校验全部 example-input / example-output（5 个状态输出示例）。
- 校验 `tests/cases.yaml` 中 6 个 case 输入。
- `tests/invalid-cases.yaml` 校验 3 个非法输入被拒绝。
- 明确输出 `runtime_behavior=NOT_EXECUTED`；不把运行时行为报告为已测试。
- 依赖记录：`jsonschema==4.25.1`、`PyYAML==6.0.3`。

### R1-m2：严格 SemVer

- 使用 SemVer 2.0.0 正则；覆盖正常版本、prerelease、build metadata、前导零、非法字符、不完整版本。
- 正向 6 例、反向 6 例，全部通过。

---

## 三、修改文件

| 文件 | 修改 |
|------|------|
| `docs/standards/skill-io-contract.md` | 输出信封、状态合法输出、artifacts/evidence、废弃 artifact_refs |
| `docs/standards/skill-metadata-standard.md` | Capability Registry 引用、平台 metadata capabilities 示例 |
| `docs/standards/skill-versioning-standard.md` | Capability Registry 引用 |
| `docs/architecture/platform-adapter-architecture.md` | Capability Registry、artifact-port 由 ContextPort 提供 |
| `docs/architecture/platform-compatibility-matrix.md` | 拆分 name/description 与 requires、平台原生/Adapter 区分 |
| `docs/architecture/skill-architecture.md` | 历史口径标记、当前规则指向、Skill/Workflow 示例修正 |
| `docs/reports/2026-11-20-P1-001-skill-standard-report.md` | 输出契约/测试结果同步 |
| `skills/requirements-clarity/SKILL.md` | 输出信封与 artifact-port 写入说明 |
| `skills/requirements-clarity/skill.yaml` | 统一 capability 清单 |
| `skills/requirements-clarity/schemas/output.schema.json` | 状态条件 Schema 与统一信封 |
| `skills/requirements-clarity/examples/example-output*.json` | 5 个状态示例 |
| `skills/requirements-clarity/tests/cases.yaml` | 6 个合法输入 + 输出示例映射 |
| `skills/requirements-clarity/tests/invalid-cases.yaml` | 3 个非法输入测试 |
| `platforms/openclaw/skill-metadata.yaml` | capabilities 块 |
| `tests/unit/requirements-clarity/validate_reference_skill.py` | Draft 2020-12 + SemVer 测试 |
| `tests/unit/requirements-clarity/requirements.txt` | 依赖版本记录 |

**R1 实施提交：** `d96dc5ae4a6462b470c7fb61f7380621f8bc6dd6`（20 files changed, 507 insertions, 199 deletions）。

---

## 四、测试命令与真实结果

```bash
python tests/unit/requirements-clarity/validate_reference_skill.py
```

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=1 examples_out=5
cases_input_validated=6 invalid_cases_rejected=3
semver_valid=6 semver_invalid=6
runtime_behavior=NOT_EXECUTED platform_entries=1
```

其他检查：

| 检查 | 结果 |
|------|------|
| Markdown 链接 | ✅ 0 断链（43 个文件） |
| Markdown 围栏 | ✅ 无未闭合 |
| JSON/YAML 解析 | ✅ 无错误 |
| Capability Registry 一致性 | ✅ skill.yaml / metadata / adapter IDs 一致 |
| 元数据分层 | ✅ 核心仅 name/description/requires |
| 六平台证据等级 | ✅ 未把 Adapter 写成原生；SDD 语义 Unknown |
| 修改范围 | ✅ 仅 P1 文档/参考 Skill/测试；未改 P0 决策 |
| 运行时测试 | ❌ 未执行（明确标注） |

---

## 五、OpenClaw 独立审查

- **结论：** **0 Blocker、0 Major、0 Minor**。
- OpenClaw 确认：
  - M1 输出信封/状态条件/示例一致；
  - M2 平台原生与 Adapter 证据已分离；
  - M3 Capability Registry 与端口映射完整；
  - M4 历史口径已标记；
  - m1 使用 `jsonschema==4.25.1` 的 Draft202012Validator；
  - m2 SemVer 正反向覆盖；
  - 未修改 P0 决策、未批量创建 Skill、未实现运行时、未启动 P1-002。
- OpenClaw 未修改任何文件。

---

## 六、Claude Code Review 结论

- 四项 Major（M1–M4）和两项 Minor（m1–m2）均已处理。
- 输出契约只有一个权威定义；其余文件引用/对齐。
- 平台矩阵不再把 `requires` 或 Adapter 设计写成平台原生。
- Capability Registry 统一，`artifact-port` 明确由 ContextPort 提供。
- 历史 P0 文档保留，但不再伪装当前标准。
- 未产生新的跨文档冲突；未扩大任务范围；未修改 P0 已验收决策。
- 测试为实际执行结果，运行时行为未冒充已测试。

---

## 七、剩余风险

| 风险 | 状态 |
|------|------|
| 六平台 SDD 语义未实测 | P7 |
| Adapter 未实现 | P2/P7 |
| 参考 Skill 未在 OpenClaw 实际加载/触发 | 后续验证 |
| 平台元数据字段可能随实测调整 | P7 |
| jsonschema/PyYAML 为本地测试依赖 | 已记录版本；CI 需按 requirements.txt 安装 |
| 运行时校验器/资产库/发布系统未实现 | P2/P7 |

---

## 八、Git 状态

```text
分支: feature/p1-001-skill-standard
原始提交: bac9d81
R1 实施提交: d96dc5a
main: 63be04d（未修改）
PR/合并: 未创建、未合并
P1-002: 未启动
```

本报告随报告提交入库；最终分支 HEAD SHA 见交付结果。

---

**P1-001-R1 状态：** Draft，待 ChatGPT 复审。未自行宣布 P1-001 通过。
