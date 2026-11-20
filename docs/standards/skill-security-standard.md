# SDD Skill 权限与安全标准

**状态：** P1-001 Draft（待 ChatGPT 评审）
**适用范围：** 所有 SDD Skill 的权限声明、工具调用、审批与安全测试
**权威关系：** 本文件定义 Skill 层安全规范；R0–R4、SA、G6 的权威定义见 [security-architecture.md](../architecture/security-architecture.md) 与 [ADR-006](../decisions/ADR-006-quality-gates.md)。

---

## 1. 核心原则

1. **默认拒绝**：Skill 未声明的权限不可用。
2. **最小权限**：只声明完成当前能力所需的最小权限。
3. **声明不等于授予**：`requires.permissions` 只是需求；实际授权由安全控制层执行。
4. **职责分离**：Skill、Agent、Orchestration、平台适配器都不得自行提升权限。
5. **可审计**：工具调用、权限使用、审批和失败必须留下记录。
6. **未实现不冒充**：P0/P1 只定义规则，不宣称运行时安全机制已实现。

---

## 2. R0–R4 权限等级

遵循 P0 定义：

| 权限 | 定义 | Skill 示例 |
|------|------|------------|
| R0 | 只读 | 读取允许的项目文件、查看状态 |
| R1 | 普通写入 | 生成需求/设计文档、修改项目文件 |
| R2 | 受控执行 | 运行测试、构建、受限脚本 |
| R3 | 高风险操作 | 部署、数据库迁移、外部网络写操作、非生产环境管理 |
| R4 | 严重敏感操作 | 生产数据破坏性操作、敏感凭证读取、不可逆高危操作 |

Skill 只能在 `requires.permissions` 中声明类别；不得声明“已获授权”。

```yaml
requires:
  permissions: [fs:read:project, fs:write:project, shell:exec:test]
```

---

## 3. 工具调用

### 3.1 ToolPort

Skill 通过统一的 ToolPort 调用工具：

- 文件：read/write/edit/list（受路径边界限制）
- Shell：受控命令执行
- Git：只读/受控写
- 测试：运行测试/构建
- 网络：默认拒绝，按 allowlist
- 浏览器/其他平台工具：由适配器映射

### 3.2 规则

- 只调用 `requires.tools` 中声明的工具类别。
- 不允许直接调用平台 SDK 或平台 CLI 绕过 ToolPort。
- 平台工具映射不得绕过 `requires.tools`、`requires.permissions`、R0–R4 或 Artifact 路径限制。
- `file-read` 通过 ToolPort 映射到平台 `read`；Artifact 写入通过 `artifact-port`/ContextPort，适配器内部 `write` 不暴露为 Skill Tool。
- `fs:write:project` 权限与 `artifacts/{task-id}/` 路径限制同时生效；不得用平台写工具绕过两者。
- 不允许把用户输入拼进 Shell 命令；使用参数化调用。
- 工具调用失败必须返回明确错误；不得静默降级为更高权限操作。
- 工具结果进入输出前必须脱敏/校验。

---

## 4. 文件、Shell、网络与环境边界

| 边界 | 要求 |
|------|------|
| 文件 | 只允许项目根、`artifacts/{task-id}/`、声明的临时目录；拒绝系统目录、凭证目录和其他项目 |
| 路径 | 规范化后校验；拒绝路径穿越和越界符号链接 |
| Shell | 默认拒绝；命令白名单；参数校验；环境隔离；超时；审计 |
| 网络 | 默认拒绝；allowlist；生产相关请求按安全架构处理 |
| 环境 | dev/test/prod 隔离；生产凭证只在部署节点临时注入 |
| 凭证 | 不写入 SKILL.md、Task Context、日志、命令历史或模型上下文 |

高风险 Shell、数据库迁移、生产部署、生产数据库破坏性操作、敏感凭证读取的具体 R 级别和 SA/G6 组合，以 [security-architecture.md §5.3](../architecture/security-architecture.md) 为准。

---

## 5. 人工审批

### 5.1 Skill 的职责

- 检测到需要审批的操作时，返回 `needs_approval`；
- 说明需要哪个 G 门禁或 SA，以及原因、影响、回滚方案；
- 暂停，不自行执行；
- 不将超时、沉默或默认值当作批准。

### 5.2 不得混淆

- **R0–R4**：操作权限等级；
- **SA**：单次高风险操作的显式安全授权；
- **G1–G6**：质量与发布门禁；
- **G6**：仅在实际生产部署动作之前触发，不是所有 Skill 的通用审批步骤。

Skill 不得自行批准 SA/G6，也不得把 G6 写成每个 Skill 的固定步骤。

---

## 6. 审计

每个 Skill 的执行至少记录：

- Skill 名称/版本、task-id、节点；
- 输入引用（路径+版本+hash）；
- 使用的 Tool 和权限类别；
- 审批/G 门禁/SA 记录（如有）；
- 输出引用和结果；
- 错误、重试、超时、回退；
- 时间、执行者/Agent、平台适配器版本。

审计日志追加写入，敏感字段脱敏；不得记录原始凭证。

---

## 7. 安全测试

Skill 发布前至少覆盖：

- 输入注入（命令、路径、模板）；
- 路径穿越和越界文件访问；
- 权限提升与未声明权限调用；
- Shell 命令注入；
- 敏感信息泄漏（输出/日志/上下文）；
- 超时/重试/审批绕过的错误路径；
- 平台适配层的权限映射失败。

安全测试失败必须阻止发布；不得以“功能测试通过”替代安全测试。

---

## 8. 实现状态

| 安全能力 | 状态 |
|----------|------|
| R0–R4 权限执行 | 未实现（P2/P5） |
| 默认拒绝/权限 lease | 未实现（P2） |
| 文件沙箱/路径校验 | 未实现（P2） |
| Shell 允许列表/环境隔离 | 未实现（P2） |
| 网络 allowlist | 未实现（P5） |
| SA 记录/审批流程 | 未实现（P2/P5） |
| 审计/脱敏 | 未实现（P2/P5） |

Skill 规范中的安全要求是设计约束，不代表运行时已具备这些能力。

---

## 9. 相关标准

- [skill-standard.md](./skill-standard.md)
- [skill-metadata-standard.md](./skill-metadata-standard.md)
- [skill-io-contract.md](./skill-io-contract.md)
- [security-architecture.md](../architecture/security-architecture.md)
- [ADR-006](../decisions/ADR-006-quality-gates.md)

---

**当前状态：** P1-001 设计产出，待 ChatGPT 评审。未实现运行时权限/审批/审计机制。
