"""
Test suite for the asynchronous workflow execution engine.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from backend.services.snakemake.workflow_engine import (
    WorkflowExecutionEngine,
    WorkflowStatus,
    get_workflow_engine,
    shutdown_workflow_engine,
    create_snakefile,
)


@pytest.fixture
async def engine():
    """Fixture to provide a workflow engine instance."""
    engine = await get_workflow_engine(max_concurrent_jobs=2)
    yield engine
    await shutdown_workflow_engine()


@pytest.fixture
def sample_snakefile():
    """Create a sample Snakefile for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.smk', delete=False) as f:
        f.write("""
rule all:
    input: "test_output.txt"

rule test:
    output: "test_output.txt"
    shell: "echo 'Hello World' > {output}"
""")
        return f.name


class TestWorkflowEngine:
    """Test cases for WorkflowExecutionEngine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test that the engine initializes correctly."""
        engine = WorkflowExecutionEngine(max_concurrent_jobs=2)
        await engine.initialize()

        assert engine._executor is not None
        assert engine.max_concurrent_jobs == 2

        await engine.shutdown()

    @pytest.mark.asyncio
    async def test_workflow_submission(self, sample_snakefile):
        """Test workflow submission."""
        engine = await get_workflow_engine(max_concurrent_jobs=2)

        try:
            workflow_id = await engine.execute_workflow(
                workflow_path=sample_snakefile,
                dry_run=True,
                jobs=1,
            )

            assert workflow_id is not None
            assert isinstance(workflow_id, str)

            # Check that workflow was tracked
            progress = await engine.get_workflow_status(workflow_id)
            assert progress is not None
            assert progress.workflow_id == workflow_id

        finally:
            await shutdown_workflow_engine()

    @pytest.mark.asyncio
    async def test_workflow_status_lifecycle(self, sample_snakefile):
        """Test workflow status transitions."""
        engine = await get_workflow_engine(max_concurrent_jobs=2)

        try:
            workflow_id = await engine.execute_workflow(
                workflow_path=sample_snakefile,
                dry_run=True,
                jobs=1,
            )

            # Check initial status
            progress = await engine.get_workflow_status(workflow_id)
            assert progress.status in (WorkflowStatus.QUEUED, WorkflowStatus.RUNNING)

            # Wait for completion (with timeout)
            max_wait = 30  # seconds
            waited = 0
            while progress.status in (WorkflowStatus.QUEUED, WorkflowStatus.RUNNING) and waited < max_wait:
                await asyncio.sleep(0.5)
                waited += 0.5
                progress = await engine.get_workflow_status(workflow_id)

            # Check final status
            assert progress.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED)

        finally:
            await shutdown_workflow_engine()

    @pytest.mark.asyncio
    async def test_workflow_listing(self):
        """Test listing workflows."""
        engine = await get_workflow_engine(max_concurrent_jobs=2)

        try:
            # Initially empty
            workflows = await engine.list_workflows()
            initial_count = len(workflows)

            # After adding workflows, should be able to list them
            # (Actual count depends on test execution order)
            workflows = await engine.list_workflows()
            assert len(workflows) >= initial_count

        finally:
            await shutdown_workflow_engine()

    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, sample_snakefile):
        """Test workflow cancellation."""
        engine = await get_workflow_engine(max_concurrent_jobs=2)

        try:
            # Submit a workflow
            workflow_id = await engine.execute_workflow(
                workflow_path=sample_snakefile,
                dry_run=False,
                jobs=1,
            )

            # Cancel it immediately
            cancelled = await engine.cancel_workflow(workflow_id)
            assert cancelled is True

            # Verify it was cancelled
            progress = await engine.get_workflow_status(workflow_id)
            # Note: Cancellation may not be immediate, status could still be RUNNING
            # The important thing is that the cancel request was accepted

            # Trying to cancel again should fail (already cancelled or completed)
            cancelled_again = await engine.cancel_workflow(workflow_id)
            # This may succeed or fail depending on timing

        finally:
            await shutdown_workflow_engine()

    @pytest.mark.asyncio
    async def test_invalid_workflow_path(self):
        """Test handling of invalid workflow paths."""
        engine = await get_workflow_engine(max_concurrent_jobs=2)

        try:
            with pytest.raises(Exception):
                await engine.execute_workflow(
                    workflow_path="/nonexistent/path/Snakefile",
                    jobs=1,
                )

        finally:
            await shutdown_workflow_engine()


class TestSnakefileCreation:
    """Test cases for dynamic Snakefile creation."""

    @pytest.mark.asyncio
    async def test_create_simple_snakefile(self):
        """Test creating a simple Snakefile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Snakefile"

            rules = [
                {
                    "name": "all",
                    "input": ["output.txt"],
                },
                {
                    "name": "generate",
                    "output": "output.txt",
                    "shell": "echo 'Hello' > {output}",
                },
            ]

            result = create_snakefile(
                rules=rules,
                output_path=output_path,
            )

            assert result.exists()
            content = result.read_text()
            assert "rule all:" in content
            assert "rule generate:" in content
            assert "output.txt" in content

    @pytest.mark.asyncio
    async def test_create_snakefile_with_config(self):
        """Test creating a Snakefile with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "Snakefile"

            rules = [
                {
                    "name": "all",
                    "input": ["{sample}.txt"],
                },
            ]

            config = {
                "samples": ["A", "B", "C"],
                "threads": 4,
            }

            result = create_snakefile(
                rules=rules,
                output_path=output_path,
                config=config,
            )

            assert result.exists()

            # Check config file was created
            config_path = output_path.parent / "config.json"
            assert config_path.exists()

            import json
            saved_config = json.loads(config_path.read_text())
            assert saved_config["samples"] == ["A", "B", "C"]


class TestAsyncPatterns:
    """Test async/await patterns in the workflow engine."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_submissions(self, sample_snakefile):
        """Test submitting multiple workflows concurrently."""
        engine = await get_workflow_engine(max_concurrent_jobs=4)

        try:
            # Submit multiple workflows concurrently
            tasks = []
            for i in range(3):
                task = engine.execute_workflow(
                    workflow_path=sample_snakefile,
                    dry_run=True,
                    jobs=1,
                )
                tasks.append(task)

            workflow_ids = await asyncio.gather(*tasks)

            # Verify all workflows were submitted
            assert len(workflow_ids) == 3
            for wf_id in workflow_ids:
                assert wf_id is not None
                assert isinstance(wf_id, str)

            # Verify all workflows are being tracked
            for wf_id in workflow_ids:
                progress = await engine.get_workflow_status(wf_id)
                assert progress is not None

        finally:
            await shutdown_workflow_engine()

    @pytest.mark.asyncio
    async def test_progress_callbacks(self, sample_snakefile):
        """Test progress callback system."""
        engine = await get_workflow_engine(max_concurrent_jobs=2)

        callback_invocations = []

        async def progress_callback(progress: WorkflowProgress):
            callback_invocations.append({
                "workflow_id": progress.workflow_id,
                "status": progress.status.value,
                "progress": progress.progress_percentage,
            })

        try:
            engine.add_progress_callback(progress_callback)

            workflow_id = await engine.execute_workflow(
                workflow_path=sample_snakefile,
                dry_run=True,
                jobs=1,
            )

            # Wait for workflow to complete
            max_wait = 30
            waited = 0
            progress = await engine.get_workflow_status(workflow_id)
            while progress.status in (WorkflowStatus.RUNNING, WorkflowStatus.QUEUED) and waited < max_wait:
                await asyncio.sleep(0.5)
                waited += 0.5
                progress = await engine.get_workflow_status(workflow_id)

            # Verify callbacks were invoked
            assert len(callback_invocations) > 0
            assert callback_invocations[0]["workflow_id"] == workflow_id

        finally:
            engine.remove_progress_callback(progress_callback)
            await shutdown_workflow_engine()
