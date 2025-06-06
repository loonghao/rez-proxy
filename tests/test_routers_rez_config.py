"""
Test rez_config router functionality.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestRezConfigRouter:
    """Test rez_config router endpoints."""

    def test_get_rez_config(self, client):
        """Test getting complete Rez configuration."""
        with patch("rez.config.config") as mock_config:
            # Mock config object
            mock_config._data = {
                "packages_path": ["/packages"],
                "local_packages_path": "/local",
            }

            response = client.get("/api/v1/config/")

            assert response.status_code == 200
            data = response.json()
            assert "config" in data

    def test_get_config_value(self, client):
        """Test getting specific config value."""
        with patch("rez.config.config") as mock_config:
            # Mock config object
            mock_config.packages_path = ["/packages"]

            response = client.get("/api/v1/config/key/packages_path")

            assert response.status_code == 200
            data = response.json()
            assert "key" in data
            assert "value" in data

    def test_get_config_value_not_found(self, client):
        """Test getting non-existent config value."""
        with patch("rez.config.config") as mock_config:
            # Mock config object without the requested attribute
            del mock_config.nonexistent_key

            response = client.get("/api/v1/config/key/nonexistent_key")

            assert response.status_code == 404

    def test_get_packages_paths(self, client):
        """Test getting package paths."""
        with patch("rez.config.config") as mock_config:
            # Mock config object
            mock_config.packages_path = ["/packages"]
            mock_config.local_packages_path = "/local"

            response = client.get("/api/v1/config/packages-path")

            assert response.status_code == 200
            data = response.json()
            assert "packages_path" in data

    def test_get_platform_info(self, client):
        """Test getting platform information."""
        with (
            patch("rez.config.config") as mock_config,
            patch("rez.system.system") as mock_system,
        ):
            # Mock config and system objects
            mock_config.platform = "linux"
            mock_config.arch = "x86_64"
            mock_system.platform = "linux"
            mock_system.arch = "x86_64"

            response = client.get("/api/v1/config/platform-info")

            assert response.status_code == 200
            data = response.json()
            assert "platform" in data

    def test_get_plugin_info(self, client):
        """Test getting plugin information."""
        with patch("rez.plugin_managers.plugin_manager") as mock_pm:
            # Mock plugin manager
            mock_pm.get_plugins.return_value = {}

            response = client.get("/api/v1/config/plugins")

            assert response.status_code == 200
            data = response.json()
            assert "plugins" in data

    def test_get_environment_variables(self, client):
        """Test getting environment variables."""
        with patch("os.environ", {"REZ_PACKAGES_PATH": "/packages"}):
            response = client.get("/api/v1/config/environment-vars")

            assert response.status_code == 200
            data = response.json()
            assert "environment_vars" in data

    def test_get_cache_info(self, client):
        """Test getting cache information."""
        with patch("rez.config.config") as mock_config:
            # Mock config object
            mock_config.package_cache_disabled = False
            mock_config.package_cache_max_size = 1000

            response = client.get("/api/v1/config/cache-info")

            assert response.status_code == 200
            data = response.json()
            assert "cache_disabled" in data

    def test_get_build_info(self, client):
        """Test getting build information."""
        with patch("rez.config.config") as mock_config:
            # Mock config object
            mock_config.build_directory = "/tmp/build"
            mock_config.build_thread_count = 4

            response = client.get("/api/v1/config/build-info")

            assert response.status_code == 200
            data = response.json()
            assert "build_directory" in data

    def test_validate_config(self, client):
        """Test config validation."""
        with patch("os.path.exists") as mock_exists:
            # Mock path existence
            mock_exists.return_value = True

            response = client.get("/api/v1/config/validation")

            assert response.status_code == 200
            data = response.json()
            assert "valid" in data

    def test_error_handling(self, client):
        """Test error handling in config endpoints."""
        with patch("rez.config.config") as mock_config:
            # Mock an exception
            mock_config.side_effect = Exception("Config error")

            response = client.get("/api/v1/config/")

            assert response.status_code == 500

    def test_get_config_value_error(self, client):
        """Test error handling in get config value."""
        with patch("rez.config.config") as mock_config:
            # Mock an exception
            mock_config.side_effect = Exception("Config error")

            response = client.get("/api/v1/config/key/test_key")

            assert response.status_code == 500

    def test_get_packages_paths_error(self, client):
        """Test error handling in get packages paths."""
        with patch("rez.config.config") as mock_config:
            # Mock an exception
            mock_config.side_effect = Exception("Config error")

            response = client.get("/api/v1/config/packages-path")

            assert response.status_code == 500

    def test_get_platform_info_error(self, client):
        """Test error handling in get platform info."""
        with patch("rez.config.config") as mock_config:
            # Mock an exception
            mock_config.side_effect = Exception("Config error")

            response = client.get("/api/v1/config/platform-info")

            assert response.status_code == 500

    def test_get_plugin_info_error(self, client):
        """Test error handling in get plugin info."""
        with patch("rez.plugin_managers.plugin_manager") as mock_pm:
            # Mock an exception
            mock_pm.side_effect = Exception("Plugin error")

            response = client.get("/api/v1/config/plugins")

            assert response.status_code == 500
