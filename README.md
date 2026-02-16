# BioWorkflow - 生物信息学工作流管理平台

[![Docker Build](https://github.com/yourusername/bioworkflow/actions/workflows/docker-build.yml/badge.svg)](https://github.com/yourusername/bioworkflow/actions/workflows/docker-build.yml)
[![Docs](https://github.com/yourusername/bioworkflow/actions/workflows/docs.yml/badge.svg)](https://yourusername.github.io/bioworkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/vue-3.5+-green.svg)](https://vuejs.org/)

一个基于 Snakemake 的现代化生物信息学工作流编排平台，采用 Python 3.14 和最新技术栈构建，具有 Web 界面、知识库、AI 集成和 conda 包管理能力。

## 🎯 核心特性

- **Snakemake 工作流编排**: 原生集成 Snakemake 9.0+，支持复杂流水线设计
- **可视化编辑器**: 基于 Vue Flow 的拖拽式工作流设计器
- **Conda 环境管理**: 自动配置、管理和切换生物学包依赖
- **知识库系统**: 集成 Elasticsearch，支持 AI 驱动的语义搜索
- **MCP 接口**: 支持 AI 工具集成，实现流水线自动编排
- **RESTful API**: 完整的 API 和 Token 认证机制
- **Docker 支持**: 多阶段构建，支持多架构（amd64/arm64）
- **高性能**: 异步架构、连接池、缓存层、性能监控

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

#### 要求

- Python 3.14+
- Node.js 20+
- Redis 7+
- Elasticsearch 8+ (可选)

#### 后端

```bash
# 创建虚拟环境
python3.14 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 启动开发服务器
cd src/backend
python -m uvicorn main:app --reload --port 8000
```

#### 前端

```bash
cd src/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev        # http://localhost:5173
```

## 📁 项目结构

```
bioworkflow/
├── src/
│   ├── backend/           # Python 后端
│   │   ├── api/          # API 路由层
│   │   ├── core/         # 核心基础设施
│   │   │   ├── interfaces.py    # 抽象接口定义
│   │   │   ├── container.py     # 依赖注入容器
│   │   │   ├── config.py        # 配置管理
│   │   │   ├── database.py      # 数据库连接
│   │   │   ├── performance.py   # 性能优化工具
│   │   │   └── logging.py       # 日志配置
│   │   ├── infrastructure/      # 基础设施实现
│   │   │   ├── cache/           # 缓存实现
│   │   │   ├── database/        # 数据库实现
│   │   │   ├── events/          # 事件系统
│   │   │   ├── metrics/         # 指标收集
│   │   │   └── search/          # 搜索服务
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑层
│   │   └── middleware/   # 中间件
│   └── frontend/         # Vue3 前端
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   ├── stores/
│       │   └── styles/
│       └── package.json
├── tests/                # 测试用例
├── docs/                 # 文档
├── Dockerfile           # Docker 构建文件
├── docker-compose.yml   # Docker Compose 配置
└── pyproject.toml       # Python 项目配置
```

## 🔧 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│           API Layer                 │
│    (Routes, Controllers, Schemas)   │
├─────────────────────────────────────┤
│         Service Layer               │
│   (Business Logic, Workflows)       │
├─────────────────────────────────────┤
│      Infrastructure Layer           │
│  (Cache, Database, Search, Events)  │
├─────────────────────────────────────┤
│        Interface Layer              │
│   (Abstract Interfaces, DI)         │
└─────────────────────────────────────┘
```

### 关键技术

- **依赖注入**: 使用自定义 IoC 容器实现松耦合
- **仓储模式**: 统一数据访问抽象
- **事件驱动**: 解耦模块间通信
- **异步架构**: 全异步支持高并发
- **缓存策略**: 多级缓存（内存 + Redis）
- **性能监控**: Prometheus 指标收集

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_health.py -v

# 运行特定测试函数
pytest tests/test_health.py::test_health_status -v

# 运行带覆盖率报告
pytest tests/ --cov=src/backend --cov-report=html

# 运行性能测试
pytest tests/test_performance.py -v

# 代码质量检查
black src/ tests/
ruff check src/ tests/
mypy src/backend
pre-commit run --all-files
```

## 📚 文档

- [开发指南](CLAUDE.md)
- [快速开始](QUICKSTART.md)
- [API 文档](http://localhost:8000/docs) (运行后访问)
- [详细文档](https://yourusername.github.io/bioworkflow/)

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `DATABASE_URL` | 数据库连接 URL | `sqlite+aiosqlite:///./bioworkflow.db` |
| `REDIS_URL` | Redis 连接 URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 密钥 | 必填 |
| `SNAKEMAKE_WORKDIR` | Snakemake 工作目录 | `./workflows` |
| `ELASTICSEARCH_HOST` | Elasticsearch 主机 | `localhost` |

完整的配置选项请参考 `.env.example` 文件。

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 提交规范

遵循 **Conventional Commits** 格式:
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `perf:` 性能优化
- `test:` 测试更新

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
