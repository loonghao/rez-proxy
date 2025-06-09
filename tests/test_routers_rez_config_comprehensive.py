"""
Comprehensive tests for rez_proxy.routers.rez_config module.

This test suite aims to achieve high coverage for the rez_config router,
testing all API endpoints including configuration retrieval, validation,
platform info, plugins, environment variables, cache info, and build info.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rez_proxy.routers.rez_config import ConfigUpdateRequest, router


@pytest.fixture
def app():
    """Create FastAPI app with rez_config router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/rez-config")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rez_config():
    """Mock rez config object."""
    config = MagicMock()
    config.packages_path = ["/path/to/packages", "/another/path"]
    config.local_packages_path = "/local/packages"
    config.release_packages_path = ["/release/packages"]
    config.rez_version = "2.114.0"
    config.build_directory = "/tmp/build"
    config.build_thread_count = 4
    config.cmake_build_args = ["-j4"]
    config.make_build_args = ["-j4"]
    config.disable_rez_1_compatibility = False
    config.package_cache_max_variant_logs = 100
    config.package_cache_same_device = True
    config.package_cache_log_days = 7

    # Add some test attributes for serialization testing
    config.test_string = "test_value"
    config.test_int = 42
    config.test_float = 3.14
    config.test_bool = True
    config.test_list = ["item1", "item2"]
    config.test_dict = {"key": "value"}
    config.test_none = None

    # Add non-serializable attribute
    config.test_function = lambda x: x

    return config


@pytest.fixture
def mock_rez_system():
    """Mock rez system object."""
    system = MagicMock()
    system.platform = "linux-x86_64"
    system.arch = "x86_64"
    system.os = "linux"
    system.python_version = "3.9.0"
    return system


@pytest.fixture
def mock_plugin_manager():
    """Mock rez plugin manager."""
    manager = MagicMock()
    manager.get_plugins.return_value = {
        "filesystem": MagicMock(),
        "memory": MagicMock(),
    }
    return manager


class TestGetRezConfig:
    """Test the get_rez_config endpoint."""

    def test_get_rez_config_success(self, client, mock_rez_config):
        """Test successful config retrieval."""
        with patch("rez.config.config", mock_rez_config):
            response = client.get("/api/v1/rez-config/")

            assert response.status_code == 200
            data = response.json()
            assert "config" in data
            config = data["config"]

            # Check serializable attributes are included
            assert config["test_string"] == "test_value"
            assert config["test_int"] == 42
            assert config["test_float"] == 3.14
            assert config["test_bool"] is True
            assert config["test_list"] == ["item1", "item2"]
            assert config["test_dict"] == {"key": "value"}
            assert config["test_none"] is None

            # Check non-serializable attributes are excluded
            assert "test_function" not in config

    def test_get_rez_config_with_attribute_error(self, client):
        """Test config retrieval with attribute errors."""
        mock_config = MagicMock()

        # Mock dir() to return some attributes
        with patch(
            "rez_proxy.routers.rez_config.dir",
            return_value=["valid_attr", "error_attr"],
        ):
            # Mock getattr to raise AttributeError for error_attr
            def mock_getattr(obj, name):
                if name == "error_attr":
                    raise AttributeError("Test error")
                return "valid_value"

            with patch(
                "builtins.getattr", side_effect=mock_getattr
            ):
                with patch("rez.config.config", mock_config):
                    response = client.get("/api/v1/rez-config/")

                    assert response.status_code == 200
                    data = response.json()
                    config = data["config"]
                    assert "valid_attr" in config
                    assert "error_attr" not in config

    def test_get_rez_config_import_error(self, client):
        """Test config retrieval with import error."""
        with patch.dict('sys.modules', {'rez.config': None}):
            response = client.get("/api/v1/rez-config/")

            assert response.status_code == 500
            assert "Failed to get Rez config" in response.json()["detail"]

    def test_get_rez_config_general_exception(self, client):
        """Test config retrieval with general exception."""
        with patch(
            "rez.config.config",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/")

            assert response.status_code == 500
            assert "Failed to get Rez config" in response.json()["detail"]


class TestGetConfigValue:
    """Test the get_config_value endpoint."""

    def test_get_config_value_success(self, client, mock_rez_config):
        """Test successful config value retrieval."""
        with patch("rez.config.config", mock_rez_config):
            response = client.get("/api/v1/rez-config/key/test_string")

            assert response.status_code == 200
            data = response.json()
            assert data["key"] == "test_string"
            assert data["value"] == "test_value"
            assert data["type"] == "str"

    def test_get_config_value_not_found(self, client, mock_rez_config):
        """Test config value retrieval for non-existent key."""
        with patch("rez.config.config", mock_rez_config):
            with patch("builtins.hasattr", return_value=False):
                response = client.get("/api/v1/rez-config/key/nonexistent")

                assert response.status_code == 404
                assert (
                    "Configuration key 'nonexistent' not found"
                    in response.json()["detail"]
                )

    def test_get_config_value_import_error(self, client):
        """Test config value retrieval with import error."""
        with patch(
            "rez.config.config",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/key/test_key")

            assert response.status_code == 500
            assert "Failed to get config value" in response.json()["detail"]

    def test_get_config_value_general_exception(self, client, mock_rez_config):
        """Test config value retrieval with general exception."""
        with patch("rez.config.config", mock_rez_config):
            with patch(
                "builtins.getattr",
                side_effect=Exception("Unexpected error"),
            ):
                response = client.get("/api/v1/rez-config/key/test_string")

                assert response.status_code == 500
                assert "Failed to get config value" in response.json()["detail"]


class TestGetPackagesPaths:
    """Test the get_packages_paths endpoint."""

    def test_get_packages_paths_success(self, client, mock_rez_config):
        """Test successful packages paths retrieval."""
        with patch("rez.config.config", mock_rez_config):
            response = client.get("/api/v1/rez-config/packages-path")

            assert response.status_code == 200
            data = response.json()
            assert data["packages_path"] == ["/path/to/packages", "/another/path"]
            assert data["local_packages_path"] == "/local/packages"
            assert data["release_packages_path"] == ["/release/packages"]

    def test_get_packages_paths_with_defaults(self, client):
        """Test packages paths retrieval with default values."""
        mock_config = MagicMock()

        # Mock getattr to return defaults for missing attributes
        def mock_getattr(obj, name, default=None):
            if name == "packages_path":
                return []
            elif name == "local_packages_path":
                return None
            elif name == "release_packages_path":
                return []
            return default

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                response = client.get("/api/v1/rez-config/packages-path")

                assert response.status_code == 200
                data = response.json()
                assert data["packages_path"] == []
                assert data["local_packages_path"] is None
                assert data["release_packages_path"] == []

    def test_get_packages_paths_import_error(self, client):
        """Test packages paths retrieval with import error."""
        with patch(
            "rez.config.config",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/packages-path")

            assert response.status_code == 500
            assert "Failed to get packages paths" in response.json()["detail"]

    def test_get_packages_paths_general_exception(self, client):
        """Test packages paths retrieval with general exception."""
        with patch(
            "rez.config.config",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/packages-path")

            assert response.status_code == 500
            assert "Failed to get packages paths" in response.json()["detail"]


class TestGetPlatformInfo:
    """Test the get_platform_info endpoint."""

    def test_get_platform_info_success(self, client, mock_rez_config, mock_rez_system):
        """Test successful platform info retrieval."""
        with patch("rez.config.config", mock_rez_config):
            with patch("rez.system.system", mock_rez_system):
                response = client.get("/api/v1/rez-config/platform-info")

                assert response.status_code == 200
                data = response.json()
                assert data["platform"] == "linux-x86_64"
                assert data["arch"] == "x86_64"
                assert data["os"] == "linux"
                assert data["python_version"] == "3.9.0"
                assert data["rez_version"] == "2.114.0"

    def test_get_platform_info_missing_rez_version(self, client, mock_rez_system):
        """Test platform info retrieval with missing rez_version."""
        mock_config = MagicMock()

        # Mock getattr to return "unknown" for missing rez_version
        def mock_getattr(obj, name, default=None):
            if name == "rez_version":
                return default
            return "test_value"

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                with patch("rez.system.system", mock_rez_system):
                    response = client.get("/api/v1/rez-config/platform-info")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["rez_version"] == "unknown"

    def test_get_platform_info_import_error(self, client):
        """Test platform info retrieval with import error."""
        with patch(
            "rez.config.config",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/platform-info")

            assert response.status_code == 500
            assert "Failed to get platform info" in response.json()["detail"]

    def test_get_platform_info_general_exception(self, client):
        """Test platform info retrieval with general exception."""
        with patch(
            "rez.config.config",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/platform-info")

            assert response.status_code == 500
            assert "Failed to get platform info" in response.json()["detail"]


class TestGetPluginInfo:
    """Test the get_plugin_info endpoint."""

    def test_get_plugin_info_success(self, client, mock_plugin_manager):
        """Test successful plugin info retrieval."""
        with patch("rez.plugin_managers.plugin_manager", mock_plugin_manager):
            response = client.get("/api/v1/rez-config/plugins")

            assert response.status_code == 200
            data = response.json()
            assert "plugins" in data
            plugins = data["plugins"]

            # Check all plugin types are present
            expected_types = [
                "package_repository",
                "shell",
                "build_system",
                "release_hook",
                "command",
            ]
            for plugin_type in expected_types:
                assert plugin_type in plugins
                assert plugins[plugin_type] == ["filesystem", "memory"]

    def test_get_plugin_info_with_plugin_exceptions(self, client):
        """Test plugin info retrieval with plugin-specific exceptions."""
        mock_manager = MagicMock()

        def mock_get_plugins(plugin_type):
            if plugin_type == "package_repository":
                return {"filesystem": MagicMock(), "memory": MagicMock()}
            elif plugin_type == "shell":
                raise Exception("Shell plugin error")
            elif plugin_type == "build_system":
                return None
            else:
                return {}

        mock_manager.get_plugins.side_effect = mock_get_plugins

        with patch("rez.plugin_managers.plugin_manager", mock_manager):
            response = client.get("/api/v1/rez-config/plugins")

            assert response.status_code == 200
            data = response.json()
            plugins = data["plugins"]

            assert plugins["package_repository"] == ["filesystem", "memory"]
            assert plugins["shell"] == []  # Exception handled
            assert plugins["build_system"] == []  # None handled
            assert plugins["release_hook"] == []  # Empty dict
            assert plugins["command"] == []  # Empty dict

    def test_get_plugin_info_import_error(self, client):
        """Test plugin info retrieval with import error."""
        with patch(
            "rez.plugin_managers.plugin_manager",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/plugins")

            assert response.status_code == 500
            assert "Failed to get plugin info" in response.json()["detail"]

    def test_get_plugin_info_general_exception(self, client):
        """Test plugin info retrieval with general exception."""
        with patch(
            "rez.plugin_managers.plugin_manager",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/plugins")

            assert response.status_code == 500
            assert "Failed to get plugin info" in response.json()["detail"]


class TestGetEnvironmentVariables:
    """Test the get_environment_variables endpoint."""

    def test_get_environment_variables_success(self, client):
        """Test successful environment variables retrieval."""
        test_env = {
            "REZ_PACKAGES_PATH": "/path/to/packages",
            "REZ_CONFIG_FILE": "/path/to/config.py",
            "REZ_TMPDIR": "/tmp/rez",
            "PATH": "/usr/bin:/bin",  # Non-REZ variable
            "HOME": "/home/user",  # Non-REZ variable
        }

        with patch.dict(os.environ, test_env, clear=True):
            response = client.get("/api/v1/rez-config/environment-vars")

            assert response.status_code == 200
            data = response.json()
            assert "environment_variables" in data
            env_vars = data["environment_variables"]

            # Only REZ_ variables should be included
            assert env_vars["REZ_PACKAGES_PATH"] == "/path/to/packages"
            assert env_vars["REZ_CONFIG_FILE"] == "/path/to/config.py"
            assert env_vars["REZ_TMPDIR"] == "/tmp/rez"
            assert "PATH" not in env_vars
            assert "HOME" not in env_vars

    def test_get_environment_variables_no_rez_vars(self, client):
        """Test environment variables retrieval with no REZ variables."""
        test_env = {"PATH": "/usr/bin:/bin", "HOME": "/home/user"}

        with patch.dict(os.environ, test_env, clear=True):
            response = client.get("/api/v1/rez-config/environment-vars")

            assert response.status_code == 200
            data = response.json()
            assert data["environment_variables"] == {}

    def test_get_environment_variables_exception(self, client):
        """Test environment variables retrieval with exception."""
        with patch(
            "os.environ", side_effect=Exception("OS error")
        ):
            response = client.get("/api/v1/rez-config/environment-vars")

            assert response.status_code == 500
            assert "Failed to get environment variables" in response.json()["detail"]


class TestGetCacheInfo:
    """Test the get_cache_info endpoint."""

    def test_get_cache_info_success(self, client, mock_rez_config):
        """Test successful cache info retrieval."""
        with patch("rez.config.config", mock_rez_config):
            response = client.get("/api/v1/rez-config/cache-info")

            assert response.status_code == 200
            data = response.json()
            assert data["package_cache_disabled"] is False
            assert data["package_cache_max_variant_logs"] == 100
            assert data["package_cache_same_device"] is True
            assert data["package_cache_log_days"] == 7

    def test_get_cache_info_with_defaults(self, client):
        """Test cache info retrieval with default values."""
        mock_config = MagicMock()

        # Mock getattr to return defaults for missing attributes
        def mock_getattr(obj, name, default=None):
            return default

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                response = client.get("/api/v1/rez-config/cache-info")

                assert response.status_code == 200
                data = response.json()
                assert data["package_cache_disabled"] is False
                assert data["package_cache_max_variant_logs"] == 0
                assert data["package_cache_same_device"] is True
                assert data["package_cache_log_days"] == 7

    def test_get_cache_info_import_error(self, client):
        """Test cache info retrieval with import error."""
        with patch(
            "rez.config.config",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/cache-info")

            assert response.status_code == 500
            assert "Failed to get cache info" in response.json()["detail"]

    def test_get_cache_info_general_exception(self, client):
        """Test cache info retrieval with general exception."""
        with patch(
            "rez.config.config",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/cache-info")

            assert response.status_code == 500
            assert "Failed to get cache info" in response.json()["detail"]


class TestGetBuildInfo:
    """Test the get_build_info endpoint."""

    def test_get_build_info_success(self, client, mock_rez_config):
        """Test successful build info retrieval."""
        with patch("rez.config.config", mock_rez_config):
            response = client.get("/api/v1/rez-config/build-info")

            assert response.status_code == 200
            data = response.json()
            assert data["build_directory"] == "/tmp/build"
            assert data["build_thread_count"] == 4
            assert data["cmake_build_args"] == ["-j4"]
            assert data["make_build_args"] == ["-j4"]

    def test_get_build_info_with_defaults(self, client):
        """Test build info retrieval with default values."""
        mock_config = MagicMock()

        # Mock getattr to return defaults for missing attributes
        def mock_getattr(obj, name, default=None):
            if name == "build_thread_count":
                return "logical_cores"
            elif name in ["cmake_build_args", "make_build_args"]:
                return []
            return default

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                response = client.get("/api/v1/rez-config/build-info")

                assert response.status_code == 200
                data = response.json()
                assert data["build_directory"] is None
                assert data["build_thread_count"] == "logical_cores"
                assert data["cmake_build_args"] == []
                assert data["make_build_args"] == []

    def test_get_build_info_import_error(self, client):
        """Test build info retrieval with import error."""
        with patch(
            "rez.config.config",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/build-info")

            assert response.status_code == 500
            assert "Failed to get build info" in response.json()["detail"]

    def test_get_build_info_general_exception(self, client):
        """Test build info retrieval with general exception."""
        with patch(
            "rez.config.config",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/build-info")

            assert response.status_code == 500
            assert "Failed to get build info" in response.json()["detail"]


class TestValidateConfig:
    """Test the validate_config endpoint."""

    def test_validate_config_success_all_valid(self, client, mock_rez_config):
        """Test successful config validation with all valid paths."""
        with patch("rez.config.config", mock_rez_config):
            with patch(
                "os.path.exists", return_value=True
            ):
                with patch("os.access", return_value=True):
                    response = client.get("/api/v1/rez-config/validation")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["valid"] is True
                    assert len(data["warnings"]) == 0
                    assert len(data["errors"]) == 0

    def test_validate_config_no_packages_path(self, client):
        """Test config validation with no packages_path."""
        mock_config = MagicMock()

        # Mock getattr to return empty packages_path
        def mock_getattr(obj, name, default=None):
            if name == "packages_path":
                return []
            elif name == "local_packages_path":
                return None
            return default

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                response = client.get("/api/v1/rez-config/validation")

                assert response.status_code == 200
                data = response.json()
                assert data["valid"] is True  # Only warnings, no errors
                assert len(data["warnings"]) == 1
                assert "No packages_path configured" in data["warnings"][0]
                assert len(data["errors"]) == 0

    def test_validate_config_missing_packages_paths(self, client, mock_rez_config):
        """Test config validation with missing packages paths."""
        with patch("rez.config.config", mock_rez_config):
            with patch(
                "os.path.exists", return_value=False
            ):
                response = client.get("/api/v1/rez-config/validation")

                assert response.status_code == 200
                data = response.json()
                assert data["valid"] is True  # Only warnings, no errors
                assert len(data["warnings"]) >= 2  # At least 2 missing paths
                assert any("does not exist" in warning for warning in data["warnings"])

    def test_validate_config_no_read_access(self, client, mock_rez_config):
        """Test config validation with no read access to packages paths."""
        with patch("rez.config.config", mock_rez_config):
            with patch(
                "os.path.exists", return_value=True
            ):
                with patch(
                    "os.access", return_value=False
                ):
                    response = client.get("/api/v1/rez-config/validation")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["valid"] is False  # Errors make it invalid
                    assert len(data["errors"]) >= 2  # At least 2 access errors
                    assert any("No read access" in error for error in data["errors"])

    def test_validate_config_missing_local_path(self, client):
        """Test config validation with missing local packages path."""
        mock_config = MagicMock()

        # Mock getattr to return valid packages_path but missing local_path
        def mock_getattr(obj, name, default=None):
            if name == "packages_path":
                return ["/valid/path"]
            elif name == "local_packages_path":
                return "/missing/local/path"
            return default

        def mock_exists(path):
            return path == "/valid/path"  # Only main path exists

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                with patch(
                    "os.path.exists",
                    side_effect=mock_exists,
                ):
                    with patch(
                        "os.access", return_value=True
                    ):
                        response = client.get("/api/v1/rez-config/validation")

                        assert response.status_code == 200
                        data = response.json()
                        assert data["valid"] is True  # Only warnings
                        assert len(data["warnings"]) == 1
                        assert (
                            "Local packages path does not exist" in data["warnings"][0]
                        )

    def test_validate_config_mixed_issues(self, client):
        """Test config validation with mixed warnings and errors."""
        mock_config = MagicMock()

        # Mock getattr to return test paths
        def mock_getattr(obj, name, default=None):
            if name == "packages_path":
                return ["/valid/path", "/missing/path", "/no-access/path"]
            elif name == "local_packages_path":
                return "/missing/local/path"
            return default

        def mock_exists(path):
            return path in ["/valid/path", "/no-access/path"]

        def mock_access(path, mode):
            return path == "/valid/path"  # Only valid path has access

        with patch("builtins.getattr", side_effect=mock_getattr):
            with patch("rez.config.config", mock_config):
                with patch(
                    "os.path.exists",
                    side_effect=mock_exists,
                ):
                    with patch(
                        "os.access",
                        side_effect=mock_access,
                    ):
                        response = client.get("/api/v1/rez-config/validation")

                        assert response.status_code == 200
                        data = response.json()
                        assert data["valid"] is False  # Has errors
                        assert len(data["warnings"]) == 2  # Missing paths
                        assert len(data["errors"]) == 1  # No access path
                        assert any(
                            "does not exist" in warning for warning in data["warnings"]
                        )
                        assert any(
                            "No read access" in error for error in data["errors"]
                        )

    def test_validate_config_import_error(self, client):
        """Test config validation with import error."""
        with patch(
            "rez.config.config",
            side_effect=ImportError("Rez not available"),
        ):
            response = client.get("/api/v1/rez-config/validation")

            assert response.status_code == 500
            assert "Failed to validate config" in response.json()["detail"]

    def test_validate_config_general_exception(self, client):
        """Test config validation with general exception."""
        with patch(
            "rez.config.config",
            side_effect=Exception("Unexpected error"),
        ):
            response = client.get("/api/v1/rez-config/validation")

            assert response.status_code == 500
            assert "Failed to validate config" in response.json()["detail"]


class TestConfigUpdateRequest:
    """Test the ConfigUpdateRequest model."""

    def test_config_update_request_creation(self):
        """Test creating a ConfigUpdateRequest."""
        request = ConfigUpdateRequest(key="test_key", value="test_value")
        assert request.key == "test_key"
        assert request.value == "test_value"

    def test_config_update_request_with_different_types(self):
        """Test ConfigUpdateRequest with different value types."""
        # String value
        request1 = ConfigUpdateRequest(key="string_key", value="string_value")
        assert request1.value == "string_value"

        # Integer value
        request2 = ConfigUpdateRequest(key="int_key", value=42)
        assert request2.value == 42

        # List value
        request3 = ConfigUpdateRequest(key="list_key", value=["item1", "item2"])
        assert request3.value == ["item1", "item2"]

        # Dict value
        request4 = ConfigUpdateRequest(key="dict_key", value={"nested": "value"})
        assert request4.value == {"nested": "value"}
