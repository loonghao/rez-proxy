"""
Test package operations router functionality.
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


class TestPackageOpsRouter:
    """Test package operations router endpoints."""

    def test_install_package(self, client):
        """Test installing a package."""
        install_request = {
            "package_name": "python",
            "version": "3.9.0",
            "repository": "central",
        }

        with patch(
            "rez_proxy.routers.package_ops.install_package_impl"
        ) as mock_install:
            mock_install.return_value = {
                "status": "success",
                "package_name": "python",
                "version": "3.9.0",
                "install_path": "/packages/python/3.9.0",
            }

            response = client.post("/api/v1/package-ops/install", json=install_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["package_name"] == "python"

    def test_install_package_validation_error(self, client):
        """Test installing package with validation error."""
        install_request = {
            "package_name": "",  # Invalid empty name
            "version": "3.9.0",
        }

        response = client.post("/api/v1/package-ops/install", json=install_request)

        assert response.status_code == 422  # Validation error

    def test_install_package_error(self, client):
        """Test installing package with error."""
        install_request = {"package_name": "nonexistent", "version": "1.0.0"}

        with patch(
            "rez_proxy.routers.package_ops.install_package_impl"
        ) as mock_install:
            mock_install.side_effect = Exception("Package not found")

            response = client.post("/api/v1/package-ops/install", json=install_request)

            assert response.status_code == 500

    def test_uninstall_package(self, client):
        """Test uninstalling a package."""
        package_name = "python"
        version = "3.9.0"

        with patch(
            "rez_proxy.routers.package_ops.uninstall_package_impl"
        ) as mock_uninstall:
            mock_uninstall.return_value = {
                "status": "success",
                "package_name": package_name,
                "version": version,
                "message": "Package uninstalled successfully",
            }

            response = client.delete(
                f"/api/v1/package-ops/uninstall/{package_name}/{version}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["package_name"] == package_name

    def test_uninstall_package_not_found(self, client):
        """Test uninstalling non-existent package."""
        package_name = "nonexistent"
        version = "1.0.0"

        with patch(
            "rez_proxy.routers.package_ops.uninstall_package_impl"
        ) as mock_uninstall:
            mock_uninstall.return_value = None

            response = client.delete(
                f"/api/v1/package-ops/uninstall/{package_name}/{version}"
            )

            assert response.status_code == 404

    def test_update_package(self, client):
        """Test updating a package."""
        package_name = "python"
        update_request = {"target_version": "3.10.0", "force": False}

        with patch("rez_proxy.routers.package_ops.update_package_impl") as mock_update:
            mock_update.return_value = {
                "status": "success",
                "package_name": package_name,
                "old_version": "3.9.0",
                "new_version": "3.10.0",
            }

            response = client.put(
                f"/api/v1/package-ops/update/{package_name}", json=update_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["new_version"] == "3.10.0"

    def test_update_package_not_found(self, client):
        """Test updating non-existent package."""
        package_name = "nonexistent"
        update_request = {"target_version": "1.0.0"}

        with patch("rez_proxy.routers.package_ops.update_package_impl") as mock_update:
            mock_update.return_value = None

            response = client.put(
                f"/api/v1/package-ops/update/{package_name}", json=update_request
            )

            assert response.status_code == 404

    def test_copy_package(self, client):
        """Test copying a package."""
        copy_request = {
            "source_package": "python",
            "source_version": "3.9.0",
            "target_repository": "local",
            "target_version": "3.9.0-local",
        }

        with patch("rez_proxy.routers.package_ops.copy_package_impl") as mock_copy:
            mock_copy.return_value = {
                "status": "success",
                "source_package": "python",
                "source_version": "3.9.0",
                "target_path": "/local/packages/python/3.9.0-local",
            }

            response = client.post("/api/v1/package-ops/copy", json=copy_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["source_package"] == "python"

    def test_copy_package_error(self, client):
        """Test copying package with error."""
        copy_request = {
            "source_package": "nonexistent",
            "source_version": "1.0.0",
            "target_repository": "local",
        }

        with patch("rez_proxy.routers.package_ops.copy_package_impl") as mock_copy:
            mock_copy.side_effect = Exception("Source package not found")

            response = client.post("/api/v1/package-ops/copy", json=copy_request)

            assert response.status_code == 500

    def test_move_package(self, client):
        """Test moving a package."""
        move_request = {
            "source_package": "python",
            "source_version": "3.9.0",
            "target_repository": "archive",
            "remove_source": True,
        }

        with patch("rez_proxy.routers.package_ops.move_package_impl") as mock_move:
            mock_move.return_value = {
                "status": "success",
                "source_package": "python",
                "source_version": "3.9.0",
                "target_path": "/archive/packages/python/3.9.0",
            }

            response = client.post("/api/v1/package-ops/move", json=move_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_validate_package(self, client):
        """Test validating a package."""
        package_name = "python"
        version = "3.9.0"

        with patch(
            "rez_proxy.routers.package_ops.validate_package_impl"
        ) as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "package_name": package_name,
                "version": version,
                "warnings": [],
                "errors": [],
            }

            response = client.get(
                f"/api/v1/package-ops/validate/{package_name}/{version}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["package_name"] == package_name

    def test_validate_package_invalid(self, client):
        """Test validating invalid package."""
        package_name = "broken_package"
        version = "1.0.0"

        with patch(
            "rez_proxy.routers.package_ops.validate_package_impl"
        ) as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "package_name": package_name,
                "version": version,
                "warnings": ["Missing dependency"],
                "errors": ["Invalid package.py syntax"],
            }

            response = client.get(
                f"/api/v1/package-ops/validate/{package_name}/{version}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert len(data["errors"]) == 1
            assert len(data["warnings"]) == 1

    def test_validate_package_not_found(self, client):
        """Test validating non-existent package."""
        package_name = "nonexistent"
        version = "1.0.0"

        with patch(
            "rez_proxy.routers.package_ops.validate_package_impl"
        ) as mock_validate:
            mock_validate.return_value = None

            response = client.get(
                f"/api/v1/package-ops/validate/{package_name}/{version}"
            )

            assert response.status_code == 404

    def test_repair_package(self, client):
        """Test repairing a package."""
        package_name = "python"
        version = "3.9.0"
        repair_request = {
            "fix_permissions": True,
            "rebuild_metadata": True,
            "verify_dependencies": True,
        }

        with patch("rez_proxy.routers.package_ops.repair_package_impl") as mock_repair:
            mock_repair.return_value = {
                "status": "success",
                "package_name": package_name,
                "version": version,
                "repairs_performed": ["Fixed permissions", "Rebuilt metadata"],
                "issues_found": 2,
                "issues_fixed": 2,
            }

            response = client.post(
                f"/api/v1/package-ops/repair/{package_name}/{version}",
                json=repair_request,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["issues_fixed"] == 2

    def test_repair_package_not_found(self, client):
        """Test repairing non-existent package."""
        package_name = "nonexistent"
        version = "1.0.0"
        repair_request = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.repair_package_impl") as mock_repair:
            mock_repair.return_value = None

            response = client.post(
                f"/api/v1/package-ops/repair/{package_name}/{version}",
                json=repair_request,
            )

            assert response.status_code == 404

    def test_list_operations(self, client):
        """Test listing package operations."""
        with patch("rez_proxy.routers.package_ops.list_operations_impl") as mock_list:
            mock_list.return_value = {
                "operations": [
                    {
                        "operation_id": "op-123",
                        "type": "install",
                        "package_name": "python",
                        "status": "completed",
                        "timestamp": "2023-01-01T10:00:00Z",
                    },
                    {
                        "operation_id": "op-124",
                        "type": "update",
                        "package_name": "numpy",
                        "status": "in_progress",
                        "timestamp": "2023-01-01T10:05:00Z",
                    },
                ],
                "total": 2,
            }

            response = client.get("/api/v1/package-ops/operations")

            assert response.status_code == 200
            data = response.json()
            assert "operations" in data
            assert len(data["operations"]) == 2
            assert data["total"] == 2

    def test_get_operation_status(self, client):
        """Test getting operation status."""
        operation_id = "op-123"

        with patch(
            "rez_proxy.routers.package_ops.get_operation_status_impl"
        ) as mock_status:
            mock_status.return_value = {
                "operation_id": operation_id,
                "type": "install",
                "package_name": "python",
                "status": "completed",
                "progress": 100,
                "result": {"install_path": "/packages/python/3.9.0"},
            }

            response = client.get(f"/api/v1/package-ops/operations/{operation_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["operation_id"] == operation_id
            assert data["status"] == "completed"

    def test_get_operation_status_not_found(self, client):
        """Test getting status for non-existent operation."""
        operation_id = "nonexistent"

        with patch(
            "rez_proxy.routers.package_ops.get_operation_status_impl"
        ) as mock_status:
            mock_status.return_value = None

            response = client.get(f"/api/v1/package-ops/operations/{operation_id}")

            assert response.status_code == 404
