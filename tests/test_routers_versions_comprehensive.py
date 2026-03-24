"""
Comprehensive tests for versions router functionality.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestVersionsRouterComprehensive:
    """Comprehensive test cases for versions router endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_parse_version_success(self, mock_rez_api, client):
        """Test successful version parsing."""
        # Mock version object
        mock_version = Mock()
        mock_version.__str__ = Mock(return_value="1.2.3")
        mock_version.tokens = [1, 2, 3]
        mock_rez_api.create_version.return_value = mock_version

        response = client.post("/api/v1/versions/parse", json={"version": "1.2.3"})

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.2.3"
        assert data["tokens"] == ["1", "2", "3"]
        assert data["is_valid"] is True

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_parse_version_invalid(self, mock_rez_api, client):
        """Test parsing invalid version."""
        mock_rez_api.create_version.side_effect = Exception("Invalid version")

        response = client.post("/api/v1/versions/parse", json={"version": "invalid"})

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "invalid"
        assert data["tokens"] == []
        assert data["is_valid"] is False

    @patch("rez_proxy.core.rez_imports.safe_rez_import")
    def test_parse_version_attribute_error(self, mock_safe_rez_import, client):
        """Test version parsing with AttributeError."""
        from rez_proxy.core.rez_imports import RezImportError

        mock_safe_rez_import.side_effect = RezImportError("Rez is not available")

        response = client.post("/api/v1/versions/parse", json={"version": "1.2.3"})

        assert response.status_code == 503
        assert "Rez is not available" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_compare_versions_success(self, mock_rez_api, client):
        """Test successful version comparison."""
        # Mock version objects
        mock_v1 = Mock()
        mock_v1.__str__ = Mock(return_value="1.2.3")
        mock_v1.__lt__ = Mock(return_value=True)
        mock_v1.__gt__ = Mock(return_value=False)

        mock_v2 = Mock()
        mock_v2.__str__ = Mock(return_value="1.2.4")

        mock_rez_api.create_version.side_effect = [mock_v1, mock_v2]

        response = client.post(
            "/api/v1/versions/compare", json={"version1": "1.2.3", "version2": "1.2.4"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version1"] == "1.2.3"
        assert data["version2"] == "1.2.4"
        assert data["comparison"] == -1
        assert data["equal"] is False
        assert data["less_than"] is True
        assert data["greater_than"] is False

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_compare_versions_equal(self, mock_rez_api, client):
        """Test version comparison with equal versions."""
        # Mock equal version objects
        mock_v1 = Mock()
        mock_v1.__str__ = Mock(return_value="1.2.3")
        mock_v1.__lt__ = Mock(return_value=False)
        mock_v1.__gt__ = Mock(return_value=False)

        mock_v2 = Mock()
        mock_v2.__str__ = Mock(return_value="1.2.3")

        mock_rez_api.create_version.side_effect = [mock_v1, mock_v2]

        response = client.post(
            "/api/v1/versions/compare", json={"version1": "1.2.3", "version2": "1.2.3"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["comparison"] == 0
        assert data["equal"] is True
        assert data["less_than"] is False
        assert data["greater_than"] is False

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_compare_versions_greater(self, mock_rez_api, client):
        """Test version comparison with first version greater."""
        # Mock version objects
        mock_v1 = Mock()
        mock_v1.__str__ = Mock(return_value="1.2.4")
        mock_v1.__lt__ = Mock(return_value=False)
        mock_v1.__gt__ = Mock(return_value=True)

        mock_v2 = Mock()
        mock_v2.__str__ = Mock(return_value="1.2.3")

        mock_rez_api.create_version.side_effect = [mock_v1, mock_v2]

        response = client.post(
            "/api/v1/versions/compare", json={"version1": "1.2.4", "version2": "1.2.3"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["comparison"] == 1
        assert data["equal"] is False
        assert data["less_than"] is False
        assert data["greater_than"] is True

    @patch("rez_proxy.core.rez_imports.safe_rez_import")
    def test_compare_versions_attribute_error(self, mock_safe_rez_import, client):
        """Test version comparison with AttributeError."""
        from rez_proxy.core.rez_imports import RezImportError

        mock_safe_rez_import.side_effect = RezImportError("Rez is not available")

        response = client.post(
            "/api/v1/versions/compare", json={"version1": "1.2.3", "version2": "1.2.4"}
        )

        assert response.status_code == 503
        assert "Rez is not available" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_compare_versions_general_error(self, mock_rez_api, client):
        """Test version comparison with general error."""
        mock_rez_api.create_version.side_effect = Exception("Version error")

        response = client.post(
            "/api/v1/versions/compare",
            json={"version1": "invalid1", "version2": "invalid2"},
        )

        assert response.status_code == 400
        assert "Failed to compare versions" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_parse_requirement_success(self, mock_rez_api, client):
        """Test successful requirement parsing."""
        # Mock requirement object - Rez uses different format
        mock_req = Mock()
        mock_req.__str__ = Mock(return_value="python-3.8+")  # Rez format
        mock_req.name = "python"
        mock_req.range = Mock()
        mock_req.range.__str__ = Mock(return_value="3.8+")  # Rez format
        mock_rez_api.create_requirement.return_value = mock_req

        response = client.post(
            "/api/v1/versions/requirements/parse", json={"requirement": "python>=3.8"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requirement"] == "python-3.8+"  # Rez format
        assert data["name"] == "python"
        assert data["range"] == "3.8+"  # Rez format
        assert data["is_valid"] is True

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_parse_requirement_no_range(self, mock_rez_api, client):
        """Test requirement parsing without range."""
        # Mock requirement object without range
        mock_req = Mock()
        mock_req.__str__ = Mock(return_value="python")
        mock_req.name = "python"
        mock_req.range = None
        mock_rez_api.create_requirement.return_value = mock_req

        response = client.post(
            "/api/v1/versions/requirements/parse", json={"requirement": "python"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requirement"] == "python"
        assert data["name"] == "python"
        assert data["range"] is None
        assert data["is_valid"] is True

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_parse_requirement_invalid(self, mock_rez_api, client):
        """Test parsing invalid requirement."""
        mock_rez_api.create_requirement.side_effect = Exception("Invalid requirement")

        response = client.post(
            "/api/v1/versions/requirements/parse",
            json={"requirement": "invalid-requirement"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requirement"] == "invalid-requirement"
        assert data["name"] == ""
        assert data["range"] is None
        assert data["is_valid"] is False

    @patch("rez_proxy.core.rez_imports.safe_rez_import")
    def test_parse_requirement_attribute_error(self, mock_safe_rez_import, client):
        """Test requirement parsing with AttributeError."""
        from rez_proxy.core.rez_imports import RezImportError

        mock_safe_rez_import.side_effect = RezImportError("Rez is not available")

        response = client.post(
            "/api/v1/versions/requirements/parse", json={"requirement": "python>=3.8"}
        )

        assert response.status_code == 503
        assert "Rez is not available" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_check_requirement_satisfaction_success(self, mock_rez_api, client):
        """Test successful requirement satisfaction check."""
        # Mock requirement and version objects
        mock_req = Mock()
        mock_req.__str__ = Mock(return_value="python-3.8+")  # Rez format
        mock_req.range = Mock()

        mock_ver = Mock()
        mock_ver.__str__ = Mock(return_value="3.9.0")
        mock_ver.__contains__ = Mock(return_value=True)

        # Mock the 'in' operator for version in range
        mock_req.range.__contains__ = Mock(return_value=True)

        mock_rez_api.create_requirement.return_value = mock_req
        mock_rez_api.create_version.return_value = mock_ver

        response = client.post(
            "/api/v1/versions/requirements/check",
            params={"requirement": "python>=3.8", "version": "3.9.0"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requirement"] == "python-3.8+"  # Rez format
        assert data["version"] == "3.9.0"
        assert data["satisfies"] is True

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_check_requirement_satisfaction_no_range(self, mock_rez_api, client):
        """Test requirement satisfaction check without range."""
        # Mock requirement and version objects
        mock_req = Mock()
        mock_req.__str__ = Mock(return_value="python")
        mock_req.name = "python"
        mock_req.range = None

        mock_ver = Mock()
        mock_ver.__str__ = Mock(return_value="3.9.0")
        mock_ver.name = "python"

        mock_rez_api.create_requirement.return_value = mock_req
        mock_rez_api.create_version.return_value = mock_ver

        response = client.post(
            "/api/v1/versions/requirements/check",
            params={"requirement": "python", "version": "3.9.0"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requirement"] == "python"
        assert data["version"] == "3.9.0"
        assert data["satisfies"] is True

    @patch("rez_proxy.core.rez_imports.safe_rez_import")
    def test_check_requirement_satisfaction_attribute_error(
        self, mock_safe_rez_import, client
    ):
        """Test requirement satisfaction check with AttributeError."""
        from rez_proxy.core.rez_imports import RezImportError

        mock_safe_rez_import.side_effect = RezImportError("Rez is not available")

        response = client.post(
            "/api/v1/versions/requirements/check",
            params={"requirement": "python>=3.8", "version": "3.9.0"},
        )

        assert response.status_code == 503
        assert "Rez is not available" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_check_requirement_satisfaction_general_error(self, mock_rez_api, client):
        """Test requirement satisfaction check with general error."""
        mock_rez_api.create_requirement.side_effect = Exception("Requirement error")

        response = client.post(
            "/api/v1/versions/requirements/check",
            params={"requirement": "invalid", "version": "invalid"},
        )

        assert response.status_code == 400
        assert "Failed to check requirement" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_get_latest_versions_success(self, mock_rez_api, client):
        """Test successful latest versions retrieval."""
        # Mock package objects
        mock_package1 = Mock()
        mock_package1.version = Mock()
        mock_package1.version.__str__ = Mock(return_value="3.9.0")

        mock_package2 = Mock()
        mock_package2.version = Mock()
        mock_package2.version.__str__ = Mock(return_value="1.21.0")

        def mock_iter_packages(name):
            if name == "python":
                return [mock_package1]
            elif name == "numpy":
                return [mock_package2]
            return []

        mock_rez_api.iter_packages.side_effect = mock_iter_packages

        # Use correct query parameter format for list
        response = client.get(
            "/api/v1/versions/latest?packages=python&packages=numpy&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "latest_versions" in data
        assert data["latest_versions"]["python"] == "3.9.0"
        assert data["latest_versions"]["numpy"] == "1.21.0"

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_get_latest_versions_no_packages(self, mock_rez_api, client):
        """Test latest versions with no packages found."""
        mock_rez_api.iter_packages.return_value = []

        response = client.get("/api/v1/versions/latest?packages=nonexistent&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "latest_versions" in data
        assert data["latest_versions"]["nonexistent"] is None

    @patch("rez_proxy.core.rez_imports.safe_rez_import")
    def test_get_latest_versions_attribute_error(self, mock_safe_rez_import, client):
        """Test latest versions with AttributeError."""
        from rez_proxy.core.rez_imports import RezImportError

        mock_safe_rez_import.side_effect = RezImportError("Rez is not available")

        response = client.get("/api/v1/versions/latest?packages=python&limit=10")

        assert response.status_code == 503
        assert "Rez is not available" in response.json()["detail"]

    @patch("rez_proxy.core.rez_imports.rez_api")
    def test_get_latest_versions_general_error(self, mock_rez_api, client):
        """Test latest versions with general error."""
        mock_rez_api.iter_packages.side_effect = Exception("Package error")

        response = client.get("/api/v1/versions/latest?packages=python&limit=10")

        assert response.status_code == 500
        assert "Failed to get latest versions" in response.json()["detail"]

    def test_parse_version_validation_error(self, client):
        """Test version parsing with validation error."""
        response = client.post("/api/v1/versions/parse", json={})
        assert response.status_code == 422

    def test_compare_versions_validation_error(self, client):
        """Test version comparison with validation error."""
        response = client.post("/api/v1/versions/compare", json={"version1": "1.2.3"})
        assert response.status_code == 422

    def test_parse_requirement_validation_error(self, client):
        """Test requirement parsing with validation error."""
        response = client.post("/api/v1/versions/requirements/parse", json={})
        assert response.status_code == 422
