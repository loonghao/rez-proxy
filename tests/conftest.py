"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_rez_info():
    """Mock Rez installation info."""
    return {
        "version": "2.114.0",
        "rez_root": "/path/to/rez",
        "python_path": "/usr/bin/python",
        "python_version": "3.9.0",
        "packages_path": ["/path/to/packages"],
        "local_packages_path": "/path/to/local",
        "release_packages_path": "/path/to/release",
        "config_file": "/path/to/config.py",
        "platform": "linux",
        "arch": "x86_64",
        "os": "linux",
        "environment_variables": {},
    }
