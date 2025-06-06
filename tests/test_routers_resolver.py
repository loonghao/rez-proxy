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

            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "solved"

    def test_advanced_resolve_validation_error(self, client):
        """Test advanced resolve with validation error."""
        resolve_request = {
            "packages": [],  # Empty packages list
        }

        response = client.post(
            "/api/v1/resolver/resolve/advanced", json=resolve_request
        )

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

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            assert response.status_code == 200
            data = response.json()
            assert "dependency_graph" in data

    def test_dependency_graph_validation_error(self, client):
        """Test dependency graph with validation error."""
        graph_request = {
            "packages": [],  # Empty packages list
        }

        response = client.post("/api/v1/resolver/dependency-graph", json=graph_request)

        assert response.status_code == 422  # Validation error

    def test_detect_conflicts(self, client):
        """Test conflict detection."""
        with patch("rez.resolved_context.ResolvedContext") as mock_context:
            # Mock the resolved context
            mock_instance = mock_context.return_value
            mock_instance.status.name = "failed"
            mock_instance.failure_description = "Version conflict"

            response = client.get(
                "/api/v1/resolver/conflicts?packages=python-2.7&packages=python-3.9"
            )

            assert response.status_code == 200
            data = response.json()
            assert "has_conflicts" in data
            assert "resolution_status" in data

    def test_validate_package_list(self, client):
        """Test package list validation."""
        packages = ["python-3.9", "numpy>=1.20"]

        with patch("rez.version.Requirement") as mock_req:
            # Mock requirement parsing
            mock_instance = mock_req.return_value
            mock_instance.name = "python"
            mock_instance.range = None

            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 200
            data = response.json()
            assert "all_valid" in data
            assert "results" in data

    def test_validate_package_list_invalid(self, client):
        """Test package list validation with invalid packages."""
        packages = ["invalid-package-spec"]

        with patch("rez.version.Requirement") as mock_req:
            # Mock requirement parsing failure
            mock_req.side_effect = Exception("Invalid requirement")

            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 200
            data = response.json()
            assert "all_valid" in data
            assert "results" in data
            # Should have validation errors
            assert not data["all_valid"]

    def test_advanced_resolve_error_handling(self, client):
        """Test error handling in advanced resolve."""
        resolve_request = {
            "packages": ["nonexistent-package"],
        }

        with patch("rez.resolved_context.ResolvedContext") as mock_context:
            # Mock an exception
            mock_context.side_effect = Exception("Package not found")

            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            # Should return error response due to our error handling
            assert response.status_code == 500

    def test_dependency_graph_error_handling(self, client):
        """Test error handling in dependency graph."""
        graph_request = {
            "packages": ["nonexistent-package"],
            "depth": 1,
        }

        with patch("rez.packages.iter_packages") as mock_iter:
            # Mock an exception
            mock_iter.side_effect = Exception("Package repository error")

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            # Should return error response due to our error handling
            assert response.status_code == 500

    def test_conflicts_error_handling(self, client):
        """Test error handling in conflict detection."""
        with patch("rez.resolved_context.ResolvedContext") as mock_context:
            # Mock an exception
            mock_context.side_effect = Exception("Resolution error")

            response = client.get("/api/v1/resolver/conflicts?packages=invalid-package")

            # Should return error response due to our error handling
            assert response.status_code == 500

    def test_validate_error_handling(self, client):
        """Test error handling in package validation."""
        packages = ["test-package"]

        with patch("rez.version.Requirement") as mock_req:
            # Mock a general exception (not requirement parsing)
            mock_req.side_effect = RuntimeError("System error")

            response = client.post("/api/v1/resolver/validate", json=packages)

            # Should return error response due to our error handling
            assert response.status_code == 500
