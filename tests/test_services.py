"""
服务层测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.conda.manager import CondaPackageManager
from backend.services.snakemake.workflow_engine import (
    ExecutionConfig,
    ResourceLimits,
    SnakemakeWorkflowEngine,
)


@pytest.mark.asyncio
async def test_conda_package_manager_list_environments():
    """测试 Conda 环境列表"""
    manager = CondaPackageManager()

    # Mock _run_conda 方法
    mock_result = {
        "envs": [
            "/home/user/miniconda3",
            "/home/user/miniconda3/envs/test-env",
        ],
        "active_prefix": "/home/user/miniconda3",
    }

    with patch.object(manager, '_run_conda', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result

        envs = await manager.list_environments()

        assert len(envs) == 2
        assert envs[0]["name"] == "miniconda3"
        assert envs[1]["name"] == "test-env"


@pytest.mark.asyncio
async def test_conda_package_manager_create_environment():
    """测试创建 Conda 环境"""
    manager = CondaPackageManager()

    with patch.object(manager, '_run_conda', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {}

        with patch.object(manager, 'list_environments', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [
                {"name": "test-env", "path": "/path/to/test-env", "is_active": False},
            ]

            result = await manager.create_environment("test-env", "3.10")

            assert result["name"] == "test-env"
            mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_engine_build_command():
    """测试工作流引擎命令构建"""
    engine = SnakemakeWorkflowEngine(
        resource_limits=ResourceLimits(max_cores=8, max_memory_gb=16),
    )

    cmd = engine._build_command(
        workflow_id="/path/to/Snakefile",
        parameters={"sample": "test"},
        config=ExecutionConfig(dry_run=True),
    )

    assert "snakemake" in cmd
    assert "-s" in cmd
    assert "/path/to/Snakefile" in cmd
    assert "--cores" in cmd
    assert "8" in cmd
    assert "--dry-run" in cmd


def test_execution_progress_percentage():
    """测试执行进度计算"""
    from backend.services.snakemake.workflow_engine import ExecutionProgress

    progress = ExecutionProgress(total_jobs=100, completed_jobs=50)
    assert progress.percentage == 50.0

    progress_empty = ExecutionProgress(total_jobs=0, completed_jobs=0)
    assert progress_empty.percentage == 0.0


@pytest.mark.asyncio
async def test_workflow_engine_parse_progress():
    """测试进度解析"""
    engine = SnakemakeWorkflowEngine()

    output = """
    Running job 1
    Finished job 1
    Running job 2
    Finished job 2
    Error in job 3
    """

    progress = engine._parse_progress(output)

    assert progress.completed_jobs == 2
    assert progress.running_jobs == 1
    assert progress.failed_jobs == 1
