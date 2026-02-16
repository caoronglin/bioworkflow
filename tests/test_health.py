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
async def test_api_routes_info(client: AsyncClient):
    """测试路由信息端点"""
    response = await client.get("/api/")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert len(data["routes"]) > 0


@pytest.mark.asyncio
async def test_health_status_detailed(client: AsyncClient):
    """测试详细健康检查端点"""
    response = await client.get("/api/health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "checks" in data
    assert "api" in data["checks"]


@pytest.mark.asyncio
async def test_ready_check(client: AsyncClient):
    """测试就绪检查端点"""
    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data
