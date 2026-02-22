"""Workflow service implementation."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bioworkflow_core import Result, BioWorkflowError
from bioworkflow_dag import YamlParser, SnakemakeParser, GraphVisualizer
from bioworkflow_scheduler import TaskScheduler, SchedulerConfig, SchedulingStrategy
from bioworkflow_dag.executor import DagExecutor, ExecutionContext, ExecutionStrategy

from .config import Settings
from ..models import (
    Workflow,
    Task,
    Execution,
)
from ..types import (
    WorkflowCreate,
    WorkflowUpdate,
    TaskCreate,
    TaskUpdate,
    ExecutionCreate,
    ExecutionUpdate,
)


class WorkflowService:
    """Workflow service for managing workflow execution."""

    def __init__(self, db_session: AsyncSession, settings: Settings):
        self.db_session = db_session
        self.settings = settings

        # Initialize scheduler
        self.scheduler = self._initialize_scheduler()

    def _initialize_scheduler(self) -> TaskScheduler:
        """Initialize task scheduler."""
        strategy = self._map_strategy(self.settings.SCHEDULING_STRATEGY)

        config = SchedulerConfig {
            strategy: strategy,
            concurrency: self.settings.SCHEDULER_CONCURRENCY,
            resources: {
                cpu: self.settings.RESOURCE_TOTAL_CPU,
                memory: self.settings.RESOURCE_TOTAL_MEMORY,
                gpu: self.settings.RESOURCE_TOTAL_GPU,
            },
            queue_size: self.settings.SCHEDULER_QUEUE_SIZE,
            prefetch_count: self.settings.SCHEDULER_PREFETCH,
            retry_count: self.settings.WORKFLOW_MAX_RETRIES,
            retry_delay: self.settings.SCHEDULER_RETRY_DELAY,
        }

        return TaskScheduler(config)

    def _map_strategy(self, strategy_name: str) -> SchedulingStrategy:
        """Map string strategy name to enum value."""
        strategy_map = {
            "fifo": SchedulingStrategy.Fifo,
            "sjf": SchedulingStrategy.Sjf,
            "priority": SchedulingStrategy.Priority,
            "least_load": SchedulingStrategy.LeastLoad,
            "resource_aware": SchedulingStrategy.ResourceAware,
        }

        return strategy_map.get(strategy_name.lower(), SchedulingStrategy.Fifo)

    # ============ Workflow Management ============

    async def create_workflow(
        self,
        create_data: WorkflowCreate,
    ) -> Result[Workflow]:
        """Create a new workflow."""
        try:
            # Parse workflow from file or content
            if create_data.snakefile_path:
                if not create_data.content:
                    with open(create_data.snakefile_path, "r") as f:
                        content = f.read()
            else:
                content = create_data.content

            if not content:
                raise ValueError("Workflow content is required")

            # Parse workflow
            parser = self._get_parser(create_data.format)
            workflow_def = parser.parse_str(content)

            # Create database record
            workflow = Workflow(
                name=create_data.name,
                description=create_data.description,
                format=create_data.format,
                content=content,
                snakefile_path=create_data.snakefile_path,
                config=create_data.config,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.db_session.add(workflow)
            await self.db_session.commit()

            # Process tasks and dependencies
            await self._process_tasks(workflow, workflow_def.tasks)

            await self.db_session.refresh(workflow)

            return workflow

        except Exception as e:
            await self.db_session.rollback()
            raise e

    async def _get_parser(self, format: str):
        """Get appropriate parser for format."""
        if format == "snakemake":
            return SnakemakeParser
        elif format == "yaml":
            return YamlParser
        else:
            raise ValueError(f"Unsupported workflow format: '{format}'")

    async def _process_tasks(self, workflow: Workflow, tasks: List[Any]):
        """Process tasks and dependencies."""
        task_map = {}

        # Create tasks
        for task_def in tasks:
            task = Task(
                workflow_id=workflow.id,
                name=task_def.name,
                command=task_def.command,
                inputs=task_def.inputs,
                outputs=task_def.outputs,
                resources=task_def.resources,
                container=task_def.container,
                environment=task_def.environment,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            task_map[task_def.name] = task
            self.db_session.add(task)

        # Set dependencies
        for task_def in tasks:
            task = task_map[task_def.name]

            for dep_name in task_def.dependencies:
                dep_task = task_map.get(dep_name)
                if dep_task:
                    task.dependencies.append(dep_task)

        await self.db_session.flush()

    async def get_workflow(
        self,
        workflow_id: UUID,
        include_tasks: bool = False,
    ) -> Optional[Workflow]:
        """Get workflow by ID."""
        query = select(Workflow).filter(Workflow.id == workflow_id)

        if include_tasks:
            query = query.options(
                selectinload(Workflow.tasks).options(
                    selectinload(Task.dependencies)
                )
            )

        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_workflows(self, offset: int = 0, limit: int = 50) -> List[Workflow]:
        """Get all workflows."""
        result = await self.db_session.execute(
            select(Workflow)
            .order_by(Workflow.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()

    async def update_workflow(
        self,
        workflow_id: UUID,
        update_data: WorkflowUpdate,
    ) -> Optional[Workflow]:
        """Update workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        if update_data.name is not None:
            workflow.name = update_data.name
        if update_data.description is not None:
            workflow.description = update_data.description
        if update_data.config is not None:
            workflow.config = update_data.config

        workflow.updated_at = datetime.now()

        await self.db_session.commit()
        await self.db_session.refresh(workflow)

        return workflow

    async def delete_workflow(self, workflow_id: UUID) -> bool:
        """Delete workflow."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False

        await self.db_session.delete(workflow)
        await self.db_session.commit()

        return True

    # ============ Task Management ============

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get task by ID."""
        result = await self.db_session.execute(
            select(Task).filter(Task.id == task_id)
        )

        return result.scalar_one_or_none()

    async def get_workflow_tasks(
        self,
        workflow_id: UUID,
        include_dependencies: bool = False,
    ) -> List[Task]:
        """Get tasks for a workflow."""
        query = select(Task).filter(Task.workflow_id == workflow_id)

        if include_dependencies:
            query = query.options(
                selectinload(Task.dependencies),
                selectinload(Task.dependents)
            )

        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def update_task(self, task_id: UUID, update_data: TaskUpdate):
        """Update task."""
        task = await self.get_task(task_id)
        if not task:
            return None

        if update_data.command is not None:
            task.command = update_data.command
        if update_data.resources is not None:
            task.resources = update_data.resources
        if update_data.container is not None:
            task.container = update_data.container
        if update_data.environment is not None:
            task.environment = update_data.environment

        task.updated_at = datetime.now()

        await self.db_session.commit()
        await self.db_session.refresh(task)

        return task

    # ============ Execution Management ============

    async def create_execution(
        self,
        workflow_id: UUID,
        create_data: ExecutionCreate,
    ) -> Execution:
        """Create execution for a workflow."""
        workflow = await self.get_workflow(workflow_id, include_tasks=True)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        execution = Execution(
            workflow_id=workflow_id,
            config=create_data.config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.db_session.add(execution)
        await self.db_session.flush()

        # Schedule tasks
        for task in workflow.tasks:
            await self.scheduler.schedule_task(task)

        # Start execution in background
        asyncio.create_task(self._start_execution(execution.id))

        await self.db_session.commit()
        await self.db_session.refresh(execution)

        return execution

    async def _start_execution(self, execution_id: UUID):
        """Start execution in background."""
        # TODO: Implement execution logic
        await asyncio.sleep(1)

    async def get_execution(self, execution_id: UUID) -> Optional[Execution]:
        """Get execution by ID."""
        result = await self.db_session.execute(
            select(Execution).filter(Execution.id == execution_id)
        )

        return result.scalar_one_or_none()

    async def get_workflow_executions(
        self,
        workflow_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Execution]:
        """Get executions for a workflow."""
        result = await self.db_session.execute(
            select(Execution)
            .filter(Execution.workflow_id == workflow_id)
            .order_by(Execution.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()

    # ============ DAG Operations ============

    async def generate_dag(self, workflow_id: UUID) -> Result[Any]:
        """Generate DAG representation of workflow."""
        tasks = await self.get_workflow_tasks(workflow_id, include_dependencies=True)

        # Convert tasks to DAG
        dag = self._tasks_to_dag(tasks)

        return dag

    def _tasks_to_dag(self, tasks: List[Task]) -> Any:
        """Convert database tasks to DAG structure."""
        nodes = []
        edges = []
        task_map = {}

        for task in tasks:
            node = {
                "id": task.id,
                "name": task.name,
                "command": task.command,
                "inputs": task.inputs,
                "outputs": task.outputs,
                "resources": task.resources,
                "container": task.container,
                "environment": task.environment,
            }
            nodes.append(node)
            task_map[task.id] = len(nodes) - 1

        for task in tasks:
            for dep in task.dependencies:
                edges.append({
                    "source": task_map.get(dep.id, -1),
                    "target": task_map.get(task.id, -1),
                })

        return {
            "nodes": nodes,
            "edges": [e for e in edges if e["source"] != -1 and e["target"] != -1],
        }

    async def generate_visualization(
        self,
        workflow_id: UUID,
        format: str,
    ) -> Result[str]:
        """Generate DAG visualization in specified format."""
        tasks = await self.get_workflow_tasks(workflow_id, include_dependencies=True)

        if format == "dot":
            return GraphVisualizer.to_dot()

        elif format == "mermaid":
            return GraphVisualizer.to_mermaid()

        elif format == "json":
            return GraphVisualizer.to_json()

        elif format == "html":
            return GraphVisualizer.to_html()

        elif format == "png":
            return GraphVisualizer.to_png()

        else:
            raise ValueError(f"Unsupported visualization format: '{format}'")

    # ============ Scheduler Operations ============

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "queue_size": self.scheduler.queue_size(),
            "active_tasks": self.scheduler.active_count(),
            "completed_tasks": len(self.scheduler.completed_tasks),
            "utilization": self.scheduler.resources.utilization(),
            "available": {
                "cpu": self.scheduler.resources.total_cpu - self.scheduler.resources.used_cpu,
                "memory": self.scheduler.resources.total_memory - self.scheduler.resources.used_memory,
                "gpu": max(0, self.scheduler.resources.total_gpu - self.scheduler.resources.used_gpu),
            },
        }

    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return self.scheduler.stats()

    # ============ Resource Operations ============

    async def get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage statistics."""
        return self.scheduler.get_resource_stats()

    # ============ Monitoring ============

    async def get_workflow_stats(self, workflow_id: UUID) -> Dict[str, Any]:
        """Get workflow statistics."""
        workflow = await self.get_workflow(workflow_id)

        if not workflow:
            raise ValueError("Workflow not found")

        # Calculate statistics
        return {
            "tasks": len(workflow.tasks),
            "executions": len(workflow.executions),
            "status_counts": {
                "pending": len([e for e in workflow.executions if e.status == "pending"]),
                "running": len([e for e in workflow.executions if e.status == "running"]),
                "completed": len([e for e in workflow.executions if e.status == "completed"]),
                "failed": len([e for e in workflow.executions if e.status == "failed"]),
            },
            "total_runtime": sum(
                e.duration or 0 for e in workflow.executions
            ),
        }

    # ============ Health Check ============

    async def health_check(self) -> Dict[str, Any]:
        """Perform service health check."""
        return {
            "service": "healthy",
            "database": True,
            "scheduler": self.scheduler.is_healthy(),
            "queue": "healthy",
        }
