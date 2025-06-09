"""
Configuration management API endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi_versioning import version
from pydantic import BaseModel

from rez_proxy.config import (
    get_config,
    get_config_manager,
    reload_config,
    save_config_to_file,
    set_rez_config_from_dict,
)

router = APIRouter()


class ConfigUpdateRequest(BaseModel):
    """Configuration update request."""

    config: dict[str, Any]
    save_to_file: bool = False
    file_path: str | None = None


class ConfigResponse(BaseModel):
    """Configuration response."""

    config: dict[str, Any]
    hot_reload_enabled: bool
    config_file_path: str


@router.get("/current", response_model=ConfigResponse)
@version(1)
async def get_current_config(request: Request) -> ConfigResponse:
    """Get current configuration."""
    try:
        config = get_config()

        # Convert to dict, excluding sensitive data
        config_dict = config.model_dump()

        # Remove sensitive fields
        sensitive_fields = ["api_key"]
        for field in sensitive_fields:
            config_dict.pop(field, None)

        return ConfigResponse(
            config=config_dict,
            hot_reload_enabled=config.enable_hot_reload,
            config_file_path=config.config_file_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {e}")


@router.post("/update")
@version(1)
async def update_config(request: ConfigUpdateRequest) -> dict[str, Any]:
    """Update configuration at runtime."""
    try:
        # Validate configuration keys
        current_config = get_config()
        valid_fields = set(current_config.__class__.model_fields.keys())

        invalid_fields = set(request.config.keys()) - valid_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration fields: {list(invalid_fields)}",
            )

        # Update configuration
        set_rez_config_from_dict(request.config)

        # Save to file if requested
        if request.save_to_file:
            new_config = get_config()
            save_config_to_file(new_config, request.file_path)

        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_fields": list(request.config.keys()),
            "saved_to_file": request.save_to_file,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update configuration: {e}"
        )


@router.post("/reload")
@version(1)
async def reload_configuration() -> dict[str, Any]:
    """Reload configuration from environment and files."""
    try:
        config = reload_config()

        return {
            "success": True,
            "message": "Configuration reloaded successfully",
            "hot_reload_enabled": config.enable_hot_reload,
            "config_file_path": config.config_file_path,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reload configuration: {e}"
        )


@router.post("/save")
@version(1)
async def save_config(file_path: str | None = None) -> dict[str, Any]:
    """Save current configuration to file."""
    try:
        config = get_config()
        save_config_to_file(config, file_path)

        actual_path = file_path or config.config_file_path

        return {
            "success": True,
            "message": f"Configuration saved to {actual_path}",
            "file_path": actual_path,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save configuration: {e}"
        )


@router.get("/hot-reload/status")
@version(1)
async def get_hot_reload_status() -> dict[str, Any]:
    """Get hot reload status and watched files."""
    try:
        config = get_config()
        config_manager = get_config_manager()

        return {
            "enabled": config.enable_hot_reload,
            "config_file_path": config.config_file_path,
            "watch_interval": config.config_watch_interval,
            "watched_files": list(config_manager._watched_files.keys()),
            "active_observers": len(config_manager._observers),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get hot reload status: {e}"
        )


@router.post("/hot-reload/enable")
@version(1)
async def enable_hot_reload() -> dict[str, Any]:
    """Enable hot reload functionality."""
    try:
        # Update environment variable
        import os

        os.environ["REZ_PROXY_API_ENABLE_HOT_RELOAD"] = "true"

        # Reload config to apply changes
        config = reload_config()

        return {
            "success": True,
            "message": "Hot reload enabled",
            "enabled": config.enable_hot_reload,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable hot reload: {e}")


@router.post("/hot-reload/disable")
@version(1)
async def disable_hot_reload() -> dict[str, Any]:
    """Disable hot reload functionality."""
    try:
        # Stop current hot reload
        config_manager = get_config_manager()
        config_manager.stop_hot_reload()

        # Update environment variable
        import os

        os.environ["REZ_PROXY_API_ENABLE_HOT_RELOAD"] = "false"

        # Reload config to apply changes
        config = reload_config()

        return {
            "success": True,
            "message": "Hot reload disabled",
            "enabled": config.enable_hot_reload,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to disable hot reload: {e}"
        )


@router.get("/schema")
@version(1)
async def get_config_schema() -> dict[str, Any]:
    """Get configuration schema for validation."""
    try:
        config = get_config()
        schema = config.model_json_schema()

        # Remove sensitive fields from schema
        if "properties" in schema:
            sensitive_fields = ["api_key"]
            for field in sensitive_fields:
                schema["properties"].pop(field, None)

        return {"schema": schema, "description": "Configuration schema for rez-proxy"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get configuration schema: {e}"
        )
