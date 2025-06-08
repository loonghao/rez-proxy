"""
Comprehensive tests for environments router.
"""

import asyncio
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import app
from rez_proxy.models.schemas import (
    CommandExecuteRequest,
    EnvironmentResolveRequest,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_resolved_context():
    """Create mock resolved context."""
    mock_context = MagicMock()
    mock_context.status = MagicMock()
    mock_context.resolved_packages = []
    mock_context.platform = "linux"
    mock_context.arch = "x86_64"
    mock_context.os = "linux"
    mock_context.get_environ.return_value = {"PATH": "/usr/bin"}
    mock_context.execute_command.return_value = {
        "stdout": "test output",
        "stderr": "",
        "return_code": 0
    }
    return mock_context


@pytest.fixture
def mock_package():
    """Create mock package."""
    mock_pkg = MagicMock()
    mock_pkg.name = "test-package"
    mock_pkg.version = "1.0.0"
    mock_pkg.description = "Test package"
    mock_pkg.authors = ["Test Author"]
    mock_pkg.requires = []
    mock_pkg.variants = None
    mock_pkg.tools = None
    mock_pkg.commands = None
    mock_pkg.uri = "file:///test/path"
    return mock_pkg


class TestEnvironmentResolve:
    """Test environment resolution functionality."""

    @patch("rez.system.system")
    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_success(self, mock_context_class, mock_status, mock_system, client, mock_resolved_context, mock_package):
        """Test successful environment resolution."""
        # Setup mocks
        mock_status.solved = "solved"
        mock_resolved_context.status = mock_status.solved
        mock_resolved_context.resolved_packages = [mock_package]
        mock_context_class.return_value = mock_resolved_context
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "linux"

        request_data = {
            "packages": ["test-package-1.0.0"]
        }

        response = client.post("/api/v1/environments/resolve", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "resolved"
        assert len(data["packages"]) == 1
        assert data["packages"][0]["name"] == "test-package"
        assert data["packages"][0]["version"] == "1.0.0"
        assert data["platform"] == "linux"
        assert data["arch"] == "x86_64"
        assert data["os_name"] == "linux"

    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_failure(self, mock_context_class, mock_status, client, mock_resolved_context):
        """Test environment resolution failure."""
        # Setup mocks for failed resolution
        mock_status.solved = "solved"
        mock_status.failed = "failed"
        mock_resolved_context.status = mock_status.failed
        mock_resolved_context.failure_description = "Package not found"
        mock_context_class.return_value = mock_resolved_context

        request_data = {
            "packages": ["nonexistent-package"]
        }

        response = client.post("/api/v1/environments/resolve", json=request_data)
        
        assert response.status_code == 400
        assert "Failed to resolve environment" in response.json()["detail"]

    @patch("rez.resolver.ResolverStatus")
    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_failure_no_description(self, mock_context_class, mock_status, client, mock_resolved_context):
        """Test environment resolution failure without description."""
        # Setup mocks for failed resolution without failure_description
        mock_status.solved = "solved"
        mock_status.failed = "failed"
        mock_resolved_context.status = mock_status.failed
        # No failure_description attribute
        del mock_resolved_context.failure_description
        mock_context_class.return_value = mock_resolved_context

        request_data = {
            "packages": ["nonexistent-package"]
        }

        response = client.post("/api/v1/environments/resolve", json=request_data)
        
        assert response.status_code == 400
        assert "Unknown resolution failure" in response.json()["detail"]

    @patch("rez.resolved_context.ResolvedContext")
    def test_resolve_environment_exception(self, mock_context_class, client):
        """Test environment resolution with exception."""
        mock_context_class.side_effect = Exception("Rez error")

        request_data = {
            "packages": ["test-package"]
        }

        response = client.post("/api/v1/environments/resolve", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Rez operation failed" in data["detail"]


class TestEnvironmentInfo:
    """Test environment information retrieval."""

    def test_get_environment_success(self, client):
        """Test successful environment retrieval."""
        # First create an environment
        with (
            patch("rez.resolved_context.ResolvedContext") as mock_context_class,
            patch("rez.resolver.ResolverStatus") as mock_status,
            patch("rez.system.system") as mock_system
        ):
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

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Get environment info
        response = client.get(f"/api/v1/environments/{env_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == env_id
        assert data["status"] == "resolved"
        assert "created_at" in data

    def test_get_environment_not_found(self, client):
        """Test getting non-existent environment."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/environments/{fake_id}")
        
        assert response.status_code == 404
        assert f"Environment '{fake_id}' not found" in response.json()["detail"]


class TestEnvironmentDeletion:
    """Test environment deletion functionality."""

    def test_delete_environment_success(self, client):
        """Test successful environment deletion."""
        # First create an environment
        with (
            patch("rez.resolved_context.ResolvedContext") as mock_context_class,
            patch("rez.resolver.ResolverStatus") as mock_status,
            patch("rez.system.system") as mock_system
        ):
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

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Delete environment
        response = client.delete(f"/api/v1/environments/{env_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert f"Environment '{env_id}' deleted successfully" in data["message"]

        # Verify environment is deleted
        get_response = client.get(f"/api/v1/environments/{env_id}")
        assert get_response.status_code == 404

    def test_delete_environment_not_found(self, client):
        """Test deleting non-existent environment."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/environments/{fake_id}")
        
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
        mock_pkg.variants = {"0": ["python-3.9"]}
        mock_pkg.tools = ["tool1", "tool2"]
        mock_pkg.commands = "echo test"
        mock_pkg.uri = "file:///test/path"

        result = _package_to_info(mock_pkg)
        
        assert result.name == "test-package"
        assert result.version == "1.0.0"
        assert result.description == "Test package description"
        assert result.authors == ["Author 1", "Author 2"]
        assert result.requires == ["dep1", "dep2"]
        assert result.variants == {"0": ["python-3.9"]}
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


class TestCommandExecution:
    """Test command execution functionality."""

    def test_execute_command_success_with_context_method(self, client):
        """Test successful command execution using context.execute_command."""
        # First create an environment
        with (
            patch("rez.resolved_context.ResolvedContext") as mock_context_class,
            patch("rez.resolver.ResolverStatus") as mock_status,
            patch("rez.system.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.execute_command.return_value = {
                "stdout": "Hello World",
                "stderr": "",
                "return_code": 0
            }
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command
        command_request = {
            "command": "echo",
            "args": ["Hello World"],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 200
        data = response.json()
        assert data["stdout"] == "Hello World"
        assert data["stderr"] == ""
        assert data["return_code"] == 0
        assert "execution_time" in data

    @patch("rez_proxy.routers.environments.subprocess")
    def test_execute_command_success_with_subprocess_fallback(self, mock_subprocess, client):
        """Test successful command execution using subprocess fallback."""
        # First create an environment
        with (
            patch("rez.resolved_context.ResolvedContext") as mock_context_class,
            patch("rez.resolver.ResolverStatus") as mock_status,
            patch("rez.system.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.get_environ.return_value = {"PATH": "/usr/bin"}
            # Remove execute_command method to trigger fallback
            del mock_context.execute_command
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Setup subprocess mock
        mock_process = MagicMock()
        mock_process.stdout = "Subprocess output"
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_subprocess.run.return_value = mock_process

        # Execute command
        command_request = {
            "command": "echo",
            "args": ["test"],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 200
        data = response.json()
        assert data["stdout"] == "Subprocess output"
        assert data["stderr"] == ""
        assert data["return_code"] == 0
        assert "execution_time" in data

        # Verify subprocess was called correctly
        mock_subprocess.run.assert_called_once()
        call_args = mock_subprocess.run.call_args
        assert call_args[0][0] == ["echo", "test"]
        assert call_args[1]["shell"] is False
        assert call_args[1]["timeout"] == 30

    def test_execute_command_environment_not_found(self, client):
        """Test command execution with non-existent environment."""
        fake_id = str(uuid.uuid4())
        command_request = {
            "command": "echo",
            "args": ["test"],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{fake_id}/execute", json=command_request)

        assert response.status_code == 404
        assert f"Environment '{fake_id}' not found" in response.json()["detail"]

    def test_execute_command_no_args(self, client):
        """Test command execution without arguments."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.execute_command.return_value = {
                "stdout": "command output",
                "stderr": "",
                "return_code": 0
            }
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command without args
        command_request = {
            "command": "pwd",
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 200
        data = response.json()
        assert data["stdout"] == "command output"

    @patch("rez_proxy.routers.environments.subprocess")
    def test_execute_command_invalid_args(self, mock_subprocess, client):
        """Test command execution with invalid arguments."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.get_environ.return_value = {"PATH": "/usr/bin"}
            # Remove execute_command method to trigger fallback
            del mock_context.execute_command
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command with invalid args (non-string)
        command_request = {
            "command": "echo",
            "args": [123, None],  # Invalid args
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 400
        assert "Invalid command arguments" in response.json()["detail"]

    @patch("rez_proxy.routers.environments.subprocess")
    def test_execute_command_timeout_error(self, mock_subprocess, client):
        """Test command execution with timeout."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.get_environ.return_value = {"PATH": "/usr/bin"}
            # Remove execute_command method to trigger fallback
            del mock_context.execute_command
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Setup subprocess to raise timeout
        import subprocess
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired("echo", 1)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        # Execute command
        command_request = {
            "command": "sleep",
            "args": ["10"],
            "timeout": 1
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 500
        data = response.json()
        assert "Rez operation failed" in data["detail"]

    def test_execute_command_general_exception(self, client):
        """Test command execution with general exception."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.execute_command.side_effect = Exception("Command execution failed")
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command
        command_request = {
            "command": "echo",
            "args": ["test"],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 500
        data = response.json()
        assert "Rez operation failed" in data["detail"]


class TestEnvironmentIntegration:
    """Test complete environment workflow integration."""

    def test_full_environment_workflow(self, client):
        """Test complete environment workflow from creation to deletion."""
        env_id = None

        try:
            # 1. Create environment
            with (
                patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
                patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
                patch("rez_proxy.routers.environments.system") as mock_system
            ):
                mock_context = MagicMock()
                mock_status.solved = "solved"
                mock_context.status = mock_status.solved
                mock_context.resolved_packages = []
                mock_context.platform = "linux"
                mock_context.arch = "x86_64"
                mock_context.os = "linux"
                mock_context.execute_command.return_value = {
                    "stdout": "python 3.9.0",
                    "stderr": "",
                    "return_code": 0
                }
                mock_context_class.return_value = mock_context
                mock_system.platform = "linux"
                mock_system.arch = "x86_64"
                mock_system.os = "linux"

                create_response = client.post("/api/v1/environments/resolve", json={
                    "packages": ["python-3.9"]
                })
                assert create_response.status_code == 200
                env_id = create_response.json()["id"]

            # 2. Get environment info
            info_response = client.get(f"/api/v1/environments/{env_id}")
            assert info_response.status_code == 200
            assert info_response.json()["id"] == env_id

            # 3. Execute command
            exec_response = client.post(f"/api/v1/environments/{env_id}/execute", json={
                "command": "python",
                "args": ["--version"],
                "timeout": 30
            })
            assert exec_response.status_code == 200
            assert "python 3.9.0" in exec_response.json()["stdout"]

        finally:
            # 4. Clean up - delete environment
            if env_id:
                delete_response = client.delete(f"/api/v1/environments/{env_id}")
                assert delete_response.status_code == 200

                # Verify deletion
                get_response = client.get(f"/api/v1/environments/{env_id}")
                assert get_response.status_code == 404


class TestEnvironmentEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("rez_proxy.routers.environments.ResolvedContext")
    @patch("rez_proxy.routers.environments.ResolverStatus")
    @patch("rez_proxy.routers.environments.system")
    def test_resolve_environment_with_missing_platform_attributes(self, mock_system, mock_status, mock_context_class, client):
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

        request_data = {
            "packages": ["test-package"]
        }

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 200
        data = response.json()
        # Should use system defaults
        assert data["platform"] == "windows"
        assert data["arch"] == "AMD64"
        assert data["os_name"] == "windows"

    @patch("rez_proxy.routers.environments.ResolvedContext")
    @patch("rez_proxy.routers.environments.ResolverStatus")
    def test_resolve_environment_with_empty_packages(self, mock_status, mock_context_class, client):
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

        request_data = {
            "packages": []
        }

        response = client.post("/api/v1/environments/resolve", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["packages"]) == 0

    def test_execute_command_with_empty_command(self, client):
        """Test command execution with empty command."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.get_environ.return_value = {"PATH": "/usr/bin"}
            # Remove execute_command method to trigger fallback
            del mock_context.execute_command
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command with empty command
        command_request = {
            "command": "",
            "args": ["test"],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 400
        assert "Invalid command arguments" in response.json()["detail"]

    @patch("rez_proxy.routers.environments.subprocess")
    def test_execute_command_subprocess_error(self, mock_subprocess, client):
        """Test command execution with subprocess error."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.get_environ.return_value = {"PATH": "/usr/bin"}
            # Remove execute_command method to trigger fallback
            del mock_context.execute_command
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Setup subprocess to raise an error
        mock_subprocess.run.side_effect = OSError("Command not found")

        # Execute command
        command_request = {
            "command": "nonexistent-command",
            "args": [],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 500
        data = response.json()
        assert "Rez operation failed" in data["detail"]

    def test_execute_command_with_stderr_output(self, client):
        """Test command execution that produces stderr output."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.execute_command.return_value = {
                "stdout": "",
                "stderr": "Warning: deprecated option",
                "return_code": 0
            }
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command
        command_request = {
            "command": "python",
            "args": ["-W", "ignore"],
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 200
        data = response.json()
        assert data["stdout"] == ""
        assert data["stderr"] == "Warning: deprecated option"
        assert data["return_code"] == 0

    def test_execute_command_with_non_zero_exit_code(self, client):
        """Test command execution with non-zero exit code."""
        # First create an environment
        with (
            patch("rez_proxy.routers.environments.ResolvedContext") as mock_context_class,
            patch("rez_proxy.routers.environments.ResolverStatus") as mock_status,
            patch("rez_proxy.routers.environments.system") as mock_system
        ):
            mock_context = MagicMock()
            mock_status.solved = "solved"
            mock_context.status = mock_status.solved
            mock_context.resolved_packages = []
            mock_context.platform = "linux"
            mock_context.arch = "x86_64"
            mock_context.os = "linux"
            mock_context.execute_command.return_value = {
                "stdout": "",
                "stderr": "Command failed",
                "return_code": 1
            }
            mock_context_class.return_value = mock_context
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"
            mock_system.os = "linux"

            # Create environment
            create_response = client.post("/api/v1/environments/resolve", json={"packages": ["python-3.9"]})
            assert create_response.status_code == 200
            env_id = create_response.json()["id"]

        # Execute command
        command_request = {
            "command": "false",  # Command that always returns 1
            "timeout": 30
        }

        response = client.post(f"/api/v1/environments/{env_id}/execute", json=command_request)

        assert response.status_code == 200
        data = response.json()
        assert data["return_code"] == 1
        assert data["stderr"] == "Command failed"
