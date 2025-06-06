"""
Test repositories router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestRepositoriesRouter:
    """Test repositories router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez.package_repository.package_repository_manager")
    def test_list_repositories(self, mock_manager, client):
        """Test listing package repositories."""
        # Mock repositories
        mock_repo1 = Mock()
        mock_repo1.name = "local"
        mock_repo1.location = "/path/to/local"
        mock_repo1.__class__.__name__ = "FileSystemPackageRepository"
        mock_repo1.uid = None  # Ensure uid is serializable

        mock_repo2 = Mock()
        mock_repo2.name = "shared"
        mock_repo2.location = "/path/to/shared"
        mock_repo2.__class__.__name__ = "FileSystemPackageRepository"
        mock_repo2.uid = None  # Ensure uid is serializable

        mock_manager.repositories = [mock_repo1, mock_repo2]

        response = client.get("/api/v1/repositories")
        assert response.status_code == 200

        data = response.json()
        assert "repositories" in data
        assert len(data["repositories"]) == 2
        assert data["repositories"][0]["name"] == "local"
        assert data["repositories"][1]["name"] == "shared"

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_info(self, mock_manager, client):
        """Test getting repository information."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.__class__.__name__ = "FileSystemPackageRepository"
        mock_repo.uid = None  # Ensure uid is serializable
        mock_repo.iter_package_families.return_value = []  # Add missing method

        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/local")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "local"
        assert data["location"] == "/path/to/local"
        assert data["type"] == "FileSystemPackageRepository"

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_info_not_found(self, mock_manager, client):
        """Test getting repository info for non-existent repository."""
        mock_manager.get_repository.return_value = None

        response = client.get("/api/v1/repositories/nonexistent")
        assert response.status_code == 404

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_packages(self, mock_manager, client):
        """Test getting packages from repository."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.uid = None  # Ensure uid is serializable

        # Mock packages
        mock_package1 = Mock()
        mock_package1.name = "python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")
        mock_package1.uri = "/path/to/python"

        mock_package2 = Mock()
        mock_package2.name = "maya"
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="2023.0")
        mock_package2.uri = "/path/to/maya"

        mock_repo.iter_packages.return_value = [mock_package1, mock_package2]
        mock_repo.iter_package_families.return_value = []  # Add this mock
        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/local/packages")
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data
        assert len(data["packages"]) == 2
        assert data["packages"][0]["name"] == "python"
        assert data["packages"][1]["name"] == "maya"

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_packages_with_filters(self, mock_manager, client):
        """Test getting packages from repository with filters."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.uid = None  # Ensure uid is serializable
        mock_repo.iter_packages.return_value = []
        mock_repo.iter_package_families.return_value = []  # Add this mock
        mock_manager.get_repository.return_value = mock_repo

        response = client.get(
            "/api/v1/repositories/local/packages?name_pattern=py*&limit=10"
        )
        assert response.status_code == 200

        data = response.json()
        assert "packages" in data

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_stats(self, mock_manager, client):
        """Test getting repository statistics."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.uid = None  # Ensure uid is serializable

        # Mock package count
        mock_packages = [Mock() for _ in range(50)]
        mock_repo.iter_packages.return_value = mock_packages
        mock_repo.iter_package_families.return_value = []  # Add this mock
        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/local/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "local"
        assert data["package_count"] == 50
        assert "location" in data

    @patch("rez.package_repository.package_repository_manager")
    def test_search_repositories(self, mock_manager, client):
        """Test searching across repositories."""
        # Mock repositories with packages
        mock_repo1 = Mock()
        mock_repo1.name = "local"
        mock_repo1.uid = None  # Ensure uid is serializable
        mock_repo1.iter_packages.return_value = []

        mock_repo2 = Mock()
        mock_repo2.name = "shared"
        mock_repo2.uid = None  # Ensure uid is serializable
        mock_repo2.iter_packages.return_value = []

        mock_manager.repositories = [mock_repo1, mock_repo2]

        search_data = {"query": "python", "repositories": ["local", "shared"]}

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "repositories_searched" in data

    def test_search_repositories_invalid_request(self, client):
        """Test repository search with invalid request."""
        # Missing required fields
        search_data = {}

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 422

    @patch("rez.package_repository.package_repository_manager")
    def test_list_repositories_empty(self, mock_manager, client):
        """Test listing repositories when none exist."""
        mock_manager.repositories = []

        response = client.get("/api/v1/repositories")
        assert response.status_code == 200

        data = response.json()
        assert data["repositories"] == []

    @patch("rez.package_repository.package_repository_manager")
    def test_repositories_exception_handling(self, mock_manager, client):
        """Test repository endpoints exception handling."""
        mock_manager.repositories = Mock(side_effect=Exception("Repository error"))

        response = client.get("/api/v1/repositories")
        assert response.status_code == 500

    @patch("rez.package_repository.package_repository_manager")
    def test_list_repository_families(self, mock_manager, client):
        """Test listing package families in repository."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.uid = None

        # Mock families
        mock_family1 = Mock()
        mock_family1.name = "python"
        mock_family1.iter_packages.return_value = [Mock(), Mock()]  # 2 packages

        mock_family2 = Mock()
        mock_family2.name = "maya"
        mock_family2.iter_packages.return_value = [Mock()]  # 1 package

        mock_repo.iter_package_families.return_value = [mock_family1, mock_family2]
        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/local/families")
        assert response.status_code == 200

        data = response.json()
        assert "families" in data
        assert len(data["families"]) == 2
        assert data["families"][0]["name"] == "python"
        assert data["families"][0]["package_count"] == 2
        assert data["families"][1]["name"] == "maya"
        assert data["families"][1]["package_count"] == 1

    @patch("rez.package_repository.package_repository_manager")
    def test_list_repository_families_with_pagination(self, mock_manager, client):
        """Test listing repository families with pagination."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.uid = None

        # Mock multiple families
        mock_families = []
        for i in range(10):
            family = Mock()
            family.name = f"package{i}"
            family.iter_packages.return_value = [Mock()]
            mock_families.append(family)

        mock_repo.iter_package_families.return_value = mock_families
        mock_manager.get_repository.return_value = mock_repo

        # Test with limit and offset
        response = client.get("/api/v1/repositories/local/families?limit=3&offset=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["families"]) == 3
        assert data["limit"] == 3
        assert data["offset"] == 2
        assert data["families"][0]["name"] == "package2"

    @patch("rez.package_repository.package_repository_manager")
    def test_list_repository_families_not_found(self, mock_manager, client):
        """Test listing families for non-existent repository."""
        mock_manager.get_repository.return_value = None

        response = client.get("/api/v1/repositories/nonexistent/families")
        assert response.status_code == 404

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_package(self, mock_manager, client):
        """Test getting specific package from repository."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.uid = None

        # Mock package family
        mock_family = Mock()
        mock_family.name = "python"

        # Mock packages in family
        mock_package1 = Mock()
        mock_package1.name = "python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")
        mock_package1.uri = "/path/to/python/3.9.0"

        mock_package2 = Mock()
        mock_package2.name = "python"
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="3.10.0")
        mock_package2.uri = "/path/to/python/3.10.0"

        mock_family.iter_packages.return_value = [mock_package1, mock_package2]
        mock_repo.get_package_family.return_value = mock_family
        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/local/packages/python")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "python"
        assert data["repository"] == "local"
        assert len(data["packages"]) == 2
        assert data["packages"][0]["version"] == "3.9.0"
        assert data["packages"][1]["version"] == "3.10.0"

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_package_not_found(self, mock_manager, client):
        """Test getting non-existent package from repository."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.uid = None
        mock_repo.get_package_family.return_value = None
        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/local/packages/nonexistent")
        assert response.status_code == 404

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_package_repo_not_found(self, mock_manager, client):
        """Test getting package from non-existent repository."""
        mock_manager.get_repository.return_value = None

        response = client.get("/api/v1/repositories/nonexistent/packages/python")
        assert response.status_code == 404

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_packages_with_offset(self, mock_manager, client):
        """Test getting repository packages with offset pagination."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.uid = None

        # Mock multiple packages
        mock_packages = []
        for i in range(10):
            package = Mock()
            package.name = f"package{i}"
            package.version = Mock()
            package.version.__str__ = Mock(return_value="1.0.0")
            package.uri = f"/path/to/package{i}"
            mock_packages.append(package)

        mock_repo.iter_packages.return_value = mock_packages
        mock_repo.iter_package_families.return_value = []
        mock_manager.get_repository.return_value = mock_repo

        # Test with offset
        response = client.get("/api/v1/repositories/local/packages?offset=3&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["packages"]) == 2
        assert data["offset"] == 3
        assert data["limit"] == 2
        assert data["packages"][0]["name"] == "package3"
        assert data["packages"][1]["name"] == "package4"

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_packages_with_name_pattern(self, mock_manager, client):
        """Test getting repository packages with name pattern filter."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.uid = None

        # Mock packages with different names
        mock_package1 = Mock()
        mock_package1.name = "python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")
        mock_package1.uri = "/path/to/python"

        mock_package2 = Mock()
        mock_package2.name = "pytest"
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="7.0.0")
        mock_package2.uri = "/path/to/pytest"

        mock_package3 = Mock()
        mock_package3.name = "maya"
        mock_package3.version = Mock()
        mock_package3.version.__str__ = Mock(return_value="2023.0")
        mock_package3.uri = "/path/to/maya"

        mock_repo.iter_packages.return_value = [
            mock_package1,
            mock_package2,
            mock_package3,
        ]
        mock_repo.iter_package_families.return_value = []
        mock_manager.get_repository.return_value = mock_repo

        # Test with pattern that matches python packages
        response = client.get("/api/v1/repositories/local/packages?name_pattern=py*")
        assert response.status_code == 200

        data = response.json()
        assert len(data["packages"]) == 2
        assert all(pkg["name"].startswith("py") for pkg in data["packages"])

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_info_with_callable_name(self, mock_manager, client):
        """Test getting repository info when name is callable."""
        # Mock repository with callable name
        mock_repo = Mock()
        mock_repo.name = Mock(return_value="callable_repo")
        mock_repo.location = "/path/to/callable"
        mock_repo.__class__.__name__ = "CallableRepository"
        mock_repo.uid = Mock(return_value="test-uid")
        mock_repo.iter_package_families.return_value = [Mock(), Mock()]  # 2 families

        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/callable_repo")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "callable_repo"
        assert data["uid"] == "test-uid"
        assert data["package_count"] == 2

    @patch("rez.package_repository.package_repository_manager")
    def test_get_repository_info_with_failing_uid(self, mock_manager, client):
        """Test getting repository info when uid call fails."""
        # Mock repository with failing uid
        mock_repo = Mock()
        mock_repo.name = "test_repo"
        mock_repo.location = "/path/to/test"
        mock_repo.__class__.__name__ = "TestRepository"
        mock_repo.uid = Mock(side_effect=Exception("UID error"))
        mock_repo.iter_package_families.return_value = []

        mock_manager.get_repository.return_value = mock_repo

        response = client.get("/api/v1/repositories/test_repo")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "test_repo"
        assert data["uid"] is None  # Should be None when uid call fails

    @patch("rez.package_repository.package_repository_manager")
    def test_search_repositories_with_specific_repos(self, mock_manager, client):
        """Test searching repositories with specific repository list."""
        # Mock repositories
        mock_repo1 = Mock()
        mock_repo1.name = "local"
        mock_repo1.uid = None

        mock_repo2 = Mock()
        mock_repo2.name = "shared"
        mock_repo2.uid = None

        # Mock packages
        mock_package1 = Mock()
        mock_package1.name = "python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")
        mock_package1.uri = "/path/to/python"

        mock_repo1.iter_packages.return_value = [mock_package1]
        mock_repo2.iter_packages.return_value = []

        # Setup manager
        mock_manager.get_repository.side_effect = lambda name: {
            "local": mock_repo1,
            "shared": mock_repo2,
        }.get(name)

        search_data = {
            "query": "python",
            "repositories": ["local", "shared"],
            "limit": 10,
        }

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "python"
        assert data["repositories_searched"] == ["local", "shared"]
        assert data["query"] == "python"

    @patch("rez.package_repository.package_repository_manager")
    def test_search_repositories_all_repos(self, mock_manager, client):
        """Test searching all repositories when none specified."""
        # Mock repositories
        mock_repo1 = Mock()
        mock_repo1.name = Mock(return_value="repo1")  # Callable name
        mock_repo1.uid = None

        mock_repo2 = Mock()
        mock_repo2.name = "repo2"  # Attribute name
        mock_repo2.uid = None

        mock_manager.repositories = [mock_repo1, mock_repo2]

        # Mock packages
        mock_package = Mock()
        mock_package.name = "test_package"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="1.0.0")
        mock_package.uri = "/path/to/test_package"

        mock_repo1.iter_packages.return_value = [mock_package]
        mock_repo2.iter_packages.return_value = []

        search_data = {"query": "test"}

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["results"]) == 1
        assert data["repositories_searched"] == ["repo1", "repo2"]

    @patch("rez.package_repository.package_repository_manager")
    def test_search_repositories_with_nonexistent_repo(self, mock_manager, client):
        """Test searching with non-existent repository in list."""
        mock_manager.get_repository.return_value = None

        search_data = {"query": "python", "repositories": ["nonexistent"]}

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert data["results"] == []
        assert data["repositories_searched"] == []

    def test_search_repositories_missing_query(self, client):
        """Test repository search without query field."""
        search_data = {"repositories": ["local"]}

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 422

    @patch("rez.package_repository.package_repository_manager")
    def test_search_repositories_exception(self, mock_manager, client):
        """Test repository search with exception."""
        mock_manager.repositories = Mock(side_effect=Exception("Search error"))

        search_data = {"query": "python"}

        response = client.post("/api/v1/repositories/search", json=search_data)
        assert response.status_code == 500


class TestRepositoryUtilities:
    """Test repository utility functions."""

    def test_repository_to_info(self):
        """Test repository to info conversion."""
        from rez_proxy.routers.repositories import _repository_to_info

        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.__class__.__name__ = "FileSystemPackageRepository"
        mock_repo.uid = None  # Ensure uid is serializable

        info = _repository_to_info(mock_repo)

        assert info["name"] == "local"
        assert info["location"] == "/path/to/local"
        assert info["type"] == "FileSystemPackageRepository"

    def test_repository_to_info_minimal(self):
        """Test repository to info conversion with minimal data."""
        from rez_proxy.routers.repositories import _repository_to_info

        mock_repo = Mock()
        mock_repo.name = "test"
        mock_repo.location = None
        mock_repo.__class__.__name__ = "TestRepository"
        mock_repo.uid = None  # Ensure uid is serializable

        info = _repository_to_info(mock_repo)

        assert info["name"] == "test"
        assert info["location"] is None
        assert info["type"] == "TestRepository"

    def test_get_repository_stats(self):
        """Test repository statistics calculation."""
        from rez_proxy.routers.repositories import _get_repository_stats

        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.uid = None  # Ensure uid is serializable

        # Mock packages
        mock_packages = [Mock() for _ in range(25)]
        mock_repo.iter_packages.return_value = mock_packages

        stats = _get_repository_stats(mock_repo)

        assert stats["name"] == "local"
        assert stats["package_count"] == 25
        assert stats["location"] == "/path/to/local"

    def test_search_repository_packages(self):
        """Test searching packages in repository."""
        from rez_proxy.routers.repositories import _search_repository_packages

        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.uid = None  # Ensure uid is serializable

        # Mock packages
        mock_package1 = Mock()
        mock_package1.name = "python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")

        mock_package2 = Mock()
        mock_package2.name = "pytest"
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="7.0.0")

        mock_repo.iter_packages.return_value = [mock_package1, mock_package2]

        results = _search_repository_packages(mock_repo, "py", limit=10)

        assert len(results) == 2
        assert results[0]["name"] == "python"
        assert results[1]["name"] == "pytest"

    def test_filter_packages_by_pattern(self):
        """Test filtering packages by name pattern."""
        from rez_proxy.routers.repositories import _filter_packages_by_pattern

        # Mock packages
        packages = [
            {"name": "python", "version": "3.9.0"},
            {"name": "pytest", "version": "7.0.0"},
            {"name": "maya", "version": "2023.0"},
        ]

        # Test pattern matching
        filtered = _filter_packages_by_pattern(packages, "py*")
        assert len(filtered) == 2
        assert all(pkg["name"].startswith("py") for pkg in filtered)

        # Test exact match
        filtered = _filter_packages_by_pattern(packages, "maya")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "maya"

        # Test no match
        filtered = _filter_packages_by_pattern(packages, "nonexistent")
        assert len(filtered) == 0

    def test_repository_to_info_with_callable_name(self):
        """Test repository to info conversion with callable name."""
        from rez_proxy.routers.repositories import _repository_to_info

        mock_repo = Mock()
        mock_repo.name = Mock(return_value="callable_repo")
        mock_repo.location = "/path/to/callable"
        mock_repo.__class__.__name__ = "CallableRepository"

        info = _repository_to_info(mock_repo)

        assert info["name"] == "callable_repo"
        assert info["location"] == "/path/to/callable"
        assert info["type"] == "CallableRepository"

    def test_get_repository_stats_with_callable_name(self):
        """Test repository statistics with callable name."""
        from rez_proxy.routers.repositories import _get_repository_stats

        mock_repo = Mock()
        mock_repo.name = Mock(return_value="callable_repo")
        mock_repo.location = "/path/to/callable"

        # Mock packages
        mock_packages = [Mock() for _ in range(15)]
        mock_repo.iter_packages.return_value = mock_packages

        stats = _get_repository_stats(mock_repo)

        assert stats["name"] == "callable_repo"
        assert stats["package_count"] == 15
        assert stats["location"] == "/path/to/callable"

    def test_search_repository_packages_with_limit(self):
        """Test searching packages with limit enforcement."""
        from rez_proxy.routers.repositories import _search_repository_packages

        mock_repo = Mock()
        mock_repo.name = "test_repo"

        # Mock many packages
        mock_packages = []
        for i in range(100):
            package = Mock()
            package.name = f"package{i}"
            package.version = Mock()
            package.version.__str__ = Mock(return_value="1.0.0")
            package.uri = f"/path/to/package{i}"
            mock_packages.append(package)

        mock_repo.iter_packages.return_value = mock_packages

        # Test with small limit
        results = _search_repository_packages(mock_repo, "package", limit=5)

        assert len(results) == 5
        assert all("package" in pkg["name"] for pkg in results)

    def test_search_repository_packages_case_insensitive(self):
        """Test case-insensitive package search."""
        from rez_proxy.routers.repositories import _search_repository_packages

        mock_repo = Mock()
        mock_repo.name = "test_repo"

        # Mock packages with mixed case
        mock_package1 = Mock()
        mock_package1.name = "Python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")

        mock_package2 = Mock()
        mock_package2.name = "PYTEST"
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="7.0.0")

        mock_package3 = Mock()
        mock_package3.name = "maya"
        mock_package3.version = Mock()
        mock_package3.version.__str__ = Mock(return_value="2023.0")

        mock_repo.iter_packages.return_value = [
            mock_package1,
            mock_package2,
            mock_package3,
        ]

        # Test case-insensitive search
        results = _search_repository_packages(mock_repo, "py", limit=10)

        assert len(results) == 2
        assert any(pkg["name"] == "Python" for pkg in results)
        assert any(pkg["name"] == "PYTEST" for pkg in results)

    def test_search_repository_packages_with_missing_uri(self):
        """Test searching packages when URI attribute is missing."""
        from rez_proxy.routers.repositories import _search_repository_packages

        mock_repo = Mock()
        mock_repo.name = "test_repo"

        # Mock package without uri attribute
        mock_package = Mock()
        mock_package.name = "test_package"
        mock_package.version = Mock()
        mock_package.version.__str__ = Mock(return_value="1.0.0")
        # Remove uri attribute to test getattr fallback
        del mock_package.uri

        mock_repo.iter_packages.return_value = [mock_package]

        results = _search_repository_packages(mock_repo, "test", limit=10)

        assert len(results) == 1
        assert results[0]["uri"] is None
