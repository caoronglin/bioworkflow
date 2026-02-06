# BioWorkflow 文档

欢迎来到 BioWorkflow 文档！这是一个基于 Snakemake 的现代化生物信息学工作流编排平台。

## 什么是 BioWorkflow？

BioWorkflow 是一个专为生物信息学设计的开源工作流管理平台，它结合了：

- **Snakemake 的强大功能**：工业级的工作流引擎
- **现代化的 Web 界面**：直观的可视化编辑器
- **完整的生态集成**：Conda、知识库、MCP 服务
- **企业级特性**：认证、授权、审计、多租户

## 核心特性

<div class="grid cards" markdown>

- :material-workflow: **工作流编排**

  可视化拖拽编辑器，支持复杂的生物信息学流程设计

- :material-package-variant-closed: **Conda 集成**

  自动管理生物信息学软件包和环境

- :material-database: **知识库**

  内置 AI 驱动的文档管理和问答系统

- :material-connection: **MCP 服务**

  标准化的 AI 工具集成接口

</div>

## 快速开始

### Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/bioworkflow.git
cd bioworkflow

# 启动服务
docker-compose up -d

# 访问应用
open http://localhost:8000
```

### 本地开发

```bash
# 后端
pip install -e ".[dev]"
uvicorn backend.main:app --reload

# 前端
cd src/frontend
npm install
npm run dev
```

## 文档结构

- **快速开始**: 安装指南、快速入门、配置说明
- **用户指南**: 工作流、Conda、知识库、MCP 服务
- **部署指南**: Docker、Kubernetes、生产配置
- **开发文档**: 架构设计、API 文档、贡献指南
- **参考**: 环境变量、CLI 命令、常见问题

## 社区与支持

- **GitHub Issues**: [报告问题](https://github.com/yourusername/bioworkflow/issues)
- **Discussions**: [讨论区](https://github.com/yourusername/bioworkflow/discussions)
- **文档**: [完整文档](https://yourusername.github.io/bioworkflow/)

## 许可证

BioWorkflow 采用 [MIT 许可证](https://opensource.org/licenses/MIT)。

---

보다 많은 정보를 원하시면 왼쪽 내비게이션 메뉴를 사용해 보세요.
