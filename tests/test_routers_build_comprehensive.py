"""
Comprehensive tests for build router.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_dev_package():
    """Create a mock developer package."""
    package = MagicMock()
    package.name = "test-package"
    package.version = "1.0.0"
    package.requires = ["python-3.9"]
    package.build_requires = ["cmake"]
    package.private_build_requires = ["gcc"]
    package.variants = []
    return package


@pytest.fixture
def mock_build_result():
    """Create a mock build result."""
    result = MagicMock()
    result.build_path = "/tmp/build"
    result.install_path = "/tmp/install"
    return result


@pytest.fixture
def mock_release_result():
    """Create a mock release result."""
    result = MagicMock()
    mock_pkg = MagicMock()
    mock_pkg.uri = "/path/to/released/package"
    result.released_packages = [mock_pkg]
    return result


@pytest.fixture
def temp_source_path():
    """Create a temporary source path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestBuildPackage:
    """Test package building functionality."""

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_success(self, mock_rez_api, client, mock_dev_package, mock_build_result, temp_source_path):
        """Test successful package build."""
        # Setup mocks
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_build_process = MagicMock()
        mock_build_process.build.return_value = mock_build_result
        mock_rez_api.create_build_process.return_value = mock_build_process
        
        request_data = {
            "source_path": temp_source_path,
            "build_args": ["--verbose"],
            "install": True,
            "clean": True,
            "variants": [0, 1]
        }
        
        response = client.post("/api/v1/build/build", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["build_path"] == "/tmp/build"
        assert data["install_path"] == "/tmp/install"
        assert data["variants_built"] == [0, 1]

    def test_build_package_source_not_found(self, client):
        """Test build with non-existent source path."""
        request_data = {
            "source_path": "/non/existent/path"
        }

        response = client.post("/api/v1/build/build", json=request_data)
        
        assert response.status_code == 404
        assert "Source path not found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_rez_api_not_available(self, mock_rez_api, client, temp_source_path):
        """Test build when Rez API is not available."""
        mock_rez_api.get_developer_package.side_effect = AttributeError("Rez API not available")
        
        request_data = {
            "source_path": temp_source_path
        }
        
        response = client.post("/api/v1/build/build", json=request_data)

        assert response.status_code == 500
        assert "Rez API not available" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_get_developer_package_error(self, mock_rez_api, client, temp_source_path):
        """Test build when getting developer package fails."""
        mock_rez_api.get_developer_package.side_effect = Exception("Package error")

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/build", json=request_data)

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_no_package_found(self, mock_rez_api, client, temp_source_path):
        """Test build when no package is found."""
        mock_rez_api.get_developer_package.return_value = None

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/build", json=request_data)
        
        assert response.status_code == 400
        assert "No valid package found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_create_build_process_api_error(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build when create_build_process API is not available."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.create_build_process.side_effect = AttributeError("Build API not available")
        
        request_data = {
            "source_path": temp_source_path
        }
        
        response = client.post("/api/v1/build/build", json=request_data)

        assert response.status_code == 500
        assert "Rez build API not available" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_create_build_process_error(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build when creating build process fails."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.create_build_process.side_effect = Exception("Build process error")

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/build", json=request_data)

        assert response.status_code == 500
        assert "Failed to create build process" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_build_failed(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build when build process fails."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_build_process = MagicMock()
        mock_build_process.build.side_effect = Exception("Build failed")
        mock_rez_api.create_build_process.return_value = mock_build_process

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/build", json=request_data)
        
        assert response.status_code == 500
        assert "Build failed" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_minimal_request(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build with minimal request data."""
        # Setup mocks
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_build_process = MagicMock()
        mock_build_result = MagicMock()
        # Mock build result without build_path and install_path attributes
        del mock_build_result.build_path
        del mock_build_result.install_path
        mock_build_process.build.return_value = mock_build_result
        mock_rez_api.create_build_process.return_value = mock_build_process
        
        request_data = {
            "source_path": temp_source_path
        }
        
        response = client.post("/api/v1/build/build", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["build_path"] is None
        assert data["install_path"] is None
        assert data["variants_built"] == []

    @patch("rez_proxy.routers.build.rez_api")
    def test_build_package_general_exception(self, mock_rez_api, client, temp_source_path):
        """Test build with unexpected exception."""
        mock_rez_api.get_developer_package.side_effect = RuntimeError("Unexpected error")

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/build", json=request_data)
        
        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]


class TestReleasePackage:
    """Test package release functionality."""

    @patch("rez_proxy.routers.build.rez_api")
    def test_release_package_success(self, mock_rez_api, client, mock_dev_package, mock_release_result, temp_source_path):
        """Test successful package release."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.create_release_from_path.return_value = mock_release_result
        
        request_data = {
            "source_path": temp_source_path,
            "release_message": "Release v1.0.0",
            "skip_repo_errors": True,
            "variants": [0]
        }
        
        response = client.post("/api/v1/build/release", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["released_packages"] == ["/path/to/released/package"]
        assert data["message"] == "Release v1.0.0"

    def test_release_package_source_not_found(self, client):
        """Test release with non-existent source path."""
        request_data = {
            "source_path": "/non/existent/path"
        }

        response = client.post("/api/v1/build/release", json=request_data)
        
        assert response.status_code == 404
        assert "Source path not found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_release_package_no_package_found(self, mock_rez_api, client, temp_source_path):
        """Test release when no package is found."""
        mock_rez_api.get_developer_package.return_value = None
        
        request_data = {
            "source_path": temp_source_path
        }
        
        response = client.post("/api/v1/build/release", json=request_data)

        assert response.status_code == 400
        assert "No valid package found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_release_package_minimal_request(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test release with minimal request data."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_release_result = MagicMock()
        # Mock release result without released_packages attribute
        del mock_release_result.released_packages
        mock_rez_api.create_release_from_path.return_value = mock_release_result

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/release", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["released_packages"] == []
        assert data["message"] is None

    @patch("rez_proxy.routers.build.rez_api")
    def test_release_package_general_exception(self, mock_rez_api, client, temp_source_path):
        """Test release with unexpected exception."""
        mock_rez_api.get_developer_package.side_effect = RuntimeError("Unexpected error")

        request_data = {
            "source_path": temp_source_path
        }

        response = client.post("/api/v1/build/release", json=request_data)

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]


class TestGetBuildSystems:
    """Test build systems retrieval functionality."""

    @patch("rez_proxy.core.platform.BuildSystemService")
    @patch("rez_proxy.core.context.get_current_context")
    def test_get_build_systems_success(self, mock_get_context, mock_service_class, client):
        """Test successful build systems retrieval."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_available_build_systems.return_value = {
            "cmake": {"version": "3.20.0"},
            "make": {"version": "4.3"}
        }
        mock_platform_info = MagicMock()
        mock_platform_info.platform = "linux"
        mock_service.get_platform_info.return_value = mock_platform_info
        mock_service_class.return_value = mock_service

        mock_context = MagicMock()
        mock_context.service_mode.value = "remote"
        mock_get_context.return_value = mock_context

        response = client.get("/api/v1/build/systems")

        assert response.status_code == 200
        data = response.json()
        assert "cmake" in data
        assert "make" in data
        assert data["service_mode"] == "remote"
        assert data["platform"] == "linux"

    @patch("rez_proxy.core.platform.BuildSystemService")
    @patch("rez_proxy.core.context.get_current_context")
    def test_get_build_systems_no_context(self, mock_get_context, mock_service_class, client):
        """Test build systems retrieval with no context."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_available_build_systems.return_value = {"cmake": {"version": "3.20.0"}}
        mock_platform_info = MagicMock()
        mock_platform_info.platform = "windows"
        mock_service.get_platform_info.return_value = mock_platform_info
        mock_service_class.return_value = mock_service

        mock_get_context.return_value = None

        response = client.get("/api/v1/build/systems")

        assert response.status_code == 200
        data = response.json()
        assert data["service_mode"] == "local"
        assert data["platform"] == "windows"

    @patch("rez_proxy.core.platform.BuildSystemService")
    def test_get_build_systems_exception(self, mock_service_class, client):
        """Test build systems retrieval with exception."""
        mock_service_class.side_effect = Exception("Service error")

        response = client.get("/api/v1/build/systems")

        assert response.status_code == 500
        assert "Failed to get build systems" in response.json()["detail"]


class TestGetBuildStatus:
    """Test build status retrieval functionality."""

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_success(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test successful build status retrieval."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package

        # Mock build process types
        mock_build_class = MagicMock()
        mock_build_class.file_types = ["CMakeLists.txt", "Makefile"]
        mock_rez_api.get_build_process_types.return_value = {"cmake": mock_build_class}

        # Create a CMakeLists.txt file in temp directory
        cmake_file = os.path.join(temp_source_path, "CMakeLists.txt")
        with open(cmake_file, "w") as f:
            f.write("cmake_minimum_required(VERSION 3.0)")

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["source_path"] == temp_source_path
        assert data["is_buildable"] is True
        assert "cmake" in data["build_systems"]
        assert data["variants"] == 0

    def test_get_build_status_source_not_found(self, client):
        """Test build status with non-existent source path."""
        response = client.get("/api/v1/build/status/non/existent/path")

        assert response.status_code == 404
        assert "Source path not found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_rez_api_not_available(self, mock_rez_api, client, temp_source_path):
        """Test build status when Rez API is not available."""
        mock_rez_api.get_developer_package.side_effect = AttributeError("Rez API not available")

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 500
        assert "Rez API not available" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_get_developer_package_error(self, mock_rez_api, client, temp_source_path):
        """Test build status when getting developer package fails."""
        mock_rez_api.get_developer_package.side_effect = Exception("Package error")

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_no_package_found(self, mock_rez_api, client, temp_source_path):
        """Test build status when no package is found."""
        mock_rez_api.get_developer_package.return_value = None

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 400
        assert "No valid package found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_no_build_files(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build status when no build files are found."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.get_build_process_types.return_value = {}

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_buildable"] is False
        assert data["build_systems"] == {}

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_build_types_attribute_error(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build status when build process types are not available."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.get_build_process_types.side_effect = AttributeError("Build types not available")

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_buildable"] is False
        assert data["build_systems"] == {}

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_build_types_general_error(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test build status when build process types have general error."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.get_build_process_types.side_effect = Exception("General error")

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_buildable"] is False
        assert data["build_systems"] == {}

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_with_variants(self, mock_rez_api, client, temp_source_path):
        """Test build status with package variants."""
        mock_dev_package = MagicMock()
        mock_dev_package.name = "test-package"
        mock_dev_package.version = "1.0.0"
        mock_dev_package.variants = [MagicMock(), MagicMock()]  # 2 variants
        mock_rez_api.get_developer_package.return_value = mock_dev_package
        mock_rez_api.get_build_process_types.return_value = {}

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["variants"] == 2

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_status_general_exception(self, mock_rez_api, client, temp_source_path):
        """Test build status with unexpected exception."""
        mock_rez_api.get_developer_package.side_effect = RuntimeError("Unexpected error")

        response = client.get(f"/api/v1/build/status/{temp_source_path}")

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]


class TestGetPackageVariants:
    """Test package variants retrieval functionality."""

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_package_variants_success(self, mock_rez_api, client, temp_source_path):
        """Test successful package variants retrieval."""
        # Create mock package with variants
        mock_dev_package = MagicMock()
        mock_dev_package.name = "test-package"
        mock_dev_package.version = "1.0.0"

        # Create mock variants
        mock_variant1 = MagicMock()
        mock_variant1.requires = ["python-3.9", "numpy"]
        mock_variant1.subpath = "python39"

        mock_variant2 = MagicMock()
        mock_variant2.requires = ["python-3.10"]
        mock_variant2.subpath = "python310"

        mock_dev_package.variants = [mock_variant1, mock_variant2]
        mock_rez_api.get_developer_package.return_value = mock_dev_package

        response = client.get(f"/api/v1/build/variants/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["total_variants"] == 2
        assert len(data["variants"]) == 2

        # Check first variant
        variant1 = data["variants"][0]
        assert variant1["index"] == 0
        assert variant1["requires"] == ["python-3.9", "numpy"]
        assert variant1["subpath"] == "python39"

        # Check second variant
        variant2 = data["variants"][1]
        assert variant2["index"] == 1
        assert variant2["requires"] == ["python-3.10"]
        assert variant2["subpath"] == "python310"

    def test_get_package_variants_source_not_found(self, client):
        """Test package variants with non-existent source path."""
        response = client.get("/api/v1/build/variants/non/existent/path")

        assert response.status_code == 404
        assert "Source path not found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_package_variants_no_package_found(self, mock_rez_api, client, temp_source_path):
        """Test package variants when no package is found."""
        mock_rez_api.get_developer_package.return_value = None

        response = client.get(f"/api/v1/build/variants/{temp_source_path}")

        assert response.status_code == 400
        assert "No valid package found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_package_variants_no_variants(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test package variants when package has no variants."""
        mock_dev_package.variants = None
        mock_rez_api.get_developer_package.return_value = mock_dev_package

        response = client.get(f"/api/v1/build/variants/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["variants"] == []
        assert data["total_variants"] == 0

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_package_variants_empty_variants(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test package variants when package has empty variants list."""
        mock_dev_package.variants = []
        mock_rez_api.get_developer_package.return_value = mock_dev_package

        response = client.get(f"/api/v1/build/variants/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["variants"] == []
        assert data["total_variants"] == 0

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_package_variants_missing_attributes(self, mock_rez_api, client, temp_source_path):
        """Test package variants when variant attributes are missing."""
        mock_dev_package = MagicMock()
        mock_dev_package.name = "test-package"
        mock_dev_package.version = "1.0.0"

        # Create mock variant without requires and subpath attributes
        mock_variant = MagicMock()
        del mock_variant.requires
        del mock_variant.subpath

        mock_dev_package.variants = [mock_variant]
        mock_rez_api.get_developer_package.return_value = mock_dev_package

        response = client.get(f"/api/v1/build/variants/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_variants"] == 1
        variant = data["variants"][0]
        assert variant["index"] == 0
        assert variant["requires"] == []
        assert variant["subpath"] is None

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_package_variants_general_exception(self, mock_rez_api, client, temp_source_path):
        """Test package variants with unexpected exception."""
        mock_rez_api.get_developer_package.side_effect = RuntimeError("Unexpected error")

        response = client.get(f"/api/v1/build/variants/{temp_source_path}")

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]


class TestGetBuildDependencies:
    """Test build dependencies retrieval functionality."""

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_dependencies_success(self, mock_rez_api, client, mock_dev_package, temp_source_path):
        """Test successful build dependencies retrieval."""
        mock_rez_api.get_developer_package.return_value = mock_dev_package

        response = client.get(f"/api/v1/build/dependencies/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["package"] == "test-package"
        assert data["version"] == "1.0.0"
        assert data["dependencies"]["requires"] == ["python-3.9"]
        assert data["dependencies"]["build_requires"] == ["cmake"]
        assert data["dependencies"]["private_build_requires"] == ["gcc"]

    def test_get_build_dependencies_source_not_found(self, client):
        """Test build dependencies with non-existent source path."""
        response = client.get("/api/v1/build/dependencies/non/existent/path")

        assert response.status_code == 404
        assert "Source path not found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_dependencies_rez_api_not_available(self, mock_rez_api, client, temp_source_path):
        """Test build dependencies when Rez API is not available."""
        mock_rez_api.get_developer_package.side_effect = AttributeError("Rez API not available")

        response = client.get(f"/api/v1/build/dependencies/{temp_source_path}")

        assert response.status_code == 500
        assert "Rez API not available" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_dependencies_get_developer_package_error(self, mock_rez_api, client, temp_source_path):
        """Test build dependencies when getting developer package fails."""
        mock_rez_api.get_developer_package.side_effect = Exception("Package error")

        response = client.get(f"/api/v1/build/dependencies/{temp_source_path}")

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_dependencies_no_package_found(self, mock_rez_api, client, temp_source_path):
        """Test build dependencies when no package is found."""
        mock_rez_api.get_developer_package.return_value = None

        response = client.get(f"/api/v1/build/dependencies/{temp_source_path}")

        assert response.status_code == 400
        assert "No valid package found" in response.json()["detail"]

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_dependencies_missing_attributes(self, mock_rez_api, client, temp_source_path):
        """Test build dependencies when package attributes are missing."""
        mock_dev_package = MagicMock()
        mock_dev_package.name = "test-package"
        mock_dev_package.version = "1.0.0"
        # Remove dependency attributes
        del mock_dev_package.requires
        del mock_dev_package.build_requires
        del mock_dev_package.private_build_requires

        mock_rez_api.get_developer_package.return_value = mock_dev_package

        response = client.get(f"/api/v1/build/dependencies/{temp_source_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["requires"] == []
        assert data["dependencies"]["build_requires"] == []
        assert data["dependencies"]["private_build_requires"] == []

    @patch("rez_proxy.routers.build.rez_api")
    def test_get_build_dependencies_general_exception(self, mock_rez_api, client, temp_source_path):
        """Test build dependencies with unexpected exception."""
        mock_rez_api.get_developer_package.side_effect = RuntimeError("Unexpected error")

        response = client.get(f"/api/v1/build/dependencies/{temp_source_path}")

        assert response.status_code == 500
        assert "Failed to get developer package" in response.json()["detail"]
