# 🚀 触发 GitHub Actions 完整指南

## ⚡ 快速触发（三种方式）

### 方式 1: 使用交互式脚本（最简单）

```bash
cd /home/crl/code/snakemake
./scripts/trigger_github_actions.sh
```

**脚本功能**:
- ✅ 自动检查 gh 是否安装
- ✅ 自动检查 GitHub 登录状态  
- ✅ 交互式菜单选择要触发的工作流
- ✅ 自动填写必要参数
- ✅ 实时显示执行状态

---

### 方式 2: 使用 gh 命令行

#### 📦 触发跨平台打包工作流

```bash
# 触发 build-packages.yml
gh workflow run build-packages.yml \
  --field version=0.2.0 \
  --field upload_to_release=true

# 查看运行状态
gh run list --watch

# 查看详细日志
gh run view --log
```

#### 🧪 触发 CI 检查工作流

```bash
# 触发 ci.yml
gh workflow run ci.yml

# 或推送代码自动触发
git push origin main
```

#### 🎉 触发发布工作流（通过标签）

```bash
# 创建版本标签
git tag v0.2.0

# 推送标签（自动触发 release.yml）
git push origin v0.2.0

# 监控运行状态
gh run watch

# 查看发布结果
gh release list
```

---

### 方式 3: GitHub Web 界面

1. **访问仓库**: https://github.com/YOUR_USERNAME/bioworkflow/actions
2. **选择工作流**: 点击左侧的工作流名称
   - `Build Packages` - 跨平台打包
   - `CI Check` - CI 检查
   - `Release` - 发布
3. **点击 "Run workflow"** 按钮
4. **填写参数**:
   - Version: `0.2.0`
   - Upload to release: `true`
5. **点击 "Run workflow"**

---

## 📋 前提条件检查清单

在触发 Actions 之前，请确保：

### 1. GitHub CLI 已安装

```bash
# 检查是否安装
gh --version

# 如果未安装 (Ubuntu/Debian)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y
```

### 2. 已登录 GitHub

```bash
# 检查登录状态
gh auth status

# 如果未登录
gh auth login
```

### 3. 仓库已推送到 GitHub

```bash
# 创建 GitHub 仓库（在 GitHub 网站上）
# https://github.com/new

# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/bioworkflow.git

# 推送代码
git push -u origin main
```

### 4. Actions 已启用

- 访问仓库 → **Settings** → **Actions** → **General**
- 确保 **Actions permissions** 设置为 "Allow all actions..."

---

## 🎯 实际执行步骤

### Step 1: 准备仓库

```bash
cd /home/crl/code/snakemake

# 确认所有文件已提交
git status
git add -A
git commit -m "feat: 添加 CI/CD 打包系统"
```

### Step 2: 推送到 GitHub

```bash
# 首次推送（需要先在 GitHub 创建空仓库）
git remote add origin https://github.com/YOUR_USERNAME/bioworkflow.git
git push -u origin main
```

### Step 3: 触发工作流

```bash
# 使用脚本触发（推荐）
./scripts/trigger_github_actions.sh

# 选择选项 1) build-packages.yml
# 输入版本号：0.2.0
# 是否上传到 Release: y
```

### Step 4: 监控执行

```bash
# 查看运行列表
gh run list

# 实时查看最新运行
gh run watch

# 查看特定运行的日志
gh run view <RUN_ID> --log
```

### Step 5: 下载产物（可选）

```bash
# 列出可用产物
gh run download --list

# 下载所有产物
gh run download

# 下载特定产物到指定目录
gh run download --name windows-installer --dir ./dist
```

---

## 📊 工作流执行时间预估

| 工作流 | 首次运行 | 使用缓存 | 产物 |
|--------|----------|----------|------|
| **build-packages.yml** | 25-35 分钟 | 15-20 分钟 | 4 个安装包 |
| **ci.yml** | 10-15 分钟 | 5-8 分钟 | 无 |
| **release.yml** | 20-30 分钟 | 15-20 分钟 | wheel + Release |
| **deploy.yml** | 15-20 分钟 | 10-15 分钟 | Docker 镜像 |

---

## 🔍 故障排查

### 问题 1: "Repository not found"

**原因**: 仓库不存在或未推送

**解决**:
```bash
# 1. 在 GitHub 创建新仓库
# https://github.com/new

# 2. 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/bioworkflow.git

# 3. 推送
git push -u origin main
```

### 问题 2: "Resource not accessible by integration"

**原因**: Actions 权限未开启

**解决**:
1. 访问仓库 Settings → Actions → General
2. 启用 "Allow all actions..."
3. 保存后重试

### 问题 3: 工作流运行失败

**解决**:
```bash
# 1. 查看详细日志
gh run view <RUN_ID> --log

# 2. 重新运行失败的任务
gh run rerun <RUN_ID> --failed

# 3. 本地测试
./scripts/build_packages.sh all
python3 scripts/test_package.py
```

### 问题 4: gh 命令找不到

**解决**:
```bash
# 安装 GitHub CLI
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y

# macOS
brew install gh
```

---

## 📚 相关文档

- [打包系统总结](.github/workflows/PACKAGING_SUMMARY.md)
- [打包详细指南](docs/packaging.md)
- [安装指南](INSTALL.md)
- [CI/CD 配置](docs/CI-CD.md)

---

## ✅ 完成标志

当你看到以下内容时，说明触发成功：

```
✓ Created workflow_run event for build-packages.yml at main
✓ Run ID: 1234567890
✓ View this run on GitHub: https://github.com/YOUR_USERNAME/bioworkflow/actions/runs/1234567890
```

然后访问链接查看实时执行进度！🎉

---

**最后更新**: 2024-03-23
