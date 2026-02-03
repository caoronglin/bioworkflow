# BioWorkflow 开发指南

## 项目简介

BioWorkflow 是一个基于 Snakemake 的现代化生物信息学工作流编排平台，提供完整的 Web 界面、知识库、AI 集成和 conda 包管理。

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+
- conda/miniconda（可选）

### 开发环境设置

#### Linux/macOS

```bash
# 克隆项目
git clone https://github.com/yourusername/bioworkflow.git
cd bioworkflow

# 使用启动脚本
chmod +x dev-start.sh
./dev-start.sh
```

#### Windows

```bash
# 克隆项目
git clone https://github.com/yourusername/bioworkflow.git
cd bioworkflow

# 运行启动脚本
dev-start.bat
```

### 手动启动

#### 启动后端

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"

# 启动服务
cd src/backend
python -m uvicorn main:app --reload
```

后端将在 `http://localhost:8000` 启动

API 文档在 `http://localhost:8000/docs`

#### 启动前端

```bash
# 在另一个终端中
cd src/frontend

# 安装依赖
npm install

# 启动开发服务
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 项目结构

```
bioworkflow/
├── src/
│   ├── backend/          # Python 后端
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务服务
│   │   ├── auth/         # 认证系统
│   │   ├── utils/        # 工具函数
│   │   ├── tasks/        # 异步任务
│   │   └── main.py       # 入口文件
│   │
│   └── frontend/         # Vue3 前端
│       ├── src/
│       │   ├── pages/    # 页面组件
│       │   ├── components/  # 可复用组件
│       │   ├── stores/   # Pinia 状态管理
│       │   ├── api/      # API 调用
│       │   ├── styles/   # 样式文件
│       │   ├── App.vue   # 根组件
│       │   ├── main.ts   # 入口文件
│       │   └── router.ts # 路由配置
│       └── vite.config.ts
│
├── tests/                # 测试用例
├── docs/                 # 文档
├── .github/workflows/    # CI/CD 工作流
├── pyproject.toml        # Python 项目配置
├── README.md            # 项目说明
└── .env.example         # 环境变量示例
```

## 核心模块开发指南

### 1. 添加新的 API 路由

在 `src/backend/api/routes/` 中创建新文件：

```python
# src/backend/api/routes/new_module.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/endpoint")
async def get_data():
    """获取数据"""
    return {"data": "example"}
```

然后在 `src/backend/api/__init__.py` 中注册：

```python
from .routes.new_module import router as new_module_router
router.include_router(new_module_router, prefix="/new-module", tags=["New Module"])
```

### 2. 添加新的前端页面

在 `src/frontend/src/pages/` 中创建新文件 `NewPage.vue`：

```vue
<template>
  <div class="new-page">
    <el-card>
      <h2>新页面</h2>
      <!-- 内容 -->
    </el-card>
  </div>
</template>

<script setup lang="ts">
// 逻辑代码
</script>

<style scoped lang="scss">
// 样式
</style>
```

在 `src/frontend/src/router.ts` 中注册：

```typescript
{
  path: '/new-page',
  component: () => import('@/pages/NewPage.vue'),
  meta: { title: '新页面' },
}
```

### 3. 添加新的业务服务

在 `src/backend/services/` 中创建新目录或文件：

```python
# src/backend/services/my_service/__init__.py
from .manager import MyServiceManager

__all__ = ["MyServiceManager"]
```

## 测试

### 运行后端测试

```bash
pytest tests/ -v
```

### 运行前端测试

```bash
cd src/frontend
npm test
```

## 代码规范

### 后端代码规范

- 使用 black 进行代码格式化
- 使用 ruff 进行代码检查
- 类型提示使用 mypy 验证

```bash
# 格式化代码
black src/backend

# 检查代码
ruff check src/backend

# 类型检查
mypy src/backend
```

### 前端代码规范

- 使用 ESLint 进行代码检查
- 使用 Prettier 进行代码格式化

```bash
cd src/frontend

# 检查代码
npm run lint

# 格式化代码
npm run format
```

## 版本发布流程

每个新功能完成后应该发布一个 Release：

1. **更新版本号**

   编辑 `pyproject.toml` 和 `src/frontend/package.json` 中的版本号

2. **创建 Git Tag**

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. **GitHub 自动发布**

   GitHub Actions 会自动运行测试并创建 Release

4. **版本回滚**

   ```bash
   git checkout v0.0.1  # 检出旧版本
   git reset --hard HEAD^  # 或重置提交
   ```

## 功能可选性

每个功能在完成后应该设置为可选项，在 `settings` 页面中允许用户启用/禁用特定功能。

## 贡献指南

1. 创建 feature 分支
2. 提交更改
3. 发起 Pull Request
4. 等待代码审查

## 常见问题

### 如何修改 conda 源？

在前端的 Conda 管理页面中，可以直接配置频道源。

### 如何添加新的生物学包？

使用 Conda API 搜索并安装包，或在 Web 界面的 Conda 管理页面操作。

### 如何集成 MCP 服务？

使用 `/api/mcp/services/register` 端点注册新的 MCP 服务。

## 技术栈

- **后端框架**：FastAPI + SQLAlchemy
- **前端框架**：Vue3 + Vite
- **状态管理**：Pinia
- **UI 库**：Element Plus
- **工作流引擎**：Snakemake
- **环境管理**：Conda
- **任务队列**：Celery
- **搜索引擎**：Elasticsearch

## 联系方式

- GitHub Issues：报告 Bug 和提交特性请求
- Email：your.email@example.com

## 许可证

MIT License - 详见 LICENSE 文件

---

**最后更新**：2026-01-25
