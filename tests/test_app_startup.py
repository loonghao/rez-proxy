"""
Test application startup and basic functionality after PRD cleanup.
"""

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


class TestAppStartup:
    """Test application startup and basic endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_app_creation(self):
        """Test that the app can be created without errors."""
        app = create_app()
        assert app is not None
    
    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/v1/system/health")
        assert response.status_code in [200, 503]  # 503 if Rez not available
    
    def test_system_info(self, client):
        """Test system info endpoint."""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200

        data = response.json()
        assert "platform" in data
        assert "python" in data
    
    def test_openapi_docs(self, client):
        """Test that OpenAPI docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json(self, client):
        """Test that OpenAPI JSON is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        
        # Verify PRD endpoints are not present
        paths = data["paths"]
        prd_paths = [path for path in paths.keys() if "prd" in path.lower()]
        assert len(prd_paths) == 0, f"Found PRD paths that should be removed: {prd_paths}"
    
    def test_available_endpoints(self, client):
        """Test that core Rez proxy endpoints are available."""
        # Test some core endpoints that should exist
        core_endpoints = [
            "/api/v1/system/info",
            "/api/v1/system/health",
            "/api/v1/packages/search",
        ]
        
        for endpoint in core_endpoints:
            response = client.get(endpoint) if endpoint.endswith("/info") or endpoint.endswith("/health") else client.post(endpoint, json={})
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404, f"Endpoint {endpoint} should exist"
