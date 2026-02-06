# 安装指南

本文档介绍如何安装和配置 BioWorkflow。

## 系统要求

### 最低要求

- **CPU**: 2 核心
- **内存**: 4 GB RAM
- **磁盘**: 20 GB 可用空间
- **操作系统**: Linux (推荐 Ubuntu 20.04+)

### 推荐配置

- **CPU**: 4 核心及以上
- **内存**: 8 GB RAM 及以上
- **磁盘**: 100 GB SSD
- **操作系统**: Ubuntu 22.04 LTS 或 CentOS 8

## 安装方式

### 方式一：Docker Compose（推荐）

这是最简单、最推荐的安装方式。

#### 1. 安装 Docker 和 Docker Compose

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# 或者使用官方脚本
curl -fsSL https://get.docker.com | sh

# 启动 Docker 服务
sudo systemctl enable docker
sudo systemctl start docker

# 将当前用户添加到 docker 组（需重新登录生效）
sudo usermod -aG docker $USER
```

#### 2. 下载 BioWorkflow

```bash
# 克隆仓库
git clone https://github.com/yourusername/bioworkflow.git
cd bioworkflow

# 或者下载最新版本
wget https://github.com/yourusername/bioworkflow/archive/refs/tags/v0.1.0.tar.gz
tar -xzf v0.1.0.tar.gz
cd bioworkflow-0.1.0
```

#### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用你喜欢的编辑器
```

关键配置项：

```bash
# 必需：设置一个安全的密钥
SECRET_KEY=your-super-secret-key-here

# 可选：修改端口（如果 8000 被占用）
PORT=8080

# 可选：数据库配置
DATABASE_URL=sqlite:///./data/bioworkflow.db
```

#### 4. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 等待服务完全启动（约 30 秒）
sleep 30
```

#### 5. 验证安装

```bash
# 检查 API 是否响应
curl http://localhost:8000/health

# 打开浏览器访问
# http://localhost:8000
```

### 方式二：手动安装

适用于开发环境或需要自定义配置的场景。

#### 1. 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.13 \
    python3.13-venv \
    python3-pip \
    nodejs \
    npm \
    git \
    build-essential \
    libpq-dev

# 安装 Miniconda（用于 Snakemake）
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
conda init bash
```

#### 2. 后端安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/bioworkflow.git
cd bioworkflow

# 创建虚拟环境
python3.13 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 安装 Snakemake
conda install -c conda-forge -c bioconda snakemake
```

#### 3. 前端安装

```bash
cd src/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

cd ../..
```

#### 4. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

#### 5. 启动服务

```bash
# 终端 1：启动后端
cd src/backend
uvicorn main:app --reload --port 8000

# 终端 2：启动前端开发服务器（开发模式）
cd src/frontend
npm run dev
```

## 常见问题

### Docker 相关问题

**Q: 端口被占用**
```bash
# 检查端口占用
sudo lsof -i :8000

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:8000"  # 主机端口:容器端口
```

**Q: 权限问题**
```bash
# 修复目录权限
sudo chown -R $USER:$USER ./data ./workflows ./logs
```

**Q: 内存不足**
```bash
# 增加 Docker 内存限制（Docker Desktop 设置中）
# 或在 docker-compose.yml 中设置
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
```

### 数据库相关问题

**Q: 数据库连接失败**
```bash
# 检查数据库 URL 格式
# SQLite: sqlite:///./data/bioworkflow.db
# PostgreSQL: postgresql+asyncpg://user:pass@localhost/dbname
```

### 性能优化

**Q: 启动速度慢**
- 使用 SSD 存储
- 增加内存到 8GB+
- 启用 Docker BuildKit: `export DOCKER_BUILDKIT=1`

## 下一步

- [快速入门](quickstart.md) - 了解基本使用
- [配置指南](configuration.md) - 详细配置说明
- [工作流管理](workflows.md) - 创建和运行工作流
