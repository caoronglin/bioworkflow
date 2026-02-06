# BioWorkflow - 生物信息学工作流管理平台

[![Docker Build](https://github.com/yourusername/bioworkflow/actions/workflows/docker-build.yml/badge.svg)](https://github.com/yourusername/bioworkflow/actions/workflows/docker-build.yml)
[![Docs](https://github.com/yourusername/bioworkflow/actions/workflows/docs.yml/badge.svg)](https://yourusername.github.io/bioworkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.5+-green.svg)](https://vuejs.org/)

一个基于 Snakemake 的现代化生物信息学工作流编排平台，具有 Web 界面、知识库、AI 集成和 conda 包管理能力。

## 🎯 核心特性

- **Snakemake 工作流编排**: 原生集成 Snakemake 9.0+，支持复杂流水线设计
- **可视化编辑器**: 基于 Vue Flow 的拖拽式工作流设计器
- **Conda 环境管理**: 自动配置、管理和切换生物学包依赖
- **知识库系统**: 集成 Elasticsearch，支持 AI 驱动的语义搜索
- **MCP 接口**: 支持 AI 工具集成，实现流水线自动编排
- **RESTful API**: 完整的 API 和 Token 认证机制
- **Docker 支持**: 多阶段构建，支持多架构（amd64/arm64）

## 🚀 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/bioworkflow.git
cd bioworkflow

# 复制环境变量文件
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

访问 http://localhost:8000 查看应用。

### 本地开发

#### 后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 启动开发服务器
cd src/backend
uvicorn main:app --reload --port 8000
```

#### 前端

```bash
cd src/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📁 项目结构

```
bioworkflow/
├── src/
│   ├── backend/           # Python 后端
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心引擎
│   │   ├── models/       # 数据模型
│   │   └── services/     # 业务逻辑
│   └── frontend/         # Vue3 前端
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   └── stores/
│       └── package.json
├── tests/                # 测试用例
├── docs/                 # 文档
├── Dockerfile           # Docker 构建文件
├── docker-compose.yml   # Docker Compose 配置
└── pyproject.toml       # Python 项目配置
```

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `DATABASE_URL` | 数据库连接 URL | `sqlite:///./bioworkflow.db` |
| `REDIS_URL` | Redis 连接 URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 密钥 | 必填 |
| `SNAKEMAKE_WORKDIR` | Snakemake 工作目录 | `./workflows` |

完整的配置选项请参考 `.env.example` 文件。

## 🧪 测试

```bash
# 运行后端测试
pytest tests/ -v --cov=src/backend --cov-report=html

# 运行前端测试
cd src/frontend
npm run test

# 代码质量检查
black src/ tests/
ruff check src/ tests/
mypy src/backend
```

## 📚 文档

- [开发指南](CLAUDE.md)
- [快速开始](QUICKSTART.md)
- [API 文档](http://localhost:8000/docs) (运行后访问)
- [详细文档](https://yourusername.github.io/bioworkflow/)

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Snakemake](https://snakemake.github.io/) - 工作流管理系统
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI 组件库

---

<p align="center">
  Made with ❤️ for the bioinformatics community
</p>
