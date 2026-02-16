# BioWorkflow 执行计划

## 📋 当前状态

**P0 安全任务：✅ 100% 完成 (3/3)**
- ✅ Task #1: 修复默认SECRET_KEY硬编码问题
- ✅ Task #2: 实现完整的速率限制中间件
- ✅ Task #3: 添加HTTP安全响应头

**系统安全等级**: 🔒 生产级安全标准

---

## 🎯 Phase 1: 核心基础设施 (本周内完成)

### 优先级: 🔴 Critical

### Task #1: 异步化 Snakemake 工作流执行
**状态**: ⏳ 待执行 | **预估工时**: 3-4天

**核心问题**:
```
当前: Snakemake同步执行 → 阻塞FastAPI事件循环
     ↓
结果: 高并发时系统完全无响应
     ↓
需求: 异步化改造，支持并发工作流执行
```

**Snakemake 最佳实践** (从DeepWiki分析):
- Snakemake支持多种执行后端(local, cluster, cloud)
- 使用`--executor`参数指定执行器
- 使用`--latency-wait`处理文件系统延迟
- 支持容器化部署

**技术方案**:

```python
# 1. Celery任务封装架构
┌─────────────────┐
│  API 请求       │
└────────┬────────┘
         │
┌────────▼────────┐
│ Celery 任务队列 │
│  (Redis/Rabbit) │
└────────┬────────┘
         │
┌────────▼────────┐
│ Worker 执行器   │
│ - 本地执行      │
│ - 集群执行      │
│ - 云执行        │
└─────────────────┘

# 2. 核心代码结构
src/backend/services/snakemake/
├── __init__.py
├── tasks.py          # Celery任务定义
├── engine.py         # 执行引擎封装
├── executor.py       # 执行器管理
├── progress.py       # 进度追踪
└── models.py         # 数据模型
```

**核心实现代码**:

```python
# src/backend/services/snakemake/tasks.py
from celery import shared_task, Task
from celery.exceptions import SoftTimeLimitExceeded
import snakemake
from datetime import datetime

class SnakemakeTask(Task):
    """Snakemake Celery Task with comprehensive tracking"""

    _engine = None

    def __call__(self, *args, **kwargs):
        """Initialize engine on first call"""
        if self._engine is None:
            from .engine import WorkflowEngine
            self._engine = WorkflowEngine()
        return super().__call__(*args, **kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"❌ Snakemake task {task_id} failed: {exc}")

        execution_id = kwargs.get('execution_id')
        if execution_id:
            _update_execution_status(
                execution_id=execution_id,
                status="failed",
                error=str(exc),
                error_traceback=str(einfo),
                failed_at=datetime.utcnow()
            )

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"✅ Snakemake task {task_id} completed successfully")

        execution_id = kwargs.get('execution_id')
        if execution_id:
            _update_execution_status(
                execution_id=execution_id,
                status="completed",
                result=retval,
                completed_at=datetime.utcnow()
            )

            # Trigger notification
            event_bus.publish("workflow.completed", {
                "execution_id": execution_id,
                "result": retval,
            })


@shared_task(
    base=SnakemakeTask,
    bind=True,
    name="snakemake.execute_workflow",
    queue="workflow",
    max_retries=3,
    soft_time_limit=3600,  # 1 hour
    time_limit=7200,  # 2 hours
)
def execute_workflow(
    self,
    workflow_id: str,
    execution_id: str,
    workdir: str,
    targets: list = None,
    dry_run: bool = False,
    config: dict = None,
    **kwargs
):
    """
    Execute Snakemake workflow asynchronously via Celery

    This task runs the actual Snakemake execution in a background worker,
    allowing the API to remain responsive and enabling features like:
    - Workflow cancellation
    - Progress tracking
    - Automatic retries
    - Resource management

    Args:
        self: Celery task instance (provided by bind=True)
        workflow_id: Unique identifier for the workflow definition
        execution_id: Unique identifier for this execution instance
        workdir: Working directory for workflow execution
        targets: Specific targets to build (None = all)
        dry_run: If True, only validate without execution
        config: Additional workflow configuration parameters
        **kwargs: Additional Snakemake options

    Returns:
        dict: Execution results including:
            - execution_id: Execution identifier
            - status: Final status (success/failure)
            - summary: Execution statistics
            - outputs: Generated output files

    Raises:
        SoftTimeLimitExceeded: If execution exceeds soft time limit
        Exception: For other execution failures (will trigger retry)

    Example:
        ```python
        # Submit workflow execution
        task = execute_workflow.delay(
            workflow_id="rna-seq-pipeline",
            execution_id="exec-123",
            workdir="/workflows/exec-123",
            targets=["results/counts.txt"],
        )

        # Check status
        result = task.get(timeout=10)
        ```
    """
    from backend.services.snakemake.engine import WorkflowEngine
    from backend.services.snakemake.progress import ProgressTracker

    logger.info(f"🚀 Starting workflow execution: {execution_id}")

    # Initialize progress tracker
    progress_tracker = ProgressTracker(execution_id, self)

    try:
        # Update status to running
        _update_execution_status(
            execution_id=execution_id,
            status="running",
            started_at=datetime.utcnow()
        )

        # Report initial progress
        progress_tracker.update(0, "Initializing workflow...")

        # Build workflow engine with progress callback
        engine = WorkflowEngine(
            workdir=workdir,
            config=config,
            progress_callback=progress_tracker.handle_event,
        )

        # Update progress
        progress_tracker.update(10, "Loading workflow definition...")

        # Load workflow
        workflow = engine.load_workflow(workflow_id)

        # Update progress
        progress_tracker.update(20, "Building execution DAG...")

        # Build DAG
        dag = engine.build_dag(workflow, targets=targets)

        # Check if dry run
        if dry_run:
            logger.info(f"🧪 Dry run mode for {execution_id}")
            progress_tracker.update(50, "Validating workflow (dry run)...")

            result = engine.validate(dag)

            progress_tracker.update(100, "Validation complete")

            return {
                "execution_id": execution_id,
                "status": "validated",
                "dry_run": True,
                "summary": result.summary(),
                "would_execute": result.jobs_count(),
            }

        # Execute workflow
        logger.info(f"▶️ Executing workflow: {execution_id}")
        progress_tracker.update(30, "Starting execution...")

        result = engine.execute(
            dag=dag,
            executor="celery",  # Use Celery-aware executor
            latency_wait=kwargs.get("latency_wait", 5),
            restart_times=kwargs.get("restart_times", 3),
            keep_going=kwargs.get("keep_going", False),
            verbose=kwargs.get("verbose", False),
        )

        # Complete progress
        progress_tracker.update(100, "Execution complete")

        logger.info(f"✅ Workflow execution completed: {execution_id}")

        return {
            "execution_id": execution_id,
            "status": "success",
            "summary": result.summary(),
            "outputs": result.output_files(),
            "duration": result.duration(),
        }

    except SoftTimeLimitExceeded:
        logger.error(f"⏱️ Workflow {execution_id} exceeded time limit")
        progress_tracker.update(0, "Time limit exceeded", failed=True)

        _update_execution_status(
            execution_id=execution_id,
            status="timeout",
            error="Execution exceeded time limit",
            timeout_at=datetime.utcnow()
        )

        # Retry with exponential backoff
        raise self.retry(
            exc=Exception("Time limit exceeded"),
            countdown=60 * (self.request.retries + 1)
        )

    except Exception as exc:
        logger.exception(f"❌ Workflow {execution_id} failed: {exc}")
        progress_tracker.update(0, f"Failed: {str(exc)}", failed=True)

        _update_execution_status(
            execution_id=execution_id,
            status="failed",
            error=str(exc),
            error_traceback=traceback.format_exc(),
            failed_at=datetime.utcnow()
        )

        # Retry if attempts remaining
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # Exponential backoff
            logger.info(f"🔄 Retrying workflow {execution_id} in {retry_delay}s (attempt {self.request.retries + 1}/{self.max_retries})")

            _update_execution_status(
                execution_id=execution_id,
                status="retrying",
                retry_count=self.request.retries + 1,
                next_retry_at=datetime.utcnow() + timedelta(seconds=retry_delay)
            )

            raise self.retry(exc=exc, countdown=retry_delay)

        # Max retries exceeded
        logger.error(f"💥 Workflow {execution_id} failed after {self.max_retries} retries")

        _update_execution_status(
            execution_id=execution_id,
            status="failed_permanently",
            error=f"Failed after {self.max_retries} retries: {str(exc)}",
            failed_at=datetime.utcnow()
        )

        # Notify on permanent failure
        event_bus.publish("workflow.failed_permanently", {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "error": str(exc),
            "retry_count": self.max_retries,
        })

        raise
