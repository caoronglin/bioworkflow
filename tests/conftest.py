"""测试配置"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_app_startup(client):
    """测试应用启动"""
    response = client.get("/api/health/status")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
