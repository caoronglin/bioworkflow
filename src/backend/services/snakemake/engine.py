"""Snakemake 工作流引擎 - 高性能执行

提供异步 Snakemake 工作流执行，支持并发控制、资源管理和实时监控
"""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from loguru import logger

from backend.models.pipeline import ExecutionStatus, Pipeline


class WorkflowError(Exception):
    """工作流执行错误"""
    pass


class WorkflowStatus(str, Enum):
    """工作流执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_cores: int = 4
    max_memory_gb: float = 8.0
    max_jobs: int = 10
    max_local_jobs: int = 4


@dataclass
class ExecutionConfig:
    """执行配置"""
    dry_run: bool = False
    force_all: bool = False
    keep_incomplete: bool = False
    print_shell_commands: bool = True
    verbose: bool = False
    latency_wait: int = 5


@dataclass
class ExecutionProgress:
    """执行进度信息"""
    total_jobs: int = 0
    completed_jobs: int = 0
    running_jobs: int = 0
    failed_jobs: int = 0
    current_step: str = ""
    start_time: Optional[datetime] = None
    estimated_end: Optional[datetime] = None

    @property
    def percentage(self) -> float:
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs / self.total_jobs) * 100


# 进度回调函数类型
ProgressCallback = Callable[[ExecutionProgress], Coroutine[Any, Any, None]]


class SnakemakeEngine:
    """
    Snakemake 工作流引擎

    支持：
    - 异步执行
    - 并发控制
    - 资源管理
    - 实时监控
    - 错误重试
    """

    def __init__(
        self,
        resource_limits: Optional[ResourceLimits] = None,
        default_config: Optional[ExecutionConfig] = None,
    ):
        self.resource_limits = resource_limits or ResourceLimits()
        self.default_config = default_config or ExecutionConfig()
        self._running_workflows: dict[str, asyncio.subprocess.Process] = {}
        self._progress_callbacks: dict[str, ProgressCallback] = {}

    async def execute(
        self,
        pipeline: Pipeline,
        parameters: Optional[dict] = None,
        config: Optional[ExecutionConfig] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ExecutionProgress:
        """
        执行 Snakemake 工作流

        Args:
            pipeline: 流水线定义
            parameters: 运行时参数
            config: 执行配置
            progress_callback: 进度回调

        Returns:
            执行进度信息

        Raises:
            WorkflowError: 执行失败
        """
        config = config or self.default_config
        execution_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # 注册回调
        if progress_callback:
            self._progress_callbacks[execution_id] = progress_callback

        try:
            # 构建命令
            cmd = self._build_command(pipeline, parameters, config)

            # 创建执行环境
            env = os.environ.copy()
            env["SNAKEMAKE_CONDA_PREFIX"] = pipeline.conda_environment or ""

            # 初始化进度
            progress = ExecutionProgress(
                total_jobs=0,  # 需要通过 --dry-run 获取
                start_time=datetime.utcnow(),
            )

            logger.info(f"启动工作流执行: {execution_id}")
            logger.debug(f"执行命令: {' '.join(cmd)}")

            if config.dry_run:
                # 干运行模式
                result = await self._dry_run(cmd, env)
                progress.total_jobs = result.get("total_jobs", 0)
                return progress

            # 实际执行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=pipeline.workdir or os.getcwd(),
            )

            self._running_workflows[execution_id] = process

            # 读取输出
            stdout, stderr = await process.communicate()

            # 解析进度
            progress = self._parse_progress(stdout.decode())

            if process.returncode != 0:
                error_msg = stderr.decode() or "Unknown error"
                logger.error(f"工作流执行失败: {error_msg}")
                raise WorkflowError(f"Execution failed: {error_msg}")

            logger.info(f"工作流执行完成: {execution_id}")
            return progress

        except asyncio.CancelledError:
            logger.warning(f"工作流执行取消: {execution_id}")
            await self.cancel(execution_id)
            raise
        finally:
            if execution_id in self._running_workflows:
                del self._running_workflows[execution_id]
            if execution_id in self._progress_callbacks:
                del self._progress_callbacks[execution_id]

    async def cancel(self, execution_id: str) -> bool:
        """取消正在执行的工作流"""
        if execution_id not in self._running_workflows:
            return False

        process = self._running_workflows[execution_id]
        try:
            process.terminate()
            # 等待优雅关闭
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # 强制终止
            process.kill()
            await process.wait()

        return True

    def _build_command(
        self,
        pipeline: Pipeline,
        parameters: Optional[dict],
        config: ExecutionConfig,
    ) -> list[str]:
        """构建 Snakemake 命令"""
        cmd = ["snakemake", "-s", pipeline.snakefile_path]

        # 资源配置
        cmd.extend(["--cores", str(self.resource_limits.max_cores)])
        cmd.extend(["--resources", f"mem_mb={int(self.resource_limits.max_memory_gb * 1000)}"])
        cmd.extend(["--jobs", str(self.resource_limits.max_jobs)])
        cmd.extend(["--local-cores", str(self.resource_limits.max_local_jobs)])

        # 执行配置
        if config.dry_run:
            cmd.append("--dry-run")
        if config.force_all:
            cmd.append("--forceall")
        if config.keep_incomplete:
            cmd.append("--keep-incomplete")
        if config.print_shell_commands:
            cmd.append("-p")
        if config.verbose:
            cmd.extend(["-v", "-v"])

        cmd.extend(["--latency-wait", str(config.latency_wait)])

        # 参数
        if parameters:
            for key, value in parameters.items():
                cmd.extend(["--config", f"{key}={value}"])

        # 输出格式
        cmd.append("--summary")

        return cmd

    async def _dry_run(self, cmd: list[str], env: dict) -> dict:
        """执行干运行，返回任务统计"""
        dry_run_cmd = cmd + ["--dry-run", "--quiet"]

        process = await asyncio.create_subprocess_exec(
            *dry_run_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await process.communicate()

        # 解析干运行输出
        output = stdout.decode()

        # 简单统计 - 实际应该解析 Snakemake 输出
        total_jobs = output.count("Job ")

        return {
            "total_jobs": total_jobs,
            "output": output[:1000],  # 限制输出大小
        }

    def _parse_progress(self, output: str) -> ExecutionProgress:
        """解析 Snakemake 输出，提取进度信息"""
        # TODO: 实现更精确的进度解析
        # 可以解析 Snakemake 的 JSON 输出或使用 --summary

        progress = ExecutionProgress()

        # 简单解析
        for line in output.split("\n"):
            if "Finished job" in line:
                progress.completed_jobs += 1
            elif "Running job" in line or "Executing" in line:
                progress.running_jobs += 1
            elif "Error" in line or "Failed" in line:
                progress.failed_jobs += 1

        return progress


# 全局引擎实例
_engine: SnakemakeEngine | None = None


def get_engine() -> SnakemakeEngine:
    """获取全局 Snakemake 引擎实例（单例）"""
    global _engine
    if _engine is None:
        _engine = SnakemakeEngine()
    return _engine


def reset_engine() -> None:
    """重置引擎（主要用于测试）"""
    global _engine
    _engine = None
