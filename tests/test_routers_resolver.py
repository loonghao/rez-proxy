"""
Test resolver router functionality.
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_rez_context():
    """Create a mock resolved context."""
    context = MagicMock()
    context.status.name = "solved"
    context.resolved_packages = []
    context.failed_packages = []
    context.num_solves = 1
    context.failure_description = None
    return context


@pytest.fixture
def mock_rez_package():
    """Create a mock rez package."""
    package = MagicMock()
    package.name = "test_package"
    package.version = "1.0.0"
    package.uri = "/path/to/package"
    package.requires = []
    return package


@pytest.fixture
def mock_rez_requirement():
    """Create a mock rez requirement."""
    req = MagicMock()
    req.name = "test_package"
    req.range = ">=1.0"
    return req


class TestResolverRouter:
    """Test resolver router endpoints."""

    def test_advanced_resolve_success(self, client, mock_rez_context, mock_rez_package):
        """Test successful advanced package resolution."""
        resolve_request = {
            "packages": ["python-3.9", "numpy-1.20"],
            "platform": "linux",
            "arch": "x86_64",
            "timestamp": 1234567890,
            "max_fails": 5,
            "time_limit": 60,
            "verbosity": 1,
        }

        # Setup mock context with resolved packages
        mock_rez_context.resolved_packages = [mock_rez_package]
        mock_rez_context.status.name = "solved"

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", return_value=mock_rez_context):
            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "solved"
            assert data["graph_size"] == 1
            assert len(data["resolved_packages"]) == 1
            assert data["resolved_packages"][0]["name"] == "test_package"
            assert data["resolved_packages"][0]["version"] == "1.0.0"
            assert data["num_solves"] == 1
            assert isinstance(data["solve_time"], float)

    def test_advanced_resolve_failed_status(self, client, mock_rez_context):
        """Test advanced resolve with failed resolution status."""
        resolve_request = {
            "packages": ["conflicting-package-1", "conflicting-package-2"],
        }

        # Setup mock context with failed status
        mock_rez_context.status.name = "failed"
        mock_rez_context.resolved_packages = []
        mock_rez_context.failed_packages = ["conflicting-package-1"]

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", return_value=mock_rez_context):
            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert len(data["failed_packages"]) == 1
            assert data["failed_packages"][0] == "conflicting-package-1"

    def test_advanced_resolve_validation_error(self, client):
        """Test advanced resolve with validation error."""
        resolve_request = {
            "packages": [],  # Empty packages list
        }

        response = client.post(
            "/api/v1/resolver/resolve/advanced", json=resolve_request
        )

        assert response.status_code == 422  # Validation error

    def test_advanced_resolve_rez_api_not_available(self, client):
        """Test advanced resolve when Rez API is not available."""
        resolve_request = {
            "packages": ["python-3.9"],
        }

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", side_effect=AttributeError("API not available")):
            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 500
            assert "Rez resolver API not available" in response.json()["detail"]

    def test_advanced_resolve_context_creation_error(self, client):
        """Test advanced resolve when context creation fails."""
        resolve_request = {
            "packages": ["invalid-package"],
        }

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", side_effect=Exception("Context creation failed")):
            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 400
            assert "Failed to create resolved context" in response.json()["detail"]

    def test_dependency_graph_success(self, client, mock_rez_package):
        """Test successful dependency graph generation."""
        graph_request = {
            "packages": ["python", "numpy"],
            "depth": 2,
        }

        # Setup mock package with dependencies
        dep_req = MagicMock()
        dep_req.name = "dependency"
        dep_req.__str__ = lambda: "dependency>=1.0"
        mock_rez_package.requires = [dep_req]

        # Mock the iter_packages function to return our mock package
        def mock_iter_packages(package_name):
            return [mock_rez_package]

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_api:
            mock_api.iter_packages = mock_iter_packages

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            assert response.status_code == 200
            data = response.json()
            assert "dependency_graph" in data
            assert "python" in data["dependency_graph"]
            assert "numpy" in data["dependency_graph"]

    def test_dependency_graph_empty_packages(self, client):
        """Test dependency graph with empty packages."""
        graph_request = {
            "packages": ["nonexistent"],
            "depth": 1,
        }

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_api:
            mock_api.iter_packages = lambda package_name: []

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            assert response.status_code == 200
            data = response.json()
            assert "dependency_graph" in data
            assert data["dependency_graph"]["nonexistent"] == {}

    def test_dependency_graph_validation_error(self, client):
        """Test dependency graph with validation error."""
        graph_request = {
            "packages": [],  # Empty packages list
        }

        response = client.post("/api/v1/resolver/dependency-graph", json=graph_request)

        assert response.status_code == 422  # Validation error

    def test_dependency_graph_rez_api_not_available(self, client):
        """Test dependency graph when Rez API is not available."""
        graph_request = {
            "packages": ["python"],
            "depth": 1,
        }

        with patch("rez_proxy.routers.resolver.rez_api") as mock_api:
            mock_api.iter_packages = MagicMock(side_effect=AttributeError("API not available"))

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            assert response.status_code == 500
            assert "Rez packages API not available" in response.json()["detail"]

    def test_dependency_graph_depth_limit(self, client, mock_rez_package):
        """Test dependency graph with depth limit."""
        graph_request = {
            "packages": ["python"],
            "depth": 0,  # Zero depth should return empty
        }

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_api:
            mock_api.iter_packages = lambda package_name: [mock_rez_package]

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["dependency_graph"]["python"] == {}

    def test_detect_conflicts_no_conflicts(self, client, mock_rez_context):
        """Test conflict detection with no conflicts."""
        mock_rez_context.status.name = "solved"

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", return_value=mock_rez_context):
            response = client.get(
                "/api/v1/resolver/conflicts",
                params={"packages": ["python-3.9", "numpy-1.20"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert "has_conflicts" in data
            assert data["has_conflicts"] is False
            assert data["resolution_status"] == "solved"

    def test_detect_conflicts_with_conflicts(self, client, mock_rez_context):
        """Test conflict detection with conflicts."""
        mock_rez_context.status.name = "failed"
        mock_rez_context.failure_description = "Version conflict between packages"

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", return_value=mock_rez_context):
            response = client.get(
                "/api/v1/resolver/conflicts",
                params={"packages": ["python-2.7", "python-3.9"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert "has_conflicts" in data
            assert data["has_conflicts"] is True
            assert data["resolution_status"] == "failed"
            assert len(data["conflicts"]) == 1
            assert data["conflicts"][0]["type"] == "resolution_failure"

    def test_detect_conflicts_rez_api_not_available(self, client):
        """Test conflict detection when Rez API is not available."""
        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", side_effect=AttributeError("API not available")):
            response = client.get(
                "/api/v1/resolver/conflicts",
                params={"packages": ["python-3.9"]}
            )

            assert response.status_code == 500
            assert "Rez resolver API not available" in response.json()["detail"]

    def test_detect_conflicts_context_creation_error(self, client):
        """Test conflict detection when context creation fails."""
        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", side_effect=Exception("Context error")):
            response = client.get(
                "/api/v1/resolver/conflicts",
                params={"packages": ["invalid-package"]}
            )

            assert response.status_code == 400
            assert "Failed to create resolved context" in response.json()["detail"]

    def test_validate_package_list_success(self, client, mock_rez_requirement):
        """Test successful package list validation."""
        packages = ["python-3.9", "numpy>=1.20"]

        with patch("rez_proxy.core.rez_imports.rez_api.create_requirement", return_value=mock_rez_requirement):
            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 200
            data = response.json()
            assert "all_valid" in data
            assert "results" in data
            assert data["all_valid"] is True
            assert len(data["results"]) == 2
            assert all(result["valid"] for result in data["results"])

    def test_validate_package_list_invalid(self, client):
        """Test package list validation with invalid packages."""
        packages = ["invalid-package-spec"]

        with patch("rez_proxy.core.rez_imports.rez_api.create_requirement", side_effect=Exception("Invalid requirement")):
            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 200
            data = response.json()
            assert "all_valid" in data
            assert "results" in data
            # Should have validation errors
            assert not data["all_valid"]
            assert len(data["results"]) == 1
            assert not data["results"][0]["valid"]
            assert "Invalid requirement" in data["results"][0]["error"]

    def test_validate_package_list_rez_api_not_available(self, client):
        """Test package validation when Rez API is not available."""
        packages = ["python-3.9"]

        with patch("rez_proxy.core.rez_imports.rez_api.create_requirement", side_effect=AttributeError("API not available")):
            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 200
            data = response.json()
            assert not data["all_valid"]
            assert "Rez API not available" in data["results"][0]["error"]

    def test_validate_package_list_mixed_results(self, client, mock_rez_requirement):
        """Test package validation with mixed valid/invalid results."""
        packages = ["python-3.9", "invalid-spec", "numpy>=1.20"]

        def mock_create_requirement(package_req):
            if "invalid" in package_req:
                raise Exception("Invalid package specification")
            return mock_rez_requirement

        with patch("rez_proxy.core.rez_imports.rez_api.create_requirement", side_effect=mock_create_requirement):
            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 200
            data = response.json()
            assert not data["all_valid"]  # Should be False due to invalid package
            assert len(data["results"]) == 3
            assert data["results"][0]["valid"] is True  # python-3.9
            assert data["results"][1]["valid"] is False  # invalid-spec
            assert data["results"][2]["valid"] is True  # numpy>=1.20

    def test_validate_package_list_general_error(self, client):
        """Test package validation with general system error."""
        packages = ["test-package"]

        with patch("rez_proxy.core.rez_imports.rez_api.create_requirement", side_effect=RuntimeError("System error")):
            response = client.post("/api/v1/resolver/validate", json=packages)

            assert response.status_code == 500
            assert "Package validation failed" in response.json()["detail"]

    def test_advanced_resolve_context_without_status(self, client):
        """Test advanced resolve with context that has no status attribute."""
        resolve_request = {
            "packages": ["python-3.9"],
        }

        mock_context = MagicMock()
        del mock_context.status  # Remove status attribute
        mock_context.resolved_packages = []
        mock_context.failed_packages = []
        mock_context.num_solves = 0

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", return_value=mock_context):
            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unknown"

    def test_advanced_resolve_context_without_resolved_packages(self, client):
        """Test advanced resolve with context that has no resolved_packages attribute."""
        resolve_request = {
            "packages": ["python-3.9"],
        }

        mock_context = MagicMock()
        mock_context.status.name = "solved"
        del mock_context.resolved_packages  # Remove resolved_packages attribute
        mock_context.failed_packages = []
        mock_context.num_solves = 1

        with patch("rez_proxy.core.rez_imports.rez_api.create_resolved_context", return_value=mock_context):
            response = client.post(
                "/api/v1/resolver/resolve/advanced", json=resolve_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "solved"
            assert len(data["resolved_packages"]) == 0

    def test_dependency_graph_circular_dependency(self, client):
        """Test dependency graph with circular dependencies."""
        graph_request = {
            "packages": ["circular-package"],
            "depth": 3,
        }

        # Create a mock package that depends on itself
        mock_package = MagicMock()
        mock_package.name = "circular-package"
        mock_package.version = "1.0.0"
        mock_package.uri = "/path/to/package"

        dep_req = MagicMock()
        dep_req.name = "circular-package"  # Self-dependency
        dep_req.__str__ = lambda: "circular-package>=1.0"
        mock_package.requires = [dep_req]

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_api:
            mock_api.iter_packages = lambda package_name: [mock_package]

            response = client.post(
                "/api/v1/resolver/dependency-graph", json=graph_request
            )

            assert response.status_code == 200
            data = response.json()
            assert "dependency_graph" in data
            # Should handle circular dependency gracefully
            assert "circular-package" in data["dependency_graph"]
