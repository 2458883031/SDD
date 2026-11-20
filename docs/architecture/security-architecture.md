# 安全架构设计

## 概述

SDD 安全架构确保 AI Agent 在执行软件研发任务时，不会造成意外的数据损坏、安全漏洞或权限滥用。安全设计贯穿六层架构的每个层级。

## 权限模型

### Agent 权限分级

| 级别 | 权限范围 | 适用场景 | 示例操作 |
|------|----------|----------|----------|
| P0-只读 | 读取文件、查看状态 | 需求澄清、分析 | read, ls, git status |
| P1-编辑 | 读写本地文件 | 编码、文档 | write, edit, exec(受限) |
| P2-执行 | 执行命令、访问工具 | 测试、部署 | exec, docker, kubectl |
| P3-管理 | 系统级操作 | 生产部署 | elevated exec, 网络请求 |
| P4-危险 | 删除、修改生产数据 | 仅授权操作 | rm -rf, DROP TABLE |

### 权限分配规则

```yaml
# 默认权限配置
default_permissions:
  requirements-clarity: [P0]
  analysis: [P0, P1]
  design: [P0, P1]
  coding: [P1]
  code-review: [P0, P1]
  testing: [P1, P2]
  deployment: [P2, P3]
  documentation: [P0, P1]
  feedback-loop: [P0]
```

## Skill 执行安全

### 输入验证

每个 Skill 必须验证输入：

```markdown
## 安全前检查

1. 验证输入格式是否符合 Schema
2. 检查路径是否在项目范围内
3. 验证文件内容不含恶意代码
4. 检查是否有路径穿越攻击（../）
```

### 输出过滤

```markdown
## 安全后检查

1. 过滤输出中的敏感信息（API Key、密码）
2. 验证生成的代码不含已知漏洞模式
3. 检查文件写入是否在允许目录
```

### 危险操作清单

以下操作需要额外审批（G6 门禁）：

- `rm -rf` 或删除生产数据
- `DROP TABLE` 或修改数据库 schema
- 修改认证/授权相关代码
- 执行网络请求到外部服务
- 修改系统配置文件
- 部署到生产环境

## 工具调用权限

### 工具白名单

| 工具 | 权限级别 | 限制条件 |
|------|----------|----------|
| read | P0 | 仅读取，不修改 |
| write | P1 | 需在项目目录内 |
| edit | P1 | 仅编辑已有文件 |
| exec | P2 | 需过滤危险命令 |
| browser | P2 | 需用户确认 |
| network | P3 | 需明确授权 |

### 危险命令过滤

```yaml
# 禁止的命令模式
blocked_commands:
  - "rm -rf /"
  - "dd if=/dev/zero"
  - ":() { :|:& };"  # fork bomb
  - "wget http://*"  # 无白名单的外部下载
  - "curl -X POST *" # 无白名单的外部请求
  
allowed_exec_patterns:
  - "npm install"
  - "npm test"
  - "python -m pytest"
  - "docker build"
  - "docker compose up"
```

## 文件系统访问边界

### 项目沙箱

```yaml
# 默认沙箱配置
sandbox:
  project_root: "{{workspace}}"
  allowed_paths:
    - "{{project_root}}/**"
    - "{{project_root}}/artifacts/**"
    - "{{project_root}}/.git/**"
  denied_paths:
    - "/etc/**"
    - "C:\\Windows\\**"
    - "~/.ssh/**"
    - "~/.aws/**"
```

### 路径验证规则

1. **禁止路径穿越** — 输入路径不得包含 `../`
2. **项目内限制** — 文件操作必须在项目根目录下
3. **绝对路径检查** — 解析后验证是否在允许目录
4. **符号链接安全** — 不跟随可疑符号链接

## Shell 命令执行限制

### 命令审计日志

所有 exec 调用记录：

```json
{
  "timestamp": "2026-11-20T12:00:00Z",
  "skill": "testing",
  "command": "npm test",
  "cwd": "/path/to/project",
  "user": "agent",
  "result": "success",
  "duration_ms": 5000
}
```

### 超时限制

```yaml
exec_timeout:
  coding: 300s      # 编码 5 分钟
  testing: 600s     # 测试 10 分钟
  deployment: 120s  # 部署 2 分钟
  analysis: 60s     # 分析 1 分钟
```

### 并发限制

- 同一时间最多 5 个并发 exec 进程
- 单 Skill 执行不超过 2 个并发子进程

## 凭证和敏感信息管理

### 敏感信息识别

以下模式自动检测并屏蔽：

- API Keys: `sk-[a-zA-Z0-9]{20,}`
- Tokens: `ghp_[a-zA-Z0-9]{36}`
- Passwords: 环境变量值中包含 `password`、`secret`
- Private Keys: `-----BEGIN.*PRIVATE KEY-----`

### 凭证注入策略

```yaml
# 安全的凭证传递方式
credential_handling:
  # 方式 1: 环境变量（推荐）
  env_vars:
    - GITHUB_TOKEN
    - AWS_ACCESS_KEY_ID
  
  # 方式 2: 密钥管理服务
  secret_manager: "vault"  # 可选 vault/secrets_manager
  
  # 禁止
  forbidden:
    - "硬编码在代码中"
    - "提交到版本控制"
    - "记录在日志中"
```

### 输出清理

Skill 输出必须经过清理：

```markdown
## 输出安全处理

1. 扫描输出中的敏感模式
2. 替换为 `[REDACTED]` 或 `[SECRET]`
3. 仅在审批日志中保留原始值（加密存储）
```

## 人工审批机制

### 审批触发条件

| 操作类型 | 审批级别 | 审批人 |
|----------|----------|--------|
| 写入项目文件 | 无需 | — |
| 执行测试命令 | 无需 | — |
| 修改生产配置 | G6 | 用户 |
| 删除数据 | G6 | 用户 + 审计 |
| 部署到生产 | G6 | 用户 |
| 访问外部 API | G5 | 用户 |

### 审批流程

```
1. Agent 检测到需要审批的操作
2. 暂停执行，生成审批请求
3. 向用户展示：
   - 操作内容
   - 影响范围
   - 风险评估
4. 等待用户明确批准
5. 记录审批日志
6. 执行操作
```

### 不可跳过的操作

以下操作严禁自动执行：

1. **生产环境变更** — 必须有用户明确确认
2. **数据破坏性操作** — 删除、覆盖、重置
3. **安全相关变更** — 认证、授权、加密
4. **外部网络请求** — 涉及敏感数据的传输

## 高风险操作审计

### 审计日志格式

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "action": "deploy_to_production",
  "skill": "deployment",
  "user": "agent",
  "target": "prod-server-01",
  "details": {
    "command": "kubectl apply -f deploy.yaml",
    "namespace": "production"
  },
  "approval": {
    "approved_by": "human-user",
    "approved_at": "ISO8601",
    "method": "manual_confirmation"
  },
  "result": "success|failed|cancelled",
  "rollback_available": true
}
```

### 回滚机制

```yaml
rollback_policy:
  auto_rollback:
    - "测试失败"
    - "健康检查失败"
    - "用户明确请求"
  
  manual_rollback:
    - "生产环境问题"
    - "性能退化"
    - "安全事件"
  
  retention:
    backup_duration: "7d"
    log_retention: "90d"
```

## 多 Agent 信任边界

### Agent 隔离

```yaml
multi_agent_security:
  isolation:
    - "独立 workspace"
    - "独立 session store"
    - "独立 auth profiles"
  
  cross_agent_communication:
    allowed_tools: ["sessions_list", "sessions_history"]
    denied_tools: ["exec", "write", "message"]
    
  trust_boundaries:
    - "同用户 Agent 可共享只读数据"
    - "不同用户 Agent 完全隔离"
    - "系统 Agent 可协调但不可越权"
```

### Agent 间通信安全

- **只读共享** — 通过 artifacts/ 目录传递只读数据
- **写隔离** — 每个 Agent 只能写入自己的 workspace
- **审计追踪** — 所有跨 Agent 操作记录日志

## 安全测试要求

### 安全测试清单

每个 Skill 必须通过：

- [ ] 输入验证测试（注入攻击）
- [ ] 路径穿越测试
- [ ] 权限提升测试
- [ ] 敏感信息泄漏测试
- [ ] 命令注入测试

### 安全审查

关键 Skill（deployment、coding）需要额外安全审查：

1. 代码审计
2. 依赖项安全检查
3. 执行路径分析
4. 边界条件测试

## 当前状态

- [x] 安全架构设计完成
- [ ] 具体实现（P2-P6）
- [ ] 安全测试框架（P7）

## 风险与限制

1. **静态分析局限** — 无法检测所有运行时安全漏洞
2. **性能开销** — 安全检查和审计日志有性能成本
3. **误报风险** — 过于严格的过滤可能影响正常功能
4. **新兴威胁** — AI 安全威胁持续演进，需定期更新策略

---

*本文档应与 ADR-001、ADR-006 配合使用，定义整体安全框架。*
