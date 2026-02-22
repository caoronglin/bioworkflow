"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from miniforge_service.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client):
        """Test health check response has expected structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_status_values(self, client):
        """Test health check status is valid."""
        response = client.get("/health")
        data = response.json()

        valid_statuses = ["healthy", "starting", "degraded"]
        assert data["status"] in valid_statuses


class TestSystemEndpoints:
    """Tests for system endpoints."""

    def test_get_channels_returns_list(self, client):
        """Test getting channels returns a list."""
        response = client.get("/api/v1/system/channels")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_system_info_service_unavailable(self, client):
        """Test system info when service is unavailable."""
        # This will fail if manager is not initialized
        response = client.get("/api/v1/system/info")
        # Should return 503 if manager not ready
        assert response.status_code in [200, 503]


class TestEnvironmentEndpoints:
    """Tests for environment endpoints."""

    def test_list_environments_service_unavailable(self, client):
        """Test list environments when service is unavailable."""
        response = client.get("/api/v1/environments")
        # Should return 503 if manager not ready, or 200 with empty list
        assert response.status_code in [200, 503]

    def test_get_environment_not_found(self, client):
        """Test getting non-existent environment."""
        response = client.get("/api/v1/environments/nonexistent-env-12345")
        assert response.status_code == 404

    def test_create_environment_invalid_data(self, client):
        """Test creating environment with invalid data."""
        # Missing required fields
        response = client.post("/api/v1/environments", json={})
        assert response.status_code == 422

    def test_create_environment_invalid_name(self, client):
        """Test creating environment with invalid name."""
        response = client.post("/api/v1/environments", json={
            "name": "invalid name with spaces!",
            "python_version": "3.11",
        })
        assert response.status_code == 422

    def test_delete_environment_not_found(self, client):
        """Test deleting non-existent environment."""
        response = client.delete("/api/v1/environments/nonexistent-env-12345")
        assert response.status_code == 404


class TestPackageEndpoints:
    """Tests for package endpoints."""

    def test_search_packages_empty_query(self, client):
        """Test searching packages with empty query."""
        response = client.get("/api/v1/packages/search?query=")
        assert response.status_code == 422

    def test_list_packages_env_not_found(self, client):
        """Test listing packages for non-existent environment."""
        response = client.get("/api/v1/packages/nonexistent-env-12345/packages")
        assert response.status_code == 404

    def test_install_packages_empty_list(self, client):
        """Test installing empty package list."""
        response = client.post(
            "/api/v1/packages/test-env/packages",
            json=[]
        )
        assert response.status_code == 422
