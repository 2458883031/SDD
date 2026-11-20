# Changelog

所有重要变更将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- 项目初始化
- P0 总体架构设计（In Review）
- 2026-11-20：补齐 platform / security / testing 三篇架构文档
- 2026-11-20：P0 接管盘点报告、P0 整改报告、P0-001 整改任务书入库

### 变更
- 2026-11-20：P0-002 架构一致性整改
  - 统一 Agent / Orchestration / Workflow / Skill / Tool / Platform Adapter 六个核心概念
  - 统一 G1–G6 门禁定义（ADR-006 为唯一权威）
  - Skill 通用规范与平台元数据分离
  - 明确 Workflow DAG、Review/Testing 并行与部署依赖
  - 权限（R0–R4）与审批分离，补充风险矩阵与实现状态
  - 统一六平台清单（含 OpenClaw）与未验证声明
  - 补充 Task Context / Artifact 生命周期
- 2026-11-20：P0-003 最终架构收敛
  - 简单修改 Workflow 增加独立 Code Review，G4 AND G5
  - 统一 R0–R4 权限口径与 G6/SA 边界
  - 补全 Task Context 正常/审批/异常/终止状态机
  - G6 统一为生产部署动作之前的授权门禁
  - 补充 P0-002 报告的提交 1829775 记录

### 修复
- 2026-11-20：修正 P0-001 遗留的文档冲突、链接、CLI 示例与状态标注
- 2026-11-20：修正 P0-002 复审发现的简单 Workflow、权限、状态机与 G6 歧义

### 删除
