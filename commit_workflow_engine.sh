#!/bin/bash
# Commit script for async workflow engine

cd /home/crl/snakemake

# Add new files
git add src/backend/services/snakemake/workflow_engine.py
git add src/backend/services/snakemake/__init__.py
git add src/backend/api/routes/workflows.py
git add src/backend/api/__init__.py
git add src/backend/api/routes/__init__.py
git add src/backend/main.py
git add examples/async_workflow_example.py
git add tests/test_workflow_engine.py

# Create commit
git commit -m "$(cat <<'COMMIT_MSG'
feat(workflow): 实现异步Snakemake工作流引擎

实现完整的异步工作流执行引擎，遵循Snakemake 8.x最佳实践:

核心功能:
- 基于asyncio的异步工作流执行
- 非阻塞API，支持高并发工作流提交
- 完整的工作流生命周期管理(提交/暂停/恢复/取消)
- 实时进度追踪和状态管理
- 支持Snakemake API和子进程两种执行模式

API端点:
- POST /workflows/submit - 提交工作流
- GET /workflows/{id}/status - 查询状态
- GET /workflows/list - 列出工作流
- POST /workflows/{id}/cancel - 取消工作流
- POST /workflows/{id}/pause - 暂停工作流
- POST /workflows/{id}/resume - 恢复工作流
- GET /workflows/{id}/stream - SSE日志流
- WebSocket /workflows/{id}/logs - WebSocket日志

测试套件:
- 完整的单元测试覆盖
- 并发提交测试
- 进度回调测试
- 生命周期管理测试

文档:
- 详细的使用示例 (examples/async_workflow_example.py)
- API文档和类型注解
- 遵循Snakemake 8.x异步最佳实践

Closes Task #1: 异步化Snakemake工作流执行

🤖 Generated with [Claude Code](https://claude.com/claude-code)
COMMIT_MSG
)"
