# Skill 架构设计

## 概述

本文件定义 SDD 体系中 Skill 的标准结构、加载机制和最佳实践。

## Skill 标准结构

### 目录布局

```
skill-name/
├── SKILL.md              # 必需：Skill 主文件
├── scripts/              # 可选：可执行脚本
│   ├── helper.sh
│   └── validate.py
├── references/           # 可选：参考文档
│   ├── aws.md
│   ├── gcp.md
│   └── azure.md
├── assets/               # 可选：输出模板
│   ├── template.md
│   └── schema.json
└── examples/             # 可选：示例用例
    ├── input.md
    └── output.md
```

### SKILL.md 元数据

```yaml
---
name: skill-name
description: "触发场景描述 + 核心功能说明（160字符内）"
user-invocable: true
disable-model-invocation: false

# 条件激活（可选）
metadata:
  openclaw:
    requires:
      bins: []        # 必需的二进制工具
      env: []         # 必需的环境变量
    primaryEnv: ""    # 主要环境变量
---
```

### SKILL.md 正文结构

```markdown
# Skill 名称

## 目标与职责
[描述这个 Skill 做什么，解决什么问题]

## 适用场景
- 场景 1
- 场景 2

## 触发条件
- 用户说「XXX」时触发
- 当检测到「YYY」特征时自动触发

## 输入要求
[明确输入格式和必需字段]

## 前置条件
- [ ] 条件 1
- [ ] 条件 2

## 执行步骤
1. 第一步：做什么，为什么
2. 第二步：做什么，为什么
3. ...

## 输出规范
[定义输出格式、文件路径、内容要求]

## 质量检查
- [ ] 检查项 1
- [ ] 检查项 2

## 异常处理
- 异常情况 1：处理方式
- 异常情况 2：处理方式

## 禁止事项
- 禁止做 X
- 禁止做 Y

## 相关 Skill
- [skill-a](../skill-a/SKILL.md)
- [skill-b](../skill-b/SKILL.md)
```

## 渐进式披露机制

### 三层加载

| 层级 | 内容 | 加载时机 | 大小限制 |
|------|------|----------|----------|
| L1 | Metadata | 始终 | ~100 词 |
| L2 | SKILL.md body | 触发时 | <500 行 |
| L3 | Bundled resources | 按需 | 无限制 |

### 使用原则

1. **Metadata 是路由关键** — 描述要全面，覆盖各种触发场景
2. **SKILL.md 保持精简** — 核心逻辑在内，细节放 references
3. **按需加载 References** — 大文件用目录索引，避免全量加载

```markdown
## 参考文档
- [详细规范](references/detailed-spec.md) — 仅当需要完整规范时阅读
- [平台适配](references/platforms/claude-code.md) — Claude Code 专属配置
- [故障排查](references/troubleshooting.md) — 常见问题解决方案
```

## Domain Organization

### 多技术栈组织

当 Skill 支持多种技术栈时，按 variant 组织：

```
deployment/
├── SKILL.md              # 工作流 + 选择逻辑
└── references/
    ├── docker.md         # Docker 部署
    ├── kubernetes.md     # K8s 部署
    ├── aws.md            # AWS 部署
    └── gcp.md            # GCP 部署
```

调用规则：
```
Agent 根据任务上下文决定读取哪个 reference 文件
例如：检测到 Dockerfile → 读取 docker.md
```

## Skill 编写原则

### 1. 单一职责
每个 Skill 只做一件事，做好一件事。

### 2. 明确边界
- 输入什么 → 输出什么
- 什么情况触发 → 什么情况不触发
- 能做什么 → 不能做什么

### 3. 解释 WHY
不要只写 MUST/NEVER，要解释为什么重要。

```markdown
# 不好的写法
ALWAYS validate input first!

# 好的写法
Validate input first to prevent cascading failures.
If input is invalid, early rejection saves time and avoids confusing errors later.
```

### 4. 渐进增强
简单情况走快速路径，复杂情况走完整流程。

```markdown
## 快速路径
如果需求已明确且影响范围小（单文件修改），直接执行编码。

## 完整路径
如果需要分析影响范围或设计新架构，先执行 requirements-clarity。
```

## 平台适配策略

### 核心 vs 适配

| 内容 | 位置 | 说明 |
|------|------|------|
| 通用逻辑 | `skills/development/*/SKILL.md` | 所有平台通用 |
| 平台特定 | `platforms/<platform>/` | 平台专属配置 |
| 适配层 | `platforms/common/compatibility.md` | 兼容性矩阵 |

### 兼容性检查清单

在 `platforms/<platform>/README.md` 中记录：

```markdown
## 兼容性状态

| 能力 | 状态 | 备注 |
|------|------|------|
| Skill 发现 | ✅ 原生支持 | 自动扫描 skills/ 目录 |
| SKILL.md 元数据 | ✅ 支持 | name + description 必需 |
| 自动触发 | ⚠️ 部分支持 | 需验证 trigger 语义 |
| 子 Agent | ❌ 不支持 | 暂无法并行执行 |
| 工具调用 | ✅ 支持 | 映射 exec/read/write |
| 审批机制 | ⚠️ 部分支持 | 需适配交互方式 |
```

## 测试与验证

### 本地测试

```bash
# 列出已加载的 Skills
openclaw skills list

# 测试特定 Skill
openclaw agent --message "trigger skill by description" --skill skill-name

# 或手动调用
/skill skill-name
```

### 集成测试

在 `tests/workflow/` 下定义端到端测试用例：

```yaml
# tests/workflow/feature-development.yaml
name: feature-development
description: "完整功能开发流程测试"
steps:
  - trigger: "帮我做一个用户管理功能"
    expected_skills: [requirements-clarity, analysis, design, coding, testing]
    expected_gates: [G1, G2]
    expected_artifacts: [requirements.md, analysis.md, design.md, code/, test-report.md]
```

## 当前状态

- [x] 结构规范定义
- [ ] 模板文件创建（P1）
- [ ] 平台适配验证（P7）
