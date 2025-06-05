"""
Test API endpoints.
"""

import pytest
from unittest.mock import patch


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "rez-proxy"}


def test_root_redirect(client):
    """Test root path redirects to docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


@patch("rez_proxy.utils.rez_detector.detect_rez_installation")
def test_system_status(mock_detect, client, mock_rez_info):
    """Test system status endpoint."""
    mock_detect.return_value = mock_rez_info
    
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["healthy", "warning"]  # May have warnings on test system
    assert data["rez_version"] == "2.114.0"
    assert data["python_version"] == "3.9.0"


@patch("rez_proxy.utils.rez_detector.detect_rez_installation")
def test_system_config(mock_detect, client, mock_rez_info):
    """Test system config endpoint."""
    mock_detect.return_value = mock_rez_info
    
    response = client.get("/api/v1/system/config")
    assert response.status_code == 200
    
    data = response.json()
    assert data["platform"] == "linux"
    assert data["arch"] == "x86_64"
    assert data["packages_path"] == ["/path/to/packages"]


def test_packages_search(client):
    """Test package search endpoint."""
    search_data = {
        "query": "python",
        "limit": 10,
        "offset": 0
    }
    
    with patch("rez.packages.iter_packages") as mock_iter:
        # Mock empty result for now
        mock_iter.return_value = []
        
        response = client.post("/api/v1/packages/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "packages" in data
        assert "total" in data
        assert data["limit"] == 10
        assert data["offset"] == 0


def test_environment_resolve(client):
    """Test environment resolve endpoint."""
    resolve_data = {
        "packages": ["python-3.9", "requests"]
    }
    
    with patch("rez.resolved_context.ResolvedContext") as mock_context:
        # Mock successful resolution
        mock_instance = mock_context.return_value
        mock_instance.status = mock_instance.Status.solved
        mock_instance.resolved_packages = []
        mock_instance.platform = "linux"
        mock_instance.arch = "x86_64"
        mock_instance.os = "linux"
        
        response = client.post("/api/v1/environments/resolve", json=resolve_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["status"] == "resolved"
        assert data["platform"] == "linux"
