# BioWorkflow 优化任务清单

> 基于 Snakemake 最佳实践和项目现状深度分析生成

## 📊 执行概览

| 阶段 | 优先级 | 任务数 | 目标 |
|------|--------|--------|------|
| Phase 1 | 🔴 P0 - 核心 | 4 | 系统可用性 |
| Phase 2 | 🟠 P1 - 性能 | 4 | 生产级性能 |
| Phase 3 | 🟡 P2 - 可观测 | 3 | 运维就绪 |
| Phase 4 | 🟢 P3 - 增强 | 3 | 企业级功能 |

**当前状态**: P0已完成3/3 (100%)，建议立即开始Phase 1

---

## Phase 1: 核心可用性 (本周内完成)

### 🔴 Task #1: 异步化 Snakemake 工作流执行
**优先级**: 🔴 Critical | **预估工时**: 3-4天

**现状问题**:
- Snakemake 同步执行阻塞 FastAPI 事件循环
- 高并发时系统完全无响应
- 工作流执行无法取消

**Snakemake 最佳实践**:
```python
# 参考 Snakemake API 设计
# 1. 使用 --dry-run 进行验证
# 2. 使用 --executor 支持多种执行后端
# 3. 使用 --latency-wait 处理文件系统延迟
# 4. 使用 --restart-times 自动重试
```

**实现方案**:

1. **Celery 异步任务封装**:
```python
# src/backend/services/snakemake/tasks.py
from celery import shared_task, Task
from celery.exceptions import SoftTimeLimitExceeded
import snakemake

class SnakemakeTask(Task):
    """Snakemake Celery Task with progress tracking"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log failure details"""
        logger.error(f"Snakemake task {task_id} failed: {exc}")
        # Update execution status in database

    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful completion"""
        logger.info(f"Snakemake task {task_id} completed successfully")
        # Update execution status and trigger notifications

@shared_task(base=SnakemakeTask, bind=True, max_retries=3, soft_time_limit=3600)
def execute_workflow(
    self,
    workflow_id: str,
    execution_id: str,
    workdir: str,
    targets: list = None,
    dry_run: bool = False,
    **kwargs
):
    """
    Execute Snakemake workflow asynchronously

    Args:
        workflow_id: Workflow definition ID
        execution_id: Execution tracking ID
        workdir: Working directory for workflow
        targets: Specific targets to build
        dry_run: If True, only validate without execution
        **kwargs: Additional Snakemake options

    Returns:
        dict: Execution results and statistics
    """
    from backend.services.snakemake.engine import WorkflowEngine

    try:
        # Update status to running
        _update_execution_status(execution_id, "running")

        # Execute workflow
        result = WorkflowEngine.execute(
            workdir=workdir,
            targets=targets,
            dry_run=dry_run,
            executor="celery",  # Use Celery-aware executor
            latency_wait=kwargs.get("latency_wait", 5),
            restart_times=kwargs.get("restart_times", 3),
            # Progress callback
            progress_callback=lambda msg: _report_progress(self, execution_id, msg),
        )

        # Update status to completed
        _update_execution_status(execution_id, "completed", result=result)

        return {
            "execution_id": execution_id,
            "status": "success",
            "summary": result.summary(),
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Workflow {execution_id} exceeded time limit")
        _update_execution_status(execution_id, "timeout")
        self.retry(countdown=60)  # Retry after 1 minute

    except Exception as exc:
        logger.exception(f"Workflow {execution_id} failed: {exc}")
        _update_execution_status(execution_id, "failed", error=str(exc))

        # Retry if attempts remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

        raise

def _update_execution_status(execution_id: str, status: str, **kwargs):
    """Update workflow execution status in database"""
    from backend.services.pipeline.models import WorkflowExecution

    execution = WorkflowExecution.get_by_id(execution_id)
    if execution:
        execution.status = status
        execution.updated_at = datetime.utcnow()

        if "result" in kwargs:
            execution.result_data = kwargs["result"]
        if "error" in kwargs:
            execution.error_message = kwargs["error"]

        execution.save()

        # Publish status change event
        event_bus.publish("workflow.status_changed", {
            "execution_id": execution_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        })

def _report_progress(task, execution_id: str, message: str):
    """Report workflow progress to Celery"""
    task.update_state(
        state="PROGRESS",
        meta={
            "execution_id": execution_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
```

2. **API层集成**:
```python
# src/backend/api/routes/pipelines.py
from fastapi import APIRouter, BackgroundTasks, Depends
from backend.services.snakemake.tasks import execute_workflow

@router.post("/workflows/{workflow_id}/execute")
async def start_workflow_execution(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """
    Start a new workflow execution asynchronously
    """
    # Create execution record
    execution = WorkflowExecution.create(
        workflow_id=workflow_id,
        user_id=user.id,
        status="pending",
    )

    # Submit to Celery
    task = execute_workflow.delay(
        workflow_id=workflow_id,
        execution_id=execution.id,
        workdir=f"./workflows/{execution.id}",
    )

    # Update execution with task ID
    execution.celery_task_id = task.id
    execution.status = "queued"
    execution.save()

    return {
        "execution_id": execution.id,
        "task_id": task.id,
        "status": "queued",
        "message": "Workflow execution queued successfully",
    }

@router.get("/executions/{execution_id}/status")
async def get_execution_status(
    execution_id: str,
    user: User = Depends(get_current_user),
):
    """
    Get workflow execution status and progress
    """
    from celery.result import AsyncResult

    execution = WorkflowExecution.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Check Celery task status
    if execution.celery_task_id:
        task_result = AsyncResult(execution.celery_task_id)
        celery_status = task_result.status

        # Sync status if needed
        if celery_status == "SUCCESS" and execution.status != "completed":
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.save()
        elif celery_status == "FAILURE" and execution.status != "failed":
            execution.status = "failed"
            execution.error_message = str(task_result.result)
            execution.save()

    return {
        "execution_id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "progress": execution.progress_data,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "error": execution.error_message if execution.status == "failed" else None,
    }
```

**验收标准:**
- [ ] Snakemake 在 Celery 任务中异步执行
- [ ] 支持工作流取消功能
- [ ] 实时进度回调和状态更新
- [ ] 失败自动重试机制（最多3次）
- [ ] WebSocket 或 Server-Sent Events 实时推送进度

---

## 后续任务请查看 OPTIMIZED_TASKS.md 完整清单

**建议下一步**: 查看完整的优化任务清单，根据业务优先级选择执行路径。
