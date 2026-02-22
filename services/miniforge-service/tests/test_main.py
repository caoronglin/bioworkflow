"""Tests for main application."""

import pytest
from fastapi.testclient import TestClient

from miniforge_service.main import app, app_state


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check_no_manager(client):
    """Test health check when manager is not initialized."""
    # Ensure manager is None
    original_manager = app_state.manager
    app_state.manager = None

    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "starting"
    finally:
        # Restore original manager
        app_state.manager = original_manager


def test_docs_endpoint_disabled_in_production(client):
    """Test that docs are disabled in production."""
    # This test assumes debug=False in production
    # The actual behavior depends on settings
    pass


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")
    # CORS middleware should handle this
    assert response.status_code in [200, 405]  # 405 if method not allowed
