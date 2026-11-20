# SDD P1-001 通用 Skill 规范与平台扩展标准实施报告

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-001 |
| 任务名称 | 通用 Skill 规范与平台扩展标准设计 |
| 基线分支 | `main` |
| 基线提交 | `63be04dfa91ffbae8b53232b84a292978288b08f` |
| 开发分支 | `feature/p1-001-skill-standard` |
| 执行/监督 | Claude Code |
| OpenClaw 角色 | 既有 SDD 会话，只读交叉审查 |
| 当前状态 | **P1-001 Draft（待 ChatGPT 评审）** |
| 完成时间 | 2026-11-20 |

> 本任务建立 P1 Skill 标准与一个最小参考 Skill；未批量创建 Skill，未实现 Orchestration/Workflow Runner/GateController/ArtifactManager，未启动 P1-002。

---

## 一、执行摘要

P1-001 在 P0 已验收架构上建立可执行的 Skill 规范：

- **核心规范**：Skill 定义、边界、目录、SKILL.md 正文结构、生命周期。
- **元数据分层**：核心 `SKILL.md` 只保留 name/description/requires；`skill.yaml` 管版本/依赖；`platforms/<platform>/skill-metadata.yaml` 管平台映射。
- **IO 契约**：JSON Schema Draft 2020-12，输入/输出/错误结构与 Artifact 引用。
- **安全规范**：R0–R4、SA、G6 职责分离；Skill 只声明权限，不授予权限。
- **版本规范**：SemVer 2.0.0、依赖、生命周期、废弃与归档。
- **平台适配**：六平台能力矩阵与证据等级；OpenClaw 仅 CLI 能力 Verified。
- **参考 Skill**：`skills/requirements-clarity/`，含 Schema、测试、示例、平台元数据。
- **ADR-007/008**：记录 Skill 标准与平台适配决策。

---

## 二、基线确认

- 分支：`feature/p1-001-skill-standard`（从 `main` `63be04d` 创建）
- 基线：`main` = `63be04d`（P0 最终验收合并提交）
- P0 证据分支全部保留
- 执行前工作区：干净
- P0 已验收内容：已在 main
- 无并行 P1 分支
- 未修改 `main`、未合并、未启动 P1-002

---

## 三、交付物

### 3.1 标准文档（5）

| 文件 | 内容 |
|------|------|
| `docs/standards/skill-standard.md` | Skill 定义、边界、目录、SKILL.md 正文、执行/组合/质量原则 |
| `docs/standards/skill-metadata-standard.md` | 核心/通用/平台元数据分层、字段归属、加载校验、上下文成本 |
| `docs/standards/skill-io-contract.md` | JSON Schema 2020-12、输入输出/错误、Artifact 引用、兼容规则 |
| `docs/standards/skill-security-standard.md` | R0–R4、Tool、SA/G6、审计、安全测试 |
| `docs/standards/skill-versioning-standard.md` | SemVer、依赖、生命周期、废弃/归档 |

### 3.2 架构文档（3 修改/新增）

| 文件 | 内容 |
|------|------|
| `docs/architecture/skill-architecture.md` | 保留 P0 架构关系，追加 P1-001 规范落地章节 |
| `docs/architecture/platform-adapter-architecture.md` | 六个端口、适配器接口、能力缺失降级 |
| `docs/architecture/platform-compatibility-matrix.md` | 六平台能力矩阵与证据等级 |

### 3.3 决策记录（2）

- `docs/decisions/ADR-007-skill-standard.md`：核心规范 + 分层元数据。
- `docs/decisions/ADR-008-platform-adapter.md`：端口/适配器 + 证据规则。

### 3.4 参考 Skill（1）

`skills/requirements-clarity/`：

```text
SKILL.md
skill.yaml
CHANGELOG.md
schemas/input.schema.json
schemas/output.schema.json
examples/example-input.json
examples/example-output.json
references/requirements-checklist.md
tests/cases.yaml
```

- 体现通用 metadata、IO 契约、执行步骤、异常处理、安全约束、验收标准、测试用例。
- 平台适配示例：`platforms/openclaw/skill-metadata.yaml`。
- 结构/契约测试：`tests/unit/requirements-clarity/validate_reference_skill.py`。

### 3.5 报告

- 本报告：`docs/reports/2026-11-20-P1-001-skill-standard-report.md`

---

## 四、关键设计决策

### 4.1 Skill 核心定义

Skill 是可复用的专业能力单元，不是 Agent、Workflow、编排引擎或 Tool。与 Agent/Orchestration/Workflow/Tool/Platform Adapter 的关系见 `skill-standard.md §2`。

### 4.2 三层元数据

| 层 | 位置 | 内容 |
|----|------|------|
| L1 核心 | `SKILL.md` Frontmatter | name/description/requires |
| L2 通用清单 | `skill.yaml` | version/status/dependencies/compatibility |
| L3 平台 | `platforms/<platform>/skill-metadata.yaml` | discovery/trigger/requirements/invocation/approval/context |

- 核心 Frontmatter 不写版本和平台字段。
- 平台字段不能改变核心语义。
- 缺失平台能力 → `not_ready`/降级，不静默改变规则。

### 4.3 IO 契约

- JSON Schema Draft 2020-12。
- `schemas/input.schema.json` + `schemas/output.schema.json`。
- 统一输出信封：status/data/artifacts/errors/evidence。
- 标准错误码与 Artifact 引用（路径+版本+sha256）。
- 契约兼容规则：新增可选字段 Minor；删除/改语义 Major。

### 4.4 执行与异常

- Skill 负责输入校验、步骤执行、输出和失败报告。
- Orchestration 负责 DAG、超时、全局重试、Task Context 状态、G 门禁暂停。
- Skill 返回 `ok/needs_input/needs_approval/blocked/failed`，不自行批准。
- 重试/幂等/中断恢复由 Workflow 与 Skill 的声明共同处理；Skill 不调度整个 Workflow。

### 4.5 权限与安全

- R0–R4、SA、G6 以 P0 安全架构和 ADR-006 为准。
- Skill 只声明 `requires.permissions`，实际授权由安全控制层执行。
- G6 仅实际生产部署触发，不是所有 Skill 的通用审批步骤。
- 工具白名单、文件/Shell/网络边界、凭证保护和审计要求写入安全标准。
- 运行时安全机制未实现（P2/P5）。

### 4.6 平台适配

- 六端口：Discovery/Metadata/Tool/Context/Approval/Result。
- 能力缺失时降级或 `not_ready`；不得猜测替代工具。
- 平台元数据独立目录；核心 Skill 不读取平台字段。
- 六平台证据等级：Verified / Documented / Assumed / Unsupported / Unknown。

### 4.7 版本与生命周期

- SemVer 2.0.0。
- `draft → review → tested → published → deprecated → retired → archived`。
- 依赖 Skill/Tool/通用能力；平台名称不进入核心依赖。
- 发布需 Schema、测试、示例、变更记录。

### 4.8 测试与质量

- Skill 级测试：元数据、结构、Schema、触发、IO、正常/异常、边界、安全、平台兼容、回归。
- Skill 测试结果不等同于整个 Workflow 的 G4/G5；G4/G5 仍由 ADR-006 定义。
- 参考 Skill 通过结构/契约测试；未做运行时 Agent 执行测试。

---

## 五、平台兼容性研究结果

| 平台 | 主要证据 | 当前状态 |
|------|----------|----------|
| OpenClaw | 官方 Skill 文档 + 本地 CLI | 格式/发现/工具/生命周期 Documented；CLI 清单/会话 Verified；SDD 语义 Unknown |
| Claude Code | 官方 Agent Skills 文档 | 核心能力 Documented；未实测 |
| Codex | 官方 Codex Skills 文档 | 核心能力 Documented；权限/审批/运行环境 Unknown |
| Cursor | 官方 Skills/Rules 文档 | 核心能力 Documented；权限/审批 Unknown |
| Gemini CLI | 官方 Skills 文档 | 核心能力 Documented；激活同意 Documented；权限/上下文 Unknown |
| OpenCode | 官方 Skills 文档 | 核心能力 Documented；permission allow/deny/ask Documented；references/scripts Unknown |

**重要：** 除 OpenClaw CLI 清单/会话能力外，没有任何平台在 SDD 语义下完成 Verified。Documented/Assumed/Unknown 不得写成 Verified。

证据 URL 见 [platform-compatibility-matrix.md](../architecture/platform-compatibility-matrix.md) §4。

---

## 六、参考 Skill 验证

### 6.1 结构/契约测试

命令：

```bash
python tests/unit/requirements-clarity/validate_reference_skill.py
```

结果：

```text
REFERENCE SKILL VALIDATION PASSED
structure=passed schema=Draft202012 examples_in=1 examples_out=5
cases_input_validated=6 invalid_cases_rejected=3
semver_valid=6 semver_invalid=6
runtime_behavior=NOT_EXECUTED platform_entries=1
```

覆盖：

- SKILL.md Frontmatter 仅 name/description/requires；
- `skill.yaml` SemVer/status/schema_version；
- 输入/输出 JSON Schema 合法（Draft 2020-12）；
- 全部 example-input/example-output 通过 Draft 2020-12 校验（5 个状态输出示例）；
- tests/cases.yaml 中 6 个输入全部通过 input.schema.json；3 个 invalid 输入被拒绝；
- SemVer 正反向测试 6/6；
- 平台元数据条目完整；
- 6 个测试用例（正常、缺失验收标准、冲突、安全敏感、空输入、不可验证词）；
- 平台元数据条目完整。

### 6.2 未做的测试

- 未在 OpenClaw 中实际加载/触发该 Skill（未修改 OpenClaw 配置/workspace）。
- 未执行 Agent 端到端测试或 Workflow 测试。
- 未验证六平台运行时行为。
- 这些属于 P2/P7 或后续验证任务。

---

## 七、自动化检查

| 检查项 | 结果 |
|--------|------|
| Markdown 内部链接 | ✅ 0 断链（42 个文件） |
| Markdown 代码块围栏 | ✅ 无未闭合 |
| 参考 Skill 结构/契约测试 | ✅ PASSED |
| 核心 Frontmatter 无平台字段 | ✅ |
| Schema/示例一致 | ✅ |
| 六平台清单统一 | ✅ |
| 未批量创建 Skill | ✅ 仅 1 个参考 Skill |
| 未实现运行时组件 | ✅ |
| P1-002 未启动 | ✅ |

---

## 八、OpenClaw 独立审查

- **审查方式：** 既有 SDD 会话（`agent:main:dashboard:cbd2f2e9-…`）只读检查，不修改文件、不提交 Git。
- **审查结论：** **0 Blocker、0 Major、1 Minor**。
- OpenClaw 确认：
  - Skill 与 Agent/Orchestration/Workflow/Tool/Platform Adapter 边界清晰；
  - 核心 SKILL.md 仍只含 name/description/requires，版本与平台字段分离；
  - 目录、IO Schema、执行责任、安全标准、平台证据等级、版本/生命周期、测试分级均完整；
  - 六平台清单一致，未把 Documented/Assumed/Unknown 写成 Verified；
  - 未批量创建 Skill，未实现运行时组件，未修改 P0 决策。
- **Minor：** 参考 Skill 的测试脚本是结构/元数据 + Draft 2020-12 Schema + SemVer 测试，不是运行时安全测试。Claude Code 复核：成立；本报告 §6.2 已明确未做运行时/安全测试，§7 也标注为“参考 Skill 结构/契约测试”。该限制属于 P2/P5/P7 范围。
- OpenClaw 未修改任何文件；其结论仅作为交叉检查输入，最终判断由 ChatGPT 复审决定。

---

## 九、遗留问题与风险

| 问题 | 状态 |
|------|------|
| 六平台 SDD 语义未实测 | P7 |
| 参考 Skill 未运行时加载/触发 | 后续验证 |
| Skill 校验器/资产库/发布系统 | P2/P7 |
| Orchestration/Workflow Runner/GateController/ArtifactManager | 未实现 |
| 平台元数据字段可能需按实测调整 | P7 |
| 历史 P0 文档与 P1 标准的引用 | 已用链接/说明区分 |

---

## 十、Git 状态与下一步

- 分支：`feature/p1-001-skill-standard`
- 基线：`main` `63be04d`
- 未修改 main，未合并
- 完成后提交并推送独立分支（提交 SHA 见交付结果）
- 不启动 P1-002
- 等待 ChatGPT 评审

```text
新增：5 个 standards + 2 个 architecture + 2 个 ADR + 参考 Skill + 测试
修改：skill-architecture.md、platform-architecture.md（仅补充 P1 引用/说明）
```

---

**当前状态：** P1-001 Draft，待 ChatGPT 评审。未自行宣布验收通过。
