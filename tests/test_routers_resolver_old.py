"""
Test resolver router functionality.
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


class TestResolverRouter:
    """Test resolver router endpoints."""

    def test_advanced_resolve(self, client):
        """Test advanced package resolution."""
        resolve_request = {
            "packages": ["python-3.9", "numpy-1.20"],
            "platform": "linux",
            "arch": "x86_64",
        }

        with patch("rez.resolved_context.ResolvedContext") as mock_context:
            # Mock the resolved context
            mock_instance = mock_context.return_value
            mock_instance.status.name = "solved"
            mock_instance.resolved_packages = []
            mock_instance.num_solves = 1

            response = client.post("/api/v1/resolver/resolve/advanced", json=resolve_request)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "solved"

    def test_advanced_resolve_validation_error(self, client):
        """Test advanced resolve with validation error."""
        resolve_request = {
            "packages": [],  # Empty packages list
        }

        response = client.post("/api/v1/resolver/resolve/advanced", json=resolve_request)

        assert response.status_code == 422  # Validation error

    def test_dependency_graph(self, client):
        """Test getting dependency graph."""
        graph_request = {
            "packages": ["python", "numpy"],
            "depth": 2,
        }

        with patch("rez.packages.iter_packages") as mock_iter:
            # Mock package iteration
            mock_iter.return_value = []

            response = client.post("/api/v1/resolver/dependency-graph", json=graph_request)

            assert response.status_code == 200
            data = response.json()
            assert "dependency_graph" in data

    def test_get_resolve_graph(self, client):
        """Test getting resolve graph."""
        resolve_request = {
            "packages": ["python-3.9", "numpy"],
            "include_dependencies": True,
        }

        with patch("rez_proxy.routers.resolver.get_resolve_graph_impl") as mock_graph:
            mock_graph.return_value = {
                "nodes": [
                    {
                        "id": "python-3.9.0",
                        "name": "python",
                        "version": "3.9.0",
                        "type": "package",
                    },
                    {
                        "id": "numpy-1.20.3",
                        "name": "numpy",
                        "version": "1.20.3",
                        "type": "package",
                    },
                ],
                "edges": [
                    {"from": "numpy-1.20.3", "to": "python-3.9.0", "type": "dependency"}
                ],
            }

            response = client.post("/api/v1/resolver/graph", json=resolve_request)

            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "edges" in data
            assert len(data["nodes"]) == 2

    def test_validate_resolve_request(self, client):
        """Test validating resolve request."""
        resolve_request = {
            "packages": ["python-3.9", "numpy-1.20"],
            "platform": "linux",
            "arch": "x86_64",
        }

        with patch(
            "rez_proxy.routers.resolver.validate_resolve_request_impl"
        ) as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "warnings": [],
                "errors": [],
                "suggestions": ["Consider using python-3.10 for better performance"],
            }

            response = client.post("/api/v1/resolver/validate", json=resolve_request)

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert len(data["suggestions"]) == 1

    def test_validate_resolve_request_invalid(self, client):
        """Test validating invalid resolve request."""
        resolve_request = {
            "packages": ["nonexistent-package", "invalid-version-spec"],
            "platform": "unsupported",
        }

        with patch(
            "rez_proxy.routers.resolver.validate_resolve_request_impl"
        ) as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "warnings": ["Unsupported platform"],
                "errors": [
                    "Package 'nonexistent-package' not found",
                    "Invalid version specification",
                ],
                "suggestions": [],
            }

            response = client.post("/api/v1/resolver/validate", json=resolve_request)

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert len(data["errors"]) == 2
            assert len(data["warnings"]) == 1

    def test_get_resolver_settings(self, client):
        """Test getting resolver settings."""
        with patch(
            "rez_proxy.routers.resolver.get_resolver_settings_impl"
        ) as mock_settings:
            mock_settings.return_value = {
                "max_solve_time": 300,
                "package_filter": None,
                "package_orderers": ["version_split", "timestamp"],
                "package_cache_disabled": False,
                "resolve_caching": True,
                "allow_unversioned": False,
            }

            response = client.get("/api/v1/resolver/settings")

            assert response.status_code == 200
            data = response.json()
            assert "max_solve_time" in data
            assert data["resolve_caching"] is True

    def test_update_resolver_settings(self, client):
        """Test updating resolver settings."""
        settings_update = {
            "max_solve_time": 600,
            "resolve_caching": False,
            "allow_unversioned": True,
        }

        with patch(
            "rez_proxy.routers.resolver.update_resolver_settings_impl"
        ) as mock_update:
            mock_update.return_value = {
                "status": "success",
                "updated_settings": settings_update,
                "message": "Resolver settings updated successfully",
            }

            response = client.put("/api/v1/resolver/settings", json=settings_update)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["updated_settings"]["max_solve_time"] == 600

    def test_get_resolve_history(self, client):
        """Test getting resolve history."""
        with patch(
            "rez_proxy.routers.resolver.get_resolve_history_impl"
        ) as mock_history:
            mock_history.return_value = {
                "resolves": [
                    {
                        "resolve_id": "resolve-123",
                        "packages": ["python-3.9", "numpy"],
                        "status": "solved",
                        "timestamp": "2023-01-01T10:00:00Z",
                        "duration": 2.5,
                    },
                    {
                        "resolve_id": "resolve-124",
                        "packages": ["python-2.7", "scipy"],
                        "status": "failed",
                        "timestamp": "2023-01-01T09:55:00Z",
                        "duration": 1.2,
                    },
                ],
                "total": 2,
            }

            response = client.get("/api/v1/resolver/history")

            assert response.status_code == 200
            data = response.json()
            assert "resolves" in data
            assert len(data["resolves"]) == 2
            assert data["total"] == 2

    def test_get_resolve_history_with_filters(self, client):
        """Test getting resolve history with filters."""
        with patch(
            "rez_proxy.routers.resolver.get_resolve_history_impl"
        ) as mock_history:
            mock_history.return_value = {
                "resolves": [
                    {
                        "resolve_id": "resolve-123",
                        "packages": ["python-3.9", "numpy"],
                        "status": "solved",
                        "timestamp": "2023-01-01T10:00:00Z",
                    }
                ],
                "total": 1,
            }

            response = client.get("/api/v1/resolver/history?status=solved&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert len(data["resolves"]) == 1
            assert data["resolves"][0]["status"] == "solved"

    def test_get_resolve_details(self, client):
        """Test getting resolve details."""
        resolve_id = "resolve-123"

        with patch(
            "rez_proxy.routers.resolver.get_resolve_details_impl"
        ) as mock_details:
            mock_details.return_value = {
                "resolve_id": resolve_id,
                "packages": ["python-3.9", "numpy"],
                "status": "solved",
                "resolved_packages": [
                    {"name": "python", "version": "3.9.0", "repository": "central"}
                ],
                "environment_vars": {"PYTHONPATH": "/packages/python/3.9.0/lib"},
                "solve_time": 2.5,
                "timestamp": "2023-01-01T10:00:00Z",
            }

            response = client.get(f"/api/v1/resolver/history/{resolve_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["resolve_id"] == resolve_id
            assert data["status"] == "solved"

    def test_get_resolve_details_not_found(self, client):
        """Test getting details for non-existent resolve."""
        resolve_id = "nonexistent"

        with patch(
            "rez_proxy.routers.resolver.get_resolve_details_impl"
        ) as mock_details:
            mock_details.return_value = None

            response = client.get(f"/api/v1/resolver/history/{resolve_id}")

            assert response.status_code == 404

    def test_clear_resolve_cache(self, client):
        """Test clearing resolve cache."""
        with patch("rez_proxy.routers.resolver.clear_resolve_cache_impl") as mock_clear:
            mock_clear.return_value = {
                "status": "success",
                "cache_entries_cleared": 42,
                "message": "Resolve cache cleared successfully",
            }

            response = client.post("/api/v1/resolver/cache/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["cache_entries_cleared"] == 42

    def test_get_cache_stats(self, client):
        """Test getting cache statistics."""
        with patch("rez_proxy.routers.resolver.get_cache_stats_impl") as mock_stats:
            mock_stats.return_value = {
                "total_entries": 150,
                "cache_size_mb": 25.6,
                "hit_rate": 0.85,
                "miss_rate": 0.15,
                "oldest_entry": "2023-01-01T08:00:00Z",
                "newest_entry": "2023-01-01T10:00:00Z",
            }

            response = client.get("/api/v1/resolver/cache/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_entries"] == 150
            assert data["hit_rate"] == 0.85
