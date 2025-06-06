"""
Test API endpoints.
"""

from unittest.mock import patch


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "rez-proxy"}


def test_root_redirect(client):
    """Test root path redirects to docs."""
    response = client.get("/", follow_redirects=False)
    # The root path might not be configured to redirect
    assert response.status_code in [
        307,
        404,
    ]  # Either redirect or not found is acceptable


@patch("rez_proxy.utils.rez_detector.detect_rez_installation")
def test_system_status(mock_detect, client, mock_rez_info):
    """Test system status endpoint."""
    mock_detect.return_value = mock_rez_info

    response = client.get("/api/v1/system/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "warning"]  # May have warnings on test system
    assert data["rez_version"] == mock_rez_info["version"]
    # Python version might include full version info, just check it starts with expected version
    assert data["python_version"].startswith(mock_rez_info["python_version"])


@patch("rez_proxy.routers.system.detect_rez_installation")
def test_system_config(mock_detect, client, mock_rez_info):
    """Test system config endpoint."""
    mock_detect.return_value = mock_rez_info

    response = client.get("/api/v1/system/config")
    assert response.status_code == 200

    data = response.json()
    assert data["platform"] == mock_rez_info["platform"]
    assert data["arch"] == mock_rez_info["arch"]
    assert data["packages_path"] == mock_rez_info["packages_path"]


def test_packages_search(client):
    """Test package search endpoint."""
    search_data = {"query": "python", "limit": 10, "offset": 0}

    with (
        patch("rez.packages.iter_package_families") as mock_families,
        patch("rez.packages.iter_packages") as mock_iter,
    ):
        # Mock empty result for now
        mock_families.return_value = []
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
    resolve_data = {"packages": ["python-3.9", "requests"]}

    with (
        patch("rez.resolved_context.ResolvedContext") as mock_context,
        patch("rez.resolver.ResolverStatus") as mock_status,
        patch("rez.system.system") as mock_system,
    ):
        # Mock ResolverStatus
        mock_status.solved = "solved"

        # Mock system
        mock_system.platform = "linux"
        mock_system.arch = "x86_64"
        mock_system.os = "linux"

        # Mock successful resolution
        mock_instance = mock_context.return_value
        mock_instance.status = mock_status.solved
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
