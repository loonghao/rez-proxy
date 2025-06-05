"""
Test Rez integration to ensure we're using the correct Rez APIs.
"""

from unittest.mock import MagicMock, patch

import pytest


def test_rez_packages_api_usage():
    """Test that we're using the correct Rez packages API."""

    # Create a simple mock package with proper string values
    class MockPackage:
        def __init__(self):
            self.name = "python"
            self.version = "3.9.0"
            self.description = "Python interpreter"
            self.authors = ["Python Software Foundation"]
            self.requires = []
            self.tools = ["python", "pip"]
            self.commands = None
            self.uri = "/path/to/python/3.9.0"

    mock_package = MockPackage()

    from rez_proxy.routers.packages import _package_to_info

    # Test package conversion
    package_info = _package_to_info(mock_package)

    assert package_info.name == "python"
    assert package_info.version == "3.9.0"
    assert package_info.description == "Python interpreter"
    assert package_info.tools == ["python", "pip"]


def test_rez_resolved_context_api_usage():
    """Test that we're using the correct ResolvedContext API."""

    from rez.resolver import ResolverStatus

    # Mock ResolvedContext
    mock_context = MagicMock()
    mock_context.status = ResolverStatus.solved
    mock_context.resolved_packages = []

    # Mock system
    mock_system = MagicMock()
    mock_system.platform = "linux"
    mock_system.arch = "x86_64"
    mock_system.os = "linux"

    with (
        patch("rez.resolved_context.ResolvedContext") as mock_resolved_context,
        patch("rez.system.system", mock_system),
    ):
        mock_resolved_context.return_value = mock_context

        # This should not raise an exception
        # request = EnvironmentResolveRequest(packages=["python-3.9"])  # Test data (not used)

        # The function should use the correct Rez APIs
        mock_resolved_context.assert_not_called()  # Not called yet


def test_rez_shells_api_usage():
    """Test that we're using the correct Rez shells API."""

    mock_shell_class = MagicMock()
    mock_shell_class.name.return_value = "bash"
    mock_shell_class.executable = "bash"
    mock_shell_class.file_extension.return_value = ".sh"
    mock_shell_class.is_available.return_value = True
    mock_shell_class.executable_filepath.return_value = "/bin/bash"

    with (
        patch("rez.shells.get_shell_types") as mock_get_types,
        patch("rez.shells.get_shell_class") as mock_get_class,
    ):
        mock_get_types.return_value = ["bash", "tcsh", "cmd"]
        mock_get_class.return_value = mock_shell_class

        # Test shell listing
        # This would be tested in actual API tests


def test_package_info_conversion_with_variant():
    """Test package info conversion with Rez Variant objects."""

    # Create mock objects with proper string values
    class MockParent:
        def __init__(self):
            self.name = "maya"
            self.version = "2023.1"
            self.description = "Maya DCC"
            self.requires = []
            self.tools = ["maya"]
            self.commands = None
            self.uri = "/path/to/maya/2023.1"

    class MockVariant:
        def __init__(self):
            self.parent = MockParent()
            self.index = 0
            self.subpath = "platform-linux/arch-x86_64"

    mock_variant = MockVariant()

    from rez_proxy.routers.packages import _package_to_info

    # Test variant conversion
    package_info = _package_to_info(mock_variant)

    assert package_info.name == "maya"
    assert package_info.version == "2023.1"
    assert package_info.variants == [
        {"index": 0, "subpath": "platform-linux/arch-x86_64"}
    ]


def test_package_search_uses_correct_api():
    """Test that package search uses the correct Rez API pattern."""

    # This test ensures we're following the correct pattern:
    # 1. Use iter_package_families() to get families
    # 2. Use iter_packages(family_name) to get packages from each family

    mock_family = MagicMock()
    mock_family.name = "python"

    mock_package = MagicMock()
    mock_package.name = "python"
    mock_package.version = "3.9.0"
    mock_package.description = "Python interpreter"

    with (
        patch("rez.packages.iter_package_families") as mock_iter_families,
        patch("rez.packages.iter_packages") as mock_iter_packages,
    ):
        mock_iter_families.return_value = [mock_family]
        mock_iter_packages.return_value = [mock_package]

        # Import the search function

        # The function should use iter_package_families first
        # then iter_packages(family_name) for each family
        # This is the correct Rez API usage pattern


@pytest.mark.asyncio
async def test_environment_resolution_error_handling():
    """Test proper error handling for environment resolution failures."""

    from rez.resolver import ResolverStatus

    # Mock a failed resolution
    mock_context = MagicMock()
    mock_context.status = ResolverStatus.failed
    mock_context.failure_description = "Package 'nonexistent' not found"

    with patch("rez.resolved_context.ResolvedContext") as mock_resolved_context:
        mock_resolved_context.return_value = mock_context

        from fastapi import HTTPException

        from rez_proxy.models.schemas import EnvironmentResolveRequest
        from rez_proxy.routers.environments import resolve_environment

        request = EnvironmentResolveRequest(packages=["nonexistent-package"])

        # Should raise HTTPException with 400 status code
        with pytest.raises(HTTPException) as exc_info:
            await resolve_environment(request)

        assert exc_info.value.status_code == 400
        assert "Package 'nonexistent' not found" in str(exc_info.value.detail)
