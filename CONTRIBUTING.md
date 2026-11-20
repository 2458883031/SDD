# 贡献指南

欢迎参与 SDD 项目建设！

## 开发流程

1. **Fork 本仓库**
2. **创建特性分支** — `git checkout -b feature/amazing-feature`
3. **提交变更** — `git commit -m 'feat: add amazing feature'`
4. **推送到分支** — `git push origin feature/amazing-feature`
5. **提交 Pull Request**

## Skill 开发规范

### SKILL.md 结构

```yaml
---
name: skill-name
description: "触发场景 + 核心功能（160字符内）"
---
```

### 目录组织

```
skill-name/
├── SKILL.md          # 必需
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：参考文档
└── assets/           # 可选：模板/字体等
```

### 编写原则

- 保持 SKILL.md 在 500 行以内
- 复杂内容放 `references/` 目录
- 使用渐进式披露：Metadata → Body → Resources
- 明确说明输入/输出契约

## 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：

- `feat:` 新功能
- `fix:` 修复
- `docs:` 文档变更
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具变更

## 代码审查

所有 PR 需要：
1. 通过自动化测试
2. 至少一名维护者审查
3. 符合本项目的架构规范

## 问题反馈

请使用 GitHub Issues 报告问题或提出建议。
