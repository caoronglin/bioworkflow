"""Pipeline 服务 - 工作流执行管理

提供流水线管理、调度和执行功能，支持异步执行和并发控制
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger

from backend.core.database import get_session
from backend.core.events import event_bus
from backend.models.pipeline import (
    ExecutionStatus,
    Pipeline,
    PipelineExecution,
)
from backend.services.snakemake.engine import (
    ExecutionConfig,
    SnakemakeEngine,
)


class PipelineError(Exception):
    """流水线错误"""
    pass


class PipelineNotFoundError(PipelineError):
    """流水线不存在"""
    pass


class PipelineExecutionError(PipelineError):
    """流水线执行错误"""
    pass


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    status: ExecutionStatus
    output_dir: Optional[str] = None
    log_path: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PipelineService:
    """
    流水线服务

    负责：
    - 流水线 CRUD 操作
    - 执行调度和管理
    - 状态跟踪
    - 并发控制
    """

    def __init__(self):
        self.engine = SnakemakeEngine()
        self._running_executions: dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(5)  # 最大并发执行数

    async def create_pipeline(
        self,
        name: str,
        description: Optional[str],
        snakefile_path: str,
        owner_id: str,
        conda_environment: Optional[str] = None,
        workdir: Optional[str] = None,
        parameters: Optional[dict] = None,
    ) -> Pipeline:
        """创建新流水线"""
        async with get_session() as session:
            pipeline = Pipeline(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                snakefile_path=snakefile_path,
                owner_id=owner_id,
                conda_environment=conda_environment,
                workdir=workdir,
                parameters=parameters,
            )
            session.add(pipeline)
            await session.commit()

            # 发布事件
            await event_bus.publish(event_bus.Event(
                event_type="pipeline.created",
                payload={"pipeline_id": pipeline.id, "name": name},
            ))

            logger.info(f"创建流水线成功: {pipeline.id} - {name}")
            return pipeline

    async def get_pipeline(self, pipeline_id: str) -> Pipeline:
        """获取流水线详情"""
        async with get_session() as session:
            result = await session.get(Pipeline, pipeline_id)
            if not result:
                raise PipelineNotFoundError(f"流水线不存在: {pipeline_id}")
            return result

    async def update_pipeline(
        self,
        pipeline_id: str,
        **updates: Any,
    ) -> Pipeline:
        """更新流水线"""
        async with get_session() as session:
            result = await session.get(Pipeline, pipeline_id)
            if not result:
                raise PipelineNotFoundError(f"流水线不存在: {pipeline_id}")

            # 更新字段
            allowed_fields = [
                "name", "description", "snakefile_path",
                "conda_environment", "workdir", "parameters", "status",
            ]
            for field, value in updates.items():
                if field in allowed_fields and hasattr(result, field):
                    setattr(result, field, value)

            await session.commit()

            logger.info(f"更新流水线成功: {pipeline_id}")
            return result

    async def delete_pipeline(self, pipeline_id: str) -> None:
        """删除流水线"""
        async with get_session() as session:
            result = await session.get(Pipeline, pipeline_id)
            if not result:
                raise PipelineNotFoundError(f"流水线不存在: {pipeline_id}")

            await session.delete(result)
            await session.commit()

            logger.info(f"删除流水线成功: {pipeline_id}")

    async def execute(
        self,
        pipeline_id: str,
        triggered_by: Optional[str] = None,
        parameters: Optional[dict] = None,
        dry_run: bool = False,
    ) -> ExecutionResult:
        """
        执行流水线

        Args:
            pipeline_id: 流水线 ID
            triggered_by: 触发用户 ID
            parameters: 执行参数
            dry_run: 是否干运行

        Returns:
            执行结果
        """
        # 获取流水线
        pipeline = await self.get_pipeline(pipeline_id)

        # 检查是否已经在运行
        if pipeline_id in self._running_executions:
            raise PipelineExecutionError(f"流水线正在执行中: {pipeline_id}")

        # 创建执行记录
        execution = await self._create_execution(
            pipeline_id=pipeline_id,
            triggered_by=triggered_by,
            parameters=parameters,
        )

        # 发布执行开始事件
        await event_bus.publish(event_bus.Event(
            event_type="execution.started",
            payload={
                "execution_id": execution.id,
                "pipeline_id": pipeline_id,
            },
        ))

        try:
            # 使用信号量控制并发
            async with self._semaphore:
                # 执行任务
                task = asyncio.create_task(
                    self._run_execution(
                        execution=execution,
                        pipeline=pipeline,
                        parameters=parameters,
                        dry_run=dry_run,
                    )
                )
                self._running_executions[execution.id] = task

                # 等待完成
                result = await task

        except Exception as e:
            logger.error(f"执行失败: {e}")
            result = ExecutionResult(
                execution_id=execution.id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
            )
        finally:
            if execution.id in self._running_executions:
                del self._running_executions[execution.id]

        # 更新执行记录
        await self._update_execution_result(execution.id, result)

        # 发布执行完成事件
        await event_bus.publish(event_bus.Event(
            event_type="execution.completed",
            payload={
                "execution_id": execution.id,
                "pipeline_id": pipeline_id,
                "status": result.status.value,
            },
        ))

        return result

    async def _create_execution(
        self,
        pipeline_id: str,
        triggered_by: Optional[str],
        parameters: Optional[dict],
    ) -> PipelineExecution:
        """创建执行记录"""
        async with get_session() as session:
            execution = PipelineExecution(
                id=str(uuid.uuid4()),
                pipeline_id=pipeline_id,
                parameters=parameters,
                status=ExecutionStatus.PENDING,
                triggered_by=triggered_by,
            )
            session.add(execution)
            await session.commit()
            return execution

    async def _run_execution(
        self,
        execution: PipelineExecution,
        pipeline: Pipeline,
        parameters: Optional[dict],
        dry_run: bool,
    ) -> ExecutionResult:
        """运行执行"""
        # 更新状态为运行中
        await self._update_execution_status(
            execution.id,
            ExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        # 构建执行配置
        config = ExecutionConfig(
            dry_run=dry_run,
            print_shell_commands=True,
        )

        # 合并参数
        merged_params = {**(pipeline.parameters or {}), **(parameters or {})}

        # 执行 Snakemake
        try:
            result = await self.engine.execute(
                pipeline=pipeline,
                parameters=merged_params,
                config=config,
            )

            return ExecutionResult(
                execution_id=execution.id,
                status=ExecutionStatus.COMPLETED if not dry_run else ExecutionStatus.PENDING,
                output_dir=result.output_dir,
                log_path=result.log_path,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc) if not dry_run else None,
            )

        except Exception as e:
            return ExecutionResult(
                execution_id=execution.id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )

    async def _update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        started_at: Optional[datetime] = None,
    ) -> None:
        """更新执行状态"""
        async with get_session() as session:
            result = await session.get(PipelineExecution, execution_id)
            if result:
                result.status = status
                if started_at:
                    result.started_at = started_at
                await session.commit()

    async def _update_execution_result(
        self,
        execution_id: str,
        result: ExecutionResult,
    ) -> None:
        """更新执行结果"""
        async with get_session() as session:
            execution = await session.get(PipelineExecution, execution_id)
            if execution:
                execution.status = result.status
                execution.output_dir = result.output_dir
                execution.log_path = result.log_path
                execution.error_message = result.error_message
                if result.completed_at:
                    execution.completed_at = result.completed_at
                await session.commit()

    async def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        if execution_id in self._running_executions:
            task = self._running_executions[execution_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        return False

    def get_running_executions(self) -> list[str]:
        """获取正在运行的执行列表"""
        return list(self._running_executions.keys())
