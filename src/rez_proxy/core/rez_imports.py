"""
Centralized Rez API import management.

This module provides a safe and efficient way to import Rez APIs with proper
error handling and lazy loading. It addresses the following issues:

1. Rez configuration dependency - Rez APIs require proper configuration before import
2. Performance optimization - Lazy loading of heavy Rez modules
3. Error isolation - Better error handling when Rez is not available
4. Import consistency - Centralized import logic across the application
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar, cast

logger = logging.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# Cache for imported modules to avoid repeated imports
_import_cache: dict[str, Any] = {}


class RezImportError(Exception):
    """Raised when Rez import fails."""

    pass


def safe_rez_import(module_path: str, attr_name: str | None = None) -> Any:
    """
    Safely import Rez modules with caching and error handling.

    Args:
        module_path: The module path to import (e.g., 'rez.packages')
        attr_name: Optional attribute name to get from the module

    Returns:
        The imported module or attribute

    Raises:
        RezImportError: If import fails
    """
    cache_key = f"{module_path}.{attr_name}" if attr_name else module_path

    if cache_key in _import_cache:
        return _import_cache[cache_key]

    try:
        # Import the module
        import importlib

        module = importlib.import_module(module_path)

        # Get specific attribute if requested
        if attr_name:
            if not hasattr(module, attr_name):
                raise RezImportError(
                    f"Module '{module_path}' has no attribute '{attr_name}'"
                )
            result = getattr(module, attr_name)
        else:
            result = module

        # Cache the result
        _import_cache[cache_key] = result
        return result

    except ImportError as e:
        error_msg = f"Failed to import {module_path}"
        if attr_name:
            error_msg += f".{attr_name}"
        error_msg += f": {e}"
        logger.error(error_msg)
        raise RezImportError(error_msg) from e


def requires_rez(func: F) -> F:
    """
    Decorator to ensure Rez is available before calling a function.

    This decorator checks if Rez can be imported and provides a clear
    error message if it's not available. Supports both sync and async functions.
    """
    import asyncio

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Test basic Rez import
            safe_rez_import("rez")
            return await func(*args, **kwargs)
        except RezImportError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=503, detail=f"Rez is not available: {e}")

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Test basic Rez import
            safe_rez_import("rez")
            return func(*args, **kwargs)
        except RezImportError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=503, detail=f"Rez is not available: {e}")

    # Check if the function is async
    if asyncio.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    else:
        return cast(F, sync_wrapper)


# Commonly used Rez imports with lazy loading
class RezAPI:
    """Lazy-loaded Rez API access."""

    @property
    def packages(self) -> Any:
        """Access to rez.packages module."""
        return safe_rez_import("rez.packages")

    @property
    def iter_packages(self) -> Any:
        """rez.packages.iter_packages function."""
        return safe_rez_import("rez.packages", "iter_packages")

    @property
    def iter_package_families(self) -> Any:
        """rez.packages.iter_package_families function."""
        return safe_rez_import("rez.packages", "iter_package_families")

    @property
    def get_package(self) -> Any:
        """rez.packages.get_package function."""
        return safe_rez_import("rez.packages", "get_package")

    @property
    def get_developer_package(self) -> Any:
        """rez.packages.get_developer_package function."""
        return safe_rez_import("rez.packages", "get_developer_package")

    @property
    def ResolvedContext(self) -> Any:  # noqa: N802
        """rez.resolved_context.ResolvedContext class."""
        return safe_rez_import("rez.resolved_context", "ResolvedContext")

    @property
    def ResolverStatus(self) -> Any:  # noqa: N802
        """rez.resolver.ResolverStatus enum."""
        return safe_rez_import("rez.resolver", "ResolverStatus")

    @property
    def package_repository_manager(self) -> Any:
        """rez.package_repository.package_repository_manager."""
        return safe_rez_import("rez.package_repository", "package_repository_manager")

    @property
    def create_build_process(self) -> Any:
        """rez.build_process.create_build_process function."""
        return safe_rez_import("rez.build_process", "create_build_process")

    @property
    def get_build_process_types(self) -> Any:
        """rez.build_process.get_build_process_types function."""
        return safe_rez_import("rez.build_process", "get_build_process_types")

    @property
    def create_release_from_path(self) -> Any:
        """rez.release_vcs.create_release_from_path function."""
        return safe_rez_import("rez.release_vcs", "create_release_from_path")

    @property
    def get_shell_class(self) -> Any:
        """rez.shells.get_shell_class function."""
        return safe_rez_import("rez.shells", "get_shell_class")

    @property
    def Version(self) -> Any:  # noqa: N802
        """rez.version.Version class."""
        return safe_rez_import("rez.version", "Version")

    @property
    def Requirement(self) -> Any:  # noqa: N802
        """rez.version.Requirement class."""
        return safe_rez_import("rez.version", "Requirement")

    def create_version(self, version_str: str) -> Any:
        """Create a Version object from string."""
        Version = self.Version  # noqa: N806
        return Version(version_str)

    def create_requirement(self, requirement_str: str) -> Any:
        """Create a Requirement object from string."""
        Requirement = self.Requirement  # noqa: N806
        return Requirement(requirement_str)

    def create_resolved_context(
        self, package_requests: Any = None, **kwargs: Any
    ) -> Any:
        """Create a ResolvedContext object."""
        ResolvedContext = self.ResolvedContext  # noqa: N806
        return ResolvedContext(package_requests, **kwargs)

    @property
    def get_shell_types(self) -> Any:
        """rez.shells.get_shell_types function."""
        return safe_rez_import("rez.shells", "get_shell_types")


# Global instance for easy access
rez_api = RezAPI()


def clear_import_cache() -> None:
    """Clear the import cache. Useful for testing or configuration changes."""
    global _import_cache
    _import_cache.clear()
    logger.info("Rez import cache cleared")


def get_cache_info() -> dict[str, Any]:
    """Get information about the current import cache."""
    return {
        "cached_imports": list(_import_cache.keys()),
        "cache_size": len(_import_cache),
    }
