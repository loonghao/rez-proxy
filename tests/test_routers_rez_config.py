"""
Test rez_config router functionality.
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


class TestRezConfigRouter:
    """Test rez_config router endpoints."""

    def test_get_config_info(self, client):
        """Test getting Rez configuration info."""
        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_configuration_summary.return_value = {
                "config_file": "/path/to/config.py",
                "packages_paths": ["/packages", "/shared/packages"],
                "local_packages_path": "/local/packages",
                "release_packages_paths": ["/release/packages"],
                "tmpdir": "/tmp/rez",
                "cache_path": "/cache/rez",
                "flags": {
                    "home_config_disabled": False,
                    "quiet_mode": False,
                    "debug_mode": False,
                },
                "environment_variables": {
                    "REZ_PACKAGES_PATH": "/packages:/shared/packages"
                },
                "warnings": [],
                "is_valid": True,
            }

            response = client.get("/api/v1/rez-config/info")

            assert response.status_code == 200
            data = response.json()
            assert data["config_file"] == "/path/to/config.py"
            assert len(data["packages_paths"]) == 2
            assert data["is_valid"] is True

    def test_get_config_info_with_warnings(self, client):
        """Test getting Rez configuration info with warnings."""
        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_configuration_summary.return_value = {
                "config_file": None,
                "packages_paths": [],
                "warnings": [
                    "No Rez packages paths configured",
                    "Config file not found",
                ],
                "is_valid": False,
            }

            response = client.get("/api/v1/rez-config/info")

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["warnings"]) == 2

    def test_get_config_info_error(self, client):
        """Test getting Rez configuration info with error."""
        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_configuration_summary.side_effect = Exception(
                "Config error"
            )

            response = client.get("/api/v1/rez-config/info")

            assert response.status_code == 500

    def test_validate_config(self, client):
        """Test validating Rez configuration."""
        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.validate_configuration.return_value = []

            response = client.get("/api/v1/rez-config/validate")

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["warnings"] == []

    def test_validate_config_with_warnings(self, client):
        """Test validating Rez configuration with warnings."""
        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.validate_configuration.return_value = [
                "Packages path does not exist: /nonexistent",
                "No write access to local packages path",
            ]

            response = client.get("/api/v1/rez-config/validate")

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert len(data["warnings"]) == 2

    def test_update_config(self, client):
        """Test updating Rez configuration."""
        config_update = {
            "packages_path": "/new/packages:/shared/packages",
            "local_packages_path": "/new/local",
            "quiet": True,
            "debug": False,
        }

        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            response = client.put("/api/v1/rez-config/update", json=config_update)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            mock_manager.apply_configuration_from_dict.assert_called_once_with(
                config_update
            )

    def test_update_config_validation_error(self, client):
        """Test updating Rez configuration with validation error."""
        config_update = {"invalid_field": "value"}

        response = client.put("/api/v1/rez-config/update", json=config_update)

        # Should still work as we accept any dict
        assert response.status_code == 200

    def test_update_config_error(self, client):
        """Test updating Rez configuration with error."""
        config_update = {"packages_path": "/new/packages"}

        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.apply_configuration_from_dict.side_effect = Exception(
                "Update failed"
            )

            response = client.put("/api/v1/rez-config/update", json=config_update)

            assert response.status_code == 500

    def test_get_environment_info(self, client):
        """Test getting Rez environment info."""
        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_env_info = MagicMock()
            mock_env_info.config_file = "/path/to/config.py"
            mock_env_info.packages_paths = ["/packages"]
            mock_env_info.local_packages_path = "/local"
            mock_env_info.release_packages_paths = ["/release"]
            mock_env_info.tmpdir = "/tmp"
            mock_env_info.cache_path = "/cache"
            mock_env_info.home_config_disabled = False
            mock_env_info.quiet_mode = False
            mock_env_info.debug_mode = True
            mock_env_info.environment_variables = {"REZ_DEBUG": "1"}
            mock_manager.get_environment_info.return_value = mock_env_info

            response = client.get("/api/v1/rez-config/environment")

            assert response.status_code == 200
            data = response.json()
            assert data["config_file"] == "/path/to/config.py"
            assert data["debug_mode"] is True
            assert "REZ_DEBUG" in data["environment_variables"]

    def test_create_config_template(self, client):
        """Test creating Rez configuration template."""
        template_request = {
            "output_path": "/tmp/rez_config_template.py",
            "include_comments": True,
        }

        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            response = client.post("/api/v1/rez-config/template", json=template_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["template_path"] == "/tmp/rez_config_template.py"
            mock_manager.create_rez_config_template.assert_called_once()

    def test_create_config_template_error(self, client):
        """Test creating Rez configuration template with error."""
        template_request = {"output_path": "/invalid/path/template.py"}

        with patch(
            "rez_proxy.routers.rez_config.get_rez_config_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.create_rez_config_template.side_effect = Exception(
                "Permission denied"
            )

            response = client.post("/api/v1/rez-config/template", json=template_request)

            assert response.status_code == 500

    def test_get_config_schema(self, client):
        """Test getting Rez configuration schema."""
        with patch(
            "rez_proxy.routers.rez_config.get_config_schema_impl"
        ) as mock_schema:
            mock_schema.return_value = {
                "type": "object",
                "properties": {
                    "packages_path": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of package repository paths",
                    },
                    "local_packages_path": {
                        "type": "string",
                        "description": "Path for local package development",
                    },
                    "quiet": {"type": "boolean", "description": "Enable quiet mode"},
                },
                "required": ["packages_path"],
            }

            response = client.get("/api/v1/rez-config/schema")

            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "object"
            assert "packages_path" in data["properties"]

    def test_reset_config(self, client):
        """Test resetting Rez configuration."""
        reset_request = {"reset_to_defaults": True, "clear_environment_vars": True}

        with patch("rez_proxy.routers.rez_config.reset_config_impl") as mock_reset:
            mock_reset.return_value = {
                "status": "success",
                "message": "Configuration reset to defaults",
                "cleared_vars": ["REZ_PACKAGES_PATH", "REZ_DEBUG"],
            }

            response = client.post("/api/v1/rez-config/reset", json=reset_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["cleared_vars"]) == 2

    def test_export_config(self, client):
        """Test exporting Rez configuration."""
        export_request = {
            "format": "json",
            "include_environment": True,
            "include_computed_values": False,
        }

        with patch("rez_proxy.routers.rez_config.export_config_impl") as mock_export:
            mock_export.return_value = {
                "config": {
                    "packages_path": ["/packages"],
                    "local_packages_path": "/local",
                    "quiet": False,
                },
                "environment": {"REZ_PACKAGES_PATH": "/packages"},
                "export_timestamp": "2023-01-01T10:00:00Z",
                "format": "json",
            }

            response = client.post("/api/v1/rez-config/export", json=export_request)

            assert response.status_code == 200
            data = response.json()
            assert "config" in data
            assert "environment" in data
            assert data["format"] == "json"

    def test_import_config(self, client):
        """Test importing Rez configuration."""
        import_request = {
            "config": {
                "packages_path": ["/imported/packages"],
                "local_packages_path": "/imported/local",
                "debug": True,
            },
            "merge_with_existing": True,
            "validate_before_import": True,
        }

        with patch("rez_proxy.routers.rez_config.import_config_impl") as mock_import:
            mock_import.return_value = {
                "status": "success",
                "message": "Configuration imported successfully",
                "imported_settings": ["packages_path", "local_packages_path", "debug"],
                "warnings": [],
            }

            response = client.post("/api/v1/rez-config/import", json=import_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["imported_settings"]) == 3

    def test_import_config_validation_error(self, client):
        """Test importing invalid Rez configuration."""
        import_request = {
            "config": {
                "packages_path": "invalid_type",  # Should be array
                "unknown_setting": "value",
            },
            "validate_before_import": True,
        }

        with patch("rez_proxy.routers.rez_config.import_config_impl") as mock_import:
            mock_import.return_value = {
                "status": "error",
                "message": "Configuration validation failed",
                "errors": [
                    "packages_path must be an array",
                    "unknown_setting is not a valid configuration option",
                ],
            }

            response = client.post("/api/v1/rez-config/import", json=import_request)

            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            assert len(data["errors"]) == 2

    def test_get_config_diff(self, client):
        """Test getting configuration diff."""
        diff_request = {"compare_with": "defaults", "include_environment": True}

        with patch("rez_proxy.routers.rez_config.get_config_diff_impl") as mock_diff:
            mock_diff.return_value = {
                "differences": [
                    {
                        "setting": "packages_path",
                        "current": ["/custom/packages"],
                        "default": ["/usr/local/packages"],
                        "type": "modified",
                    },
                    {
                        "setting": "debug",
                        "current": True,
                        "default": False,
                        "type": "modified",
                    },
                ],
                "total_differences": 2,
                "comparison_target": "defaults",
            }

            response = client.post("/api/v1/rez-config/diff", json=diff_request)

            assert response.status_code == 200
            data = response.json()
            assert len(data["differences"]) == 2
            assert data["total_differences"] == 2
