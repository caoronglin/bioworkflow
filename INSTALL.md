# BioWorkflow 快速安装指南

## 🚀 一键安装

### Linux (推荐 - DEB 包)

```bash
# 1. 下载安装包
wget https://github.com/bioworkflow-platform/bioworkflow/releases/latest/download/bioworkflow_latest_amd64.deb

# 2. 安装
sudo apt install ./bioworkflow_latest_amd64.deb

# 3. 启动服务
sudo systemctl start bioworkflow

# 4. 访问界面
# 打开浏览器访问 http://localhost:8000
```

### Linux (RPM 包)

```bash
# 1. 下载安装包
wget https://github.com/bioworkflow-platform/bioworkflow/releases/latest/download/bioworkflow_latest.x86_64.rpm

# 2. 安装
sudo dnf install ./bioworkflow_latest.x86_64.rpm

# 3. 启动服务
sudo systemctl start bioworkflow
```

### Linux (AppImage - 无需安装)

```bash
# 1. 下载
wget https://github.com/bioworkflow-platform/bioworkflow/releases/latest/download/bioworkflow_latest-x86_64.AppImage

# 2. 添加执行权限
chmod +x bioworkflow_latest-x86_64.AppImage

# 3. 运行
./bioworkflow_latest-x86_64.AppImage
```

### Windows

```powershell
# 1. 下载安装程序
# 访问 https://github.com/bioworkflow-platform/bioworkflow/releases/latest
# 下载 bioworkflow-*-windows-x64-installer.exe

# 2. 双击运行安装程序

# 3. 启动应用
# 从开始菜单或桌面快捷方式启动
```

## 📦 其他安装方式

### Python PIP (开发环境)

```bash
# 1. 克隆仓库
git clone https://github.com/bioworkflow-platform/bioworkflow.git
cd bioworkflow

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 构建 Rust 扩展
cd rust/
cargo build --release

# 4. 构建前端
cd ../src/frontend/
pnpm install
pnpm build

# 5. 启动服务
cd ../..
uvicorn src.backend.main:app --reload
```

### Docker (即将推出)

```bash
# 拉取镜像
docker pull bioworkflow/bioworkflow:latest

# 运行
docker run -d -p 8000:8000 bioworkflow/bioworkflow:latest
```

## ✅ 验证安装

### 检查版本

```bash
bioworkflow --version
```

### 检查服务状态

```bash
# Linux systemd
sudo systemctl status bioworkflow

# 或直接访问健康检查端点
curl http://localhost:8000/health
```

### 测试功能

```bash
# 访问 Web 界面
# http://localhost:8000

# 或使用 API
curl http://localhost:8000/api/pipelines
```

## ⚙️ 配置

### 默认配置

- **Web 界面**: http://localhost:8000
- **数据目录**: `/var/lib/bioworkflow`
- **日志文件**: `/var/log/bioworkflow/bioworkflow.log`
- **配置文件**: `/etc/bioworkflow/config.yaml`

### 修改配置

```bash
# 编辑配置文件
sudo nano /etc/bioworkflow/config.yaml

# 重启服务使配置生效
sudo systemctl restart bioworkflow
```

### 环境变量

```bash
# 设置环境变量
export BIOWORKFLOW_HOST=0.0.0.0
export BIOWORKFLOW_PORT=8080

# 或编辑 /etc/bioworkflow/env
```

## 🔧 常见问题

### 安装失败

**DEB 包依赖问题**:
```bash
sudo apt install -f
```

**RPM 包签名问题**:
```bash
sudo rpm --import https://github.com/bioworkflow-platform/bioworkflow/releases/download/GPG-KEY
```

### 服务无法启动

**检查日志**:
```bash
# systemd 日志
sudo journalctl -u bioworkflow -n 50

# 应用日志
sudo tail -f /var/log/bioworkflow/bioworkflow.log
```

**端口被占用**:
```bash
# 查找占用端口的进程
sudo lsof -i :8000

# 修改配置文件使用其他端口
```

### 权限问题

```bash
# 修复目录权限
sudo chown -R bioworkflow:bioworkflow /var/lib/bioworkflow
sudo chown -R bioworkflow:bioworkflow /var/log/bioworkflow
```

## 📚 下一步

- [用户指南](docs/guide/quickstart.md) - 快速开始使用
- [API 文档](docs/api/README.md) - REST API 参考
- [开发指南](docs/DEVELOPMENT.md) - 贡献代码

## 🆘 获取帮助

- **GitHub Issues**: https://github.com/bioworkflow-platform/bioworkflow/issues
- **讨论区**: https://github.com/bioworkflow-platform/bioworkflow/discussions
- **文档**: https://bioworkflow.org/docs

---

**最后更新**: 2024-03-23
