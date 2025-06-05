"""
Test environments router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestEnvironmentsRouter:
    """Test environments router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez.resolved_context.ResolvedContext")
    @patch("rez.system.system")
    def test_resolve_environment_success(self, mock_system, mock_context_class, client):
        """Test successful environment resolution."""
        # Mock system
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "ubuntu-20.04"

        # Mock resolved context
        mock_context = Mock()
        mock_context.status = Mock()
        mock_context.status.name = "solved"
        mock_context.resolved_packages = []
        mock_context.platform = "linux"
        mock_context.arch = "x86_64"
        mock_context.os = "ubuntu-20.04"

        mock_context_class.return_value = mock_context

        resolve_data = {"packages": ["python-3.9", "requests"]}

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["status"] == "resolved"
        assert data["platform"] == "linux"
        assert data["arch"] == "x86_64"

    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_failed(self, mock_context_class, client):
        """Test failed environment resolution."""
        # Mock failed resolution
        mock_context = Mock()
        mock_context.status = Mock()
        mock_context.status.name = "failed"
        mock_context.failure_description = "Package not found"

        mock_context_class.return_value = mock_context

        resolve_data = {"packages": ["nonexistent-package"]}

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "failed" in data["detail"].lower()

    def test_resolve_environment_invalid_request(self, client):
        """Test environment resolution with invalid request."""
        # Missing packages field
        resolve_data = {}

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 422  # Validation error

    def test_resolve_environment_empty_packages(self, client):
        """Test environment resolution with empty packages list."""
        resolve_data = {"packages": []}

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 422  # Validation error

    @patch("rez.resolved_context.ResolvedContext")
    @patch("rez.system.system")
    def test_resolve_environment_with_platform_override(
        self, mock_system, mock_context_class, client
    ):
        """Test environment resolution with platform override."""
        # Mock system
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "ubuntu-20.04"

        # Mock resolved context
        mock_context = Mock()
        mock_context.status = Mock()
        mock_context.status.name = "solved"
        mock_context.resolved_packages = []
        mock_context.platform = "windows"  # Override platform
        mock_context.arch = "x86_64"
        mock_context.os = "windows-10"

        mock_context_class.return_value = mock_context

        resolve_data = {
            "packages": ["python-3.9"],
            "platform": "windows",
            "arch": "x86_64",
            "os_name": "windows-10",
        }

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 200

        data = response.json()
        assert data["platform"] == "windows"
        assert data["os"] == "windows-10"

    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_exception_handling(self, mock_context_class, client):
        """Test environment resolution exception handling."""
        mock_context_class.side_effect = Exception("Rez error")

        resolve_data = {"packages": ["python-3.9"]}

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 500

    @patch("rez_proxy.routers.environments.environment_store")
    def test_get_environment_info_success(self, mock_store, client):
        """Test successful environment info retrieval."""
        # Mock environment data
        mock_env_data = {
            "id": "test-env-123",
            "status": "resolved",
            "packages": ["python-3.9", "requests"],
            "resolved_packages": [
                {"name": "python", "version": "3.9.0"},
                {"name": "requests", "version": "2.28.0"},
            ],
            "platform": "linux",
            "arch": "x86_64",
            "os": "ubuntu-20.04",
            "created_at": "2023-01-01T00:00:00Z",
        }

        mock_store.get.return_value = mock_env_data

        response = client.get("/api/v1/environments/test-env-123")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test-env-123"
        assert data["status"] == "resolved"
        assert len(data["resolved_packages"]) == 2

    @patch("rez_proxy.routers.environments.environment_store")
    def test_get_environment_info_not_found(self, mock_store, client):
        """Test environment info retrieval for non-existent environment."""
        mock_store.get.return_value = None

        response = client.get("/api/v1/environments/nonexistent")
        assert response.status_code == 404

    @patch("rez_proxy.routers.environments.environment_store")
    def test_list_environments_success(self, mock_store, client):
        """Test successful environments listing."""
        # Mock environments list
        mock_environments = [
            {
                "id": "env-1",
                "status": "resolved",
                "packages": ["python-3.9"],
                "created_at": "2023-01-01T00:00:00Z",
            },
            {
                "id": "env-2",
                "status": "failed",
                "packages": ["nonexistent"],
                "created_at": "2023-01-01T01:00:00Z",
            },
        ]

        mock_store.list.return_value = mock_environments

        response = client.get("/api/v1/environments")
        assert response.status_code == 200

        data = response.json()
        assert "environments" in data
        assert len(data["environments"]) == 2
        assert data["environments"][0]["id"] == "env-1"

    @patch("rez_proxy.routers.environments.environment_store")
    def test_delete_environment_success(self, mock_store, client):
        """Test successful environment deletion."""
        mock_store.delete.return_value = True

        response = client.delete("/api/v1/environments/test-env-123")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Environment deleted successfully"

    @patch("rez_proxy.routers.environments.environment_store")
    def test_delete_environment_not_found(self, mock_store, client):
        """Test environment deletion for non-existent environment."""
        mock_store.delete.return_value = False

        response = client.delete("/api/v1/environments/nonexistent")
        assert response.status_code == 404

    @patch("rez.resolved_context.ResolvedContext")
    @patch("rez.system.system")
    def test_resolve_environment_with_timestamp(
        self, mock_system, mock_context_class, client
    ):
        """Test environment resolution with timestamp."""
        # Mock system
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "ubuntu-20.04"

        # Mock resolved context
        mock_context = Mock()
        mock_context.status = Mock()
        mock_context.status.name = "solved"
        mock_context.resolved_packages = []
        mock_context.platform = "linux"
        mock_context.arch = "x86_64"
        mock_context.os = "ubuntu-20.04"

        mock_context_class.return_value = mock_context

        resolve_data = {
            "packages": ["python-3.9"],
            "timestamp": 1640995200,  # 2022-01-01 00:00:00 UTC
        }

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 200

        # Verify timestamp was passed to ResolvedContext
        mock_context_class.assert_called_once()
        call_kwargs = mock_context_class.call_args[1]
        assert "timestamp" in call_kwargs

    @patch("rez.resolved_context.ResolvedContext")
    @patch("rez.system.system")
    def test_resolve_environment_with_verbosity(
        self, mock_system, mock_context_class, client
    ):
        """Test environment resolution with verbosity setting."""
        # Mock system
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "ubuntu-20.04"

        # Mock resolved context
        mock_context = Mock()
        mock_context.status = Mock()
        mock_context.status.name = "solved"
        mock_context.resolved_packages = []
        mock_context.platform = "linux"
        mock_context.arch = "x86_64"
        mock_context.os = "ubuntu-20.04"

        mock_context_class.return_value = mock_context

        resolve_data = {"packages": ["python-3.9"], "verbosity": 2}

        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 200

        # Verify verbosity was passed to ResolvedContext
        mock_context_class.assert_called_once()
        call_kwargs = mock_context_class.call_args[1]
        assert "verbosity" in call_kwargs
        assert call_kwargs["verbosity"] == 2


class TestEnvironmentStore:
    """Test environment store functionality."""

    def test_environment_store_operations(self):
        """Test basic environment store operations."""
        from rez_proxy.routers.environments import environment_store

        # Test store is available
        assert environment_store is not None

        # Test basic operations exist
        assert hasattr(environment_store, "store")
        assert hasattr(environment_store, "get")
        assert hasattr(environment_store, "list")
        assert hasattr(environment_store, "delete")
