"""
Asynchronous Snakemake Workflow Engine

This module provides async/await based Snakemake workflow execution,
following Snakemake 8.x best practices for non-blocking execution.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import os
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Union,
)

from pydantic import BaseModel, Field

try:
    import snakemake
    from snakemake.api import SnakemakeApi
    from snakemake.settings import Settings, ExecMode
    SNAKEMAKE_AVAILABLE = True
except ImportError:
    SNAKEMAKE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Snakemake not installed. Workflow engine will be limited.")

from backend.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobStatus(str, Enum):
    """Individual job status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Information about a workflow job."""
    job_id: str
    rule_name: str
    status: JobStatus = JobStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    log_file: Optional[str] = None
    error_message: Optional[str] = None
    resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowProgress:
    """Progress information for a workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    current_jobs: List[JobInfo] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs / self.total_jobs) * 100

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time


class ProgressCallback(Protocol):
    """Protocol for progress update callbacks."""

    async def __call__(self, progress: WorkflowProgress) -> None:
        """Called when progress is updated."""
        ...


class WorkflowExecutionEngine:
    """
    Asynchronous Snakemake workflow execution engine.

    This engine provides non-blocking workflow execution using asyncio,
    following Snakemake 8.x best practices.
    """

    def __init__(
        self,
        max_concurrent_jobs: int = 4,
        executor_type: str = "thread",
        snakemake_api: Optional[Any] = None,
    ):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.executor_type = executor_type
        self.snakemake_api = snakemake_api

        # Execution tracking
        self._workflows: Dict[str, WorkflowProgress] = {}
        self._cancelled: Set[str] = set()
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)

        # Thread/process pool for blocking operations
        self._executor: Optional[Union[ThreadPoolExecutor, ProcessPoolExecutor]] = None

        # Progress callbacks
        self._callbacks: List[ProgressCallback] = []

    async def initialize(self) -> None:
        """Initialize the execution engine."""
        if self.executor_type == "thread":
            self._executor = ThreadPoolExecutor(max_workers=self.max_concurrent_jobs)
        elif self.executor_type == "process":
            self._executor = ProcessPoolExecutor(max_workers=self.max_concurrent_jobs)
        else:
            raise ValueError(f"Unknown executor type: {self.executor_type}")

        logger.info(f"Workflow engine initialized with {self.executor_type} executor")

    async def shutdown(self) -> None:
        """Shutdown the execution engine."""
        # Cancel all running workflows
        for workflow_id in list(self._workflows.keys()):
            await self.cancel_workflow(workflow_id)

        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

        logger.info("Workflow engine shutdown complete")

    def add_progress_callback(self, callback: ProgressCallback) -> None:
        """Add a progress update callback."""
        self._callbacks.append(callback)

    def remove_progress_callback(self, callback: ProgressCallback) -> None:
        """Remove a progress update callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _notify_progress(self, progress: WorkflowProgress) -> None:
        """Notify all progress callbacks."""
        for callback in self._callbacks:
            try:
                await callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    async def execute_workflow(
        self,
        workflow_path: Union[str, Path],
        workdir: Optional[Union[str, Path]] = None,
        targets: Optional[List[str]] = None,
        dry_run: bool = False,
        config: Optional[Dict[str, Any]] = None,
        config_files: Optional[List[str]] = None,
        executor: Optional[str] = None,
        jobs: int = 1,
        resources: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Execute a Snakemake workflow asynchronously.

        Args:
            workflow_path: Path to the Snakefile
            workdir: Working directory for the workflow
            targets: Target rules or files to build
            dry_run: If True, perform a dry run without executing jobs
            config: Configuration dictionary
            config_files: List of config files to load
            executor: Executor to use (e.g., 'local', 'slurm', 'drmaa')
            jobs: Number of parallel jobs
            resources: Resource requirements
            **kwargs: Additional arguments passed to Snakemake

        Returns:
            workflow_id: Unique identifier for the workflow execution
        """
        workflow_id = str(uuid.uuid4())

        # Initialize progress tracking
        progress = WorkflowProgress(
            workflow_id=workflow_id,
            status=WorkflowStatus.QUEUED,
            start_time=time.time(),
        )
        self._workflows[workflow_id] = progress

        # Start workflow execution in background
        asyncio.create_task(
            self._execute_workflow_async(
                workflow_id=workflow_id,
                workflow_path=Path(workflow_path),
                workdir=Path(workdir) if workdir else Path(workflow_path).parent,
                targets=targets,
                dry_run=dry_run,
                config=config or {},
                config_files=config_files or [],
                executor=executor or "local",
                jobs=jobs,
                resources=resources or {},
                **kwargs,
            )
        )

        return workflow_id

    async def _execute_workflow_async(
        self,
        workflow_id: str,
        workflow_path: Path,
        workdir: Path,
        targets: Optional[List[str]],
        dry_run: bool,
        config: Dict[str, Any],
        config_files: List[str],
        executor: str,
        jobs: int,
        resources: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """
        Internal method to execute workflow asynchronously.
        """
        progress = self._workflows.get(workflow_id)
        if not progress:
            logger.error(f"Workflow {workflow_id} not found")
            return

        try:
            # Update status to running
            progress.status = WorkflowStatus.RUNNING
            await self._notify_progress(progress)

            # Acquire semaphore to limit concurrent executions
            async with self._semaphore:
                if workflow_id in self._cancelled:
                    progress.status = WorkflowStatus.CANCELLED
                    await self._notify_progress(progress)
                    return

                # Execute workflow using appropriate method
                if SNAKEMAKE_AVAILABLE and self.snakemake_api:
                    await self._execute_with_api(
                        workflow_id=workflow_id,
                        workflow_path=workflow_path,
                        workdir=workdir,
                        targets=targets,
                        dry_run=dry_run,
                        config=config,
                        config_files=config_files,
                        executor=executor,
                        jobs=jobs,
                        resources=resources,
                        progress=progress,
                        **kwargs,
                    )
                else:
                    await self._execute_with_subprocess(
                        workflow_id=workflow_id,
                        workflow_path=workflow_path,
                        workdir=workdir,
                        targets=targets,
                        dry_run=dry_run,
                        config=config,
                        config_files=config_files,
                        executor=executor,
                        jobs=jobs,
                        resources=resources,
                        progress=progress,
                        **kwargs,
                    )

                # Update final status
                if progress.failed_jobs > 0:
                    progress.status = WorkflowStatus.FAILED
                else:
                    progress.status = WorkflowStatus.COMPLETED

        except asyncio.CancelledError:
            progress.status = WorkflowStatus.CANCELLED
            logger.info(f"Workflow {workflow_id} cancelled")
            raise

        except Exception as e:
            progress.status = WorkflowStatus.FAILED
            progress.messages.append(f"Error: {str(e)}")
            logger.exception(f"Workflow {workflow_id} failed: {e}")

        finally:
            progress.end_time = time.time()
            await self._notify_progress(progress)

    async def _execute_with_api(
        self,
        workflow_id: str,
        workflow_path: Path,
        workdir: Path,
        targets: Optional[List[str]],
        dry_run: bool,
        config: Dict[str, Any],
        config_files: List[str],
        executor: str,
        jobs: int,
        resources: Dict[str, Any],
        progress: WorkflowProgress,
        **kwargs: Any,
    ) -> None:
        """
        Execute workflow using Snakemake Python API (async version).

        Following Snakemake 8.x best practices for async execution.
        """
        import snakemake
        from snakemake.api import SnakemakeApi
        from snakemake.settings import Settings, ExecMode

        # Build snakemake arguments
        snakemake_args = {
            "snakefile": str(workflow_path),
            "workdir": str(workdir),
            "cores": jobs,
            "dry_run": dry_run,
            "config": config,
            "configfiles": config_files,
            "executor": executor if executor != "local" else None,
        }

        # Add targets if specified
        if targets:
            snakemake_args["targets"] = targets

        # Add resources
        if resources:
            snakemake_args["resources"] = resources

        # Update progress
        progress.total_jobs = 1  # Will be updated during execution
        progress.messages.append(f"Starting workflow with {jobs} cores")
        await self._notify_progress(progress)

        # Use async_run pattern from Snakemake best practices
        loop = asyncio.get_event_loop()

        # Execute Snakemake in thread pool to avoid blocking
        def execute_snakemake():
            """Execute snakemake in separate thread."""
            try:
                with SnakemakeApi() as snakemake_api:
                    # Execute the workflow
                    result = snakemake_api.execute_workflow(**snakemake_args)
                    return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run in thread pool
        try:
            result = await loop.run_in_executor(
                self._executor,
                execute_snakemake
            )

            if result["success"]:
                progress.completed_jobs = 1
                progress.messages.append("Workflow completed successfully")
            else:
                progress.failed_jobs = 1
                progress.messages.append(f"Workflow failed: {result.get('error')}")

        except Exception as e:
            progress.failed_jobs = 1
            progress.messages.append(f"Execution error: {str(e)}")
            logger.exception("Snakemake API execution failed")

    async def _execute_with_subprocess(
        self,
        workflow_id: str,
        workflow_path: Path,
        workdir: Path,
        targets: Optional[List[str]],
        dry_run: bool,
        config: Dict[str, Any],
        config_files: List[str],
        executor: str,
        jobs: int,
        resources: Dict[str, Any],
        progress: WorkflowProgress,
        **kwargs: Any,
    ) -> None:
        """
        Execute workflow using snakemake subprocess (async version).

        This method uses asyncio.create_subprocess_exec for non-blocking execution.
        """
        import json
        import tempfile

        # Build snakemake command
        cmd = [
            "snakemake",
            "--snakefile", str(workflow_path),
            "--directory", str(workdir),
            "--cores", str(jobs),
            "--json",  # Output JSON format for parsing
        ]

        # Add dry run flag
        if dry_run:
            cmd.append("--dry-run")

        # Add targets
        if targets:
            cmd.extend(targets)

        # Add config
        for key, value in config.items():
            cmd.extend(["--config", f"{key}={value}"])

        # Add config files
        for config_file in config_files:
            cmd.extend(["--configfile", config_file])

        # Add executor if not local
        if executor and executor != "local":
            cmd.extend(["--executor", executor])

        # Add resources
        if resources:
            for key, value in resources.items():
                cmd.extend(["--resources", f"{key}={value}"])

        logger.info(f"Executing workflow {workflow_id}: {' '.join(cmd)}")
        progress.messages.append(f"Starting subprocess execution: snakemake --cores {jobs}")
        await self._notify_progress(progress)

        # Execute subprocess asynchronously
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workdir),
            )

            # Read output in real-time
            stdout_lines = []
            stderr_lines = []

            # Create tasks to read stdout and stderr concurrently
            async def read_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode().strip()
                    stdout_lines.append(line_str)
                    logger.debug(f"[{workflow_id}] {line_str}")

            async def read_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    line_str = line.decode().strip()
                    stderr_lines.append(line_str)
                    logger.debug(f"[{workflow_id}] stderr: {line_str}")

            # Wait for both streams to complete
            await asyncio.gather(
                read_stdout(),
                read_stderr(),
                process.wait(),
            )

            # Parse results
            returncode = process.returncode

            # Try to parse JSON output if available
            try:
                for line in stdout_lines:
                    if line.startswith("{"):
                        result = json.loads(line)
                        if "jobs" in result:
                            progress.total_jobs = len(result["jobs"])
                            break
            except (json.JSONDecodeError, KeyError):
                pass

            if returncode == 0:
                progress.status = WorkflowStatus.COMPLETED
                progress.completed_jobs = progress.total_jobs
                progress.messages.append("Workflow completed successfully")
            else:
                progress.status = WorkflowStatus.FAILED
                progress.failed_jobs = 1
                error_msg = f"Process exited with code {returncode}"
                if stderr_lines:
                    error_msg += f": {stderr_lines[-1]}"
                progress.messages.append(error_msg)

        except asyncio.CancelledError:
            progress.status = WorkflowStatus.CANCELLED
            progress.messages.append("Workflow cancelled")
            if 'process' in locals() and process:
                process.terminate()
                await process.wait()
            raise

        except Exception as e:
            progress.status = WorkflowStatus.FAILED
            progress.failed_jobs = 1
            progress.messages.append(f"Execution error: {str(e)}")
            logger.exception("Workflow execution failed")

    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get the status of a workflow."""
        return self._workflows.get(workflow_id)

    async def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowProgress]:
        """List all workflows, optionally filtered by status."""
        workflows = list(self._workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return workflows

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        if workflow_id not in self._workflows:
            return False

        progress = self._workflows[workflow_id]
        if progress.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            return False

        self._cancelled.add(workflow_id)
        progress.status = WorkflowStatus.CANCELLED
        progress.messages.append("Cancellation requested")
        await self._notify_progress(progress)

        return True

    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        if workflow_id not in self._workflows:
            return False

        progress = self._workflows[workflow_id]
        if progress.status != WorkflowStatus.RUNNING:
            return False

        progress.status = WorkflowStatus.PAUSED
        progress.messages.append("Workflow paused")
        await self._notify_progress(progress)

        return True

    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow."""
        if workflow_id not in self._workflows:
            return False

        progress = self._workflows[workflow_id]
        if progress.status != WorkflowStatus.PAUSED:
            return False

        progress.status = WorkflowStatus.RUNNING
        progress.messages.append("Workflow resumed")
        await self._notify_progress(progress)

        return True

    async def stream_workflow_logs(
        self,
        workflow_id: str,
    ) -> AsyncIterator[str]:
        """
        Stream workflow logs in real-time.

        This is an async generator that yields log lines as they become available.
        """
        # This is a placeholder implementation
        # In a real implementation, you would read from log files or pipes
        progress = self._workflows.get(workflow_id)
        if not progress:
            return

        for message in progress.messages:
            yield message

        # Keep yielding new messages
        last_count = len(progress.messages)
        while progress.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED):
            if len(progress.messages) > last_count:
                for i in range(last_count, len(progress.messages)):
                    yield progress.messages[i]
                last_count = len(progress.messages)
            await asyncio.sleep(0.5)


# Global engine instance
_engine: Optional[WorkflowExecutionEngine] = None


async def get_workflow_engine(
    max_concurrent_jobs: int = 4,
    executor_type: str = "thread",
) -> WorkflowExecutionEngine:
    """
    Get or create the global workflow engine instance.

    This follows the singleton pattern to ensure only one engine exists.
    """
    global _engine

    if _engine is None:
        _engine = WorkflowExecutionEngine(
            max_concurrent_jobs=max_concurrent_jobs,
            executor_type=executor_type,
        )
        await _engine.initialize()

    return _engine


async def shutdown_workflow_engine() -> None:
    """Shutdown the global workflow engine."""
    global _engine

    if _engine is not None:
        await _engine.shutdown()
        _engine = None


# Convenience functions for direct use

async def run_workflow(
    workflow_path: Union[str, Path],
    workdir: Optional[Union[str, Path]] = None,
    targets: Optional[List[str]] = None,
    dry_run: bool = False,
    config: Optional[Dict[str, Any]] = None,
    jobs: int = 1,
    **kwargs: Any,
) -> str:
    """
    Convenience function to run a workflow.

    This creates the engine if needed and starts the workflow.
    """
    engine = await get_workflow_engine()

    return await engine.execute_workflow(
        workflow_path=workflow_path,
        workdir=workdir,
        targets=targets,
        dry_run=dry_run,
        config=config,
        jobs=jobs,
        **kwargs,
    )


async def get_status(workflow_id: str) -> Optional[WorkflowProgress]:
    """Get workflow status by ID."""
    engine = await get_workflow_engine()
    return await engine.get_workflow_status(workflow_id)


async def cancel(workflow_id: str) -> bool:
    """Cancel a workflow by ID."""
    engine = await get_workflow_engine()
    return await engine.cancel_workflow(workflow_id)


def create_snakefile(
    rules: List[Dict[str, Any]],
    output_path: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Helper function to create a Snakefile from rule definitions.

    This is useful for dynamically generated workflows.
    """
    output_path = Path(output_path)

    lines = []

    # Add config if provided
    if config:
        lines.append("configfile: \"config.json\"")
        lines.append("")

    # Add rules
    for rule in rules:
        rule_name = rule.get("name", " unnamed_rule")
        lines.append(f"rule {rule_name}:")

        # Add inputs
        inputs = rule.get("input", [])
        if inputs:
            if isinstance(inputs, list):
                input_str = ", ".join(f'"{i}"' for i in inputs)
                lines.append(f"    input:")
                for inp in inputs:
                    lines.append(f"        \"{inp}\",")
            else:
                lines.append(f"    input: \"{inputs}\"")

        # Add outputs
        outputs = rule.get("output", [])
        if outputs:
            if isinstance(outputs, list):
                lines.append(f"    output:")
                for out in outputs:
                    lines.append(f"        \"{out}\",")
            else:
                lines.append(f"    output: \"{outputs}\"")

        # Add params
        params = rule.get("params", {})
        if params:
            lines.append(f"    params:")
            for key, value in params.items():
                lines.append(f"        {key}=\"{value}\",")

        # Add shell command
        shell = rule.get("shell", "")
        if shell:
            lines.append("    shell:")
            lines.append(f'        "{shell}"')

        # Add run directive (Python code)
        run_code = rule.get("run", "")
        if run_code:
            lines.append(f"    run:")
            for code_line in run_code.split("\\n"):
                lines.append(f"        {code_line}")

        lines.append("")

    # Write to file
    output_path.write_text("\\n".join(lines))

    # Write config if provided
    if config:
        import json
        config_path = output_path.parent / "config.json"
        config_path.write_text(json.dumps(config, indent=2))

    return output_path
