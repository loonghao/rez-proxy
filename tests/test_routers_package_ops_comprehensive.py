"""
Comprehensive tests for rez_proxy.routers.package_ops module.

This test suite aims to achieve high coverage for the package operations router,
testing all major functionality including package installation, uninstallation,
updates, validation, repair, copy, move, and operation management.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from rez_proxy.routers.package_ops import (
    router,
    PackageOpsService,
    package_ops_service,
    install_package_impl,
    uninstall_package_impl,
    update_package_impl,
    validate_package_impl,
    repair_package_impl,
    copy_package_impl,
    move_package_impl,
    list_operations_impl,
    get_operation_status_impl,
)


@pytest.fixture
def app():
    """Create FastAPI app with package_ops router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/package-ops")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_context():
    """Mock context for testing."""
    with patch("rez_proxy.routers.package_ops.get_current_context") as mock_get_context:
        mock_context = MagicMock()
        mock_context.service_mode.value = "local"
        mock_get_context.return_value = mock_context
        yield mock_context


@pytest.fixture
def mock_local_mode():
    """Mock local mode."""
    with patch("rez_proxy.routers.package_ops.is_local_mode", return_value=True):
        yield


@pytest.fixture
def mock_remote_mode():
    """Mock remote mode."""
    with patch("rez_proxy.routers.package_ops.is_local_mode", return_value=False):
        yield


class TestPackageOpsService:
    """Test the PackageOpsService class."""

    @pytest.fixture
    def service(self):
        """Create a PackageOpsService instance."""
        return PackageOpsService()

    def test_install_package_local_mode(self, service, mock_local_mode):
        """Test package installation in local mode."""
        request = {
            "package_name": "test-package",
            "version": "1.0.0",
            "repository": "local-repo"
        }
        
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.install_package(request)
            
            assert result["status"] == "success"
            assert result["package_name"] == "test-package"
            assert result["version"] == "1.0.0"
            assert result["repository"] == "local-repo"
            assert "install_path" in result
            assert result["platform_info"]["platform"] == "linux"

    def test_install_package_local_mode_no_version(self, service, mock_local_mode):
        """Test package installation in local mode without version."""
        request = {"package_name": "test-package"}
        
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.install_package(request)
            
            assert result["status"] == "success"
            assert result["version"] == "latest"

    def test_install_package_local_mode_exception(self, service, mock_local_mode):
        """Test package installation in local mode with exception."""
        request = {"package_name": "test-package"}
        
        with patch.object(service, "get_platform_specific_config", side_effect=Exception("Platform error")):
            with pytest.raises(Exception, match="Failed to install package"):
                service.install_package(request)

    def test_install_package_remote_mode(self, service, mock_remote_mode):
        """Test package installation in remote mode."""
        request = {
            "package_name": "test-package",
            "version": "1.0.0"
        }
        
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.install_package(request)
            
            assert result["status"] == "success"
            assert result["package_name"] == "test-package"
            assert result["version"] == "1.0.0"
            assert "Remote mode" in result["message"]

    def test_uninstall_package_local_mode_success(self, service, mock_local_mode):
        """Test package uninstallation in local mode - success."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"
                
                with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                    result = service.uninstall_package("test-package", "1.0.0")
                    
                    assert result["status"] == "success"
                    assert result["package_name"] == "test-package"
                    assert result["version"] == "1.0.0"
                    assert "uninstalled successfully" in result["message"]

    def test_uninstall_package_local_mode_not_found(self, service, mock_local_mode):
        """Test package uninstallation in local mode - package not found."""
        with patch("rez_proxy.routers.package_ops.get_package", return_value=None):
            with patch("rez_proxy.routers.package_ops.Version"):
                result = service.uninstall_package("test-package", "1.0.0")
                assert result is None

    def test_uninstall_package_local_mode_exception_in_get_package(self, service, mock_local_mode):
        """Test package uninstallation in local mode - exception in get_package."""
        with patch("rez_proxy.routers.package_ops.get_package", side_effect=Exception("Package error")):
            with patch("rez_proxy.routers.package_ops.Version"):
                result = service.uninstall_package("test-package", "1.0.0")
                assert result is None

    def test_uninstall_package_local_mode_general_exception(self, service, mock_local_mode):
        """Test package uninstallation in local mode - general exception."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"
                
                with patch.object(service, "get_platform_specific_config", side_effect=Exception("Platform error")):
                    with pytest.raises(Exception, match="Failed to uninstall package"):
                        service.uninstall_package("test-package", "1.0.0")

    def test_uninstall_package_remote_mode(self, service, mock_remote_mode):
        """Test package uninstallation in remote mode."""
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.uninstall_package("test-package", "1.0.0")
            
            assert result["status"] == "success"
            assert result["package_name"] == "test-package"
            assert result["version"] == "1.0.0"
            assert "Remote mode" in result["message"]

    def test_update_package_local_mode_success(self, service, mock_local_mode):
        """Test package update in local mode - success."""
        request = {"target_version": "2.0.0"}
        
        with patch("rez_proxy.routers.package_ops.iter_packages") as mock_iter_packages:
            mock_package = MagicMock()
            mock_package.version = "1.0.0"
            mock_iter_packages.return_value = [mock_package]
            
            with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                result = service.update_package("test-package", request)
                
                assert result["status"] == "success"
                assert result["package_name"] == "test-package"
                assert result["current_version"] == "1.0.0"
                assert result["target_version"] == "2.0.0"

    def test_update_package_local_mode_no_target_version(self, service, mock_local_mode):
        """Test package update in local mode without target version."""
        request = {}
        
        with patch("rez_proxy.routers.package_ops.iter_packages") as mock_iter_packages:
            mock_package = MagicMock()
            mock_package.version = "1.0.0"
            mock_iter_packages.return_value = [mock_package]
            
            with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                result = service.update_package("test-package", request)
                
                assert result["target_version"] == "latest"

    def test_update_package_local_mode_not_found(self, service, mock_local_mode):
        """Test package update in local mode - package not found."""
        request = {"target_version": "2.0.0"}
        
        with patch("rez_proxy.routers.package_ops.iter_packages", return_value=[]):
            result = service.update_package("test-package", request)
            assert result is None

    def test_update_package_local_mode_exception(self, service, mock_local_mode):
        """Test package update in local mode - exception."""
        request = {"target_version": "2.0.0"}
        
        with patch("rez_proxy.routers.package_ops.iter_packages", side_effect=Exception("Package error")):
            with pytest.raises(Exception, match="Failed to update package"):
                service.update_package("test-package", request)

    def test_update_package_remote_mode(self, service, mock_remote_mode):
        """Test package update in remote mode."""
        request = {"target_version": "2.0.0"}
        
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.update_package("test-package", request)
            
            assert result["status"] == "success"
            assert result["package_name"] == "test-package"
            assert result["target_version"] == "2.0.0"
            assert "Remote mode" in result["message"]

    def test_update_package_remote_mode_no_target_version(self, service, mock_remote_mode):
        """Test package update in remote mode without target version."""
        request = {}

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.update_package("test-package", request)

            assert result["target_version"] == "latest"

    def test_validate_package_local_mode_success(self, service, mock_local_mode):
        """Test package validation in local mode - success."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_package.description = "Test package"
                mock_package.authors = ["Test Author"]
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                    result = service.validate_package("test-package", "1.0.0")

                    assert result["valid"] is True
                    assert result["package_name"] == "test-package"
                    assert result["version"] == "1.0.0"
                    assert len(result["warnings"]) == 0
                    assert len(result["errors"]) == 0

    def test_validate_package_local_mode_with_warnings(self, service, mock_local_mode):
        """Test package validation in local mode - with warnings."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                # Package without description and authors
                mock_package.description = None
                mock_package.authors = None
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                    result = service.validate_package("test-package", "1.0.0")

                    assert result["valid"] is True  # No errors, just warnings
                    assert len(result["warnings"]) == 2
                    assert "no description" in result["warnings"][0]
                    assert "no authors" in result["warnings"][1]

    def test_validate_package_local_mode_not_found(self, service, mock_local_mode):
        """Test package validation in local mode - package not found."""
        with patch("rez_proxy.routers.package_ops.get_package", return_value=None):
            with patch("rez_proxy.routers.package_ops.Version"):
                result = service.validate_package("test-package", "1.0.0")
                assert result is None

    def test_validate_package_local_mode_exception_in_get_package(self, service, mock_local_mode):
        """Test package validation in local mode - exception in get_package."""
        with patch("rez_proxy.routers.package_ops.get_package", side_effect=Exception("Package error")):
            with patch("rez_proxy.routers.package_ops.Version"):
                result = service.validate_package("test-package", "1.0.0")
                assert result is None

    def test_validate_package_local_mode_general_exception(self, service, mock_local_mode):
        """Test package validation in local mode - general exception."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                with patch.object(service, "get_platform_specific_config", side_effect=Exception("Platform error")):
                    with pytest.raises(Exception, match="Failed to validate package"):
                        service.validate_package("test-package", "1.0.0")

    def test_validate_package_remote_mode(self, service, mock_remote_mode):
        """Test package validation in remote mode."""
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.validate_package("test-package", "1.0.0")

            assert result["valid"] is True
            assert result["package_name"] == "test-package"
            assert result["version"] == "1.0.0"
            assert len(result["warnings"]) == 0
            assert len(result["errors"]) == 0
            assert "Remote mode" in result["message"]

    def test_repair_package_local_mode_success(self, service, mock_local_mode):
        """Test package repair in local mode - success."""
        request = {
            "fix_permissions": True,
            "rebuild_metadata": True,
            "verify_dependencies": True
        }

        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                    result = service.repair_package("test-package", "1.0.0", request)

                    assert result["status"] == "success"
                    assert result["package_name"] == "test-package"
                    assert result["version"] == "1.0.0"
                    assert result["issues_found"] == 2  # fix_permissions and rebuild_metadata
                    assert result["issues_fixed"] == 2
                    assert len(result["repairs_performed"]) == 3

    def test_repair_package_local_mode_minimal_request(self, service, mock_local_mode):
        """Test package repair in local mode - minimal request."""
        request = {"verify_dependencies": True}

        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
                    result = service.repair_package("test-package", "1.0.0", request)

                    assert result["issues_found"] == 0
                    assert result["issues_fixed"] == 0
                    assert len(result["repairs_performed"]) == 1
                    assert "Verified dependencies" in result["repairs_performed"]

    def test_repair_package_local_mode_not_found(self, service, mock_local_mode):
        """Test package repair in local mode - package not found."""
        request = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.get_package", return_value=None):
            with patch("rez_proxy.routers.package_ops.Version"):
                result = service.repair_package("test-package", "1.0.0", request)
                assert result is None

    def test_repair_package_local_mode_exception_in_get_package(self, service, mock_local_mode):
        """Test package repair in local mode - exception in get_package."""
        request = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.get_package", side_effect=Exception("Package error")):
            with patch("rez_proxy.routers.package_ops.Version"):
                result = service.repair_package("test-package", "1.0.0", request)
                assert result is None

    def test_repair_package_local_mode_general_exception(self, service, mock_local_mode):
        """Test package repair in local mode - general exception."""
        request = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                with patch.object(service, "get_platform_specific_config", side_effect=Exception("Platform error")):
                    with pytest.raises(Exception, match="Failed to repair package"):
                        service.repair_package("test-package", "1.0.0", request)

    def test_repair_package_remote_mode(self, service, mock_remote_mode):
        """Test package repair in remote mode."""
        request = {"fix_permissions": True}

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.repair_package("test-package", "1.0.0", request)

            assert result["status"] == "success"
            assert result["package_name"] == "test-package"
            assert result["version"] == "1.0.0"
            assert result["issues_found"] == 0
            assert result["issues_fixed"] == 0
            assert "Remote mode" in result["message"]

    def test_copy_package_local_mode(self, service, mock_local_mode):
        """Test package copy in local mode."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo",
            "target_version": "1.1.0"
        }

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.copy_package(request)

            assert result["status"] == "success"
            assert result["source_package"] == "test-package"
            assert result["source_version"] == "1.0.0"
            assert result["target_repository"] == "target-repo"
            assert result["target_version"] == "1.1.0"
            assert "copied successfully" in result["message"]

    def test_copy_package_local_mode_no_target_version(self, service, mock_local_mode):
        """Test package copy in local mode without target version."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.copy_package(request)

            assert result["target_version"] == "1.0.0"  # Should default to source_version

    def test_copy_package_local_mode_exception(self, service, mock_local_mode):
        """Test package copy in local mode - exception."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch.object(service, "get_platform_specific_config", side_effect=Exception("Platform error")):
            with pytest.raises(Exception, match="Failed to copy package"):
                service.copy_package(request)

    def test_copy_package_remote_mode(self, service, mock_remote_mode):
        """Test package copy in remote mode."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.copy_package(request)

            assert result["status"] == "success"
            assert result["source_package"] == "test-package"
            assert result["source_version"] == "1.0.0"
            assert result["target_repository"] == "target-repo"
            assert "Remote mode" in result["message"]

    def test_move_package_local_mode(self, service, mock_local_mode):
        """Test package move in local mode."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo",
            "remove_source": True
        }

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.move_package(request)

            assert result["status"] == "success"
            assert result["source_package"] == "test-package"
            assert result["source_version"] == "1.0.0"
            assert result["target_repository"] == "target-repo"
            assert result["remove_source"] is True
            assert "moved successfully" in result["message"]

    def test_move_package_local_mode_default_remove_source(self, service, mock_local_mode):
        """Test package move in local mode with default remove_source."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.move_package(request)

            assert result["remove_source"] is True  # Should default to True

    def test_move_package_local_mode_exception(self, service, mock_local_mode):
        """Test package move in local mode - exception."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch.object(service, "get_platform_specific_config", side_effect=Exception("Platform error")):
            with pytest.raises(Exception, match="Failed to move package"):
                service.move_package(request)

    def test_move_package_remote_mode(self, service, mock_remote_mode):
        """Test package move in remote mode."""
        request = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.move_package(request)

            assert result["status"] == "success"
            assert result["source_package"] == "test-package"
            assert result["source_version"] == "1.0.0"
            assert result["target_repository"] == "target-repo"
            assert "Remote mode" in result["message"]

    def test_list_operations(self, service):
        """Test listing operations."""
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.list_operations()

            assert "operations" in result
            assert "total" in result
            assert result["total"] == len(result["operations"])
            assert len(result["operations"]) == 2  # Based on the implementation

            # Check first operation
            op1 = result["operations"][0]
            assert op1["operation_id"] == "op_001"
            assert op1["type"] == "install"
            assert op1["status"] == "completed"
            assert op1["progress"] == 100

    def test_get_operation_status_found_completed(self, service):
        """Test getting operation status - found completed operation."""
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.get_operation_status("op_001")

            assert result["operation_id"] == "op_001"
            assert result["type"] == "install"
            assert result["status"] == "completed"
            assert result["progress"] == 100
            assert "completed_at" in result

    def test_get_operation_status_found_in_progress(self, service):
        """Test getting operation status - found in-progress operation."""
        with patch.object(service, "get_platform_specific_config", return_value={"platform": "linux"}):
            result = service.get_operation_status("op_002")

            assert result["operation_id"] == "op_002"
            assert result["type"] == "update"
            assert result["status"] == "in_progress"
            assert result["progress"] == 75
            assert "completed_at" not in result

    def test_get_operation_status_not_found(self, service):
        """Test getting operation status - not found."""
        result = service.get_operation_status("nonexistent")
        assert result is None


class TestImplementationFunctions:
    """Test the implementation functions."""

    def test_install_package_impl(self, mock_local_mode):
        """Test install_package_impl function."""
        request = {"package_name": "test-package", "version": "1.0.0"}

        with patch.object(package_ops_service, "install_package") as mock_install:
            mock_install.return_value = {"status": "success"}

            result = install_package_impl(request)

            mock_install.assert_called_once_with(request)
            assert result["status"] == "success"

    def test_uninstall_package_impl(self, mock_local_mode):
        """Test uninstall_package_impl function."""
        with patch.object(package_ops_service, "uninstall_package") as mock_uninstall:
            mock_uninstall.return_value = {"status": "success"}

            result = uninstall_package_impl("test-package", "1.0.0")

            mock_uninstall.assert_called_once_with("test-package", "1.0.0")
            assert result["status"] == "success"

    def test_update_package_impl(self, mock_local_mode):
        """Test update_package_impl function."""
        request = {"target_version": "2.0.0"}

        with patch.object(package_ops_service, "update_package") as mock_update:
            mock_update.return_value = {"status": "success"}

            result = update_package_impl("test-package", request)

            mock_update.assert_called_once_with("test-package", request)
            assert result["status"] == "success"

    def test_validate_package_impl(self, mock_local_mode):
        """Test validate_package_impl function."""
        with patch.object(package_ops_service, "validate_package") as mock_validate:
            mock_validate.return_value = {"valid": True}

            result = validate_package_impl("test-package", "1.0.0")

            mock_validate.assert_called_once_with("test-package", "1.0.0")
            assert result["valid"] is True

    def test_repair_package_impl(self, mock_local_mode):
        """Test repair_package_impl function."""
        request = {"fix_permissions": True}

        with patch.object(package_ops_service, "repair_package") as mock_repair:
            mock_repair.return_value = {"status": "success"}

            result = repair_package_impl("test-package", "1.0.0", request)

            mock_repair.assert_called_once_with("test-package", "1.0.0", request)
            assert result["status"] == "success"

    def test_copy_package_impl(self, mock_local_mode):
        """Test copy_package_impl function."""
        request = {"source_package": "test-package"}

        with patch.object(package_ops_service, "copy_package") as mock_copy:
            mock_copy.return_value = {"status": "success"}

            result = copy_package_impl(request)

            mock_copy.assert_called_once_with(request)
            assert result["status"] == "success"

    def test_move_package_impl(self, mock_local_mode):
        """Test move_package_impl function."""
        request = {"source_package": "test-package"}

        with patch.object(package_ops_service, "move_package") as mock_move:
            mock_move.return_value = {"status": "success"}

            result = move_package_impl(request)

            mock_move.assert_called_once_with(request)
            assert result["status"] == "success"

    def test_list_operations_impl(self, mock_local_mode):
        """Test list_operations_impl function."""
        with patch.object(package_ops_service, "list_operations") as mock_list:
            mock_list.return_value = {"operations": [], "total": 0}

            result = list_operations_impl()

            mock_list.assert_called_once()
            assert result["total"] == 0

    def test_get_operation_status_impl(self, mock_local_mode):
        """Test get_operation_status_impl function."""
        with patch.object(package_ops_service, "get_operation_status") as mock_get_status:
            mock_get_status.return_value = {"operation_id": "op_001"}

            result = get_operation_status_impl("op_001")

            mock_get_status.assert_called_once_with("op_001")
            assert result["operation_id"] == "op_001"


class TestAPIEndpoints:
    """Test the API endpoints."""

    def test_install_package_endpoint_success(self, client, mock_context):
        """Test install package endpoint - success."""
        request_data = {
            "package_name": "test-package",
            "version": "1.0.0",
            "repository": "local-repo"
        }

        with patch("rez_proxy.routers.package_ops.install_package_impl") as mock_impl:
            mock_impl.return_value = {"status": "success", "package_name": "test-package"}

            with patch.object(package_ops_service, "get_platform_info") as mock_platform:
                mock_platform.return_value = MagicMock(platform="linux")

                response = client.post("/api/v1/package-ops/install", json=request_data)

                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert "context" in result
                assert result["context"]["service_mode"] == "local"

    def test_install_package_endpoint_exception(self, client, mock_context):
        """Test install package endpoint - exception."""
        request_data = {"package_name": "test-package"}

        with patch("rez_proxy.routers.package_ops.install_package_impl", side_effect=Exception("Install error")):
            response = client.post("/api/v1/package-ops/install", json=request_data)

            assert response.status_code == 500
            assert "Failed to install package" in response.json()["detail"]

    def test_uninstall_package_endpoint_success(self, client, mock_context):
        """Test uninstall package endpoint - success."""
        with patch("rez_proxy.routers.package_ops.uninstall_package_impl") as mock_impl:
            mock_impl.return_value = {"status": "success", "package_name": "test-package"}

            with patch.object(package_ops_service, "get_platform_info") as mock_platform:
                mock_platform.return_value = MagicMock(platform="linux")

                response = client.delete("/api/v1/package-ops/uninstall/test-package/1.0.0")

                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert "context" in result

    def test_uninstall_package_endpoint_not_found(self, client, mock_context):
        """Test uninstall package endpoint - package not found."""
        with patch("rez_proxy.routers.package_ops.uninstall_package_impl", return_value=None):
            response = client.delete("/api/v1/package-ops/uninstall/test-package/1.0.0")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_uninstall_package_endpoint_exception(self, client, mock_context):
        """Test uninstall package endpoint - exception."""
        with patch("rez_proxy.routers.package_ops.uninstall_package_impl", side_effect=Exception("Uninstall error")):
            response = client.delete("/api/v1/package-ops/uninstall/test-package/1.0.0")

            assert response.status_code == 500
            assert "Failed to uninstall package" in response.json()["detail"]

    def test_update_package_endpoint_success(self, client, mock_context):
        """Test update package endpoint - success."""
        request_data = {"target_version": "2.0.0"}

        with patch("rez_proxy.routers.package_ops.update_package_impl") as mock_impl:
            mock_impl.return_value = {"status": "success", "package_name": "test-package"}

            response = client.put("/api/v1/package-ops/update/test-package", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    def test_update_package_endpoint_not_found(self, client, mock_context):
        """Test update package endpoint - package not found."""
        request_data = {"target_version": "2.0.0"}

        with patch("rez_proxy.routers.package_ops.update_package_impl", return_value=None):
            response = client.put("/api/v1/package-ops/update/test-package", json=request_data)

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_update_package_endpoint_not_implemented(self, client, mock_context):
        """Test update package endpoint - not implemented."""
        request_data = {"target_version": "2.0.0"}

        with patch("rez_proxy.routers.package_ops.update_package_impl", side_effect=NotImplementedError()):
            response = client.put("/api/v1/package-ops/update/test-package", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_update_package_endpoint_exception(self, client, mock_context):
        """Test update package endpoint - exception."""
        request_data = {"target_version": "2.0.0"}

        with patch("rez_proxy.routers.package_ops.update_package_impl", side_effect=Exception("Update error")):
            response = client.put("/api/v1/package-ops/update/test-package", json=request_data)

            assert response.status_code == 500
            assert "Failed to update package" in response.json()["detail"]

    def test_validate_package_endpoint_success(self, client, mock_context):
        """Test validate package endpoint - success."""
        with patch("rez_proxy.routers.package_ops.validate_package_impl") as mock_impl:
            mock_impl.return_value = {"valid": True, "package_name": "test-package"}

            response = client.get("/api/v1/package-ops/validate/test-package/1.0.0")

            assert response.status_code == 200
            result = response.json()
            assert result["valid"] is True

    def test_validate_package_endpoint_not_found(self, client, mock_context):
        """Test validate package endpoint - package not found."""
        with patch("rez_proxy.routers.package_ops.validate_package_impl", return_value=None):
            response = client.get("/api/v1/package-ops/validate/test-package/1.0.0")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_validate_package_endpoint_not_implemented(self, client, mock_context):
        """Test validate package endpoint - not implemented."""
        with patch("rez_proxy.routers.package_ops.validate_package_impl", side_effect=NotImplementedError()):
            response = client.get("/api/v1/package-ops/validate/test-package/1.0.0")

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_validate_package_endpoint_exception(self, client, mock_context):
        """Test validate package endpoint - exception."""
        with patch("rez_proxy.routers.package_ops.validate_package_impl", side_effect=Exception("Validate error")):
            response = client.get("/api/v1/package-ops/validate/test-package/1.0.0")

            assert response.status_code == 500
            assert "Failed to validate package" in response.json()["detail"]

    def test_repair_package_endpoint_success(self, client, mock_context):
        """Test repair package endpoint - success."""
        request_data = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.repair_package_impl") as mock_impl:
            mock_impl.return_value = {"status": "success", "package_name": "test-package"}

            response = client.post("/api/v1/package-ops/repair/test-package/1.0.0", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    def test_repair_package_endpoint_not_found(self, client, mock_context):
        """Test repair package endpoint - package not found."""
        request_data = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.repair_package_impl", return_value=None):
            response = client.post("/api/v1/package-ops/repair/test-package/1.0.0", json=request_data)

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_repair_package_endpoint_not_implemented(self, client, mock_context):
        """Test repair package endpoint - not implemented."""
        request_data = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.repair_package_impl", side_effect=NotImplementedError()):
            response = client.post("/api/v1/package-ops/repair/test-package/1.0.0", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_repair_package_endpoint_exception(self, client, mock_context):
        """Test repair package endpoint - exception."""
        request_data = {"fix_permissions": True}

        with patch("rez_proxy.routers.package_ops.repair_package_impl", side_effect=Exception("Repair error")):
            response = client.post("/api/v1/package-ops/repair/test-package/1.0.0", json=request_data)

            assert response.status_code == 500
            assert "Failed to repair package" in response.json()["detail"]

    def test_list_operations_endpoint_success(self, client, mock_context):
        """Test list operations endpoint - success."""
        with patch("rez_proxy.routers.package_ops.list_operations_impl") as mock_impl:
            mock_impl.return_value = {"operations": [], "total": 0}

            response = client.get("/api/v1/package-ops/operations")

            assert response.status_code == 200
            result = response.json()
            assert result["total"] == 0

    def test_list_operations_endpoint_not_implemented(self, client, mock_context):
        """Test list operations endpoint - not implemented."""
        with patch("rez_proxy.routers.package_ops.list_operations_impl", side_effect=NotImplementedError()):
            response = client.get("/api/v1/package-ops/operations")

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_list_operations_endpoint_exception(self, client, mock_context):
        """Test list operations endpoint - exception."""
        with patch("rez_proxy.routers.package_ops.list_operations_impl", side_effect=Exception("List error")):
            response = client.get("/api/v1/package-ops/operations")

            assert response.status_code == 500
            assert "Failed to list operations" in response.json()["detail"]

    def test_get_operation_status_endpoint_success(self, client, mock_context):
        """Test get operation status endpoint - success."""
        with patch("rez_proxy.routers.package_ops.get_operation_status_impl") as mock_impl:
            mock_impl.return_value = {"operation_id": "op_001", "status": "completed"}

            response = client.get("/api/v1/package-ops/operations/op_001")

            assert response.status_code == 200
            result = response.json()
            assert result["operation_id"] == "op_001"

    def test_get_operation_status_endpoint_not_found(self, client, mock_context):
        """Test get operation status endpoint - not found."""
        with patch("rez_proxy.routers.package_ops.get_operation_status_impl", return_value=None):
            response = client.get("/api/v1/package-ops/operations/nonexistent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_operation_status_endpoint_not_implemented(self, client, mock_context):
        """Test get operation status endpoint - not implemented."""
        with patch("rez_proxy.routers.package_ops.get_operation_status_impl", side_effect=NotImplementedError()):
            response = client.get("/api/v1/package-ops/operations/op_001")

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_get_operation_status_endpoint_exception(self, client, mock_context):
        """Test get operation status endpoint - exception."""
        with patch("rez_proxy.routers.package_ops.get_operation_status_impl", side_effect=Exception("Status error")):
            response = client.get("/api/v1/package-ops/operations/op_001")

            assert response.status_code == 500
            assert "Failed to get operation status" in response.json()["detail"]

    def test_copy_package_endpoint_success(self, client, mock_context):
        """Test copy package endpoint - success."""
        request_data = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch("rez_proxy.routers.package_ops.copy_package_impl") as mock_impl:
            mock_impl.return_value = {"status": "success", "source_package": "test-package"}

            response = client.post("/api/v1/package-ops/copy", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    def test_copy_package_endpoint_not_implemented(self, client, mock_context):
        """Test copy package endpoint - not implemented."""
        request_data = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch("rez_proxy.routers.package_ops.copy_package_impl", side_effect=NotImplementedError()):
            response = client.post("/api/v1/package-ops/copy", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_copy_package_endpoint_exception(self, client, mock_context):
        """Test copy package endpoint - exception."""
        request_data = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch("rez_proxy.routers.package_ops.copy_package_impl", side_effect=Exception("Copy error")):
            response = client.post("/api/v1/package-ops/copy", json=request_data)

            assert response.status_code == 500
            assert "Failed to copy package" in response.json()["detail"]

    def test_move_package_endpoint_success(self, client, mock_context):
        """Test move package endpoint - success."""
        request_data = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo",
            "remove_source": True
        }

        with patch("rez_proxy.routers.package_ops.move_package_impl") as mock_impl:
            mock_impl.return_value = {"status": "success", "source_package": "test-package"}

            response = client.post("/api/v1/package-ops/move", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    def test_move_package_endpoint_not_implemented(self, client, mock_context):
        """Test move package endpoint - not implemented."""
        request_data = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch("rez_proxy.routers.package_ops.move_package_impl", side_effect=NotImplementedError()):
            response = client.post("/api/v1/package-ops/move", json=request_data)

            assert response.status_code == 200
            result = response.json()
            assert "implementation pending" in result["message"]

    def test_move_package_endpoint_exception(self, client, mock_context):
        """Test move package endpoint - exception."""
        request_data = {
            "source_package": "test-package",
            "source_version": "1.0.0",
            "target_repository": "target-repo"
        }

        with patch("rez_proxy.routers.package_ops.move_package_impl", side_effect=Exception("Move error")):
            response = client.post("/api/v1/package-ops/move", json=request_data)

            assert response.status_code == 500
            assert "Failed to move package" in response.json()["detail"]


class TestLegacyAPIEndpoints:
    """Test the legacy API endpoints that use Rez directly."""

    def test_copy_package_legacy_success(self, client, mock_context):
        """Test legacy copy package endpoint - success."""
        request_data = {
            "source_uri": "package://test-package-1.0.0",
            "dest_repository": "target-repo",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.copy_package") as mock_copy:
            with patch("rez_proxy.routers.package_ops.package_repository_manager") as mock_repo_mgr:
                mock_repo = MagicMock()
                mock_repo_mgr.get_repository.return_value = mock_repo
                mock_result = MagicMock()
                mock_result.uri = "package://test-package-1.0.0-copied"
                mock_copy.return_value = mock_result

                response = client.post("/api/v1/package-ops/copy", json=request_data)

                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                assert result["source_uri"] == request_data["source_uri"]

    def test_copy_package_legacy_repo_not_found(self, client, mock_context):
        """Test legacy copy package endpoint - repository not found."""
        request_data = {
            "source_uri": "package://test-package-1.0.0",
            "dest_repository": "nonexistent-repo",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.package_repository_manager") as mock_repo_mgr:
            mock_repo_mgr.get_repository.return_value = None

            response = client.post("/api/v1/package-ops/copy", json=request_data)

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_copy_package_legacy_exception(self, client, mock_context):
        """Test legacy copy package endpoint - exception."""
        request_data = {
            "source_uri": "package://test-package-1.0.0",
            "dest_repository": "target-repo",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.copy_package", side_effect=Exception("Copy failed")):
            with patch("rez_proxy.routers.package_ops.package_repository_manager") as mock_repo_mgr:
                mock_repo = MagicMock()
                mock_repo_mgr.get_repository.return_value = mock_repo

                response = client.post("/api/v1/package-ops/copy", json=request_data)

                assert response.status_code == 500
                assert "Failed to copy package" in response.json()["detail"]

    def test_move_package_legacy_success(self, client, mock_context):
        """Test legacy move package endpoint - success."""
        request_data = {
            "source_uri": "package://test-package-1.0.0",
            "dest_repository": "target-repo",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.move_package") as mock_move:
            with patch("rez_proxy.routers.package_ops.package_repository_manager") as mock_repo_mgr:
                mock_repo = MagicMock()
                mock_repo_mgr.get_repository.return_value = mock_repo
                mock_result = MagicMock()
                mock_result.uri = "package://test-package-1.0.0-moved"
                mock_move.return_value = mock_result

                response = client.post("/api/v1/package-ops/move", json=request_data)

                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                assert result["source_uri"] == request_data["source_uri"]

    def test_remove_package_version_success(self, client, mock_context):
        """Test remove package version endpoint - success."""
        request_data = {
            "package_name": "test-package",
            "version": "1.0.0",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.remove_package") as mock_remove:
                with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                    mock_package = MagicMock()
                    mock_get_package.return_value = mock_package
                    mock_version.return_value = "1.0.0"

                    response = client.delete("/api/v1/package-ops/remove", json=request_data)

                    assert response.status_code == 200
                    result = response.json()
                    assert result["success"] is True
                    assert result["action"] == "removed_version"

    def test_remove_package_family_success(self, client, mock_context):
        """Test remove package family endpoint - success."""
        request_data = {
            "package_name": "test-package",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.iter_packages") as mock_iter:
            with patch("rez_proxy.routers.package_ops.remove_package_family") as mock_remove:
                mock_packages = [MagicMock(), MagicMock()]
                mock_iter.return_value = mock_packages

                response = client.delete("/api/v1/package-ops/remove", json=request_data)

                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                assert result["action"] == "removed_family"
                assert result["versions_removed"] == 2

    def test_remove_package_not_found(self, client, mock_context):
        """Test remove package endpoint - package not found."""
        request_data = {
            "package_name": "nonexistent-package",
            "version": "1.0.0",
            "force": False
        }

        with patch("rez_proxy.routers.package_ops.get_package", return_value=None):
            with patch("rez_proxy.routers.package_ops.Version"):
                response = client.delete("/api/v1/package-ops/remove", json=request_data)

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_get_package_from_uri_success(self, client, mock_context):
        """Test get package from URI endpoint - success."""
        package_uri = "package://test-package-1.0.0"

        with patch("rez_proxy.routers.package_ops.get_package_from_uri") as mock_get:
            mock_package = MagicMock()
            mock_package.name = "test-package"
            mock_package.version = "1.0.0"
            mock_package.description = "Test package"
            mock_package.authors = ["Test Author"]
            mock_package.requires = []
            mock_get.return_value = mock_package

            response = client.get(f"/api/v1/package-ops/uri/{package_uri}")

            assert response.status_code == 200
            result = response.json()
            assert result["name"] == "test-package"
            assert result["version"] == "1.0.0"

    def test_get_package_from_uri_not_found(self, client, mock_context):
        """Test get package from URI endpoint - not found."""
        package_uri = "package://nonexistent-package-1.0.0"

        with patch("rez_proxy.routers.package_ops.get_package_from_uri", return_value=None):
            response = client.get(f"/api/v1/package-ops/uri/{package_uri}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_variant_from_uri_success(self, client, mock_context):
        """Test get variant from URI endpoint - success."""
        variant_uri = "package://test-package-1.0.0[0]"

        with patch("rez_proxy.routers.package_ops.get_variant_from_uri") as mock_get:
            mock_variant = MagicMock()
            mock_variant.parent.name = "test-package"
            mock_variant.parent.version = "1.0.0"
            mock_variant.index = 0
            mock_variant.subpath = None
            mock_variant.requires = []
            mock_get.return_value = mock_variant

            response = client.get(f"/api/v1/package-ops/variant/{variant_uri}")

            assert response.status_code == 200
            result = response.json()
            assert result["name"] == "test-package"
            assert result["version"] == "1.0.0"
            assert result["index"] == 0

    def test_get_variant_from_uri_not_found(self, client, mock_context):
        """Test get variant from URI endpoint - not found."""
        variant_uri = "package://nonexistent-package-1.0.0[0]"

        with patch("rez_proxy.routers.package_ops.get_variant_from_uri", return_value=None):
            response = client.get(f"/api/v1/package-ops/variant/{variant_uri}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_package_help_success(self, client, mock_context):
        """Test get package help endpoint - success."""
        with patch("rez_proxy.routers.package_ops.get_package_help") as mock_get_help:
            with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
                with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                    mock_package = MagicMock()
                    mock_package.version = "1.0.0"
                    mock_get_package.return_value = mock_package
                    mock_version.return_value = "1.0.0"
                    mock_get_help.return_value = "This is help text for test-package"

                    response = client.get("/api/v1/package-ops/help/test-package?version=1.0.0")

                    assert response.status_code == 200
                    result = response.json()
                    assert result["package"] == "test-package"
                    assert result["version"] == "1.0.0"
                    assert "help text" in result["help"]

    def test_get_package_help_latest_version(self, client, mock_context):
        """Test get package help endpoint - latest version."""
        with patch("rez_proxy.routers.package_ops.get_package_help") as mock_get_help:
            with patch("rez_proxy.routers.package_ops.iter_packages") as mock_iter:
                mock_package = MagicMock()
                mock_package.version = "2.0.0"
                mock_iter.return_value = [mock_package]
                mock_get_help.return_value = "This is help text for test-package"

                response = client.get("/api/v1/package-ops/help/test-package")

                assert response.status_code == 200
                result = response.json()
                assert result["package"] == "test-package"
                assert result["version"] == "2.0.0"

    def test_get_package_help_not_found(self, client, mock_context):
        """Test get package help endpoint - package not found."""
        with patch("rez_proxy.routers.package_ops.get_package", return_value=None):
            with patch("rez_proxy.routers.package_ops.Version"):
                response = client.get("/api/v1/package-ops/help/nonexistent-package?version=1.0.0")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    def test_get_package_tests_success(self, client, mock_context):
        """Test get package tests endpoint - success."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_package.version = "1.0.0"
                mock_package.tests = {"unit": "python -m pytest"}
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                response = client.get("/api/v1/package-ops/test/test-package?version=1.0.0")

                assert response.status_code == 200
                result = response.json()
                assert result["package"] == "test-package"
                assert result["version"] == "1.0.0"
                assert result["has_tests"] is True
                assert "unit" in result["tests"]

    def test_get_package_tests_no_tests(self, client, mock_context):
        """Test get package tests endpoint - no tests."""
        with patch("rez_proxy.routers.package_ops.get_package") as mock_get_package:
            with patch("rez_proxy.routers.package_ops.Version") as mock_version:
                mock_package = MagicMock()
                mock_package.version = "1.0.0"
                # Package without tests attribute
                del mock_package.tests
                mock_get_package.return_value = mock_package
                mock_version.return_value = "1.0.0"

                response = client.get("/api/v1/package-ops/test/test-package?version=1.0.0")

                assert response.status_code == 200
                result = response.json()
                assert result["has_tests"] is False
                assert result["tests"] == {}
