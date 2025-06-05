"""
Test system router functionality.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestSystemRouter:
    """Test system router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez_proxy.core.context.is_local_mode")
    @patch("rez_proxy.utils.rez_detector.validate_rez_environment")
    @patch("rez_proxy.utils.rez_detector.detect_rez_installation")
    def test_get_system_status_healthy(
        self, mock_detect, mock_validate, mock_is_local, client, mock_rez_info
    ):
        """Test system status endpoint with healthy system."""
        mock_detect.return_value = mock_rez_info
        mock_validate.return_value = []  # No warnings
        mock_is_local.return_value = True  # Force local mode

        response = client.get("/api/v1/system/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "warning"]
        assert data["rez_version"] == mock_rez_info["version"]
        # Python version should start with the expected version (may include full version info)
        assert data["python_version"].startswith(mock_rez_info["python_version"])
        assert data["platform"] == mock_rez_info["platform"]
        assert data["arch"] == mock_rez_info["arch"]

    @patch("rez_proxy.utils.rez_detector.detect_rez_installation")
    def test_get_system_status_with_warnings(self, mock_detect, client):
        """Test system status endpoint with warnings."""
        # Mock Rez info with potential issues
        mock_rez_info_with_issues = {
            "version": "3.2.1",
            "python_path": "/usr/bin/python",
            "python_version": "3.9.0",
            "packages_path": [],  # Empty packages path might cause warnings
            "platform": "linux",
            "arch": "x86_64",
            "os": "ubuntu-20.04",
        }
        mock_detect.return_value = mock_rez_info_with_issues

        response = client.get("/api/v1/system/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "warning"]
        if data["status"] == "warning":
            assert "warnings" in data
            assert isinstance(data["warnings"], list)

    @patch("rez_proxy.core.context.is_local_mode")
    @patch("rez_proxy.routers.system.detect_rez_installation")
    def test_get_system_status_rez_not_found(self, mock_detect, mock_is_local, client):
        """Test system status endpoint when Rez is not found."""
        mock_detect.side_effect = RuntimeError("Rez not found")
        mock_is_local.return_value = True  # Force local mode

        response = client.get("/api/v1/system/status")
        assert response.status_code == 500

    @patch("rez_proxy.routers.system.detect_rez_installation")
    def test_get_system_config(self, mock_detect, client, mock_rez_info):
        """Test system config endpoint."""
        mock_detect.return_value = mock_rez_info

        response = client.get("/api/v1/system/config")
        assert response.status_code == 200

        data = response.json()
        assert data["platform"] == mock_rez_info["platform"]
        assert data["arch"] == mock_rez_info["arch"]
        assert data["packages_path"] == mock_rez_info["packages_path"]
        assert data["python_path"] == mock_rez_info["python_path"]

    @patch("rez_proxy.routers.system.detect_rez_installation")
    def test_get_system_info(self, mock_detect, client, mock_rez_info):
        """Test system info endpoint."""
        mock_detect.return_value = mock_rez_info

        response = client.get("/api/v1/system/info")
        assert response.status_code == 200

        data = response.json()
        assert "rez" in data
        assert "platform" in data
        assert "python" in data

        # Check Rez info
        assert data["rez"]["version"] == mock_rez_info["version"]
        assert data["rez"]["root"] == mock_rez_info.get("rez_root")

        # Check platform info
        assert data["platform"]["name"] == mock_rez_info["platform"]
        assert data["platform"]["arch"] == mock_rez_info["arch"]

        # Check Python info
        assert data["python"]["version"] == mock_rez_info["python_version"]
        assert data["python"]["executable"] == mock_rez_info["python_path"]

    @patch("rez_proxy.utils.rez_detector.detect_rez_installation")
    def test_get_system_environment(self, mock_detect, client, mock_rez_info):
        """Test system environment endpoint."""
        mock_rez_info_with_env = {
            **mock_rez_info,
            "environment_variables": {"REZ_PACKAGES_PATH": "/path/to/packages"},
        }
        mock_detect.return_value = mock_rez_info_with_env

        response = client.get("/api/v1/system/environment")
        assert response.status_code == 200

        data = response.json()
        assert "environment" in data
        assert isinstance(data["environment"], dict)

    @patch("rez.config.config")
    def test_get_rez_config(self, mock_config, client):
        """Test Rez config endpoint."""
        # Mock config object
        mock_config.packages_path = ["/path/to/packages"]
        mock_config.local_packages_path = "/path/to/local"
        mock_config.release_packages_path = ["/path/to/release"]
        mock_config.tmpdir = "/tmp/rez"
        mock_config.default_shell = "bash"

        response = client.get("/api/v1/system/rez-config")
        assert response.status_code == 200

        data = response.json()
        assert "packages_path" in data
        assert "local_packages_path" in data
        assert "default_shell" in data

    def test_get_system_health(self, client):
        """Test system health endpoint."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime" in data

    @patch("rez_proxy.utils.rez_detector.detect_rez_installation")
    def test_get_system_diagnostics(self, mock_detect, client, mock_rez_info):
        """Test system diagnostics endpoint."""
        mock_detect.return_value = mock_rez_info

        response = client.get("/api/v1/system/diagnostics")
        assert response.status_code == 200

        data = response.json()
        assert "rez_installation" in data
        assert "platform_info" in data
        assert "python_info" in data
        assert "system_checks" in data

    @patch("rez_proxy.utils.rez_detector.detect_rez_installation")
    def test_get_system_version(self, mock_detect, client, mock_rez_info):
        """Test system version endpoint."""
        mock_detect.return_value = mock_rez_info

        response = client.get("/api/v1/system/version")
        assert response.status_code == 200

        data = response.json()
        assert "rez_proxy_version" in data
        assert "rez_version" in data
        assert "python_version" in data
        assert data["rez_version"] == mock_rez_info["version"]

    @patch("rez_proxy.routers.system.detect_rez_installation")
    def test_system_endpoints_exception_handling(self, mock_detect, client):
        """Test system endpoints exception handling."""
        mock_detect.side_effect = Exception("System error")

        endpoints = [
            "/api/v1/system/config",
            "/api/v1/system/info",
            "/api/v1/system/environment",
            "/api/v1/system/diagnostics",
            "/api/v1/system/version",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 500

    def test_get_rez_config_exception_handling(self, client):
        """Test Rez config endpoint fallback behavior."""
        # Test that the endpoint works even when rez is not available
        # (it should use fallback data)
        response = client.get("/api/v1/system/rez-config")
        assert response.status_code == 200
        data = response.json()
        assert "packages_path" in data
        assert "local_packages_path" in data
        assert "default_shell" in data


class TestSystemUtilities:
    """Test system utility functions."""

    def test_system_status_determination(self):
        """Test system status determination logic."""
        from rez_proxy.routers.system import _determine_system_status

        # Test healthy system
        healthy_info = {
            "version": "3.2.1",
            "packages_path": ["/path/to/packages"],
            "python_path": "/usr/bin/python",
            "platform": "linux",
        }

        status, warnings = _determine_system_status(healthy_info)
        assert status == "healthy"
        assert warnings == []

    def test_system_status_with_warnings(self):
        """Test system status with warnings."""
        from rez_proxy.routers.system import _determine_system_status

        # Test system with potential issues
        warning_info = {
            "version": "3.2.1",
            "packages_path": [],  # Empty packages path
            "python_path": "/usr/bin/python",
            "platform": "linux",
        }

        status, warnings = _determine_system_status(warning_info)
        assert status == "warning"
        assert len(warnings) > 0

    def test_format_system_info(self):
        """Test system info formatting."""
        from rez_proxy.routers.system import _format_system_info

        raw_info = {
            "version": "3.2.1",
            "rez_root": "/path/to/rez",
            "python_path": "/usr/bin/python",
            "python_version": "3.9.0",
            "platform": "linux",
            "arch": "x86_64",
            "os": "ubuntu-20.04",
        }

        formatted = _format_system_info(raw_info)

        assert "rez" in formatted
        assert "platform" in formatted
        assert "python" in formatted
        assert formatted["rez"]["version"] == "3.2.1"
        assert formatted["platform"]["name"] == "linux"
        assert formatted["python"]["version"] == "3.9.0"

    def test_get_system_diagnostics_data(self):
        """Test system diagnostics data collection."""
        from rez_proxy.routers.system import _get_diagnostics_data

        mock_rez_info = {
            "version": "3.2.1",
            "python_path": "/usr/bin/python",
            "python_version": "3.9.0",
            "platform": "linux",
            "arch": "x86_64",
        }

        diagnostics = _get_diagnostics_data(mock_rez_info)

        assert "rez_installation" in diagnostics
        assert "platform_info" in diagnostics
        assert "python_info" in diagnostics
        assert "system_checks" in diagnostics

        # Check system checks
        checks = diagnostics["system_checks"]
        assert isinstance(checks, list)
        assert len(checks) > 0

        # Each check should have name, status, and message
        for check in checks:
            assert "name" in check
            assert "status" in check
            assert "message" in check
            assert check["status"] in ["pass", "fail", "warning"]
