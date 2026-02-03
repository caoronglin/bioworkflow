"""健康检查 API 测试"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_status():
    """测试健康检查端点"""
    response = client.get("/api/health/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data


def test_routes_info():
    """测试路由信息端点"""
    response = client.get("/api/")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert len(data["routes"]) > 0
