"""
Pytest configuration and fixtures.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from rez_proxy.main import create_app
from rez_proxy.models.schemas import ClientContext, PlatformInfo, ServiceMode


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_rez_info():
    """Mock Rez installation info."""
    import platform
    import sys

    # Use actual system info for better compatibility
    system_platform = platform.system().lower()
    if system_platform == "darwin":
        system_platform = "osx"

    return {
        "version": "3.2.1",  # Use actual rez version
        "rez_root": "/path/to/rez",
        "python_path": sys.executable,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "packages_path": ["/path/to/packages"],
        "local_packages_path": "/path/to/local",
        "release_packages_path": ["/path/to/release"],
        "config_file": "/path/to/config.py",
        "platform": system_platform,
        "arch": platform.machine(),  # Keep original case
        "os": f"{system_platform}-{platform.release()}",
        "environment_variables": {},
    }


@pytest.fixture
def mock_rez_info_minimal():
    """Mock minimal Rez installation info."""
    return {
        "version": "2.114.0",
        "python_path": "/usr/bin/python",
        "python_version": "3.9.0",
        "packages_path": [],
        "platform": "linux",
        "arch": "x86_64",
        "os": "ubuntu-20.04",
    }


@pytest.fixture
def mock_platform_info():
    """Mock platform information."""
    return PlatformInfo(
        platform="linux",
        arch="x86_64",
        os="ubuntu-20.04",
        python_version="3.9.0",
        rez_version="2.114.0",
    )


@pytest.fixture
def mock_client_context():
    """Mock client context."""
    return ClientContext(
        client_id="test-client",
        session_id="test-session",
        platform_info=PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="2.114.0",
        ),
        service_mode=ServiceMode.LOCAL,
        user_agent="test-agent",
        request_id="test-request",
    )


@pytest.fixture
def mock_rez_package():
    """Mock Rez package object."""
    package = Mock()
    package.name = "test-package"
    package.version = Mock()
    package.version.__str__ = Mock(return_value="1.0.0")
    package.description = "Test package"
    package.authors = ["Test Author"]
    package.requires = []
    package.tools = ["test-tool"]
    package.commands = None
    package.uri = "/path/to/package"
    package.variants = []
    return package


@pytest.fixture
def mock_rez_package_with_variants():
    """Mock Rez package with variants."""
    package = Mock()
    package.name = "test-package"
    package.version = Mock()
    package.version.__str__ = Mock(return_value="1.0.0")
    package.description = "Test package with variants"
    package.authors = ["Test Author"]
    package.requires = []
    package.tools = ["test-tool"]
    package.commands = None
    package.uri = "/path/to/package"

    # Mock variants
    variant1 = Mock()
    variant1.index = 0
    variant1.requires = []

    variant2 = Mock()
    variant2.index = 1
    variant2.requires = ["python-3.9"]

    package.variants = [variant1, variant2]
    return package


@pytest.fixture
def mock_shell_class():
    """Mock Rez shell class."""
    shell_class = Mock()
    shell_class.name.return_value = "bash"
    shell_class.executable = "bash"
    shell_class.file_extension.return_value = ".sh"
    shell_class.is_available.return_value = True
    shell_class.executable_filepath.return_value = "/bin/bash"
    return shell_class


@pytest.fixture
def mock_build_system():
    """Mock Rez build system."""
    return {
        "cmake": Mock(__doc__="CMake build system", file_types=["CMakeLists.txt"]),
        "python": Mock(__doc__="Python build system", file_types=["setup.py"]),
    }


@pytest.fixture(autouse=True)
def reset_context():
    """Reset context manager state between tests."""
    from rez_proxy.core.context import context_manager

    context_manager._local_platform_info = None
    context_manager.set_current_context(None)
    yield
    context_manager.set_current_context(None)
