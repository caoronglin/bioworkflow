# GitHub Actions 触发指南

## 📋 前提条件

1. **GitHub CLI 已安装**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update && sudo apt install gh -y
   
   # macOS
   brew install gh
   ```

2. **已登录 GitHub**
   ```bash
   gh auth login
   ```

3. **仓库已推送到 GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/bioworkflow.git
   git push -u origin main
   ```

## 🚀 触发方式

### 方式一：使用触发脚本（推荐）

```bash
cd /home/crl/code/snakemake
./scripts/trigger_github_actions.sh
```

脚本会自动：
- 检查 gh 是否安装
- 检查登录状态
- 提供交互式菜单选择要触发的工作流
- 自动填写必要的参数

### 方式二：手动触发

#### 1. 跨平台打包工作流

```bash
# 触发打包工作流
gh workflow run build-packages.yml \
  --field version=0.2.0 \
  --field upload_to_release=true

# 查看运行状态
gh run list --watch
```

#### 2. CI 检查工作流

```bash
# 触发 CI
gh workflow run ci.yml

# 或推送代码自动触发
git push origin main
```

#### 3. 发布工作流（通过标签触发）

```bash
# 创建版本标签
git tag v0.2.0

# 推送标签（自动触发 release.yml）
git push origin v0.2.0

# 查看发布状态
gh release list
```

### 方式三：GitHub Web 界面

1. 访问仓库页面：https://github.com/YOUR_USERNAME/bioworkflow
2. 点击 **Actions** 标签
3. 选择要运行的工作流
4. 点击 **Run workflow** 按钮
5. 填写参数（如版本号）
6. 点击 **Run workflow**

## 📊 工作流说明

### build-packages.yml

**触发条件**:
- 手动触发（workflow_dispatch）
- 推送版本标签（push tags: v*）

**产物**:
- `bioworkflow-<version>-windows-x64-installer.exe`
- `bioworkflow_<version>_amd64.deb`
- `bioworkflow-<version>.x86_64.rpm`
- `bioworkflow-<version>-x86_64.AppImage`

**预计运行时间**: 15-25 分钟

### ci.yml

**触发条件**:
- 推送到 main 分支
- Pull Request

**检查项目**:
- Python 代码质量（ruff, black, mypy）
- Rust 编译和测试
- 前端构建和 lint
- 单元测试

### release.yml

**触发条件**:
- 推送版本标签（v*）

**执行步骤**:
1. 构建所有平台的 wheel 包
2. 发布到 PyPI
3. 创建 GitHub Release
4. 上传所有构建产物

### deploy.yml

**触发条件**:
- 手动触发
- 发布到 main 分支

**部署目标**:
- Vercel（前端）
- Docker Hub（容器镜像）

## 🔍 监控和调试

### 查看运行状态

```bash
# 列出最近的运行
gh run list

# 查看特定运行的详细信息
gh run view <RUN_ID>

# 实时查看日志
gh run view <RUN_ID> --log --watch
```

### 下载构建产物

```bash
# 列出产物
gh run download <RUN_ID> --dir ./artifacts

# 下载特定产物
gh run download <RUN_ID> --name windows-installer
```

### 失败调试

1. **查看完整日志**
   ```bash
   gh run view <RUN_ID> --log > run_logs.txt
   ```

2. **重新运行失败的任务**
   ```bash
   gh run rerun <RUN_ID> --failed
   ```

3. **启用调试日志**
   - 在 GitHub Actions 设置中启用 "Debug logging"
   - 或使用 `ACTIONS_RUNNER_DEBUG=true` secret

## ⚙️ 配置 Secrets

在 GitHub 仓库设置中添加以下 secrets：

### PyPI 发布
- `PYPI_API_TOKEN`: PyPI API token

### Docker 部署
- `DOCKERHUB_USERNAME`: Docker Hub 用户名
- `DOCKERHUB_TOKEN`: Docker Hub access token

### Vercel 部署
- `VERCEL_TOKEN`: Vercel token
- `VERCEL_ORG_ID`: Vercel 组织 ID
- `VERCEL_PROJECT_ID`: Vercel 项目 ID

### 代码签名（可选）
- `CODE_SIGN_CERT`: Windows 代码签名证书（base64 编码）
- `CODE_SIGN_PASSWORD`: 证书密码

## 📝 最佳实践

1. **本地测试后再触发**
   ```bash
   # 本地构建测试
   ./scripts/build_packages.sh all
   
   # 验证包
   python3 scripts/test_package.py
   ```

2. **先发布到 TestPyPI**
   - 修改 release.yml 中的 PyPI URL 为 TestPyPI
   - 验证无误后再发布正式版本

3. **使用缓存加速**
   - Rust: Swatinem/rust-cache
   - Python: actions/cache
   - Node.js: actions/cache with pnpm

4. **并行构建**
   - build-packages.yml 已经配置并行构建
   - 各平台独立构建，互不影响

## 🎯 完整发布流程

```bash
# 1. 更新版本号
# 编辑 pyproject.toml, CHANGELOG.md

# 2. 提交更改
git add -A
git commit -m "chore: release version 0.2.0"

# 3. 推送到 main
git push origin main

# 4. 等待 CI 通过
gh run watch

# 5. 创建标签
git tag v0.2.0

# 6. 推送标签（自动触发发布）
git push origin v0.2.0

# 7. 监控发布过程
gh run watch

# 8. 验证发布产物
gh release list
gh release view v0.2.0
```

## 🆘 故障排查

### 问题：工作流无法触发

**解决**:
1. 检查仓库是否有 Actions 权限
2. 检查是否已登录 gh
3. 确认工作流文件语法正确

### 问题：构建失败

**解决**:
1. 查看详细日志
2. 检查依赖是否完整
3. 本地重现构建

### 问题：产物上传失败

**解决**:
1. 检查仓库权限
2. 检查产物路径是否正确
3. 查看 Release 是否已创建

## 📚 相关文档

- [打包指南](docs/packaging.md)
- [安装指南](INSTALL.md)
- [CI/CD 配置](docs/CI-CD.md)

---

**最后更新**: 2024-03-23
