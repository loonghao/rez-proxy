"""
Basic tests for environments router to improve coverage.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestEnvironmentResolve:
    """Test environment resolution functionality."""

    @patch("rez.system.system")
    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_success(
        self, mock_context_class, mock_status, mock_system, client
    ):
        """Test successful environment resolution."""
        # Setup mocks
        mock_context = MagicMock()
        mock_status.solved = "solved"
        mock_context.status = mock_status.solved
        mock_context.resolved_packages = []
        mock_context.platform = "linux"
        mock_context.arch = "x86_64"
        mock_context.os = "linux"
        mock_context_class.return_value = mock_context
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "linux"

        request_data = {"packages": ["test-package-1.0.0"]}

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "resolved"
        assert data["platform"] == "linux"
        assert data["arch"] == "x86_64"
        assert data["os_name"] == "linux"

    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_failure(self, mock_context_class, mock_status, client):
        """Test environment resolution failure."""
        # Setup mocks for failed resolution
        mock_context = MagicMock()
        mock_status.solved = "solved"
        mock_status.failed = "failed"
        mock_context.status = mock_status.failed
        mock_context.failure_description = "Package not found"
        mock_context_class.return_value = mock_context

        request_data = {"packages": ["nonexistent-package"]}

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 400
        assert "Failed to resolve environment" in response.json()["detail"]

    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_exception(self, mock_context_class, client):
        """Test environment resolution with exception."""
        mock_context_class.side_effect = Exception("Rez error")

        request_data = {"packages": ["test-package"]}

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert "Rez operation failed" in data["detail"]


class TestEnvironmentInfo:
    """Test environment information retrieval."""

    def test_get_environment_not_found(self, client):
        """Test getting non-existent environment."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/environments/{fake_id}")

        assert response.status_code == 404
        assert f"Environment '{fake_id}' not found" in response.json()["detail"]


class TestEnvironmentDeletion:
    """Test environment deletion functionality."""

    def test_delete_environment_not_found(self, client):
        """Test deleting non-existent environment."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/environments/{fake_id}")

        assert response.status_code == 404
        assert f"Environment '{fake_id}' not found" in response.json()["detail"]


class TestCommandExecution:
    """Test command execution functionality."""

    def test_execute_command_environment_not_found(self, client):
        """Test command execution with non-existent environment."""
        fake_id = str(uuid.uuid4())
        command_request = {"command": "echo", "args": ["test"], "timeout": 30}

        response = client.post(
            f"/api/v1/environments/{fake_id}/execute", json=command_request
        )

        assert response.status_code == 404
        assert f"Environment '{fake_id}' not found" in response.json()["detail"]


class TestPackageToInfo:
    """Test package conversion functionality."""

    def test_package_to_info_complete(self):
        """Test package conversion with all attributes."""
        from rez_proxy.routers.environments import _package_to_info

        mock_pkg = MagicMock()
        mock_pkg.name = "test-package"
        mock_pkg.version = "1.0.0"
        mock_pkg.description = "Test package description"
        mock_pkg.authors = ["Author 1", "Author 2"]
        mock_pkg.requires = ["dep1", "dep2"]
        mock_pkg.variants = [{"0": ["python-3.9"]}]
        mock_pkg.tools = ["tool1", "tool2"]
        mock_pkg.commands = "echo test"
        mock_pkg.uri = "file:///test/path"

        result = _package_to_info(mock_pkg)

        assert result.name == "test-package"
        assert result.version == "1.0.0"
        assert result.description == "Test package description"
        assert result.authors == ["Author 1", "Author 2"]
        assert result.requires == ["dep1", "dep2"]
        assert result.variants == [{"0": ["python-3.9"]}]
        assert result.tools == ["tool1", "tool2"]
        assert result.commands == "echo test"
        assert result.uri == "file:///test/path"

    def test_package_to_info_minimal(self):
        """Test package conversion with minimal attributes."""
        from rez_proxy.routers.environments import _package_to_info

        mock_pkg = MagicMock()
        mock_pkg.name = "minimal-package"
        mock_pkg.version = "0.1.0"
        # Remove optional attributes
        del mock_pkg.description
        del mock_pkg.authors
        del mock_pkg.requires
        del mock_pkg.variants
        del mock_pkg.tools
        del mock_pkg.commands
        del mock_pkg.uri

        result = _package_to_info(mock_pkg)

        assert result.name == "minimal-package"
        assert result.version == "0.1.0"
        assert result.description is None
        assert result.authors is None
        assert result.requires == []
        assert result.variants is None
        assert result.tools is None
        assert result.commands is None
        assert result.uri is None


class TestEnvironmentWorkflow:
    """Test basic environment workflow."""

    @patch("rez.system.system")
    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_create_get_delete_workflow(
        self, mock_context_class, mock_status, mock_system, client
    ):
        """Test basic create -> get -> delete workflow."""
        # Setup mocks
        mock_context = MagicMock()
        mock_status.solved = "solved"
        mock_context.status = mock_status.solved
        mock_context.resolved_packages = []
        mock_context.platform = "linux"
        mock_context.arch = "x86_64"
        mock_context.os = "linux"
        mock_context_class.return_value = mock_context
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "linux"

        # 1. Create environment
        create_response = client.post(
            "/api/v1/environments/resolve", json={"packages": ["python-3.9"]}
        )
        assert create_response.status_code == 200
        env_id = create_response.json()["id"]

        # 2. Get environment info
        info_response = client.get(f"/api/v1/environments/{env_id}")
        assert info_response.status_code == 200
        assert info_response.json()["id"] == env_id

        # 3. Delete environment
        delete_response = client.delete(f"/api/v1/environments/{env_id}")
        assert delete_response.status_code == 200

        # 4. Verify deletion
        get_response = client.get(f"/api/v1/environments/{env_id}")
        assert get_response.status_code == 404


class TestEnvironmentEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("rez.system.system")
    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_missing_platform_attributes(
        self, mock_context_class, mock_status, mock_system, client
    ):
        """Test environment resolution when context lacks platform attributes."""
        # Setup mocks
        mock_context = MagicMock()
        mock_status.solved = "solved"
        mock_context.status = mock_status.solved
        mock_context.resolved_packages = []
        # Remove platform attributes from context
        del mock_context.platform
        del mock_context.arch
        del mock_context.os
        mock_context_class.return_value = mock_context
        mock_system.platform = "windows"
        mock_system.arch = "AMD64"
        mock_system.os = "windows"

        request_data = {"packages": ["test-package"]}

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 200
        data = response.json()
        # Should use system defaults
        assert data["platform"] == "windows"
        assert data["arch"] == "AMD64"
        assert data["os_name"] == "windows"

    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_empty_packages(
        self, mock_context_class, mock_status, client
    ):
        """Test environment resolution with empty package list."""
        # Setup mocks
        mock_context = MagicMock()
        mock_status.solved = "solved"
        mock_context.status = mock_status.solved
        mock_context.resolved_packages = []
        mock_context.platform = "linux"
        mock_context.arch = "x86_64"
        mock_context.os = "linux"
        mock_context_class.return_value = mock_context

        request_data = {"packages": []}

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["packages"]) == 0
