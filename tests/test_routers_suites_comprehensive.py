"""
Comprehensive tests for suites router.
"""

import json
import tempfile
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_suite():
    """Create a mock Rez Suite."""
    suite = MagicMock()
    suite.context_names = []
    suite.get_tools.return_value = {}
    suite.validate.return_value = None
    suite.save.return_value = None
    suite.add_context.return_value = None
    suite.alias_tool.return_value = None
    return suite


@pytest.fixture
def mock_environment():
    """Create a mock environment for testing."""
    context = MagicMock()
    context.resolved_packages = []
    return {
        "context": context,
        "packages": ["python-3.9"],
        "created_at": datetime.utcnow().isoformat(),
        "status": "resolved"
    }


@pytest.fixture(autouse=True)
def clear_suites():
    """Clear suites storage before each test."""
    from rez_proxy.routers.suites import _suites
    _suites.clear()
    yield
    _suites.clear()


class TestSuiteCreation:
    """Test suite creation functionality."""

    @patch("rez.suite.Suite")
    def test_create_suite_success(self, mock_suite_class, client, mock_suite):
        """Test successful suite creation."""
        mock_suite_class.return_value = mock_suite
        
        request_data = {
            "name": "test-suite",
            "description": "A test suite"
        }
        
        response = client.post("/api/v1/suites/", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-suite"
        assert data["description"] == "A test suite"
        assert data["status"] == "created"
        assert "id" in data
        assert "created_at" in data
        assert data["contexts"] == []
        assert data["tools"] == {}

    @patch("rez.suite.Suite")
    def test_create_suite_minimal(self, mock_suite_class, client, mock_suite):
        """Test suite creation with minimal data."""
        mock_suite_class.return_value = mock_suite

        request_data = {
            "name": "minimal-suite"
        }

        response = client.post("/api/v1/suites/", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "minimal-suite"
        assert data["description"] is None

    @patch("rez.suite.Suite")
    def test_create_suite_rez_error(self, mock_suite_class, client):
        """Test suite creation with Rez error."""
        mock_suite_class.side_effect = Exception("Rez Suite creation failed")
        
        request_data = {
            "name": "failing-suite"
        }
        
        response = client.post("/api/v1/suites/", json=request_data)
        
        assert response.status_code == 500

    def test_create_suite_validation_error(self, client):
        """Test suite creation with validation error."""
        request_data = {
            "description": "Missing name field"
        }
        
        response = client.post("/api/v1/suites/", json=request_data)
        
        assert response.status_code == 422


class TestSuiteRetrieval:
    """Test suite retrieval functionality."""

    @patch("rez.suite.Suite")
    def test_get_suite_success(self, mock_suite_class, client, mock_suite):
        """Test successful suite retrieval."""
        # First create a suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]
        
        # Mock tools for retrieval
        mock_tool = MagicMock()
        mock_tool.context_name = "test-context"
        mock_tool.__str__ = lambda self: "test-command"
        mock_suite.get_tools.return_value = {"test-tool": mock_tool}
        mock_suite.context_names = ["test-context"]
        
        # Get the suite
        response = client.get(f"/api/v1/suites/{suite_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == suite_id
        assert data["name"] == "test-suite"
        assert data["contexts"] == ["test-context"]
        assert "test-tool" in data["tools"]

    def test_get_suite_not_found(self, client):
        """Test getting non-existent suite."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/suites/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("rez.suite.Suite")
    def test_get_suite_tools_error(self, mock_suite_class, client, mock_suite):
        """Test suite retrieval when get_tools fails."""
        # Create a suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock tools error
        mock_suite.get_tools.side_effect = Exception("Tools error")
        mock_suite.context_names = []

        # Get the suite - should handle tools error gracefully
        response = client.get(f"/api/v1/suites/{suite_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["tools"] == {}


class TestSuiteContextManagement:
    """Test suite context management functionality."""

    @patch("rez.suite.Suite")
    @patch("rez_proxy.routers.environments._environments")
    def test_add_context_to_suite_success(self, mock_environments, mock_suite_class, client, mock_suite, mock_environment):
        """Test successfully adding context to suite."""
        # Setup
        mock_suite_class.return_value = mock_suite
        env_id = str(uuid.uuid4())
        mock_environments.__contains__ = lambda self, x: x == env_id
        mock_environments.__getitem__ = lambda self, x: mock_environment
        
        # Create suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]
        
        # Add context
        request_data = {
            "context_name": "test-context",
            "environment_id": env_id,
            "prefix_char": "t"
        }
        
        response = client.post(f"/api/v1/suites/{suite_id}/contexts", json=request_data)
        
        assert response.status_code == 200
        assert "added to suite" in response.json()["message"]
        mock_suite.add_context.assert_called_once()

    def test_add_context_suite_not_found(self, client):
        """Test adding context to non-existent suite."""
        fake_id = str(uuid.uuid4())
        request_data = {
            "context_name": "test-context",
            "environment_id": str(uuid.uuid4())
        }
        
        response = client.post(f"/api/v1/suites/{fake_id}/contexts", json=request_data)
        
        assert response.status_code == 404

    @patch("rez.suite.Suite")
    @patch("rez_proxy.routers.environments._environments")
    def test_add_context_environment_not_found(self, mock_environments, mock_suite_class, client, mock_suite):
        """Test adding non-existent environment to suite."""
        # Setup
        mock_suite_class.return_value = mock_suite
        mock_environments.__contains__ = lambda self, x: False

        # Create suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Try to add non-existent environment
        request_data = {
            "context_name": "test-context",
            "environment_id": str(uuid.uuid4())
        }

        response = client.post(f"/api/v1/suites/{suite_id}/contexts", json=request_data)

        assert response.status_code == 404
        assert "Environment" in response.json()["detail"]


class TestSuiteToolManagement:
    """Test suite tool management functionality."""

    @patch("rez.suite.Suite")
    def test_alias_tool_success(self, mock_suite_class, client, mock_suite):
        """Test successful tool aliasing."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]
        
        # Alias tool
        request_data = {
            "context_name": "test-context",
            "tool_name": "python",
            "alias_name": "py"
        }
        
        response = client.post(f"/api/v1/suites/{suite_id}/tools/alias", json=request_data)
        
        assert response.status_code == 200
        assert "aliased as" in response.json()["message"]
        mock_suite.alias_tool.assert_called_once()

    def test_alias_tool_suite_not_found(self, client):
        """Test aliasing tool in non-existent suite."""
        fake_id = str(uuid.uuid4())
        request_data = {
            "context_name": "test-context",
            "tool_name": "python",
            "alias_name": "py"
        }
        
        response = client.post(f"/api/v1/suites/{fake_id}/tools/alias", json=request_data)
        
        assert response.status_code == 404

    @patch("rez.suite.Suite")
    def test_get_suite_tools_success(self, mock_suite_class, client, mock_suite):
        """Test getting suite tools."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock tools
        mock_tool = MagicMock()
        mock_tool.context_name = "test-context"
        mock_tool.__str__ = lambda self: "test-command"
        mock_suite.get_tools.return_value = {"test-tool": mock_tool}
        mock_suite.tool_conflicts = {"conflicted-tool": "conflict reason"}

        response = client.get(f"/api/v1/suites/{suite_id}/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "conflicts" in data
        assert "total_tools" in data
        assert data["total_tools"] == 1

    def test_get_suite_tools_not_found(self, client):
        """Test getting tools from non-existent suite."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/suites/{fake_id}/tools")

        assert response.status_code == 404


class TestSuitePersistence:
    """Test suite saving and loading functionality."""

    @patch("rez.suite.Suite")
    def test_save_suite_success(self, mock_suite_class, client, mock_suite):
        """Test successful suite saving."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Save suite
        response = client.post(f"/api/v1/suites/{suite_id}/save")

        assert response.status_code == 200
        data = response.json()
        assert "saved to" in data["message"]
        assert "path" in data
        mock_suite.validate.assert_called_once()
        mock_suite.save.assert_called_once()

    @patch("rez.suite.Suite")
    def test_save_suite_with_custom_path(self, mock_suite_class, client, mock_suite):
        """Test saving suite with custom path."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Save suite with custom path
        custom_path = "/tmp/custom_suite_path"
        response = client.post(f"/api/v1/suites/{suite_id}/save", params={"path": custom_path})

        assert response.status_code == 200
        data = response.json()
        assert custom_path in data["message"]
        assert data["path"] == custom_path

    def test_save_suite_not_found(self, client):
        """Test saving non-existent suite."""
        fake_id = str(uuid.uuid4())
        response = client.post(f"/api/v1/suites/{fake_id}/save")

        assert response.status_code == 404

    @patch("rez.suite.Suite")
    def test_save_suite_validation_error(self, mock_suite_class, client, mock_suite):
        """Test saving suite with validation error."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock validation error
        mock_suite.validate.side_effect = Exception("Validation failed")

        response = client.post(f"/api/v1/suites/{suite_id}/save")

        assert response.status_code == 500

    @patch("rez.suite.Suite")
    def test_save_suite_save_error(self, mock_suite_class, client, mock_suite):
        """Test saving suite with save error."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock save error
        mock_suite.save.side_effect = Exception("Save failed")

        response = client.post(f"/api/v1/suites/{suite_id}/save")

        assert response.status_code == 500


class TestSuiteManagement:
    """Test suite management functionality."""

    @patch("rez.suite.Suite")
    def test_delete_suite_success(self, mock_suite_class, client, mock_suite):
        """Test successful suite deletion."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Delete suite
        response = client.delete(f"/api/v1/suites/{suite_id}")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify suite is deleted
        get_response = client.get(f"/api/v1/suites/{suite_id}")
        assert get_response.status_code == 404

    def test_delete_suite_not_found(self, client):
        """Test deleting non-existent suite."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/suites/{fake_id}")

        assert response.status_code == 404

    def test_list_suites_empty(self, client):
        """Test listing suites when none exist."""
        response = client.get("/api/v1/suites/")

        assert response.status_code == 200
        data = response.json()
        assert data["suites"] == []
        assert data["total"] == 0

    @patch("rez.suite.Suite")
    def test_list_suites_with_data(self, mock_suite_class, client, mock_suite):
        """Test listing suites with existing data."""
        # Create multiple suites
        mock_suite_class.return_value = mock_suite
        mock_suite.context_names = ["context1", "context2"]

        suite_ids = []
        for i in range(3):
            response = client.post("/api/v1/suites/", json={"name": f"suite-{i}", "description": f"Suite {i}"})
            suite_ids.append(response.json()["id"])

        # List suites
        response = client.get("/api/v1/suites/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["suites"]) == 3
        assert data["total"] == 3

        # Check suite data
        for i, suite in enumerate(data["suites"]):
            assert suite["name"] == f"suite-{i}"
            assert suite["description"] == f"Suite {i}"
            assert suite["contexts"] == ["context1", "context2"]
            assert "id" in suite
            assert "created_at" in suite
            assert "status" in suite


class TestSuiteErrorHandling:
    """Test error handling in suite operations."""

    @patch("rez.suite.Suite")
    def test_add_context_rez_error(self, mock_suite_class, client, mock_suite, mock_environment):
        """Test adding context with Rez error."""
        # Setup
        mock_suite_class.return_value = mock_suite

        # Create suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock add_context error
        mock_suite.add_context.side_effect = Exception("Rez context error")

        with patch("rez_proxy.routers.environments._environments") as mock_environments:
            env_id = str(uuid.uuid4())
            mock_environments.__contains__ = lambda self, x: x == env_id
            mock_environments.__getitem__ = lambda self, x: mock_environment

            request_data = {
                "context_name": "test-context",
                "environment_id": env_id
            }

            response = client.post(f"/api/v1/suites/{suite_id}/contexts", json=request_data)

            assert response.status_code == 500

    @patch("rez.suite.Suite")
    def test_alias_tool_rez_error(self, mock_suite_class, client, mock_suite):
        """Test tool aliasing with Rez error."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock alias_tool error
        mock_suite.alias_tool.side_effect = Exception("Rez alias error")

        request_data = {
            "context_name": "test-context",
            "tool_name": "python",
            "alias_name": "py"
        }

        response = client.post(f"/api/v1/suites/{suite_id}/tools/alias", json=request_data)

        assert response.status_code == 500

    @patch("rez.suite.Suite")
    def test_get_suite_tools_rez_error(self, mock_suite_class, client, mock_suite):
        """Test getting suite tools with Rez error."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock get_tools error
        mock_suite.get_tools.side_effect = Exception("Rez tools error")

        response = client.get(f"/api/v1/suites/{suite_id}/tools")

        # Should return 200 with empty tools due to safe error handling
        assert response.status_code == 200
        assert response.json()["tools"] == {}
        assert response.json()["total_tools"] == 0

    @patch("rez.suite.Suite")
    def test_get_suite_rez_error(self, mock_suite_class, client, mock_suite):
        """Test getting suite with Rez error."""
        # Create suite
        mock_suite_class.return_value = mock_suite
        create_response = client.post("/api/v1/suites/", json={"name": "test-suite"})
        suite_id = create_response.json()["id"]

        # Mock context_names access error
        type(mock_suite).context_names = PropertyMock(side_effect=Exception("Rez context error"))

        response = client.get(f"/api/v1/suites/{suite_id}")

        # Should return 200 with empty contexts due to safe error handling
        assert response.status_code == 200
        assert response.json()["contexts"] == []


class TestSuiteIntegration:
    """Test suite integration scenarios."""

    @patch("rez.suite.Suite")
    def test_full_suite_workflow(self, mock_suite_class, client, mock_suite, mock_environment):
        """Test complete suite workflow."""
        # Setup
        mock_suite_class.return_value = mock_suite
        mock_suite.context_names = []

        # 1. Create suite
        create_response = client.post("/api/v1/suites/", json={
            "name": "integration-suite",
            "description": "Full workflow test"
        })
        assert create_response.status_code == 200
        suite_id = create_response.json()["id"]

        # 2. Add context
        with patch("rez_proxy.routers.environments._environments") as mock_environments:
            env_id = str(uuid.uuid4())
            mock_environments.__contains__ = lambda self, x: x == env_id
            mock_environments.__getitem__ = lambda self, x: mock_environment

            context_response = client.post(f"/api/v1/suites/{suite_id}/contexts", json={
                "context_name": "python-context",
                "environment_id": env_id,
                "prefix_char": "p"
            })
            assert context_response.status_code == 200
            mock_suite.context_names = ["python-context"]

        # 3. Alias tool
        alias_response = client.post(f"/api/v1/suites/{suite_id}/tools/alias", json={
            "context_name": "python-context",
            "tool_name": "python",
            "alias_name": "py"
        })
        assert alias_response.status_code == 200

        # 4. Get tools
        mock_tool = MagicMock()
        mock_tool.context_name = "python-context"
        mock_tool.__str__ = lambda self: "python"
        mock_suite.get_tools.return_value = {"py": mock_tool}

        tools_response = client.get(f"/api/v1/suites/{suite_id}/tools")
        assert tools_response.status_code == 200
        assert "py" in tools_response.json()["tools"]

        # 5. Save suite
        save_response = client.post(f"/api/v1/suites/{suite_id}/save")
        assert save_response.status_code == 200

        # 6. Get suite info
        info_response = client.get(f"/api/v1/suites/{suite_id}")
        assert info_response.status_code == 200
        suite_data = info_response.json()
        assert suite_data["name"] == "integration-suite"
        assert "python-context" in suite_data["contexts"]

        # 7. List suites
        list_response = client.get("/api/v1/suites/")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1

        # 8. Delete suite
        delete_response = client.delete(f"/api/v1/suites/{suite_id}")
        assert delete_response.status_code == 200

        # 9. Verify deletion
        final_list_response = client.get("/api/v1/suites/")
        assert final_list_response.status_code == 200
        assert final_list_response.json()["total"] == 0
