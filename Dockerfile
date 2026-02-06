# BioWorkflow 多阶段构建 Dockerfile
# 阶段1: 构建前端
# 阶段2: 构建后端
# 阶段3: 生产镜像

# ==================== 阶段1: 前端构建 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制 package.json 和 lock 文件
COPY src/frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端源代码
COPY src/frontend/ ./

# 构建生产版本
RUN npm run build

# ==================== 阶段2: 后端基础镜像 ====================
FROM python:3.13-slim AS backend-base

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    git \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 Miniconda (用于 Snakemake 和生物信息学工具)
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh

# 设置 Conda 环境变量
ENV PATH=/opt/conda/bin:$PATH
ENV CONDA_DEFAULT_ENV=base

# 配置 Conda 频道
RUN conda config --add channels conda-forge && \
    conda config --add channels bioconda && \
    conda config --set channel_priority strict

# 安装 Snakemake
RUN conda install -y snakemake=9.0 && \
    conda clean -afy

# ==================== 阶段3: 后端构建 ====================
FROM backend-base AS backend-builder

WORKDIR /app

# 复制项目文件
COPY pyproject.toml ./
COPY src/backend ./src/backend
COPY README.md ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -e ".[dev]"

# ==================== 阶段4: 生产镜像 ====================
FROM backend-base AS production

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r bioworkflow && useradd -r -g bioworkflow bioworkflow

# 复制 Python 依赖
COPY --from=backend-builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --from=backend-builder /app/src/backend ./src/backend
COPY --from=backend-builder /app/pyproject.toml ./

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./src/frontend/dist

# 创建工作目录
RUN mkdir -p /app/workflows /app/conda_envs /app/knowledge_base /app/logs && \
    chown -R bioworkflow:bioworkflow /app

# 切换到非 root 用户
USER bioworkflow

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
