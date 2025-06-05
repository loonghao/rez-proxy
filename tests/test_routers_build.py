"""
Test build router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestBuildRouter:
    """Test build router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez.build_system.get_build_system_types")
    def test_list_build_systems(self, mock_get_types, client):
        """Test listing available build systems."""
        mock_get_types.return_value = ["cmake", "python", "make"]

        response = client.get("/api/v1/build/systems")
        assert response.status_code == 200

        data = response.json()
        assert "build_systems" in data
        assert "cmake" in data["build_systems"]
        assert "python" in data["build_systems"]

    @patch("rez.build_system.get_build_system_class")
    def test_get_build_system_info(self, mock_get_class, client):
        """Test getting build system information."""
        mock_class = Mock()
        mock_class.__doc__ = "CMake build system"
        mock_class.file_types = ["CMakeLists.txt"]

        mock_get_class.return_value = mock_class

        response = client.get("/api/v1/build/systems/cmake")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "cmake"
        assert data["description"] == "CMake build system"
        assert "CMakeLists.txt" in data["file_types"]

    @patch("rez.build_system.get_build_system_class")
    def test_get_build_system_info_not_found(self, mock_get_class, client):
        """Test getting build system info for non-existent system."""
        mock_get_class.side_effect = Exception("Build system not found")

        response = client.get("/api/v1/build/systems/nonexistent")
        assert response.status_code == 404

    @patch("rez.developer_package.get_developer_package")
    @patch("rez.build_process.create_build_process")
    def test_build_package_success(self, mock_create_process, mock_get_package, client):
        """Test successful package build."""
        # Mock developer package
        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.version = "1.0.0"
        mock_get_package.return_value = mock_package

        # Mock build process
        mock_process = Mock()
        mock_process.build.return_value = 0  # Success
        mock_create_process.return_value = mock_process

        build_data = {"package_path": "/path/to/package", "build_args": ["--verbose"]}

        response = client.post("/api/v1/build/package", json=build_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["package_name"] == "test-package"

    @patch("rez.developer_package.get_developer_package")
    def test_build_package_not_found(self, mock_get_package, client):
        """Test building non-existent package."""
        mock_get_package.return_value = None

        build_data = {"package_path": "/path/to/nonexistent"}

        response = client.post("/api/v1/build/package", json=build_data)
        assert response.status_code == 404

    @patch("rez.developer_package.get_developer_package")
    @patch("rez.build_process.create_build_process")
    def test_build_package_failure(self, mock_create_process, mock_get_package, client):
        """Test package build failure."""
        # Mock developer package
        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.version = "1.0.0"
        mock_get_package.return_value = mock_package

        # Mock build process with failure
        mock_process = Mock()
        mock_process.build.return_value = 1  # Failure
        mock_create_process.return_value = mock_process

        build_data = {"package_path": "/path/to/package"}

        response = client.post("/api/v1/build/package", json=build_data)
        assert response.status_code == 400

        data = response.json()
        assert "failed" in data["detail"].lower()

    def test_build_package_invalid_request(self, client):
        """Test build package with invalid request."""
        # Missing required fields
        build_data = {}

        response = client.post("/api/v1/build/package", json=build_data)
        assert response.status_code == 422

    @patch("rez.developer_package.get_developer_package")
    def test_validate_package_success(self, mock_get_package, client):
        """Test successful package validation."""
        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.version = "1.0.0"
        mock_package.validate.return_value = True
        mock_get_package.return_value = mock_package

        response = client.post(
            "/api/v1/build/validate", json={"package_path": "/path/to/package"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is True
        assert data["package_name"] == "test-package"

    @patch("rez.developer_package.get_developer_package")
    def test_validate_package_invalid(self, mock_get_package, client):
        """Test package validation failure."""
        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.version = "1.0.0"
        mock_package.validate.side_effect = Exception("Validation error")
        mock_get_package.return_value = mock_package

        response = client.post(
            "/api/v1/build/validate", json={"package_path": "/path/to/package"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is False
        assert "errors" in data

    @patch("rez.developer_package.get_developer_package")
    def test_get_build_requirements(self, mock_get_package, client):
        """Test getting build requirements."""
        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.build_requires = ["cmake", "gcc"]
        mock_get_package.return_value = mock_package

        response = client.get(
            "/api/v1/build/requirements?package_path=/path/to/package"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["package_name"] == "test-package"
        assert "cmake" in data["build_requires"]
        assert "gcc" in data["build_requires"]

    @patch("rez.developer_package.get_developer_package")
    def test_get_build_requirements_not_found(self, mock_get_package, client):
        """Test getting build requirements for non-existent package."""
        mock_get_package.return_value = None

        response = client.get(
            "/api/v1/build/requirements?package_path=/path/to/nonexistent"
        )
        assert response.status_code == 404


class TestBuildUtilities:
    """Test build utility functions."""

    def test_build_system_to_info(self):
        """Test build system to info conversion."""
        from rez_proxy.routers.build import _build_system_to_info

        mock_class = Mock()
        mock_class.__doc__ = "CMake build system"
        mock_class.file_types = ["CMakeLists.txt", "cmake"]

        info = _build_system_to_info("cmake", mock_class)

        assert info["name"] == "cmake"
        assert info["description"] == "CMake build system"
        assert info["file_types"] == ["CMakeLists.txt", "cmake"]

    def test_build_system_to_info_minimal(self):
        """Test build system to info conversion with minimal data."""
        from rez_proxy.routers.build import _build_system_to_info

        mock_class = Mock()
        mock_class.__doc__ = None
        mock_class.file_types = []

        info = _build_system_to_info("test", mock_class)

        assert info["name"] == "test"
        assert info["description"] is None
        assert info["file_types"] == []

    def test_format_build_result(self):
        """Test build result formatting."""
        from rez_proxy.routers.build import _format_build_result

        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.version = "1.0.0"

        result = _format_build_result(mock_package, 0, "Build completed successfully")

        assert result["status"] == "success"
        assert result["package_name"] == "test-package"
        assert result["package_version"] == "1.0.0"
        assert result["message"] == "Build completed successfully"

    def test_format_build_result_failure(self):
        """Test build result formatting for failure."""
        from rez_proxy.routers.build import _format_build_result

        mock_package = Mock()
        mock_package.name = "test-package"
        mock_package.version = "1.0.0"

        result = _format_build_result(mock_package, 1, "Build failed with errors")

        assert result["status"] == "failed"
        assert result["package_name"] == "test-package"
        assert result["package_version"] == "1.0.0"
        assert result["message"] == "Build failed with errors"
