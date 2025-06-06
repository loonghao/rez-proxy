"""
Test packages router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


def create_mock_package(
    name="python",
    version="3.9.0",
    description="Python interpreter",
    authors=None,
    requires=None,
    tools=None,
    variants=None,
):
    """Create a properly configured mock package."""
    # Create Mock objects for lists to avoid iteration issues
    requires_list = requires or []
    tools_list = tools if tools is not None else ["python", "pip"]
    variants_list = variants or []

    # Use a custom Mock that doesn't have parent attribute
    class PackageMock(Mock):
        def __getattr__(self, name):
            if name == "parent":
                raise AttributeError(
                    f"'{type(self).__name__}' object has no attribute 'parent'"
                )
            return super().__getattr__(name)

    # Create the main package mock
    package_mock = PackageMock()
    package_mock.name = name
    package_mock.version = Mock()
    package_mock.version.__str__ = Mock(return_value=version)
    package_mock.description = description
    # Fix authors handling - only set default if authors is None and not explicitly passed as empty list
    if authors is None:
        package_mock.authors = ["Python Software Foundation"]
    else:
        package_mock.authors = authors
    package_mock.commands = None
    package_mock.uri = f"/path/to/{name}/{version}"

    # Create simple list-like objects instead of complex Mock objects
    package_mock.requires = requires_list
    package_mock.tools = tools_list
    package_mock.variants = variants_list

    return package_mock


class TestPackagesRouter:
    """Test packages router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    def test_list_packages_success(
        self, mock_iter_packages, mock_iter_families, client
    ):
        """Test successful package listing."""
        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"
        mock_iter_families.return_value = [mock_family]

        # Mock package
        mock_package = create_mock_package()

        mock_iter_packages.return_value = [mock_package]

        response = client.get("/api/v1/packages/")
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert "total" in data
        assert "context" in data
        assert len(data["packages"]) == 1
        assert data["packages"][0]["name"] == "python"
        assert data["packages"][0]["version"] == "3.9.0"

    @patch("rez.packages.iter_package_families")
    def test_list_packages_empty_result(self, mock_iter_families, client):
        """Test package listing with empty result."""
        mock_iter_families.return_value = []

        response = client.get("/api/v1/packages/")
        assert response.status_code == 200

        data = response.json()
        assert data["packages"] == []
        assert data["total"] == 0
        assert "context" in data

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    def test_list_packages_with_filters(
        self, mock_iter_packages, mock_iter_families, client
    ):
        """Test package listing with filters."""
        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"
        mock_iter_families.return_value = [mock_family]

        mock_package = create_mock_package()

        mock_iter_packages.return_value = [mock_package]

        response = client.get("/api/v1/packages/?name=python&limit=5&offset=10")
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert "total" in data
        assert "context" in data

    @patch("rez.packages.get_package")
    def test_get_package_info_with_version_success(self, mock_get_package, client):
        """Test successful package info retrieval with specific version."""
        # Mock package
        mock_package = create_mock_package()

        mock_get_package.return_value = mock_package

        response = client.get("/api/v1/packages/python?version=3.9.0")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "python"
        assert data["version"] == "3.9.0"
        assert data["description"] == "Python interpreter"
        assert "context" in data

    @patch("rez.packages.iter_packages")
    def test_get_package_info_latest_version_success(self, mock_iter_packages, client):
        """Test successful package info retrieval for latest version."""
        # Use create_mock_package to avoid Mock parent attribute issues
        mock_package = create_mock_package()

        mock_iter_packages.return_value = [mock_package]

        response = client.get("/api/v1/packages/python")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "python"
        assert data["version"] == "3.9.0"
        assert "context" in data

    @patch("rez.packages.get_package")
    def test_get_package_info_not_found(self, mock_get_package, client):
        """Test package info retrieval for non-existent package."""
        mock_get_package.return_value = None

        response = client.get("/api/v1/packages/nonexistent?version=1.0.0")
        assert response.status_code == 404

    @patch("rez.packages.iter_packages")
    def test_get_package_versions_success(self, mock_iter_packages, client):
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
            mock_package.uri = f"/path/to/python/{version}"
            mock_package.timestamp = None
            mock_packages.append(mock_package)

        mock_iter_packages.return_value = mock_packages

        response = client.get("/api/v1/packages/python/versions")
        assert response.status_code == 200

        data = response.json()
        assert "versions" in data
        assert "context" in data
        assert len(data["versions"]) == 3
        assert data["package"] == "python"

    @patch("rez.packages.iter_packages")
    def test_get_package_variants_success(self, mock_iter_packages, client):
        """Test successful package variants listing."""
        # Mock package with variants
        mock_variant1 = Mock()
        mock_variant1.index = 0
        mock_variant1.requires = []

        mock_variant2 = Mock()
        mock_variant2.index = 1
        mock_variant2.requires = ["python-3.9"]

        # Use create_mock_package to avoid Mock parent attribute issues
        mock_package = create_mock_package(variants=[mock_variant1, mock_variant2])

        mock_iter_packages.return_value = [mock_package]

        response = client.get("/api/v1/packages/python/variants?platform_filter=false")
        assert response.status_code == 200

        data = response.json()
        assert "variants" in data
        assert "context" in data
        assert len(data["variants"]) == 2
        assert data["package"] == "python"

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    def test_search_packages_success(
        self, mock_iter_packages, mock_iter_families, client
    ):
        """Test successful package search."""
        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"
        mock_iter_families.return_value = [mock_family]

        # Use create_mock_package to avoid Mock parent attribute issues
        mock_package = create_mock_package()

        mock_iter_packages.return_value = [mock_package]

        search_data = {"query": "python", "limit": 10, "offset": 0}

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert "total" in data
        assert len(data["packages"]) == 1
        assert data["packages"][0]["name"] == "python"

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

    @patch("rez.packages.iter_package_families")
    def test_list_packages_exception_handling(self, mock_iter_families, client):
        """Test package listing exception handling."""
        mock_iter_families.side_effect = Exception("Rez error")

        response = client.get("/api/v1/packages/")
        assert response.status_code == 500

    @patch("rez.packages.iter_package_families")
    def test_search_packages_exception_handling(self, mock_iter_families, client):
        """Test package search exception handling."""
        mock_iter_families.side_effect = Exception("Rez error")

        search_data = {"query": "python", "limit": 10, "offset": 0}

        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 500

    @patch("rez.packages.get_package")
    def test_get_package_info_exception_handling(self, mock_get_package, client):
        """Test package info retrieval exception handling."""
        mock_get_package.side_effect = Exception("Rez error")

        response = client.get("/api/v1/packages/python?version=3.9.0")
        assert response.status_code == 500

    @patch("rez.packages.iter_packages")
    def test_get_package_info_not_found_latest(self, mock_iter_packages, client):
        """Test package info retrieval for non-existent package (latest version)."""
        mock_iter_packages.return_value = []

        response = client.get("/api/v1/packages/nonexistent")
        assert response.status_code == 404

    @patch("rez_proxy.routers.packages.is_local_mode")
    def test_list_packages_remote_mode(self, mock_is_local_mode, client):
        """Test package listing in remote mode."""
        mock_is_local_mode.return_value = False

        response = client.get("/api/v1/packages/")
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert len(data["packages"]) == 1  # Remote mode returns placeholder
        assert data["packages"][0]["name"] == "example-package"
        assert "context" in data

    @patch("rez_proxy.routers.packages.is_local_mode")
    def test_get_package_info_remote_mode(self, mock_is_local_mode, client):
        """Test package info retrieval in remote mode."""
        mock_is_local_mode.return_value = False

        response = client.get("/api/v1/packages/python")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "python"
        assert "note" in data
        assert "context" in data


class TestPackageConversion:
    """Test package conversion utilities."""

    def test_package_to_info_complete(self):
        """Test complete package to info conversion."""
        from rez_proxy.routers.packages import _package_to_info

        # Mock complete package
        mock_package = create_mock_package(requires=["zlib", "openssl"])

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

        # Mock minimal package - fix Mock object iteration issue
        mock_package = create_mock_package(
            name="test",
            version="1.0.0",
            description=None,
            authors=[],
            requires=[],
            tools=[],
        )

        info = _package_to_info(mock_package)

        assert info.name == "test"
        assert info.version == "1.0.0"
        assert info.description is None
        assert info.authors == []
        assert info.requires == []
        assert info.tools == []
        assert info.uri == "/path/to/test/1.0.0"


class TestPackageService:
    """Test PackageService class methods."""

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    @patch("rez_proxy.core.context.is_local_mode")
    def test_list_packages_local_mode(
        self, mock_is_local_mode, mock_iter_packages, mock_iter_families
    ):
        """Test PackageService.list_packages in local mode."""
        from rez_proxy.routers.packages import PackageService

        mock_is_local_mode.return_value = True

        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"
        mock_iter_families.return_value = [mock_family]

        # Use create_mock_package to avoid Mock parent attribute issues
        mock_package = create_mock_package()

        mock_iter_packages.return_value = [mock_package]

        service = PackageService()
        result = service.list_packages()

        assert "packages" in result
        assert "total" in result
        assert len(result["packages"]) == 1
        assert result["packages"][0]["name"] == "python"

    @patch("rez_proxy.routers.packages.is_local_mode")
    def test_list_packages_remote_mode(self, mock_is_local_mode):
        """Test PackageService.list_packages in remote mode."""
        from rez_proxy.routers.packages import PackageService

        mock_is_local_mode.return_value = False

        service = PackageService()
        result = service.list_packages()

        assert "packages" in result
        assert "total" in result
        assert len(result["packages"]) == 1
        assert result["packages"][0]["name"] == "example-package"

    def test_package_to_dict_basic(self):
        """Test PackageService._package_to_dict method."""
        from rez_proxy.routers.packages import PackageService

        # Use create_mock_package to avoid Mock parent attribute issues
        mock_package = create_mock_package()

        service = PackageService()
        result = service._package_to_dict(mock_package)

        assert result["name"] == "python"
        assert result["version"] == "3.9.0"
        assert result["description"] == "Python interpreter"
        assert result["authors"] == ["Python Software Foundation"]
        assert result["requires"] == []
        assert result["tools"] == ["python", "pip"]

    def test_is_variant_compatible(self):
        """Test PackageService._is_variant_compatible method."""
        from rez_proxy.routers.packages import PackageService

        service = PackageService()

        # Mock variant with platform-specific index
        mock_variant = Mock()
        mock_variant.index = "linux-x86_64"

        # Test compatible platform
        assert service._is_variant_compatible(mock_variant, "linux")

        # Test incompatible platform
        assert not service._is_variant_compatible(mock_variant, "windows")

        # Test variant without index
        mock_variant_no_index = Mock()
        del mock_variant_no_index.index  # Remove index attribute
        assert service._is_variant_compatible(mock_variant_no_index, "linux")

    def test_package_to_dict_with_variants(self):
        """Test PackageService._package_to_dict with variants."""
        from rez_proxy.routers.packages import PackageService

        # Mock variants
        mock_variant1 = Mock()
        mock_variant1.index = 0
        mock_variant1.requires = []

        mock_variant2 = Mock()
        mock_variant2.index = 1
        mock_variant2.requires = ["python-3.9"]

        # Use create_mock_package to avoid Mock parent attribute issues
        mock_package = create_mock_package(variants=[mock_variant1, mock_variant2])

        service = PackageService()
        result = service._package_to_dict(mock_package)

        assert result["name"] == "python"
        assert "variants" in result
        assert len(result["variants"]) == 2

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    @patch("rez.version.Version")
    def test_list_packages_with_version_filter(
        self, mock_version, mock_iter_packages, mock_iter_families
    ):
        """Test PackageService.list_packages with version filter."""
        from rez_proxy.routers.packages import PackageService

        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"
        mock_iter_families.return_value = [mock_family]

        # Mock package with version
        mock_package = create_mock_package(version="3.9.0")
        mock_iter_packages.return_value = [mock_package]

        # Mock version comparison
        mock_version_obj = Mock()
        mock_version_obj.in_range.return_value = True
        mock_version.return_value = mock_version_obj

        service = PackageService()
        result = service.list_packages(version_filter=">=3.8")

        assert "packages" in result
        assert len(result["packages"]) == 1

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    def test_list_packages_with_invalid_version_filter(
        self, mock_iter_packages, mock_iter_families
    ):
        """Test PackageService.list_packages with invalid version filter."""
        from rez_proxy.routers.packages import PackageService

        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"
        mock_iter_families.return_value = [mock_family]

        # Mock package with invalid version
        mock_package = Mock()
        mock_package.name = "python"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="invalid-version")
        mock_iter_packages.return_value = [mock_package]

        service = PackageService()
        result = service.list_packages(version_filter=">=3.8")

        # Should skip packages with invalid versions
        assert "packages" in result
        assert len(result["packages"]) == 0

    @patch("rez.packages.iter_package_families")
    @patch("rez.packages.iter_packages")
    def test_list_packages_with_offset_and_limit(
        self, mock_iter_packages, mock_iter_families
    ):
        """Test PackageService.list_packages with offset and limit."""
        from rez_proxy.routers.packages import PackageService

        # Mock multiple package families
        families = []
        for i in range(5):
            family = Mock()
            family.name = f"package{i}"
            families.append(family)
        mock_iter_families.return_value = families

        # Mock packages
        packages = []
        for i in range(5):
            package = create_mock_package(name=f"package{i}", version="1.0.0")
            packages.append(package)

        mock_iter_packages.side_effect = lambda name: [
            pkg for pkg in packages if pkg.name == name
        ]

        service = PackageService()
        result = service.list_packages(limit=2, offset=1)

        assert "packages" in result
        assert len(result["packages"]) == 2
        assert result["limit"] == 2
        assert result["offset"] == 1

    def test_package_to_dict_with_variant_object(self):
        """Test PackageService._package_to_dict with variant object."""
        from rez_proxy.routers.packages import PackageService

        # Mock variant object (has parent attribute)
        mock_parent = create_mock_package()
        mock_variant = Mock()
        mock_variant.parent = mock_parent
        mock_variant.index = 0
        mock_variant.subpath = "variants/0"

        service = PackageService()
        result = service._package_to_dict(mock_variant)

        assert result["name"] == "python"
        assert "variants" in result
        assert result["variants"][0]["index"] == 0
        assert result["variants"][0]["subpath"] == "variants/0"

    def test_package_to_dict_with_requires_error(self):
        """Test PackageService._package_to_dict with requires processing error."""
        from rez_proxy.routers.packages import PackageService

        # Mock package with problematic requires
        mock_package = create_mock_package()
        mock_package.requires = Mock(side_effect=TypeError("Cannot iterate"))

        service = PackageService()
        result = service._package_to_dict(mock_package)

        assert result["name"] == "python"
        assert result["requires"] == []  # Should fallback to empty list

    def test_package_to_dict_with_tools_error(self):
        """Test PackageService._package_to_dict with tools processing error."""
        from rez_proxy.routers.packages import PackageService

        # Mock package with problematic tools
        mock_package = create_mock_package()
        mock_package.tools = Mock(side_effect=TypeError("Cannot iterate"))

        service = PackageService()
        result = service._package_to_dict(mock_package)

        assert result["name"] == "python"
        assert result["tools"] == []  # Should fallback to empty list
