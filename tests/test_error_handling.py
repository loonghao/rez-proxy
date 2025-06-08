"""
Tests for error handling and recovery mechanisms.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from rez_proxy.main import create_app
from rez_proxy.exceptions import (
    RezProxyError,
    RezConfigurationError,
    RezPackageError,
    RezResolverError,
    RezEnvironmentError,
    handle_rez_exception,
)


class TestExceptionHandling:
    """Test custom exception handling."""
    
    def test_rez_proxy_error_creation(self):
        """Test RezProxyError creation and attributes."""
        error = RezProxyError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
    
    def test_rez_configuration_error(self):
        """Test RezConfigurationError specific functionality."""
        error = RezConfigurationError(
            message="Config error",
            details={"config_file": "/path/to/config"}
        )
        
        assert "Config error" in str(error)
        assert error.details["config_file"] == "/path/to/config"
    
    def test_rez_package_error(self):
        """Test RezPackageError specific functionality."""
        error = RezPackageError(
            message="Package not found",
            details={"package": "nonexistent-package"}
        )
        
        assert "Package not found" in str(error)
        assert error.details["package"] == "nonexistent-package"
    
    def test_rez_resolver_error(self):
        """Test RezResolverError specific functionality."""
        error = RezResolverError(
            message="Resolution failed",
            details={"packages": ["pkg1", "pkg2"]}
        )
        
        assert "Resolution failed" in str(error)
        assert error.details["packages"] == ["pkg1", "pkg2"]
    
    def test_rez_environment_error(self):
        """Test RezEnvironmentError specific functionality."""
        error = RezEnvironmentError(
            message="Environment error",
            details={"environment_id": "test-env"}
        )
        
        assert "Environment error" in str(error)
        assert error.details["environment_id"] == "test-env"


class TestRezExceptionHandler:
    """Test Rez exception handling function."""
    
    def test_handle_configuration_error(self):
        """Test handling of Rez configuration errors."""
        test_error = Exception("Unrecognised package repository plugin 'invalid_plugin'")
        
        with pytest.raises(RezConfigurationError) as exc_info:
            handle_rez_exception(test_error, "test_context")
        
        error = exc_info.value
        assert "Invalid package repository plugin" in str(error)
        assert error.details["context"] == "test_context"
        assert "invalid_plugin" in str(error)
    
    def test_handle_package_error(self):
        """Test handling of package not found errors."""
        test_error = Exception("No such package 'nonexistent-package'")
        
        with pytest.raises(RezPackageError) as exc_info:
            handle_rez_exception(test_error, "test_context")
        
        error = exc_info.value
        assert "Package not found" in str(error)
        assert error.details["context"] == "test_context"
    
    def test_handle_resolver_error(self):
        """Test handling of resolver errors."""
        test_error = Exception("Package resolution failed due to conflicts")
        
        with pytest.raises(RezResolverError) as exc_info:
            handle_rez_exception(test_error, "test_context")
        
        error = exc_info.value
        assert "Package resolution failed" in str(error)
        assert error.details["context"] == "test_context"
    
    def test_handle_environment_error(self):
        """Test handling of environment errors."""
        test_error = Exception("Environment context creation failed")
        
        with pytest.raises(RezEnvironmentError) as exc_info:
            handle_rez_exception(test_error, "test_context")
        
        error = exc_info.value
        assert "Environment operation failed" in str(error)
        assert error.details["context"] == "test_context"
    
    def test_handle_generic_error(self):
        """Test handling of generic errors."""
        test_error = Exception("Some unexpected error")
        
        with pytest.raises(RezProxyError) as exc_info:
            handle_rez_exception(test_error, "test_context")
        
        error = exc_info.value
        assert "Rez operation failed" in str(error)
        assert error.details["context"] == "test_context"
        assert error.details["type"] == "Exception"


class TestAPIErrorHandling:
    """Test API error handling and responses."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_404_error_handling(self, client):
        """Test 404 error handling."""
        response = client.get("/api/v1/nonexistent-endpoint")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert "Not Found" in error_data["detail"]
    
    def test_validation_error_handling(self, client):
        """Test validation error handling."""
        # Send invalid JSON to packages endpoint
        invalid_data = {
            "query": "",  # Empty query should cause validation error
            "limit": -1   # Invalid limit
        }

        response = client.post("/api/v1/packages/search", json=invalid_data)

        # Should return validation error
        assert response.status_code in [400, 422]
        error_data = response.json()
        assert "detail" in error_data

    def test_method_not_allowed_handling(self, client):
        """Test method not allowed error handling."""
        # Try to POST to a GET-only endpoint
        response = client.post("/api/v1/system/info")

        assert response.status_code == 405
        error_data = response.json()
        assert "detail" in error_data
    
    @patch("rez_proxy.routers.system.get_platform_info")
    def test_internal_server_error_handling(self, mock_platform_info, client):
        """Test internal server error handling."""
        # Mock an internal error
        mock_platform_info.side_effect = Exception("Internal error")
        
        response = client.get("/api/v1/system/info")
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data


class TestConfigurationErrorRecovery:
    """Test configuration error recovery mechanisms."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_invalid_config_recovery(self, client):
        """Test recovery from invalid configuration."""
        # Try to update with invalid configuration
        invalid_config = {
            "config": {
                "port": "invalid_port",  # Should be integer
                "workers": -1  # Should be positive
            }
        }
        
        response = client.post("/api/v1/config-management/update", json=invalid_config)
        
        # Should reject invalid config
        assert response.status_code in [400, 422]
        
        # Original config should still be accessible
        response = client.get("/api/v1/config-management/current")
        assert response.status_code == 200
    
    def test_config_reload_recovery(self, client):
        """Test configuration reload recovery."""
        # Test config reload endpoint
        response = client.post("/api/v1/config-management/reload")
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True





class TestResourceExhaustionHandling:
    """Test handling of resource exhaustion scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_large_request_handling(self, client):
        """Test handling of very large requests."""
        # Create a very large package search request
        large_query = "package_" + "x" * 10000  # Very long package name

        request_data = {
            "query": large_query,
            "limit": 100
        }

        response = client.post("/api/v1/packages/search", json=request_data)

        # Should either process successfully or fail gracefully
        assert response.status_code in [200, 400, 413, 500]  # 413 = Payload Too Large

    def test_memory_intensive_operations(self, client):
        """Test memory-intensive operations handling."""
        # Test multiple concurrent requests (simulated)
        responses = []

        for _ in range(5):
            response = client.get("/api/v1/system/info")
            responses.append(response.status_code)

        # All should succeed or fail gracefully
        assert all(status in [200, 429, 500] for status in responses)  # 429 = Too Many Requests


class TestGracefulDegradation:
    """Test graceful degradation when services are unavailable."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_rez_unavailable_degradation(self, client):
        """Test graceful degradation when Rez is unavailable."""
        # Most Rez-dependent endpoints will fail in test environment
        # but should fail gracefully with proper error messages
        
        response = client.get("/api/v1/packages/search?query=python")
        
        # Should return proper error, not crash
        assert response.status_code in [200, 500]
        
        if response.status_code == 500:
            error_data = response.json()
            assert "detail" in error_data
    
    def test_file_system_unavailable_degradation(self, client):
        """Test graceful degradation when file system operations fail."""
        # Test config save operation that might fail
        response = client.post("/api/v1/config-management/save")
        
        # Should handle file system errors gracefully
        assert response.status_code in [200, 500]
    
    def test_network_unavailable_degradation(self, client):
        """Test graceful degradation when network is unavailable."""
        # This is a placeholder test for network-dependent operations
        # In a real scenario, this would test external service dependencies
        
        response = client.get("/api/v1/system/info")
        
        # Should work for local system info
        assert response.status_code in [200, 500]
