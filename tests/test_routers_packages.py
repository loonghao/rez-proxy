"""
Test packages router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestPackagesRouter:
    """Test packages router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez.packages.iter_packages")
    def test_search_packages_success(self, mock_iter_packages, client):
        """Test successful package search."""
        # Mock package
        mock_package = Mock()
        mock_package.name = "python"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="3.9.0")
        mock_package.description = "Python interpreter"
        mock_package.authors = ["Python Software Foundation"]
        mock_package.requires = []
        mock_package.tools = ["python", "pip"]
        mock_package.commands = None
        mock_package.uri = "/path/to/python/3.9.0"
        mock_package.variants = []

        mock_iter_packages.return_value = [mock_package]

        search_data = {"query": "python", "limit": 10, "offset": 0}

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert "total" in data
        assert len(data["packages"]) == 1
        assert data["packages"][0]["name"] == "python"
        assert data["packages"][0]["version"] == "3.9.0"

    @patch("rez.packages.iter_packages")
    def test_search_packages_empty_result(self, mock_iter_packages, client):
        """Test package search with empty result."""
        mock_iter_packages.return_value = []

        search_data = {"query": "nonexistent", "limit": 10, "offset": 0}

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert data["packages"] == []
        assert data["total"] == 0

    @patch("rez.packages.iter_packages")
    def test_search_packages_with_filters(self, mock_iter_packages, client):
        """Test package search with filters."""
        mock_package = Mock()
        mock_package.name = "python"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="3.9.0")
        mock_package.description = "Python interpreter"
        mock_package.authors = ["Python Software Foundation"]
        mock_package.requires = []
        mock_package.tools = ["python", "pip"]
        mock_package.commands = None
        mock_package.uri = "/path/to/python/3.9.0"
        mock_package.variants = []

        mock_iter_packages.return_value = [mock_package]

        search_data = {
            "query": "python",
            "limit": 5,
            "offset": 10,
            "filters": {"name_pattern": "py*", "version_range": ">=3.0"},
        }

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert "total" in data

    @patch("rez.packages.get_package")
    def test_get_package_info_success(self, mock_get_package, client):
        """Test successful package info retrieval."""
        # Mock package
        mock_package = Mock()
        mock_package.name = "python"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="3.9.0")
        mock_package.description = "Python interpreter"
        mock_package.authors = ["Python Software Foundation"]
        mock_package.requires = []
        mock_package.tools = ["python", "pip"]
        mock_package.commands = None
        mock_package.uri = "/path/to/python/3.9.0"
        mock_package.variants = []

        mock_get_package.return_value = mock_package

        response = client.get("/api/v1/packages/python/3.9.0")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "python"
        assert data["version"] == "3.9.0"
        assert data["description"] == "Python interpreter"

    @patch("rez.packages.get_package")
    def test_get_package_info_not_found(self, mock_get_package, client):
        """Test package info retrieval for non-existent package."""
        mock_get_package.return_value = None

        response = client.get("/api/v1/packages/nonexistent/1.0.0")
        assert response.status_code == 404

    @patch("rez.packages.iter_package_families")
    def test_list_package_families_success(self, mock_iter_families, client):
        """Test successful package families listing."""
        mock_families = ["python", "maya", "nuke", "houdini"]
        mock_iter_families.return_value = [Mock(name=name) for name in mock_families]

        response = client.get("/api/v1/packages/families")
        assert response.status_code == 200

        data = response.json()
        assert "families" in data
        assert len(data["families"]) == 4
        assert "python" in data["families"]

    @patch("rez.packages.iter_packages")
    def test_list_package_versions_success(self, mock_iter_packages, client):
        """Test successful package versions listing."""
        # Mock packages with different versions
        versions = ["3.7.0", "3.8.0", "3.9.0"]
        mock_packages = []

        for version in versions:
            mock_package = Mock()
            mock_package.name = "python"
            mock_package.version = Mock()
            mock_package.version.__str__ = Mock(return_value=version)
            mock_package.description = "Python interpreter"
            mock_package.authors = ["Python Software Foundation"]
            mock_package.requires = []
            mock_package.tools = ["python", "pip"]
            mock_package.commands = None
            mock_package.uri = f"/path/to/python/{version}"
            mock_package.variants = []
            mock_packages.append(mock_package)

        mock_iter_packages.return_value = mock_packages

        response = client.get("/api/v1/packages/python/versions")
        assert response.status_code == 200

        data = response.json()
        assert "versions" in data
        assert len(data["versions"]) == 3
        assert "3.9.0" in data["versions"]

    @patch("rez.packages.iter_packages")
    def test_get_package_dependencies_success(self, mock_iter_packages, client):
        """Test successful package dependencies retrieval."""
        # Mock package with dependencies
        mock_package = Mock()
        mock_package.name = "maya"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="2023.0")
        mock_package.requires = ["python-3.9", "qt-5.15"]
        mock_package.description = "Maya DCC"
        mock_package.authors = ["Autodesk"]
        mock_package.tools = ["maya"]
        mock_package.commands = None
        mock_package.uri = "/path/to/maya/2023.0"
        mock_package.variants = []

        mock_iter_packages.return_value = [mock_package]

        response = client.get("/api/v1/packages/maya/2023.0/dependencies")
        assert response.status_code == 200

        data = response.json()
        assert "dependencies" in data
        assert "python-3.9" in data["dependencies"]
        assert "qt-5.15" in data["dependencies"]

    def test_search_packages_invalid_request(self, client):
        """Test package search with invalid request data."""
        # Missing required fields
        search_data = {}

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 422  # Validation error

    def test_search_packages_invalid_limit(self, client):
        """Test package search with invalid limit."""
        search_data = {
            "query": "python",
            "limit": -1,  # Invalid limit
            "offset": 0,
        }

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 422  # Validation error

    @patch("rez.packages.iter_packages")
    def test_search_packages_exception_handling(self, mock_iter_packages, client):
        """Test package search exception handling."""
        mock_iter_packages.side_effect = Exception("Rez error")

        search_data = {"query": "python", "limit": 10, "offset": 0}

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 500

    @patch("rez.packages.get_package")
    def test_get_package_info_exception_handling(self, mock_get_package, client):
        """Test package info retrieval exception handling."""
        mock_get_package.side_effect = Exception("Rez error")

        response = client.get("/api/v1/packages/python/3.9.0")
        assert response.status_code == 500


class TestPackageConversion:
    """Test package conversion utilities."""

    def test_package_to_info_complete(self):
        """Test complete package to info conversion."""
        from rez_proxy.routers.packages import _package_to_info

        # Mock complete package
        mock_package = Mock()
        mock_package.name = "python"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="3.9.0")
        mock_package.description = "Python interpreter"
        mock_package.authors = ["Python Software Foundation"]
        mock_package.requires = ["zlib", "openssl"]
        mock_package.tools = ["python", "pip"]
        mock_package.commands = None
        mock_package.uri = "/path/to/python/3.9.0"
        mock_package.variants = []

        info = _package_to_info(mock_package)

        assert info.name == "python"
        assert info.version == "3.9.0"
        assert info.description == "Python interpreter"
        assert info.authors == ["Python Software Foundation"]
        assert info.requires == ["zlib", "openssl"]
        assert info.tools == ["python", "pip"]
        assert info.uri == "/path/to/python/3.9.0"

    def test_package_to_info_minimal(self):
        """Test minimal package to info conversion."""
        from rez_proxy.routers.packages import _package_to_info

        # Mock minimal package
        mock_package = Mock()
        mock_package.name = "test"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="1.0.0")
        mock_package.description = None
        mock_package.authors = None
        mock_package.requires = None
        mock_package.tools = None
        mock_package.commands = None
        mock_package.uri = "/path/to/test/1.0.0"
        mock_package.variants = None

        info = _package_to_info(mock_package)

        assert info.name == "test"
        assert info.version == "1.0.0"
        assert info.description is None
        assert info.authors == []
        assert info.requires == []
        assert info.tools == []
        assert info.uri == "/path/to/test/1.0.0"
