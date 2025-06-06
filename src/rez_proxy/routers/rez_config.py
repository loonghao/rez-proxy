"""
Rez configuration API endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi_versioning import version
from pydantic import BaseModel

router = APIRouter()


class ConfigUpdateRequest(BaseModel):
    """Configuration update request."""

    key: str
    value: Any


@router.get("/")
@version(1)
async def get_rez_config() -> dict[str, Any]:
    """Get complete Rez configuration."""
    try:
        from rez.config import config

        # Get all configuration as dict
        config_dict = {}
        for key in dir(config):
            if not key.startswith("_"):
                try:
                    value = getattr(config, key)
                    # Only include serializable values
                    if isinstance(
                        value, str | int | float | bool | list | dict | type(None)
                    ):
                        config_dict[key] = value
                except (AttributeError, TypeError, ValueError):
                    # Skip config attributes that can't be serialized
                    continue  # nosec B112

        return {"config": config_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Rez config: {e}")


@router.get("/key/{config_key}")
async def get_config_value(config_key: str) -> dict[str, Any]:
    """Get a specific configuration value."""
    try:
        from rez.config import config

        if not hasattr(config, config_key):
            raise HTTPException(
                status_code=404, detail=f"Configuration key '{config_key}' not found"
            )

        value = getattr(config, config_key)

        return {
            "key": config_key,
            "value": value,
            "type": type(value).__name__,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config value: {e}")


@router.get("/packages-path")
@version(1)
async def get_packages_paths() -> dict[str, Any]:
    """Get configured package paths."""
    try:
        from rez.config import config

        paths_info = {
            "packages_path": getattr(config, "packages_path", []),
            "local_packages_path": getattr(config, "local_packages_path", None),
            "release_packages_path": getattr(config, "release_packages_path", []),
        }

        return paths_info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get packages paths: {e}"
        )


@router.get("/platform-info")
async def get_platform_info() -> dict[str, Any]:
    """Get platform and system information."""
    try:
        from rez.config import config
        from rez.system import system

        platform_info = {
            "platform": str(system.platform),
            "arch": str(system.arch),
            "os": str(system.os),
            "python_version": system.python_version,
            "rez_version": getattr(config, "rez_version", "unknown"),
        }

        return platform_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get platform info: {e}")


@router.get("/plugins")
async def get_plugin_info() -> dict[str, Any]:
    """Get information about loaded plugins."""
    try:
        from rez.plugin_managers import plugin_manager

        plugins_info = {}

        # Get all plugin types
        plugin_types = [
            "package_repository",
            "shell",
            "build_system",
            "release_hook",
            "command",
        ]

        for plugin_type in plugin_types:
            try:
                plugins = plugin_manager.get_plugins(plugin_type)
                plugins_info[plugin_type] = list(plugins.keys()) if plugins else []
            except Exception:
                plugins_info[plugin_type] = []

        return {"plugins": plugins_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin info: {e}")


@router.get("/environment-vars")
async def get_environment_variables() -> dict[str, Any]:
    """Get Rez-related environment variables."""
    try:
        import os

        rez_env_vars = {}
        for key, value in os.environ.items():
            if key.startswith("REZ_"):
                rez_env_vars[key] = value

        return {"environment_variables": rez_env_vars}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get environment variables: {e}"
        )


@router.get("/cache-info")
async def get_cache_info() -> dict[str, Any]:
    """Get package cache information."""
    try:
        from rez.config import config

        cache_info = {
            "package_cache_disabled": getattr(
                config, "disable_rez_1_compatibility", False
            ),
            "package_cache_max_variant_logs": getattr(
                config, "package_cache_max_variant_logs", 0
            ),
            "package_cache_same_device": getattr(
                config, "package_cache_same_device", True
            ),
            "package_cache_log_days": getattr(config, "package_cache_log_days", 7),
        }

        return cache_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache info: {e}")


@router.get("/build-info")
async def get_build_info() -> dict[str, Any]:
    """Get build system information."""
    try:
        from rez.config import config

        build_info = {
            "build_directory": getattr(config, "build_directory", None),
            "build_thread_count": getattr(
                config, "build_thread_count", "logical_cores"
            ),
            "cmake_build_args": getattr(config, "cmake_build_args", []),
            "make_build_args": getattr(config, "make_build_args", []),
        }

        return build_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get build info: {e}")


@router.get("/validation")
async def validate_config() -> dict[str, Any]:
    """Validate current Rez configuration."""
    try:
        import os

        from rez.config import config

        validation_results: dict[str, Any] = {
            "valid": True,
            "warnings": [],
            "errors": [],
        }
        warnings: list[str] = validation_results["warnings"]
        errors: list[str] = validation_results["errors"]

        # Check packages paths
        packages_path = getattr(config, "packages_path", [])
        if not packages_path:
            warnings.append("No packages_path configured")
        else:
            for path in packages_path:
                if not os.path.exists(path):
                    warnings.append(f"Packages path does not exist: {path}")
                elif not os.access(path, os.R_OK):
                    errors.append(f"No read access to packages path: {path}")

        # Check local packages path
        local_path = getattr(config, "local_packages_path", None)
        if local_path and not os.path.exists(local_path):
            warnings.append(f"Local packages path does not exist: {local_path}")

        if errors:
            validation_results["valid"] = False

        return validation_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate config: {e}")
