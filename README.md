# SDD - Software Development Skills

面向多 Agent 平台的模块化、可编排、可验证的软件研发能力体系。

## 项目定位

SDD 不是简单的 Skill 集合，而是一套完整的软件研发方法论，让 AI Agent 能够执行从需求澄清到部署上线的完整研发流程。

### 核心原则

- **架构统一** — 核心（L1–L5）+ 平台适配边界（L6），职责清晰
- **概念收敛** — Agent / Orchestration / Workflow / Skill / Tool / Platform Adapter 各有唯一定义
- **能力模块化** — 专业 Skill 独立复用
- **流程动态编排** — 根据任务类型自动选择 Workflow
- **平台适配解耦** — 核心能力与平台差异分离
- **质量门禁** — G1–G6 统一规则，Review 与 Testing 独立
- **安全可控** — 权限（R0–R4）与审批分离，默认拒绝

### 核心概念

六个核心概念的权威定义见 [system-architecture.md §2](./docs/architecture/system-architecture.md#2-核心概念权威定义)：

- **Agent** — 有角色、任务边界、上下文和权限的执行主体
- **Orchestration** — 任务识别、拆解、路由、协调、状态和结果汇总
- **Workflow** — 步骤、依赖、分支、并行和门禁的流程定义
- **Skill** — 封装专业能力的可复用能力包
- **Tool** — 文件、Shell、Git、浏览器、测试等操作原语
- **Platform Adapter** — 把核心契约映射到具体平台，不决定核心流程

### 参考项目

- [obra/superpowers](https://github.com/obra/superpowers) — 完整研发工作流
- [anthropics/skills](https://github.com/anthropics/skills) — Skill 设计规范
- [Agent Skills 规范](https://agentskills.io/) — 跨平台兼容标准

## 当前状态

**P0：总体架构设计** — In Review（待评审）

> 状态说明：架构设计工作已完成，交付物已创建，正在等待 ChatGPT 评审验收。P0-002 一致性收敛与 P0-003 最终收敛已完成。未经正式评审通过前，不得标记为 Accepted。

## 权威文档

| 主题 | 文档 |
|------|------|
| 核心概念与依赖方向 | [docs/architecture/system-architecture.md](./docs/architecture/system-architecture.md) |
| G1–G6 门禁 | [docs/decisions/ADR-006-quality-gates.md](./docs/decisions/ADR-006-quality-gates.md) |
| Task Context / Artifact | [docs/decisions/ADR-005-task-context.md](./docs/decisions/ADR-005-task-context.md) |
| Skill 规范与平台元数据 | [docs/architecture/skill-architecture.md](./docs/architecture/skill-architecture.md) |
| Workflow DAG | [docs/architecture/orchestration-architecture.md](./docs/architecture/orchestration-architecture.md) |
| 安全权限与审批 | [docs/architecture/security-architecture.md](./docs/architecture/security-architecture.md) |
| 平台能力与适配 | [docs/architecture/platform-architecture.md](./docs/architecture/platform-architecture.md) |

## 建设路线

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 总体架构设计 | In Review |
| P1 | 规范体系 | 待规划 |
| P2 | 调度核心 | 待规划 |
| P3 | 研发前置能力 | 待规划 |
| P4 | 工程开发能力 | 待规划 |
| P5 | 交付能力 | 待规划 |
| P6 | 反馈能力 | 待规划 |
| P7 | 体系集成 | 待规划 |

## 目标平台

- Codex
- Claude Code
- Cursor
- Gemini CLI
- OpenCode
- OpenClaw

## 快速开始

详见 [docs/architecture/](./docs/architecture/) 和 [docs/decisions/](./docs/decisions/)。
