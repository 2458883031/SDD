# SDD 项目建设路线图

## 总体规划

| 阶段 | 内容 | 预计周期 | 状态 |
|------|------|----------|------|
| P0 | 总体架构设计 | 1 周 | **In Review** |
| P1 | 规范体系 | 1 周 | 待规划 |
| P2 | 调度核心 | 2 周 | 待规划 |
| P3 | 研发前置能力 | 2 周 | 待规划 |
| P4 | 工程开发能力 | 3 周 | 待规划 |
| P5 | 交付能力 | 2 周 | 待规划 |
| P6 | 反馈能力 | 1 周 | 待规划 |
| P7 | 体系集成 | 2 周 | 待规划 |

## P0：总体架构设计

### 建设目标
- 完成六层架构设计
- 定义模块划分和接口
- 建立决策记录（ADR）
- 确定目录结构和规范

### 任务清单
- [x] 项目初始化
- [x] 目录结构创建
- [x] 架构文档编写（7篇）
- [x] ADR 决策记录（6篇）
- [x] 平台兼容性研究（初步矩阵）
- [x] 项目路线图制定
- [x] 自检与验收报告
- [x] 整改报告编写
- [ ] 自检与验收报告

### 交付物
- [docs/architecture/](../architecture/) — 架构设计文档
- [docs/decisions/](../decisions/) — 架构决策记录
- [docs/roadmap/](./) — 项目路线图
- [docs/risks-and-questions.md](../risks-and-questions.md) — 风险与待确认事项

### 依赖关系
- P1 依赖 P0 完成
- P2 依赖 P0 和 P1

### 验收标准
- [ ] 架构文档完整，覆盖六层
- [ ] ADR 数量不少于 6 个
- [ ] 目录结构符合规划
- [ ] 平台兼容性矩阵完成初稿

### 风险
- 复杂度评估可能不足，导致后续返工
- 平台兼容性研究可能发现重大障碍

## P1：规范体系

### 建设目标
- 定义 Skill 标准规范
- 创建 Schema 定义
- 建立模板库
- 制定代码审查标准

### 任务清单
- [ ] 定义 SKILL.md 标准
- [ ] 创建 Schema 验证工具
- [ ] 建立模板库
- [ ] 定义产物格式规范
- [ ] 制定命名约定

### 交付物
- [core/standards/](../../core/standards/) — 规范文档
- [core/schemas/](../../core/schemas/) — Schema 定义
- [core/templates/](../../core/templates/) — 模板文件
- [tools/skill-validator/](../../tools/skill-validator/) — 验证工具

### 依赖关系
- 依赖 P0 完成

### 验收标准
- [ ] 规范文档完整
- [ ] Schema 可验证 SKILL.md
- [ ] 模板可直接使用
- [ ] 验证工具可运行

### 风险
- Schema 设计可能过于严格或宽松

## P2：调度核心

### 建设目标
- 实现编排引擎
- 定义工作流 Schema
- 实现 HARD-GATE 机制
- 建立任务上下文管理

### 任务清单
- [ ] 实现 TaskIdentifier
- [ ] 实现 SkillRouter
- [ ] 实现 GateController
- [ ] 实现 ArtifactManager
- [ ] 定义工作流 YAML Schema
- [ ] 实现子 Agent 协作机制

### 交付物
- [skills/development/orchestration/SKILL.md](../../../skills/development/orchestration/SKILL.md)
- [core/schemas/workflow.schema.json](../../../core/schemas/workflow.schema.json)
- [workflows/*.yaml](../../../workflows/) — 工作流定义
- [tools/workflow-validator/](../../../tools/workflow-validator/) — 工作流验证工具

### 依赖关系
- 依赖 P0、P1 完成

### 验收标准
- [ ] 编排引擎可正确路由任务
- [ ] HARD-GATE 正常工作
- [ ] 产物管理符合契约
- [ ] 子 Agent 协作测试通过

### 风险
- 复杂工作流的边缘情况处理

## P3：研发前置能力

### 建设目标
- 实现需求澄清 Skill
- 实现技术分析 Skill
- 实现架构设计 Skill

### 任务清单
- [ ] requirements-clarity Skill
- [ ] analysis Skill
- [ ] design Skill
- [ ] Builder Check 实现
- [ ] 相关测试用例

### 交付物
- [skills/development/requirements-clarity/](../../../skills/development/requirements-clarity/)
- [skills/development/analysis/](../../../skills/development/analysis/)
- [skills/development/design/](../../../skills/development/design/)

### 依赖关系
- 依赖 P2 完成

### 验收标准
- [ ] 三个 Skill 可独立运行
- [ ] 输入输出符合契约
- [ ] 端到端流程测试通过

### 风险
- 需求理解的准确性

## P4：工程开发能力

### 建设目标
- 实现代码开发 Skill
- 实现代码审查 Skill
- 实现测试 Skill
- 集成专业技术 Skill

### 任务清单
- [ ] coding Skill（含前端/后端/数据库/AI 子 Skill）
- [ ] code-review Skill
- [ ] testing Skill
- [ ] 专业技术 Skill 集成
- [ ] 相关测试用例

### 交付物
- [skills/development/coding/](../../../skills/development/coding/)
- [skills/development/code-review/](../../../skills/development/code-review/)
- [skills/development/testing/](../../../skills/development/testing/)

### 依赖关系
- 依赖 P2、P3 完成

### 验收标准
- [ ] 编码 Skill 可生成有效代码
- [ ] Review Skill 可检出问题
- [ ] Testing Skill 可执行测试
- [ ] 专业技术 Skill 集成正常

### 风险
- 代码质量的不确定性
- 技术栈覆盖范围

## P5：交付能力

### 建设目标
- 实现部署 Skill
- 实现文档生成 Skill
- 集成 DevOps 工具

### 任务清单
- [ ] deployment Skill
- [ ] documentation Skill
- [ ] CI/CD 集成
- [ ] 部署模板

### 交付物
- [skills/development/deployment/](../../../skills/development/deployment/)
- [skills/development/documentation/](../../../skills/development/documentation/)

### 依赖关系
- 依赖 P4 完成

### 验收标准
- [ ] 部署流程可执行
- [ ] 文档生成质量合格
- [ ] 支持至少一种云平台

### 风险
- 部署环境的差异性

## P6：反馈能力

### 建设目标
- 实现反馈收集 Skill
- 实现复盘分析 Skill
- 建立持续改进机制

### 任务清单
- [ ] feedback-loop Skill
- [ ] 评估指标定义
- [ ] 改进建议生成

### 交付物
- [skills/development/feedback-loop/](../../../skills/development/feedback-loop/)

### 依赖关系
- 依赖 P5 完成

### 验收标准
- [ ] 反馈可被收集和分析
- [ ] 改进建议有价值
- [ ] 闭环机制可运行

### 风险
- 反馈数据的可用性

## P7：体系集成

### 建设目标
- 跨平台兼容性验证
- 端到端集成测试
- 性能优化
- 文档完善

### 任务清单
- [ ] 平台兼容性测试
- [ ] 集成测试套件
- [ ] 性能基准测试
- [ ] 用户文档编写
- [ ] 示例项目创建

### 交付物
- [tests/compatibility/](../../../tests/compatibility/)
- [docs/guides/](../../../docs/guides/)
- 示例项目

### 依赖关系
- 依赖 P1-P6 完成

### 验收标准
- [ ] 至少支持 2 个平台
- [ ] 端到端流程测试通过
- [ ] 性能达到预期
- [ ] 文档完整

### 风险
- 平台差异可能导致适配问题
- 集成测试可能发现架构缺陷

## 里程碑

| 时间 | 里程碑 | 目标 |
|------|--------|------|
| Week 1 | P0 完成 | 架构设计文档定稿 |
| Week 2 | P1 完成 | 规范体系可用 |
| Week 4 | P2 完成 | 编排引擎可用 |
| Week 6 | P3 完成 | 需求-设计流程可用 |
| Week 9 | P4 完成 | 编码-测试流程可用 |
| Week 11 | P5 完成 | 部署能力可用 |
| Week 12 | P6 完成 | 反馈闭环可用 |
| Week 14 | P7 完成 | 体系集成完成 |

## 当前状态

**P0 进行中**

已完成：
- 项目初始化
- 目录结构创建
- 基础文档编写
- ADR 决策记录

待完成：
- 平台兼容性研究
- 风险与问题清单
- 自检与验收报告
