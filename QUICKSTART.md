# BioWorkflow 快速参考

## 🎯 项目概述一句话

**BioWorkflow** 是一个基于 Snakemake 的现代化生物信息学工作流管理平台，集 Web 界面、知识库、AI 集成和 Conda 包管理于一体。

## ⚡ 30 秒快速开始

```bash
# Windows
dev-start.bat

# Linux/macOS
./dev-start.sh

# 然后访问：
# 🌐 前端: http://localhost:5173
# 🔌 API: http://localhost:8000
# 📖 文档: http://localhost:8000/docs
```

## 📂 我需要修改什么文件？

| 要做的事 | 在这里修改 |
|--------|----------|
| 添加新 API 端点 | `src/backend/api/routes/*.py` |
| 添加新页面 | `src/frontend/src/pages/*.vue` |
| 修改配置 | `src/backend/core/config.py` |
| 修改样式 | `src/frontend/src/styles/` |
| 添加路由 | `src/frontend/src/router.ts` |
| 实现业务逻辑 | `src/backend/services/*/` |
| 写测试 | `tests/test_*.py` |

## 🔄 日常开发工作流

```bash
# 1. 创建分支
git checkout -b feature/my-feature

# 2. 开发功能（在 IDE 中编辑代码）

# 3. 运行测试
pytest tests/ -v

# 4. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 5. 推送
git push origin feature/my-feature

# 6. 在 GitHub 创建 PR

# 7. 合并后发布
git tag v0.1.0
git push origin v0.1.0
```

## 📚 API 文档快速查看

打开 http://localhost:8000/docs 查看所有 API 端点的实时文档。

## 🗂️ 核心目录速查

```
src/backend/
  ├─ main.py              # 应用主入口
  ├─ api/routes/          # 所有 API 端点
  └─ services/            # 业务逻辑

src/frontend/
  ├─ src/pages/           # 所有页面
  ├─ src/api/             # API 客户端
  └─ vite.config.ts       # 构建配置

tests/                    # 单元测试
docs/                     # 文档
```

## 🎨 前端快速开发

### 创建新页面
```vue
<template>
  <div class="page">
    <!-- 你的内容 -->
  </div>
</template>

<script setup lang="ts">
// 逻辑代码
</script>

<style scoped lang="scss">
// 样式
</style>
```

保存到 `src/frontend/src/pages/MyPage.vue`，然后在 `router.ts` 中添加：
```typescript
{
  path: '/my-page',
  component: () => import('@/pages/MyPage.vue'),
  meta: { title: '我的页面' },
}
```

### 调用 API
```typescript
import { pipelinesAPI } from '@/api'

// 获取数据
const data = await pipelinesAPI.list()
```

## 🔧 后端快速开发

### 创建新 API 端点
```python
# src/backend/api/routes/my_module.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

在 `src/backend/api/__init__.py` 中注册：
```python
from .routes.my_module import router as my_router
router.include_router(my_router, prefix="/my-module")
```

### 添加依赖
编辑 `pyproject.toml` 的 `dependencies` 部分，然后：
```bash
pip install -e ".[dev]"
```

## 🧪 测试速查

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_health.py

# 生成覆盖率报告
pytest tests/ --cov=src/backend --cov-report=html

# 运行特定测试函数
pytest tests/test_health.py::test_health_status
```

## 📝 常见任务

### 我想...

**添加新的 Conda 频道**
- 编辑 `.env` 中的 `CONDA_CHANNELS`
- 或在前端设置页面配置

**创建新的 Snakemake 工作流**
- 在 `workflows/` 目录创建 Snakefile
- 通过 API 上传或指定路径

**添加知识库文档**
- 上传到 `knowledge_base/` 目录
- 或通过 Web 界面上传

**注册 MCP 服务**
- 调用 `POST /api/mcp/services/register` 端点
- 提供服务端点和能力列表

**发布新版本**
- 更新版本号（3 个位置）
- 创建 Git tag
- GitHub Actions 自动发布

## 🐛 调试技巧

### 后端调试
```python
# 添加日志
from loguru import logger
logger.debug("Debug message", data=my_data)

# 在代码中调试
import pdb; pdb.set_trace()
```

### 前端调试
```vue
<!-- Vue DevTools 浏览器扩展 -->
<!-- 在浏览器 DevTools 中查看组件树和状态 -->

<!-- 控制台输出 -->
console.log('Debug:', data)
```

## 🌐 环境变量速查

| 变量 | 含义 | 示例 |
|------|------|------|
| `DEBUG` | 调试模式 | `true` |
| `PORT` | 服务端口 | `8000` |
| `CONDA_CHANNELS` | Conda 频道 | `conda-forge,bioconda` |
| `DATABASE_URL` | 数据库连接 | `sqlite:///./db.db` |
| `SECRET_KEY` | JWT 密钥 | `your-secret` |
| `VITE_API_URL` | API 地址 | `http://localhost:8000/api` |

## 📦 依赖管理

### 添加 Python 依赖
```bash
# 编辑 pyproject.toml，然后
pip install -e ".[dev]"
```

### 添加 Node 依赖
```bash
cd src/frontend
npm install package-name
```

## 🚢 发布检查清单

- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 版本号更新（3 个位置）
- [ ] CHANGELOG 更新
- [ ] 文档更新
- [ ] Git tag 创建
- [ ] Release 说明编写

## 💡 性能优化建议

### 后端
- 使用异步操作处理 I/O
- 实现缓存机制
- 数据库查询优化

### 前端
- 使用代码分割
- 启用 gzip 压缩
- 图片懒加载

## 🔐 安全检查清单

- [ ] 环境变量中的敏感信息不提交
- [ ] API Token 定期轮换
- [ ] 使用 HTTPS（生产环境）
- [ ] SQL 注入防护
- [ ] CORS 正确配置
- [ ] 输入验证

## 🎓 学习资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Snakemake 文档](https://snakemake.readthedocs.io/)
- [Conda 文档](https://docs.conda.io/)

## 🆘 遇到问题？

1. 查看 [开发指南](./docs/DEVELOPMENT.md)
2. 搜索 GitHub Issues
3. 查看错误日志：`logs/bioworkflow.log`
4. 运行诊断：`python -m bioworkflow --version`

## 📞 获取帮助

- 📖 文档：`docs/` 目录
- 💬 讨论：GitHub Discussions
- 🐛 报告 Bug：GitHub Issues
- 📧 邮件：your.email@example.com

---

**提示**：这个文件经常需要查阅，建议保存为浏览器书签或收藏！

**最后更新**：2026-01-25
