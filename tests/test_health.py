"""
健康检查 API 测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_health_status(client: AsyncClient):
    """测试 API 健康状态端点"""
    response = await client.get("/api/health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data


@pytest.mark.asyncio
async def test_ready_check(client: AsyncClient):
    """测试就绪检查端点"""
    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data


@pytest.mark.asyncio
async def test_api_docs_available(client: AsyncClient):
    """测试 API 文档可用性"""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
