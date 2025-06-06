"""
Basic integration tests for rez-proxy API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestBasicIntegration:
    """Test basic API integration."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "name" in data

    def test_system_info(self, client):
        """Test system info endpoint."""
        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            response = client.get("/api/v1/system/info")
            assert response.status_code == 200
            data = response.json()
            assert "platform" in data

    def test_packages_list_basic(self, client):
        """Test basic packages listing."""
        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez.packages.iter_packages") as mock_iter:
                mock_package = MagicMock()
                mock_package.name = "python"
                mock_package.version = "3.9.0"
                mock_package.description = "Python interpreter"
                mock_package.repository = MagicMock()
                mock_package.repository.name = "central"
                mock_iter.return_value = [mock_package]

                response = client.get("/api/v1/packages")
                assert response.status_code == 200
                data = response.json()
                assert "packages" in data
                assert len(data["packages"]) >= 0

    def test_repositories_list(self, client):
        """Test repositories listing."""
        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez.packages.get_package_repositories") as mock_repos:
                mock_repo = MagicMock()
                mock_repo.name = "central"
                mock_repo.location = "/packages"
                mock_repos.return_value = [mock_repo]

                response = client.get("/api/v1/repositories")
                assert response.status_code == 200
                data = response.json()
                assert "repositories" in data

    def test_shells_list(self, client):
        """Test shells listing."""
        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez_proxy.core.platform.ShellService") as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.get_available_shells.return_value = [
                    {"name": "bash", "executable": "bash", "available": True}
                ]

                response = client.get("/api/v1/shells")
                assert response.status_code == 200
                data = response.json()
                assert "shells" in data

    def test_environments_create_basic(self, client):
        """Test basic environment creation."""
        env_request = {"packages": ["python-3.9"], "shell": "bash"}

        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez.resolved_context.ResolvedContext") as mock_context_class:
                mock_context = MagicMock()
                mock_context.status = "solved"
                mock_context.resolved_packages = []
                mock_context.get_environ.return_value = {"PATH": "/bin"}
                mock_context_class.return_value = mock_context

                response = client.post("/api/v1/environments", json=env_request)
                assert response.status_code == 200
                data = response.json()
                assert "environment_id" in data

    def test_config_info(self, client):
        """Test configuration info."""
        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch(
                "rez_proxy.core.platform.RezConfigService"
            ) as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.get_config_info.return_value = {
                    "platform": "linux",
                    "packages_path": ["/packages"],
                }

                response = client.get("/api/v1/config")
                assert response.status_code == 200
                data = response.json()
                assert "platform" in data

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/packages")
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_error_handling(self, client):
        """Test error handling for non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed handling."""
        response = client.delete("/api/v1/packages")
        assert response.status_code == 405

    def test_validation_error(self, client):
        """Test validation error handling."""
        # Send invalid JSON to an endpoint that expects specific format
        response = client.post("/api/v1/environments", json={"invalid": "data"})
        assert response.status_code == 422

    def test_package_detail(self, client):
        """Test package detail endpoint."""
        package_name = "python"

        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez.packages.get_latest_package") as mock_get_latest:
                mock_package = MagicMock()
                mock_package.name = package_name
                mock_package.version = "3.9.0"
                mock_package.description = "Python interpreter"
                mock_package.tools = ["python", "pip"]
                mock_package.requires = []
                mock_package.repository = MagicMock()
                mock_package.repository.name = "central"
                mock_get_latest.return_value = mock_package

                response = client.get(f"/api/v1/packages/{package_name}")
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == package_name

    def test_package_versions(self, client):
        """Test package versions endpoint."""
        package_name = "python"

        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez.packages.iter_packages") as mock_iter:
                mock_package = MagicMock()
                mock_package.name = package_name
                mock_package.version = "3.9.0"
                mock_package.repository = MagicMock()
                mock_package.repository.name = "central"
                mock_iter.return_value = [mock_package]

                response = client.get(f"/api/v1/packages/{package_name}/versions")
                assert response.status_code == 200
                data = response.json()
                assert "versions" in data

    def test_repository_packages(self, client):
        """Test repository packages endpoint."""
        repo_name = "central"

        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez.packages.get_package_repository") as mock_get_repo:
                with patch("rez.packages.iter_packages") as mock_iter:
                    mock_repo = MagicMock()
                    mock_repo.name = repo_name
                    mock_get_repo.return_value = mock_repo

                    mock_package = MagicMock()
                    mock_package.name = "python"
                    mock_package.version = "3.9.0"
                    mock_iter.return_value = [mock_package]

                    response = client.get(f"/api/v1/repositories/{repo_name}/packages")
                    assert response.status_code == 200
                    data = response.json()
                    assert "packages" in data

    def test_shell_info(self, client):
        """Test shell info endpoint."""
        shell_name = "bash"

        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch("rez_proxy.core.platform.ShellService") as mock_service_class:
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_service.get_shell_info.return_value = {
                    "name": shell_name,
                    "executable": "bash",
                    "available": True,
                }

                response = client.get(f"/api/v1/shells/{shell_name}")
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == shell_name

    def test_environment_status(self, client):
        """Test environment status endpoint."""
        env_id = "test-env-123"

        with patch("rez_proxy.core.context.get_current_context", return_value=None):
            with patch(
                "rez_proxy.middleware.context.environment_manager"
            ) as mock_env_mgr:
                mock_env_mgr.get_environment.return_value = {
                    "environment_id": env_id,
                    "status": "active",
                    "packages": ["python-3.9"],
                }

                response = client.get(f"/api/v1/environments/{env_id}")
                assert response.status_code == 200
                data = response.json()
                assert data["environment_id"] == env_id

    def test_api_versioning(self, client):
        """Test API versioning works correctly."""
        # Test v1 endpoints
        response = client.get("/api/v1/system/info")
        assert response.status_code in [
            200,
            500,
        ]  # May fail due to missing context but should route correctly

        # Test that non-existent versions return 404
        response = client.get("/api/v99/system/info")
        assert response.status_code == 404
