# SDD P1-001-R2 Capability Registry 示例一致性整改报告

| 项目 | 内容 |
|------|------|
| 任务编号 | P1-001-R2 |
| 原始分支 | `feature/p1-001-skill-standard` |
| 原始 HEAD | `b54e7dfa45d313b4d19d7ec78bd311ab234996e0` |
| R2 实施提交 | `3fb05a2d00b25bab8b5072107e5b8b73649a2e6a` |
| 报告提交 | 见最终交付结果（本报告随报告提交入库） |
| main | `63be04dfa91ffbae8b53232b84a292978288b08f`（未修改） |
| 执行/监督 | Claude Code |
| OpenClaw 角色 | 既有 SDD 会话，只读交叉审查 |
| 当前状态 | **P1-001-R2 Draft（待 ChatGPT 复审）** |

> 本轮只修复 R2-M1/R2-m1，不重新设计已通过的 M1/M2/M4；未修改 main，未创建 PR，未合并，未启动 P1-002。

---

## 一、原始问题

| 编号 | 问题 | 级别 |
|------|------|------|
| R2-M1 | `skill-versioning-standard.md` §3.2 有重复 `optional_capabilities`；§8 仍使用 `tool-port`；Capability 示例不一致 | Major |
| R2-m1 | 平台工具映射边界未明确：`file-read`、`artifact-port`、OpenClaw `write`、`fs:write:project` 的关系 | Minor |

---

## 二、修正内容

### R2-M1：Capability Registry 示例

**文件：** `docs/standards/skill-versioning-standard.md`

- §3.2 删除重复的 `optional_capabilities`。
- `requires_capabilities` 补齐为 Registry 的必需能力：
  - `skill-discovery`
  - `skill-metadata`
  - `tool-invocation`
  - `context-port`
  - `artifact-port`
  - `result-port`
- `optional_capabilities` 仅保留 `approval-port`。
- §8 示例：
  - `tool-port` → `tool-invocation`；
  - 补齐 `skill-metadata`、`context-port`、`result-port`；
  - 增加 `optional_capabilities: [approval-port]`。

**同步一致性：**

- `skills/requirements-clarity/skill.yaml` 的 required capabilities 补齐 `result-port`。
- `docs/standards/skill-metadata-standard.md` 示例同步补齐 `result-port`。
- `platforms/openclaw/skill-metadata.yaml` 的 `capabilities` 增加 `result-port: true`。
- 未创建任何新 Capability ID。

### R2-m1：平台工具映射边界

**修改文件：**

- `docs/architecture/platform-adapter-architecture.md`
- `docs/standards/skill-security-standard.md`
- `docs/standards/skill-metadata-standard.md`
- `skills/requirements-clarity/skill.yaml`
- `platforms/openclaw/skill-metadata.yaml`

**明确规则：**

| 核心声明 | 映射 | 说明 |
|----------|------|------|
| `requires.tools: [file-read]` | ToolPort → OpenClaw `read` | Skill 可见的 ToolPort 工具 |
| `artifact-port` | ContextPort | Artifact 读写；适配器内部使用 OpenClaw `write`，但不暴露为 Skill Tool |
| `fs:write:project` | 安全控制层 | 权限 scope；与 Artifact 路径限制同时生效 |

- OpenClaw `write` 是 ContextPort 的内部平台实现，不是该 Skill 的 ToolPort 工具。
- `platforms/openclaw/skill-metadata.yaml` 的 `invocation.tools` 改为 `[read]`，并注明 write 为 ContextPort-internal。
- 平台工具映射不得绕过 `requires.tools`、`requires.permissions`、R0–R4 或 Artifact 路径限制。
- 如 Skill 需要通用工作区写入，必须显式声明 `file-write` Tool；参考 Skill 不声明。

### 自动检查增强

`tests/unit/requirements-clarity/validate_reference_skill.py` 新增：

1. 唯一 `REGISTRY` 集合（7 个 ID）。
2. 校验 skill.yaml required/optional capabilities 均来自 Registry。
3. 校验平台 metadata capabilities 均来自 Registry。
4. 扫描 10 个当前规范性文件，拒绝 `tool-port` 等废弃 ID。
5. 使用 `UniqueKeyLoader` 拒绝 YAML 重复键。
6. 解析 `docs/standards/*.md` 中所有 YAML 代码块（8 个）。
7. 校验 OpenClaw `invocation.tools == [read]`，artifact/result capability 为 true。
8. 保留结构、Schema、示例、cases、invalid cases、SemVer 检查。

---

## 三、修改文件

| 文件 | 修改 |
|------|------|
| `docs/standards/skill-versioning-standard.md` | 去重 optional、修正 tool-port、补齐 result-port |
| `docs/standards/skill-metadata-standard.md` | 示例补齐 result-port；invocation.tools 说明 |
| `docs/standards/skill-security-standard.md` | 增加 ToolPort/ContextPort 映射与不可绕过规则 |
| `docs/architecture/platform-adapter-architecture.md` | 增加 §2.2 文件写入边界表 |
| `skills/requirements-clarity/skill.yaml` | result-port；file-read 注释 |
| `platforms/openclaw/skill-metadata.yaml` | tools `[read]`；result-port capability |
| `tests/unit/requirements-clarity/validate_reference_skill.py` | Registry/YAML/工具映射检查 |

**R2 实施提交：** `3fb05a2d00b25bab8b5072107e5b8b73649a2e6a`（7 files changed, 95 insertions, 9 deletions）。

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
yaml_blocks_checked=8 registry_ids=7
runtime_behavior=NOT_EXECUTED platform_entries=1
```

其他检查：

| 检查 | 结果 |
|------|------|
| Markdown 链接 | ✅ 0 断链（44 个文件） |
| Markdown 围栏 | ✅ 无未闭合 |
| JSON/YAML 解析 | ✅ 无错误 |
| YAML 重复键 | ✅ `UniqueKeyLoader` 检查 8 个示例块 |
| Capability Registry 全局一致性 | ✅ 7 个 ID；无 `tool-port` |
| 平台工具映射 | ✅ `file-read → read`；write 为 ContextPort 内部实现 |
| P0 决策 | ✅ 未修改 |
| 运行时测试 | ❌ 未执行（明确标注） |

---

## 五、Capability Registry 全局检查

| ID | Port | required | skill.yaml | platform metadata |
|----|------|----------|------------|-------------------|
| skill-discovery | DiscoveryPort | ✅ | ✅ | true |
| skill-metadata | MetadataPort | ✅ | ✅ | true |
| tool-invocation | ToolPort | ✅ | ✅ | true |
| context-port | ContextPort | ✅ | ✅ | true |
| artifact-port | ContextPort | ✅ | ✅ | true |
| result-port | ResultPort | ✅ | ✅ | true |
| approval-port | ApprovalPort | optional | optional | false |

- 无新增 ID。
- 无 `tool-port` 残留。
- `artifact-port` 与 `context-port` 均映射到 ContextPort，未新增端口。
- `requirements-clarity` 的文件写入通过 `artifact-port`/ContextPort。

---

## 六、OpenClaw 独立审查

- **结论：** **0 Blocker、0 Major、0 Minor**。
- OpenClaw 确认：
  - §3.2 无重复 optional_capabilities；
  - §8 已使用 `tool-invocation`；
  - 示例与 skill.yaml/metadata/Registry 一致；
  - `file-read → read`、`write` 为 ContextPort 内部实现、`fs:write:project` 与路径限制共同生效；
  - 测试覆盖 Registry ID、废弃 ID、YAML 重复键、平台 metadata；
  - 未修改 P0 决策、M1/M2/M4；未批量创建 Skill、未实现运行时、未启动 P1-002。
- OpenClaw 未修改任何文件。

---

## 七、Claude Code Review 结论

- R2-M1、R2-m1 均已修复。
- Capability Registry 的 7 个 ID 在所有当前规范性文件与参考 Skill 中一致。
- 无新增抽象端口；`artifact-port` 仍由 ContextPort 提供。
- 工具映射边界明确：Skill 只见 `file-read → read`；write 仅作为 ContextPort 内部实现。
- 测试实际执行，YAML 重复键/废弃 ID/平台映射均有自动检查。
- 未修改 P0 决策，未扩大任务范围。

---

## 八、剩余风险

| 风险 | 状态 |
|------|------|
| 六平台 SDD 语义未实测 | P7 |
| Adapter 未实现 | P2/P7 |
| 参考 Skill 未运行时加载/触发 | 后续验证 |
| 平台工具映射需在真实适配器中验证 | P2/P7 |
| 测试依赖 `jsonschema==4.25.1`/`PyYAML==6.0.3` | 已记录 |
| 运行时校验器/资产库/发布系统未实现 | P2/P7 |

---

## 九、Git 状态

```text
分支: feature/p1-001-skill-standard
原始 HEAD: b54e7df
R2 实施提交: 3fb05a2
main: 63be04d（未修改）
PR/合并: 未创建、未合并
P1-002: 未启动
```

本报告随后续报告提交入库；最终 HEAD SHA 见交付结果。

---

**P1-001-R2 状态：** Draft，待 ChatGPT 复审。未自行宣布 P1-001 通过。
