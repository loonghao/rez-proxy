"""
Test package operations router functionality.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from rez_proxy.main import create_app
from rez_proxy.routers.package_ops import PackageOpsService


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def package_ops_service():
    """Create PackageOpsService instance."""
    return PackageOpsService()


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


class TestPackageOpsService:
    """Test PackageOpsService class methods."""

    def test_install_package_local_mode(self, package_ops_service):
        """Test installing package in local mode."""
        request = {
            "package_name": "python",
            "version": "3.9.0",
            "repository": "central",
        }

        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = True

            result = package_ops_service.install_package(request)

            assert result["status"] == "success"
            assert result["package_name"] == "python"
            assert result["version"] == "3.9.0"
            assert "install_path" in result

    def test_install_package_remote_mode(self, package_ops_service):
        """Test installing package in remote mode."""
        request = {
            "package_name": "python",
            "version": "3.9.0",
        }

        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = False

            result = package_ops_service.install_package(request)

            assert result["status"] == "success"
            assert result["package_name"] == "python"
            assert "Remote mode" in result["message"]

    def test_uninstall_package_local_mode_success(self, package_ops_service):
        """Test uninstalling package in local mode successfully."""
        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_package = MagicMock()
            mock_get_package.return_value = mock_package

            result = package_ops_service.uninstall_package("python", "3.9.0")

            assert result["status"] == "success"
            assert result["package_name"] == "python"
            assert result["version"] == "3.9.0"

    def test_uninstall_package_local_mode_not_found(self, package_ops_service):
        """Test uninstalling non-existent package in local mode."""
        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_get_package.return_value = None

            result = package_ops_service.uninstall_package("nonexistent", "1.0.0")

            assert result is None

    def test_uninstall_package_remote_mode(self, package_ops_service):
        """Test uninstalling package in remote mode."""
        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = False

            result = package_ops_service.uninstall_package("python", "3.9.0")

            assert result["status"] == "success"
            assert "Remote mode" in result["message"]

    def test_update_package_local_mode_success(self, package_ops_service):
        """Test updating package in local mode successfully."""
        request = {"target_version": "3.10.0"}

        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.iter_packages") as mock_iter,
        ):
            mock_local.return_value = True
            mock_package = MagicMock()
            mock_package.version = "3.9.0"
            mock_iter.return_value = [mock_package]

            result = package_ops_service.update_package("python", request)

            assert result["status"] == "success"
            assert result["package_name"] == "python"
            assert result["current_version"] == "3.9.0"
            assert result["target_version"] == "3.10.0"

    def test_update_package_local_mode_not_found(self, package_ops_service):
        """Test updating non-existent package in local mode."""
        request = {"target_version": "1.0.0"}

        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.iter_packages") as mock_iter,
        ):
            mock_local.return_value = True
            mock_iter.return_value = []

            result = package_ops_service.update_package("nonexistent", request)

            assert result is None

    def test_validate_package_local_mode_success(self, package_ops_service):
        """Test validating package in local mode successfully."""
        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_package = MagicMock()
            mock_package.description = "Test package"
            mock_package.authors = ["Test Author"]
            mock_get_package.return_value = mock_package

            result = package_ops_service.validate_package("python", "3.9.0")

            assert result["valid"] is True
            assert result["package_name"] == "python"
            assert result["version"] == "3.9.0"
            assert len(result["errors"]) == 0

    def test_validate_package_local_mode_with_warnings(self, package_ops_service):
        """Test validating package with warnings in local mode."""
        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_package = MagicMock()
            mock_package.description = None
            mock_package.authors = None
            mock_get_package.return_value = mock_package

            result = package_ops_service.validate_package("python", "3.9.0")

            assert result["valid"] is True
            assert len(result["warnings"]) == 2
            assert "no description" in result["warnings"][0]
            assert "no authors" in result["warnings"][1]

    def test_repair_package_local_mode_success(self, package_ops_service):
        """Test repairing package in local mode successfully."""
        request = {
            "fix_permissions": True,
            "rebuild_metadata": True,
            "verify_dependencies": True,
        }

        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_package = MagicMock()
            mock_get_package.return_value = mock_package

            result = package_ops_service.repair_package("python", "3.9.0", request)

            assert result["status"] == "success"
            assert result["package_name"] == "python"
            assert result["issues_found"] == 2
            assert result["issues_fixed"] == 2
            assert len(result["repairs_performed"]) == 3

    def test_copy_package_local_mode(self, package_ops_service):
        """Test copying package in local mode."""
        request = {
            "source_package": "python",
            "source_version": "3.9.0",
            "target_repository": "backup",
            "target_version": "3.9.0",
        }

        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = True

            result = package_ops_service.copy_package(request)

            assert result["status"] == "success"
            assert result["source_package"] == "python"
            assert result["target_repository"] == "backup"

    def test_move_package_local_mode(self, package_ops_service):
        """Test moving package in local mode."""
        request = {
            "source_package": "python",
            "source_version": "3.9.0",
            "target_repository": "archive",
            "remove_source": True,
        }

        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = True

            result = package_ops_service.move_package(request)

            assert result["status"] == "success"
            assert result["source_package"] == "python"
            assert result["remove_source"] is True

    def test_list_operations(self, package_ops_service):
        """Test listing operations."""
        result = package_ops_service.list_operations()

        assert "operations" in result
        assert "total" in result
        assert result["total"] == len(result["operations"])
        assert len(result["operations"]) > 0

    def test_get_operation_status_found(self, package_ops_service):
        """Test getting operation status for existing operation."""
        result = package_ops_service.get_operation_status("op_001")

        assert result is not None
        assert result["operation_id"] == "op_001"
        assert result["status"] == "completed"
        assert result["progress"] == 100

    def test_get_operation_status_not_found(self, package_ops_service):
        """Test getting operation status for non-existent operation."""
        result = package_ops_service.get_operation_status("nonexistent")

        assert result is None


class TestPackageOpsIntegration:
    """Test package operations integration scenarios."""

    def test_service_methods_integration(self, package_ops_service):
        """Test integration between service methods."""
        # Test install -> validate -> repair workflow
        install_request = {
            "package_name": "test-package",
            "version": "1.0.0",
        }

        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_package = MagicMock()
            mock_package.description = "Test package"
            mock_package.authors = ["Test Author"]
            mock_get_package.return_value = mock_package

            # 1. Install package
            install_result = package_ops_service.install_package(install_request)
            assert install_result["status"] == "success"

            # 2. Validate installed package
            validate_result = package_ops_service.validate_package(
                "test-package", "1.0.0"
            )
            assert validate_result["valid"] is True

            # 3. Repair package if needed
            repair_request = {"fix_permissions": True}
            repair_result = package_ops_service.repair_package(
                "test-package", "1.0.0", repair_request
            )
            assert repair_result["status"] == "success"

    def test_local_vs_remote_mode_consistency(self, package_ops_service):
        """Test consistency between local and remote mode operations."""
        request = {
            "package_name": "test-package",
            "version": "1.0.0",
        }

        # Test local mode
        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = True
            local_result = package_ops_service.install_package(request)

        # Test remote mode
        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = False
            remote_result = package_ops_service.install_package(request)

        # Both should succeed but with different implementations
        assert local_result["status"] == "success"
        assert remote_result["status"] == "success"
        assert "install_path" in local_result
        assert "Remote mode" in remote_result["message"]

    def test_error_propagation(self, package_ops_service):
        """Test error propagation through service methods."""
        with (
            patch("rez_proxy.core.context.is_local_mode") as mock_local,
            patch("rez.packages.get_package") as mock_get_package,
        ):
            mock_local.return_value = True
            mock_get_package.side_effect = Exception("Database error")

            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                package_ops_service.uninstall_package("test-package", "1.0.0")

            assert exc_info.value.status_code == 500
            assert "Database error" in str(exc_info.value.detail)

    def test_platform_info_consistency(self, package_ops_service):
        """Test that platform info is consistently included in responses."""
        request = {"package_name": "test-package", "version": "1.0.0"}

        with patch("rez_proxy.core.context.is_local_mode") as mock_local:
            mock_local.return_value = True

            # Test various operations
            install_result = package_ops_service.install_package(request)
            copy_result = package_ops_service.copy_package(request)
            move_result = package_ops_service.move_package(request)
            list_result = package_ops_service.list_operations()

            # All should include platform_info
            assert "platform_info" in install_result
            assert "platform_info" in copy_result
            assert "platform_info" in move_result
            assert "platform_info" in list_result

    def test_operation_status_workflow(self, package_ops_service):
        """Test operation status tracking workflow."""
        # Test getting status for known operations
        status_1 = package_ops_service.get_operation_status("op_001")
        status_2 = package_ops_service.get_operation_status("op_002")

        assert status_1 is not None
        assert status_1["status"] == "completed"
        assert status_2 is not None
        assert status_2["status"] == "in_progress"

        # Test getting status for unknown operation
        status_unknown = package_ops_service.get_operation_status("unknown")
        assert status_unknown is None

    def test_operations_list_consistency(self, package_ops_service):
        """Test operations list consistency."""
        operations_result = package_ops_service.list_operations()

        assert "operations" in operations_result
        assert "total" in operations_result
        assert operations_result["total"] == len(operations_result["operations"])

        # Check that each operation has required fields
        for operation in operations_result["operations"]:
            assert "operation_id" in operation
            assert "type" in operation
            assert "status" in operation
            assert "progress" in operation
