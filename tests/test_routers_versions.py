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

        with patch("rez.version.Version") as mock_version:
            # Mock version object
            mock_instance = mock_version.return_value
            mock_instance.tokens = [1, 2, 3]

            response = client.post("/api/v1/versions/parse", json=version_request)

            assert response.status_code == 200
            data = response.json()
            assert "version" in data
            assert "is_valid" in data

    def test_parse_version_invalid(self, client):
        """Test parsing an invalid version string."""
        version_request = {"version": "invalid.version"}

        with patch("rez.version.Version") as mock_version:
            # Mock version parsing failure
            mock_version.side_effect = Exception("Invalid version")

            response = client.post("/api/v1/versions/parse", json=version_request)

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False

    def test_compare_versions(self, client):
        """Test comparing two versions."""
        compare_request = {"version1": "1.2.3", "version2": "1.2.4"}

        with patch("rez.version.Version") as mock_version:
            # Mock version objects
            mock_v1 = mock_version.return_value
            mock_v1.__lt__ = lambda self, other: True
            mock_v1.__eq__ = lambda self, other: False
            mock_v1.__gt__ = lambda self, other: False

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

        with patch("rez.version.Version") as mock_version:
            # Mock version parsing failure
            mock_version.side_effect = Exception("Invalid version")

            response = client.post("/api/v1/versions/compare", json=compare_request)

            assert response.status_code == 400

    def test_parse_requirement(self, client):
        """Test parsing a requirement string."""
        requirement_request = {"requirement": "python>=3.8"}

        with patch("rez.version.Requirement") as mock_req:
            # Mock requirement object
            mock_instance = mock_req.return_value
            mock_instance.name = "python"
            mock_instance.range = ">=3.8"

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

        with patch("rez.version.Requirement") as mock_req:
            # Mock requirement parsing failure
            mock_req.side_effect = Exception("Invalid requirement")

            response = client.post(
                "/api/v1/versions/requirements/parse", json=requirement_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False

    def test_check_requirement_satisfaction(self, client):
        """Test checking if version satisfies requirement."""
        with patch("rez.version.Requirement") as mock_req, patch("rez.version.Version"):
            # Mock requirement and version objects
            mock_req_instance = mock_req.return_value
            mock_req_instance.contains_version.return_value = True

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
        with patch("rez.version.Requirement") as mock_req:
            # Mock requirement parsing failure
            mock_req.side_effect = Exception("Invalid requirement")

            response = client.post(
                "/api/v1/versions/requirements/check",
                params={"requirement": "invalid", "version": "1.0.0"},
            )

            assert response.status_code == 400

    def test_get_latest_versions(self, client):
        """Test getting latest versions of packages."""
        with patch("rez.packages.iter_packages") as mock_iter:
            # Mock package iteration
            mock_iter.return_value = []

            response = client.get(
                "/api/v1/versions/latest?packages=python&packages=numpy&limit=5"
            )

            assert response.status_code == 200
            data = response.json()
            assert "latest_versions" in data

    def test_get_latest_versions_error(self, client):
        """Test getting latest versions with error."""
        with patch("rez.packages.iter_packages") as mock_iter:
            # Mock package iteration failure
            mock_iter.side_effect = Exception("Package repository error")

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
