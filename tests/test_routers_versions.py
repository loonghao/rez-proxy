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

    def test_parse_version(self, client):
        """Test parsing a version string."""
        version_request = {"version": "1.2.3"}

        with patch("rez_proxy.core.rez_imports.safe_rez_import") as mock_safe_import, \
             patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock successful rez import for decorator
            mock_safe_import.return_value = True
            # Mock version object
            mock_version = mock_rez_api.create_version.return_value
            mock_version.__str__ = lambda: "1.2.3"
            mock_version.tokens = [1, 2, 3]

            response = client.post("/api/v1/versions/parse", json=version_request)

            assert response.status_code == 200
            data = response.json()
            assert "version" in data
            assert "is_valid" in data

    def test_parse_version_invalid(self, client):
        """Test parsing an invalid version string."""
        version_request = {"version": "invalid.version"}

        with patch("rez_proxy.core.rez_imports.safe_rez_import") as mock_safe_import, \
             patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock successful rez import for decorator
            mock_safe_import.return_value = True
            # Mock version parsing failure
            mock_rez_api.create_version.side_effect = Exception("Invalid version")

            response = client.post("/api/v1/versions/parse", json=version_request)

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False

    def test_compare_versions(self, client):
        """Test comparing two versions."""
        compare_request = {"version1": "1.2.3", "version2": "1.2.4"}

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock version objects
            mock_v1 = mock_rez_api.create_version.return_value
            mock_v2 = mock_rez_api.create_version.return_value
            mock_v1.__str__ = lambda: "1.2.3"
            mock_v2.__str__ = lambda: "1.2.4"
            mock_v1.__lt__ = lambda other: True
            mock_v1.__eq__ = lambda other: False
            mock_v1.__gt__ = lambda other: False

            response = client.post("/api/v1/versions/compare", json=compare_request)

            assert response.status_code == 200
            data = response.json()
            assert "comparison" in data
            assert "equal" in data
            assert "less_than" in data
            assert "greater_than" in data

    def test_compare_versions_error(self, client):
        """Test version comparison with error."""
        compare_request = {"version1": "invalid", "version2": "1.2.3"}

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock version parsing failure
            mock_rez_api.create_version.side_effect = Exception("Invalid version")

            response = client.post("/api/v1/versions/compare", json=compare_request)

            assert response.status_code == 400

    def test_parse_requirement(self, client):
        """Test parsing a requirement string."""
        requirement_request = {"requirement": "python>=3.8"}

        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock requirement object
            mock_req = mock_rez_api.create_requirement.return_value
            mock_req.__str__ = lambda: "python>=3.8"
            mock_req.name = "python"
            mock_req.range = ">=3.8"

            response = client.post(
                "/api/v1/versions/requirements/parse", json=requirement_request
            )

            assert response.status_code == 200
            data = response.json()
            assert "requirement" in data
            assert "is_valid" in data

    def test_parse_requirement_invalid(self, client):
        """Test parsing an invalid requirement string."""
        requirement_request = {"requirement": "invalid-requirement"}

        with patch("rez_proxy.core.rez_imports.safe_rez_import") as mock_safe_import, \
             patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock successful rez import for decorator
            mock_safe_import.return_value = True
            # Mock requirement parsing failure
            mock_rez_api.create_requirement.side_effect = Exception("Invalid requirement")

            response = client.post(
                "/api/v1/versions/requirements/parse", json=requirement_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False

    def test_check_requirement_satisfaction(self, client):
        """Test checking if version satisfies requirement."""
        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock requirement and version objects
            mock_req = mock_rez_api.create_requirement.return_value
            mock_ver = mock_rez_api.create_version.return_value
            mock_req.__str__ = lambda: "python>=3.8"
            mock_ver.__str__ = lambda: "3.9.0"
            mock_req.range = mock_rez_api.create_version_range.return_value
            mock_ver.__contains__ = lambda other: True

            response = client.post(
                "/api/v1/versions/requirements/check",
                params={"requirement": "python>=3.8", "version": "3.9.0"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "requirement" in data
            assert "version" in data
            assert "satisfies" in data

    def test_check_requirement_satisfaction_error(self, client):
        """Test requirement satisfaction check with error."""
        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock requirement parsing failure
            mock_rez_api.create_requirement.side_effect = Exception("Invalid requirement")

            response = client.post(
                "/api/v1/versions/requirements/check",
                params={"requirement": "invalid", "version": "1.0.0"},
            )

            assert response.status_code == 400

    def test_get_latest_versions(self, client):
        """Test getting latest versions of packages."""
        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock package iteration
            mock_rez_api.iter_packages.return_value = []

            response = client.get(
                "/api/v1/versions/latest?packages=python&packages=numpy&limit=5"
            )

            assert response.status_code == 200
            data = response.json()
            assert "latest_versions" in data

    def test_get_latest_versions_error(self, client):
        """Test getting latest versions with error."""
        with patch("rez_proxy.core.rez_imports.rez_api") as mock_rez_api:
            # Mock package iteration failure
            mock_rez_api.iter_packages.side_effect = Exception("Package repository error")

            response = client.get("/api/v1/versions/latest?packages=python")

            assert response.status_code == 500

    def test_parse_version_validation_error(self, client):
        """Test version parsing with validation error."""
        # Missing version field
        version_request = {}

        response = client.post("/api/v1/versions/parse", json=version_request)

        assert response.status_code == 422  # Validation error

    def test_compare_versions_validation_error(self, client):
        """Test version comparison with validation error."""
        # Missing version2 field
        compare_request = {"version1": "1.2.3"}

        response = client.post("/api/v1/versions/compare", json=compare_request)

        assert response.status_code == 422  # Validation error

    def test_parse_requirement_validation_error(self, client):
        """Test requirement parsing with validation error."""
        # Missing requirement field
        requirement_request = {}

        response = client.post(
            "/api/v1/versions/requirements/parse", json=requirement_request
        )

        assert response.status_code == 422  # Validation error
