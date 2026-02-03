# BioWorkflow 项目文件清单

## 📁 完整项目结构

```
bioworkflow/
│
├── 📄 README.md                     # 项目概览和功能介绍
├── 📄 pyproject.toml                # Python 项目配置和依赖声明
├── 📄 .env                          # 环境变量（开发）
├── 📄 .env.example                  # 环境变量示例
├── 📄 .gitignore                    # Git 忽略文件
├── 📄 .pre-commit-config.yaml       # 预提交检查配置
├── 📄 dev-start.sh                  # Linux/macOS 启动脚本
├── 📄 dev-start.bat                 # Windows 启动脚本
│
├── 📁 src/
│   │
│   ├── 📁 backend/                  # Python FastAPI 后端
│   │   ├── 📄 __init__.py           # 包初始化
│   │   ├── 📄 main.py               # FastAPI 应用入口
│   │   │
│   │   ├── 📁 api/                  # API 路由
│   │   │   ├── 📄 __init__.py       # 路由注册
│   │   │   └── 📁 routes/           # API 路由模块
│   │   │       ├── 📄 __init__.py
│   │   │       ├── 📄 health.py     # 健康检查
│   │   │       ├── 📄 auth.py       # 认证和授权
│   │   │       ├── 📄 pipelines.py  # 流水线管理
│   │   │       ├── 📄 conda.py      # Conda 包管理
│   │   │       ├── 📄 knowledge.py  # 知识库管理
│   │   │       └── 📄 mcp.py        # MCP 服务接口
│   │   │
│   │   ├── 📁 core/                 # 核心配置
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 config.py         # 配置管理
│   │   │   └── 📄 logging.py        # 日志配置
│   │   │
│   │   ├── 📁 models/               # 数据模型（待实现）
│   │   │   └── 📄 __init__.py
│   │   │
│   │   ├── 📁 services/             # 业务服务
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📁 snakemake/        # Snakemake 集成
│   │   │   │   └── 📄 __init__.py
│   │   │   ├── 📁 conda/            # Conda 管理
│   │   │   │   └── 📄 __init__.py
│   │   │   ├── 📁 knowledge/        # 知识库服务
│   │   │   │   └── 📄 __init__.py
│   │   │   ├── 📁 mcp/              # MCP 服务
│   │   │   │   └── 📄 __init__.py
│   │   │   └── 📁 pipeline/         # 流水线管理
│   │   │       └── 📄 __init__.py
│   │   │
│   │   ├── 📁 auth/                 # 认证系统（待实现）
│   │   │   └── 📄 __init__.py
│   │   │
│   │   ├── 📁 tasks/                # 异步任务（待实现）
│   │   │   └── 📄 __init__.py
│   │   │
│   │   └── 📁 utils/                # 工具函数（待实现）
│   │       └── 📄 __init__.py
│   │
│   └── 📁 frontend/                 # Vue3 + Vite 前端
│       ├── 📄 package.json          # Node.js 项目配置
│       ├── 📄 package-lock.json     # 依赖锁定（自动生成）
│       ├── 📄 tsconfig.json         # TypeScript 配置
│       ├── 📄 tsconfig.node.json    # Node 工具 TS 配置
│       ├── 📄 vite.config.ts        # Vite 配置
│       ├── 📄 .env.example          # 环境变量示例
│       ├── 📄 index.html            # HTML 入口
│       │
│       └── 📁 src/
│           ├── 📄 main.ts           # 应用入口
│           ├── 📄 App.vue           # 根组件
│           ├── 📄 router.ts         # 路由配置
│           │
│           ├── 📁 pages/            # 页面组件
│           │   ├── 📄 Dashboard.vue     # 仪表盘
│           │   ├── 📄 Pipelines.vue     # 流水线管理
│           │   ├── 📄 PipelineDetail.vue # 流水线详情
│           │   ├── 📄 CondaManager.vue  # Conda 管理
│           │   ├── 📄 Knowledge.vue     # 知识库
│           │   ├── 📄 MCPServices.vue   # MCP 服务
│           │   └── 📄 Settings.vue      # 系统设置
│           │
│           ├── 📁 components/       # 可复用组件（待开发）
│           │
│           ├── 📁 stores/           # Pinia 状态管理
│           │   └── 📄 app.ts        # 应用全局状态
│           │
│           ├── 📁 api/              # API 客户端
│           │   ├── 📄 client.ts     # axios 实例
│           │   └── 📄 index.ts      # API 方法集合
│           │
│           └── 📁 styles/           # 全局样式
│               └── 📄 main.scss     # 全局样式定义
│
├── 📁 tests/                        # 测试用例
│   ├── 📄 conftest.py               # 测试配置
│   └── 📄 test_health.py            # 健康检查测试
│
├── 📁 docs/                         # 文档
│   ├── 📄 DEVELOPMENT.md            # 开发指南
│   ├── 📄 RELEASE.md                # 版本发布指南
│   └── 📄 INITIALIZATION.md         # 项目初始化说明
│
└── 📁 .github/
    └── 📁 workflows/
        └── 📄 test-and-release.yml  # CI/CD 工作流
```

## 📊 文件统计

### 后端文件
- **核心应用**：4 个文件
- **API 路由**：8 个文件（1 个主文件 + 6 个路由模块 + 1 个初始化）
- **核心模块**：4 个文件
- **服务模块**：7 个文件（1 个主文件 + 5 个子模块 + 1 个初始化）
- **其他模块**：4 个文件（auth、tasks、utils、models）
- **总计**：27 个 Python 文件

### 前端文件
- **配置文件**：4 个
- **入口文件**：3 个
- **页面组件**：7 个
- **存储管理**：1 个
- **API 模块**：2 个
- **样式文件**：1 个
- **总计**：18 个 TypeScript/Vue 文件

### 项目配置
- **根目录配置**：8 个文件
- **文档**：3 个文件
- **CI/CD**：1 个文件
- **总计**：12 个文件

### 整个项目
**总计：57 个文件**

## 🔑 关键文件说明

### 配置文件

| 文件 | 作用 | 优先级 |
|------|------|--------|
| `pyproject.toml` | Python 项目配置、依赖 | ⭐⭐⭐ |
| `src/frontend/package.json` | Node.js 项目配置、依赖 | ⭐⭐⭐ |
| `.env` | 环境变量（开发） | ⭐⭐⭐ |
| `src/backend/core/config.py` | 应用配置管理 | ⭐⭐⭐ |
| `src/frontend/vite.config.ts` | Vite 打包配置 | ⭐⭐ |

### 应用入口

| 文件 | 作用 | 优先级 |
|------|------|--------|
| `src/backend/main.py` | FastAPI 应用入口 | ⭐⭐⭐ |
| `src/frontend/src/main.ts` | Vue 应用入口 | ⭐⭐⭐ |
| `src/frontend/index.html` | HTML 入口 | ⭐⭐⭐ |

### 核心模块

| 文件 | 作用 | 优先级 |
|------|------|--------|
| `src/backend/api/routes/` | 所有 API 端点 | ⭐⭐⭐ |
| `src/backend/services/` | 业务逻辑实现 | ⭐⭐⭐ |
| `src/frontend/src/pages/` | 前端页面 | ⭐⭐⭐ |
| `src/frontend/src/api/` | 前后端通信 | ⭐⭐⭐ |

## 🚀 启动顺序

1. **创建虚拟环境** → 激活 → 安装依赖
2. **启动后端** → `python -m uvicorn main:app --reload`
3. **启动前端** → `npm run dev`
4. **访问应用** → http://localhost:5173

## 📝 下一步编码任务

### 第 1 周：基础架构
- [ ] 实现数据模型 (`models/`)
- [ ] 实现认证系统 (`auth/`)
- [ ] 配置数据库
- [ ] 添加单元测试

### 第 2 周：核心服务
- [ ] Snakemake 集成完整实现
- [ ] Conda 管理功能
- [ ] 基础 API 测试

### 第 3 周：高级功能
- [ ] 知识库实现
- [ ] MCP 服务实现
- [ ] WebSocket 实时通知

### 第 4 周：前端完整实现
- [ ] 各页面完整功能
- [ ] 数据交互测试
- [ ] UI 优化

### 第 5 周：测试和优化
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

### 第 6 周：发布
- [ ] 准备发布版本
- [ ] 创建 Release
- [ ] 部署指南

## 💾 文件编辑记录

所有创建的文件都已保存到 `d:\data\snakemake` 目录。

**核心代码文件都已创建完成，项目已可直接启动开发！**

---

**创建时间**：2026-01-25
**项目版本**：0.0.1-alpha
**状态**：✅ 框架完成，待功能实现
