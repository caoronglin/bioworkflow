# BioWorkflow - 生物信息学工作流管理平台

一个基于 Snakemake 的现代化生物信息学工作流编排平台，具有 Web 界面、知识库、AI 集成和 conda 包管理能力。

## 🎯 核心特性

- **Snakemake 工作流编排**：原生集成 Snakemake 9.0+，支持复杂流水线设计
- **Conda 环境管理**：自动配置、管理和切换生物学包依赖
- **Web 界面**：基于 Vite + Vue3 的现代化简约设计
- **知识库系统**：集成知识库，支持 AI 查询和学习
- **MCP 接口**：支持 AI 工具集成（类似 n8n），实现流水线自动编排
- **API 与认证**：完整的 REST API 和 Token 认证机制，支持跨平台调用
- **版本管理**：每个功能发布对应 GitHub Release，支持代码回滚
- **模块化设计**：所有功能模块化，易于扩展和维护
- **多语言插件系统**：支持 Python、R、Shell 等多种语言的插件

## 🏗️ 项目结构

```
src/
├── backend/                 # Python 后端
│   ├── api/
│   │   └── routes/         # API 路由
│   ├── core/               # 核心引擎
│   ├── models/             # 数据模型
│   ├── services/
│   │   ├── snakemake/      # Snakemake 集成
│   │   ├── conda/          # Conda 管理
│   │   ├── knowledge/      # 知识库
│   │   ├── mcp/            # MCP 接口
│   │   └── pipeline/       # 流水线管理
│   ├── tasks/              # 异步任务
│   ├── auth/               # 认证系统
│   └── utils/              # 工具函数
├── frontend/               # Vue3 前端（Vite）
│   └── src/
│       ├── components/     # 组件库
│       ├── pages/          # 页面
│       ├── stores/         # 状态管理
│       └── api/            # API 客户端
├── docs/                   # 文档
└── tests/                  # 测试用例
```

## 🚀 快速开始

### 后端安装

```bash
cd src/backend
pip install -e ".[dev]"
```

### 前端安装

```bash
cd src/frontend
npm install
npm run dev
```

## 📚 核心模块说明

### 1. Snakemake 集成
- 支持 Snakemake 工作流的加载、验证和执行
- 实时监控工作流进度
- 支持工作流版本管理

### 2. Conda 管理
- 自动检测系统 conda 环境
- 支持在线换源
- 包依赖解析和自动安装
- 环境克隆和备份

### 3. 知识库
- 文档管理和检索
- AI 驱动的语义搜索
- 与工作流集成的上下文建议

### 4. MCP 接口
- 支持第三方 AI 工具集成
- 流水线编排 API
- 事件驱动的数据流

### 5. API 与认证
- RESTful API 设计
- JWT Token 认证
- 细粒度权限控制

## 📦 依赖要求

- **Python 3.13+** (推荐 3.14)
- **Node.js 20+** (前端)
- **Snakemake 9.0+**
- **Conda/Miniconda** (最新版)
- **Pandas 3.0+** (PyArrow 后端)
- **NumPy 2.2+**

## 🔄 开发流程

1. 新增功能开发
2. 完整测试
3. 功能转为可选项
4. 发布 GitHub Release
5. 可随时回滚到历史版本

## 📖 参考资源

- [Snakemake 文档](https://snakemake.readthedocs.io/en/stable/)
- [n8n 架构](https://docs.n8n.io/)
- [WeKnora 知识库](https://github.com/Tencent/WeKnora)

## 📄 许可证

MIT License

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

**当前版本**：v0.1.0
**最后更新**：2026-01-25
**Python 版本**：3.13+ / 3.14
