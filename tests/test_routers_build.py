"""
Test build router functionality.
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


class TestBuildRouter:
    """Test build router endpoints."""

    def test_get_build_systems(self, client):
        """Test getting available build systems."""
        with patch("rez_proxy.core.platform.BuildSystemService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_available_build_systems.return_value = {
                "build_systems": {
                    "cmake": {
                        "name": "cmake",
                        "description": "CMake build system",
                        "file_types": ["CMakeLists.txt"],
                    }
                }
            }
            mock_platform_info = MagicMock()
            mock_platform_info.platform = "linux"
            mock_service.get_platform_info.return_value = mock_platform_info

            with patch("rez_proxy.core.context.get_current_context", return_value=None):
                response = client.get("/api/v1/build/systems")

                assert response.status_code == 200
                data = response.json()
                assert "build_systems" in data
                assert "cmake" in data["build_systems"]

    def test_get_build_systems_error(self, client):
        """Test getting build systems with error."""
        with patch("rez_proxy.core.platform.BuildSystemService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_available_build_systems.side_effect = Exception(
                "Test error"
            )

            response = client.get("/api/v1/build/systems")

            assert response.status_code == 500

    def test_build_package_basic(self, client):
        """Test basic package building."""
        build_request = {
            "source_path": "/path/to/source",
            "build_args": ["-DCMAKE_BUILD_TYPE=Release"],
            "install": True,
            "clean": False,
        }

        with patch("os.path.exists", return_value=True):
            with patch(
                "rez.developer_package.get_developer_package"
            ) as mock_get_dev_pkg:
                with patch(
                    "rez.build_process.create_build_process"
                ) as mock_create_build:
                    # Mock developer package
                    mock_dev_pkg = MagicMock()
                    mock_dev_pkg.name = "test_package"
                    mock_dev_pkg.version = "1.0.0"
                    mock_get_dev_pkg.return_value = mock_dev_pkg

                    # Mock build process
                    mock_build_process = MagicMock()
                    mock_build_result = MagicMock()
                    mock_build_result.build_path = "/build/path"
                    mock_build_result.install_path = "/install/path"
                    mock_build_process.build.return_value = mock_build_result
                    mock_create_build.return_value = mock_build_process

                    response = client.post("/api/v1/build/build", json=build_request)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["package"] == "test_package"

    def test_build_package_validation_error(self, client):
        """Test package building with validation error."""
        build_request = {
            "source_path": "",  # Invalid empty path
            "install": True,
        }

        response = client.post("/api/v1/build/build", json=build_request)

        assert response.status_code == 422  # Validation error

    def test_build_package_source_not_found(self, client):
        """Test package building with non-existent source path."""
        build_request = {"source_path": "/nonexistent/path", "install": True}

        with patch("os.path.exists", return_value=False):
            response = client.post("/api/v1/build/build", json=build_request)

            assert response.status_code == 404

    def test_get_build_status(self, client):
        """Test getting build status."""
        source_path = "/path/to/source"

        with patch("os.path.exists", return_value=True):
            with patch(
                "rez.developer_package.get_developer_package"
            ) as mock_get_dev_pkg:
                with patch(
                    "rez.build_process.get_build_process_types"
                ) as mock_get_types:
                    # Mock developer package
                    mock_dev_pkg = MagicMock()
                    mock_dev_pkg.name = "test_package"
                    mock_dev_pkg.version = "1.0.0"
                    mock_dev_pkg.variants = []
                    mock_get_dev_pkg.return_value = mock_dev_pkg

                    # Mock build types
                    mock_build_class = MagicMock()
                    mock_build_class.file_types = ["CMakeLists.txt"]
                    mock_get_types.return_value = {"cmake": mock_build_class}

                    with patch(
                        "os.path.join", return_value="/path/to/source/CMakeLists.txt"
                    ):
                        response = client.get(f"/api/v1/build/status/{source_path}")

                        assert response.status_code == 200
                        data = response.json()
                        assert data["package"] == "test_package"
                        assert data["is_buildable"] is True

    def test_get_build_status_not_found(self, client):
        """Test getting build status for non-existent source."""
        source_path = "/nonexistent/path"

        with patch("os.path.exists", return_value=False):
            response = client.get(f"/api/v1/build/status/{source_path}")

            assert response.status_code == 404

    def test_get_package_variants(self, client):
        """Test getting package variants."""
        source_path = "/path/to/source"

        with patch("os.path.exists", return_value=True):
            with patch(
                "rez.developer_package.get_developer_package"
            ) as mock_get_dev_pkg:
                # Mock developer package with variants
                mock_dev_pkg = MagicMock()
                mock_dev_pkg.name = "test_package"
                mock_dev_pkg.version = "1.0.0"

                mock_variant = MagicMock()
                mock_variant.requires = ["python-3.9"]
                mock_variant.subpath = "python39"
                mock_dev_pkg.variants = [mock_variant]
                mock_get_dev_pkg.return_value = mock_dev_pkg

                response = client.get(f"/api/v1/build/variants/{source_path}")

                assert response.status_code == 200
                data = response.json()
                assert data["package"] == "test_package"
                assert data["total_variants"] == 1
                assert len(data["variants"]) == 1

    def test_get_build_dependencies(self, client):
        """Test getting build dependencies."""
        source_path = "/path/to/source"

        with patch("os.path.exists", return_value=True):
            with patch(
                "rez.developer_package.get_developer_package"
            ) as mock_get_dev_pkg:
                # Mock developer package with dependencies
                mock_dev_pkg = MagicMock()
                mock_dev_pkg.name = "test_package"
                mock_dev_pkg.version = "1.0.0"
                mock_dev_pkg.requires = ["python-3.9"]
                mock_dev_pkg.build_requires = ["cmake"]
                mock_dev_pkg.private_build_requires = ["gcc"]
                mock_get_dev_pkg.return_value = mock_dev_pkg

                response = client.get(f"/api/v1/build/dependencies/{source_path}")

                assert response.status_code == 200
                data = response.json()
                assert data["package"] == "test_package"
                assert "dependencies" in data
                assert data["dependencies"]["requires"] == ["python-3.9"]
                assert data["dependencies"]["build_requires"] == ["cmake"]

    def test_release_package(self, client):
        """Test releasing a package."""
        release_request = {
            "source_path": "/path/to/source",
            "release_message": "Release v1.0.0",
            "skip_repo_errors": False,
        }

        with patch("os.path.exists", return_value=True):
            with patch(
                "rez.developer_package.get_developer_package"
            ) as mock_get_dev_pkg:
                with patch("rez.release_vcs.create_release_from_path") as mock_release:
                    # Mock developer package
                    mock_dev_pkg = MagicMock()
                    mock_dev_pkg.name = "test_package"
                    mock_dev_pkg.version = "1.0.0"
                    mock_get_dev_pkg.return_value = mock_dev_pkg

                    # Mock release result
                    mock_release_result = MagicMock()
                    mock_pkg = MagicMock()
                    mock_pkg.uri = "/released/package/path"
                    mock_release_result.released_packages = [mock_pkg]
                    mock_release.return_value = mock_release_result

                    response = client.post(
                        "/api/v1/build/release", json=release_request
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["package"] == "test_package"
