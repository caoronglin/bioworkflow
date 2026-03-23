# BioWorkflow 打包指南

本文档介绍如何将 BioWorkflow 打包成独立的可执行文件和安装包。

## 📦 支持的包格式

| 平台 | 格式 | 文件类型 | 说明 |
|------|------|----------|------|
| **Windows** | NSIS | `.exe` | 安装向导，包含卸载程序 |
| **Linux** | DEB | `.deb` | Debian/Ubuntu 原生包 |
| **Linux** | RPM | `.rpm` | RHEL/CentOS/Fedora 原生包 |
| **Linux** | AppImage | `.AppImage` | 通用 Linux，无需安装 |

## 🚀 快速开始

### 方法一：使用构建脚本（推荐）

```bash
# 构建所有格式
./scripts/build_packages.sh all

# 或构建特定格式
./scripts/build_packages.sh deb
./scripts/build_packages.sh rpm
./scripts/build_packages.sh appimage
```

### 方法二：使用 GitHub Actions

```bash
# 手动触发工作流
gh workflow run build-packages.yml --field version=0.2.0

# 或推送标签自动触发
git tag v0.2.0
git push --tags
```

## 📋 依赖要求

### 通用依赖

```bash
# Python 3.10+
python3 --version

# PyInstaller
pip3 install pyinstaller
```

### Linux 额外依赖

```bash
# DEB/RPM 打包 (需要 Ruby)
sudo gem install fpm

# AppImage 打包
wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool

# 图标生成 (可选)
sudo apt install imagemagick
```

## 🔧 本地构建

### 步骤 1: 准备环境

```bash
# 安装依赖
pip3 install -e ".[dev]"
pip3 install pyinstaller

# 构建 Rust 扩展
cd rust/
cargo build --release

# 构建前端
cd src/frontend/
pnpm install
pnpm build
```

### 步骤 2: 运行 PyInstaller

```bash
cd packaging/
pyinstaller bioworkflow.spec --noconfirm
```

### 步骤 3: 验证打包产物

```bash
# 测试版本
./dist/bioworkflow/bioworkflow --version

# 运行测试脚本
python3 ../scripts/test_package.py
```

## 📱 平台特定说明

### Windows (NSIS)

**构建产物**:
- `bioworkflow-0.2.0-windows-x64-installer.exe`

**安装步骤**:
1. 双击运行安装程序
2. 选择安装目录（默认：`C:\Program Files\BioWorkflow`）
3. 创建桌面快捷方式（可选）
4. 完成安装

**卸载**:
- 通过 Windows 控制面板 → 程序和功能

### Linux (DEB)

**构建产物**:
- `bioworkflow_0.2.0_amd64.deb`

**安装**:
```bash
sudo apt install ./bioworkflow_0.2.0_amd64.deb
```

**验证**:
```bash
# 检查服务状态
sudo systemctl status bioworkflow

# 查看日志
sudo journalctl -u bioworkflow -f
```

**卸载**:
```bash
sudo apt remove bioworkflow
```

### Linux (RPM)

**构建产物**:
- `bioworkflow-0.2.0.x86_64.rpm`

**安装**:
```bash
sudo dnf install ./bioworkflow-0.2.0.x86_64.rpm
```

**验证**:
```bash
# 检查服务状态
sudo systemctl status bioworkflow
```

**卸载**:
```bash
sudo dnf remove bioworkflow
```

### Linux (AppImage)

**构建产物**:
- `bioworkflow-0.2.0-x86_64.AppImage`

**运行**:
```bash
# 添加执行权限
chmod +x bioworkflow-0.2.0-x86_64.AppImage

# 运行
./bioworkflow-0.2.0-x86_64.AppImage

# 或挂载查看内容
./bioworkflow-0.2.0-x86_64.AppImage --appimage-mount
```

**集成到桌面** (可选):
```bash
# 创建快捷方式
mkdir -p ~/.local/bin
cp bioworkflow-*.AppImage ~/.local/bin/bioworkflow
chmod +x ~/.local/bin/bioworkflow

# 创建桌面文件
cat > ~/.local/share/applications/bioworkflow.desktop << EOF
[Desktop Entry]
Type=Application
Name=BioWorkflow
Exec=$HOME/.local/bin/bioworkflow
Icon=bioworkflow
Categories=Science;Education;
EOF
```

## 🧪 测试打包产物

### 使用测试脚本

```bash
# 测试本地打包目录
python3 scripts/test_package.py

# 测试指定的包文件
python3 scripts/test_package.py dist/bioworkflow_0.2.0_amd64.deb
```

### 手动测试

```bash
# 1. 版本检查
./dist/bioworkflow/bioworkflow --version

# 2. 帮助信息
./dist/bioworkflow/bioworkflow --help

# 3. 启动服务（测试模式）
./dist/bioworkflow/bioworkflow --config /dev/null

# 4. 健康检查
curl http://localhost:8000/health
```

## 🛠️ 故障排查

### PyInstaller 打包问题

**问题**: Rust 扩展模块找不到

**解决**:
```python
# 在 bioworkflow.spec 中添加
hiddenimports += ['bioworkflow']
datas += collect_data_files('bioworkflow')
```

**问题**: 前端静态文件 404

**解决**:
- 确认 `src/frontend/dist` 目录存在
- 检查 `runtime_hook.py` 中的 FRONTEND_DIST 路径
- 在 spec 文件中正确添加 datas

### Linux 包安装问题

**问题**: DEB 包依赖不满足

**解决**:
```bash
# 自动修复依赖
sudo apt install -f
```

**问题**: systemd 服务启动失败

**解决**:
```bash
# 查看服务日志
sudo journalctl -u bioworkflow -n 50

# 手动测试启动命令
sudo -u bioworkflow /usr/bin/bioworkflow --config /etc/bioworkflow/config.yaml
```

### AppImage 问题

**问题**: FUSE 未安装

**解决**:
```bash
# Ubuntu/Debian
sudo apt install libfuse2

# Fedora
sudo dnf install fuse
```

## 📊 包大小优化

### 默认配置下的大小

| 格式 | 大小 | 解压后 |
|------|------|--------|
| DEB | ~300 MB | ~800 MB |
| RPM | ~320 MB | ~850 MB |
| AppImage | ~350 MB | ~900 MB |
| Windows EXE | ~280 MB | ~750 MB |

### 优化方法

1. **使用 UPX 压缩** (已在 spec 中启用)
2. **排除不必要的模块**:
   ```python
   # bioworkflow.spec
   excludes=['pytest', 'mypy', 'coverage']
   ```
3. **使用 onefile 模式** (减小文件数，但启动稍慢)
4. **分离大型依赖** (如 Conda 环境)

## 🔄 自动更新

### Windows

NSIS 安装包不包含自动更新功能。建议：
1. 定期检查 GitHub Releases
2. 使用第三方更新工具

### Linux

**DEB/RPM**:
```bash
# 添加 APT 仓库 (未来实现)
sudo add-apt-repository ppa:bioworkflow/stable
sudo apt update
sudo apt install bioworkflow
```

**AppImage**:
```bash
# 使用 AppImageUpdate (需要构建时启用)
./bioworkflow-*.AppImage --appimage-update
```

## 📝 发布流程

1. **更新版本号**
   ```bash
   # pyproject.toml
   version = "0.2.0"
   ```

2. **更新 CHANGELOG.md**
   ```markdown
   ## [0.2.0] - 2024-03-23
   ### Added
   - 新增跨平台打包支持
   - 新增 Rust 矩阵运算模块
   
   ### Changed
   - 优化 PyInstaller 配置
   ```

3. **创建 Git 标签**
   ```bash
   git tag v0.2.0
   git push --tags
   ```

4. **GitHub Actions 自动构建**
   - 等待工作流完成
   - 检查所有包格式是否生成
   - 验证 Release 资产

5. **发布说明**
   - 编辑 GitHub Release 说明
   - 添加安装指南链接
   - 通知用户更新

## 📚 参考资源

- [PyInstaller 文档](https://pyinstaller.org/)
- [FPM 文档](https://fpm.readthedocs.io/)
- [AppImage 文档](https://docs.appimage.org/)
- [NSIS 文档](https://nsis.sourceforge.io/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

## 🤝 贡献

发现打包问题？请提交 Issue 或 Pull Request：
- 报告具体的错误信息
- 提供操作系统版本
- 附上构建日志

---

**维护者**: BioWorkflow Team  
**最后更新**: 2024-03-23
