# BioWorkflow 版本发布指南

## 发布流程

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范，每个新功能完成后必须发布一个 GitHub Release。

### 版本号格式

`MAJOR.MINOR.PATCH-STATUS`

- **MAJOR**: 主版本号 - 重大功能更新或不兼容的 API 变更
- **MINOR**: 次版本号 - 新增功能，向后兼容
- **PATCH**: 修订版本号 - Bug 修复，向后兼容
- **STATUS**: 状态标签 - alpha、beta、rc（可选）

示例：`0.1.0-alpha`、`1.0.0`、`1.1.0-beta`

## 发布步骤

### 1. 开发阶段

```bash
# 创建特性分支
git checkout -b feature/new-feature

# 开发功能...
# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature
```

### 2. 测试阶段

```bash
# 创建 Pull Request
# 在 GitHub 上创建 PR，进行代码审查

# 运行所有测试
pytest tests/ -v
npm test (前端)

# 功能测试通过后，合并到 develop 分支
```

### 3. 发布准备

#### 更新版本号

编辑 `pyproject.toml`：
```toml
[project]
version = "0.1.0"
```

编辑 `src/frontend/package.json`：
```json
{
  "version": "0.1.0"
}
```

#### 更新 CHANGELOG

创建或编辑 `CHANGELOG.md`：
```markdown
## [0.1.0] - 2026-01-25

### Added
- 新增功能 1
- 新增功能 2

### Fixed
- 修复 Bug 1

### Changed
- 优化性能

[0.1.0]: https://github.com/yourusername/bioworkflow/releases/tag/v0.1.0
```

### 4. 创建 Release

```bash
# 合并到 main 分支
git checkout main
git pull origin develop
git merge develop

# 创建标签
git tag -a v0.1.0 -m "Release version 0.1.0"

# 推送到远程
git push origin main
git push origin v0.1.0
```

GitHub Actions 会自动：
1. 运行所有测试
2. 构建应用
3. 创建 Release 页面

### 5. 发布完成

GitHub Release 页面会自动创建，包含：
- 版本信息
- 变更日志
- 自动生成的源代码压缩包

## 功能完整性清单

在发布每个版本前，确保以下检查项都已完成：

- [ ] 所有新增功能已完成
- [ ] 所有测试用例通过
- [ ] 代码审查完成
- [ ] 文档已更新
- [ ] 功能已设为可选项（如适用）
- [ ] 没有已知的 Bug
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 提交消息遵循 Conventional Commits

## 可选功能标记

在 Web 界面的设置页面中，每个功能应该有一个开关来启用/禁用：

```python
# 示例：在数据库中添加 Feature Flag
class FeatureFlag:
    feature_name: str
    enabled: bool
    description: str
    version: str  # 功能首次引入的版本
```

## 版本回滚

如果某个版本有严重问题，可以进行回滚：

### 方法 1：Git 回滚

```bash
# 查看历史版本
git tag

# 检出旧版本
git checkout v0.0.1

# 创建新分支（如果需要在旧版本基础上修复）
git checkout -b hotfix/v0.0.1
```

### 方法 2：创建 Hotfix 版本

```bash
# 从旧版本创建修复分支
git checkout -b hotfix/v0.0.1-patch v0.0.1

# 修复问题
git commit -m "fix: 重要 Bug 修复"

# 创建新的补丁版本
git tag v0.0.2
git push origin hotfix/v0.0.1-patch
git push origin v0.0.2
```

## Alpha/Beta 版本

对于不稳定的版本，使用预发布版本号：

```bash
# Alpha 版本
git tag v0.1.0-alpha

# Beta 版本  
git tag v0.1.0-beta

# Release Candidate
git tag v0.1.0-rc1
```

这些版本不会被标记为最新发布，但仍然可以下载和测试。

## 发布工作流自动化

GitHub Actions 会自动处理以下任务（`.github/workflows/test-and-release.yml`）：

1. **测试**：运行 Python 和 JavaScript 测试
2. **构建**：构建前端应用
3. **发布**：创建 GitHub Release

## 破坏性变更

如果新版本包含破坏性变更，必须：

1. 在版本号中明确标记（如 `2.0.0`）
2. 在 CHANGELOG 中详细说明
3. 在 Release 说明中提供迁移指南
4. 标记为 `breaking-change` 标签

## 安全更新

对于安全漏洞修复：

1. 不要在公共分支上讨论细节
2. 创建 security.md 文件说明报告流程
3. 立即发布补丁版本
4. 在 CHANGELOG 中标记为 `SECURITY`

## 发布后的维护

发布后的 7 天内：

- 监控用户反馈
- 修复紧急 Bug
- 如有必要，发布补丁版本

---

**最后更新**：2026-01-25
