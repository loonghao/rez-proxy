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

        mock_repo2 = Mock()
        mock_repo2.name = "shared"
        mock_repo2.location = "/path/to/shared"
        mock_repo2.__class__.__name__ = "FileSystemPackageRepository"

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

        # Mock packages
        mock_package1 = Mock()
        mock_package1.name = "python"
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")

        mock_package2 = Mock()
        mock_package2.name = "maya"
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="2023.0")

        mock_repo.iter_packages.return_value = [mock_package1, mock_package2]
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
        mock_repo.iter_packages.return_value = []
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

        # Mock package count
        mock_packages = [Mock() for _ in range(50)]
        mock_repo.iter_packages.return_value = mock_packages
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
        mock_repo1.iter_packages.return_value = []

        mock_repo2 = Mock()
        mock_repo2.name = "shared"
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


class TestRepositoryUtilities:
    """Test repository utility functions."""

    def test_repository_to_info(self):
        """Test repository to info conversion."""
        from rez_proxy.routers.repositories import _repository_to_info

        mock_repo = Mock()
        mock_repo.name = "local"
        mock_repo.location = "/path/to/local"
        mock_repo.__class__.__name__ = "FileSystemPackageRepository"

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
