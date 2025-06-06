"""
Test versions router functionality.
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


class TestVersionsRouter:
    """Test versions router endpoints."""

    def test_get_package_versions(self, client):
        """Test getting package versions."""
        package_name = "python"

        with patch(
            "rez_proxy.routers.versions.get_package_versions_impl"
        ) as mock_versions:
            mock_versions.return_value = {
                "package_name": package_name,
                "versions": [
                    {
                        "version": "3.9.0",
                        "repository": "central",
                        "timestamp": "2023-01-01T10:00:00Z",
                        "is_latest": False,
                    },
                    {
                        "version": "3.10.0",
                        "repository": "central",
                        "timestamp": "2023-06-01T10:00:00Z",
                        "is_latest": True,
                    },
                ],
                "total": 2,
            }

            response = client.get(f"/api/v1/versions/{package_name}")

            assert response.status_code == 200
            data = response.json()
            assert data["package_name"] == package_name
            assert len(data["versions"]) == 2
            assert data["total"] == 2

    def test_get_package_versions_not_found(self, client):
        """Test getting versions for non-existent package."""
        package_name = "nonexistent"

        with patch(
            "rez_proxy.routers.versions.get_package_versions_impl"
        ) as mock_versions:
            mock_versions.return_value = None

            response = client.get(f"/api/v1/versions/{package_name}")

            assert response.status_code == 404

    def test_get_package_versions_with_filters(self, client):
        """Test getting package versions with filters."""
        package_name = "python"

        with patch(
            "rez_proxy.routers.versions.get_package_versions_impl"
        ) as mock_versions:
            mock_versions.return_value = {
                "package_name": package_name,
                "versions": [
                    {"version": "3.10.0", "repository": "central", "is_latest": True}
                ],
                "total": 1,
                "filters_applied": {"min_version": "3.10", "repository": "central"},
            }

            response = client.get(
                f"/api/v1/versions/{package_name}?min_version=3.10&repository=central"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["versions"]) == 1
            assert "filters_applied" in data

    def test_get_package_versions_error(self, client):
        """Test getting package versions with error."""
        package_name = "python"

        with patch(
            "rez_proxy.routers.versions.get_package_versions_impl"
        ) as mock_versions:
            mock_versions.side_effect = Exception("Repository error")

            response = client.get(f"/api/v1/versions/{package_name}")

            assert response.status_code == 500

    def test_get_latest_version(self, client):
        """Test getting latest package version."""
        package_name = "python"

        with patch("rez_proxy.routers.versions.get_latest_version_impl") as mock_latest:
            mock_latest.return_value = {
                "package_name": package_name,
                "latest_version": "3.10.0",
                "repository": "central",
                "timestamp": "2023-06-01T10:00:00Z",
                "changelog": "Added new features and bug fixes",
            }

            response = client.get(f"/api/v1/versions/{package_name}/latest")

            assert response.status_code == 200
            data = response.json()
            assert data["package_name"] == package_name
            assert data["latest_version"] == "3.10.0"

    def test_get_latest_version_not_found(self, client):
        """Test getting latest version for non-existent package."""
        package_name = "nonexistent"

        with patch("rez_proxy.routers.versions.get_latest_version_impl") as mock_latest:
            mock_latest.return_value = None

            response = client.get(f"/api/v1/versions/{package_name}/latest")

            assert response.status_code == 404

    def test_compare_versions(self, client):
        """Test comparing package versions."""
        package_name = "python"
        version1 = "3.9.0"
        version2 = "3.10.0"

        with patch("rez_proxy.routers.versions.compare_versions_impl") as mock_compare:
            mock_compare.return_value = {
                "package_name": package_name,
                "version1": version1,
                "version2": version2,
                "comparison_result": "version2_newer",
                "differences": [
                    {
                        "category": "features",
                        "changes": [
                            "Added pattern matching",
                            "Improved error messages",
                        ],
                    },
                    {
                        "category": "dependencies",
                        "changes": ["Updated openssl requirement"],
                    },
                ],
                "compatibility": "backward_compatible",
            }

            response = client.get(
                f"/api/v1/versions/{package_name}/compare/{version1}/{version2}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["comparison_result"] == "version2_newer"
            assert len(data["differences"]) == 2

    def test_compare_versions_not_found(self, client):
        """Test comparing versions for non-existent package or versions."""
        package_name = "nonexistent"
        version1 = "1.0.0"
        version2 = "2.0.0"

        with patch("rez_proxy.routers.versions.compare_versions_impl") as mock_compare:
            mock_compare.return_value = None

            response = client.get(
                f"/api/v1/versions/{package_name}/compare/{version1}/{version2}"
            )

            assert response.status_code == 404

    def test_get_version_info(self, client):
        """Test getting specific version info."""
        package_name = "python"
        version = "3.10.0"

        with patch("rez_proxy.routers.versions.get_version_info_impl") as mock_info:
            mock_info.return_value = {
                "package_name": package_name,
                "version": version,
                "repository": "central",
                "timestamp": "2023-06-01T10:00:00Z",
                "description": "Python interpreter",
                "dependencies": ["openssl-1.1"],
                "tools": ["python", "pip"],
                "size_mb": 45.2,
                "changelog": "Added new features",
                "is_latest": True,
                "is_deprecated": False,
            }

            response = client.get(f"/api/v1/versions/{package_name}/{version}")

            assert response.status_code == 200
            data = response.json()
            assert data["package_name"] == package_name
            assert data["version"] == version
            assert data["is_latest"] is True

    def test_get_version_info_not_found(self, client):
        """Test getting info for non-existent version."""
        package_name = "python"
        version = "99.99.99"

        with patch("rez_proxy.routers.versions.get_version_info_impl") as mock_info:
            mock_info.return_value = None

            response = client.get(f"/api/v1/versions/{package_name}/{version}")

            assert response.status_code == 404

    def test_get_version_dependencies(self, client):
        """Test getting version dependencies."""
        package_name = "numpy"
        version = "1.20.0"

        with patch(
            "rez_proxy.routers.versions.get_version_dependencies_impl"
        ) as mock_deps:
            mock_deps.return_value = {
                "package_name": package_name,
                "version": version,
                "dependencies": [
                    {
                        "name": "python",
                        "version_range": "3.7+",
                        "type": "runtime",
                        "optional": False,
                    },
                    {
                        "name": "blas",
                        "version_range": "1.0+",
                        "type": "runtime",
                        "optional": True,
                    },
                ],
                "total_dependencies": 2,
            }

            response = client.get(
                f"/api/v1/versions/{package_name}/{version}/dependencies"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["dependencies"]) == 2
            assert data["total_dependencies"] == 2

    def test_get_version_dependents(self, client):
        """Test getting packages that depend on a version."""
        package_name = "python"
        version = "3.9.0"

        with patch(
            "rez_proxy.routers.versions.get_version_dependents_impl"
        ) as mock_dependents:
            mock_dependents.return_value = {
                "package_name": package_name,
                "version": version,
                "dependents": [
                    {
                        "name": "numpy",
                        "version": "1.20.0",
                        "dependency_type": "runtime",
                    },
                    {"name": "scipy", "version": "1.7.0", "dependency_type": "runtime"},
                ],
                "total_dependents": 2,
            }

            response = client.get(
                f"/api/v1/versions/{package_name}/{version}/dependents"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["dependents"]) == 2
            assert data["total_dependents"] == 2

    def test_search_versions(self, client):
        """Test searching versions across packages."""
        search_request = {
            "query": "python",
            "version_pattern": "3.*",
            "repositories": ["central", "local"],
            "include_deprecated": False,
        }

        with patch("rez_proxy.routers.versions.search_versions_impl") as mock_search:
            mock_search.return_value = {
                "query": "python",
                "results": [
                    {
                        "package_name": "python",
                        "version": "3.9.0",
                        "repository": "central",
                        "relevance_score": 0.95,
                    },
                    {
                        "package_name": "python",
                        "version": "3.10.0",
                        "repository": "central",
                        "relevance_score": 1.0,
                    },
                ],
                "total_results": 2,
                "search_time_ms": 45,
            }

            response = client.post("/api/v1/versions/search", json=search_request)

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2
            assert data["total_results"] == 2

    def test_search_versions_validation_error(self, client):
        """Test searching versions with validation error."""
        search_request = {
            "query": "",  # Empty query
        }

        response = client.post("/api/v1/versions/search", json=search_request)

        assert response.status_code == 422  # Validation error

    def test_get_version_changelog(self, client):
        """Test getting version changelog."""
        package_name = "python"
        version = "3.10.0"

        with patch(
            "rez_proxy.routers.versions.get_version_changelog_impl"
        ) as mock_changelog:
            mock_changelog.return_value = {
                "package_name": package_name,
                "version": version,
                "changelog": {
                    "release_date": "2023-06-01",
                    "changes": [
                        {"type": "feature", "description": "Added pattern matching"},
                        {
                            "type": "bugfix",
                            "description": "Fixed memory leak in parser",
                        },
                    ],
                    "breaking_changes": [],
                    "migration_notes": "No migration required",
                },
            }

            response = client.get(
                f"/api/v1/versions/{package_name}/{version}/changelog"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["changelog"]["changes"]) == 2
            assert data["changelog"]["breaking_changes"] == []

    def test_get_version_changelog_not_found(self, client):
        """Test getting changelog for non-existent version."""
        package_name = "nonexistent"
        version = "1.0.0"

        with patch(
            "rez_proxy.routers.versions.get_version_changelog_impl"
        ) as mock_changelog:
            mock_changelog.return_value = None

            response = client.get(
                f"/api/v1/versions/{package_name}/{version}/changelog"
            )

            assert response.status_code == 404

    def test_deprecate_version(self, client):
        """Test deprecating a version."""
        package_name = "python"
        version = "2.7.18"
        deprecation_request = {
            "reason": "End of life",
            "replacement_version": "3.9.0",
            "deprecation_date": "2023-01-01",
        }

        with patch(
            "rez_proxy.routers.versions.deprecate_version_impl"
        ) as mock_deprecate:
            mock_deprecate.return_value = {
                "status": "success",
                "package_name": package_name,
                "version": version,
                "deprecated": True,
                "deprecation_info": deprecation_request,
            }

            response = client.post(
                f"/api/v1/versions/{package_name}/{version}/deprecate",
                json=deprecation_request,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["deprecated"] is True

    def test_deprecate_version_not_found(self, client):
        """Test deprecating non-existent version."""
        package_name = "nonexistent"
        version = "1.0.0"
        deprecation_request = {"reason": "Test"}

        with patch(
            "rez_proxy.routers.versions.deprecate_version_impl"
        ) as mock_deprecate:
            mock_deprecate.return_value = None

            response = client.post(
                f"/api/v1/versions/{package_name}/{version}/deprecate",
                json=deprecation_request,
            )

            assert response.status_code == 404
