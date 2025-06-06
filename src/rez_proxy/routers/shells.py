"""
Shell API endpoints with context awareness.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi_versioning import version

from ..core.platform import ShellService

router = APIRouter()


def _shell_to_info(shell_class: Any) -> dict[str, Any]:
    """Convert shell class to info dictionary."""
    try:
        info = {
            "name": shell_class.name(),
            "executable": getattr(shell_class, "executable", None),
            "file_extension": shell_class.file_extension(),
            "available": shell_class.is_available(),
            "executable_path": None,
            "description": getattr(shell_class, "__doc__", None),
        }

        try:
            info["executable_path"] = shell_class.executable_filepath()
        except Exception:
            info["executable_path"] = None

        return info
    except Exception:
        # Handle exceptions gracefully
        return {
            "name": getattr(shell_class, "executable", "unknown"),
            "executable": getattr(shell_class, "executable", None),
            "file_extension": ".sh",
            "available": False,
            "executable_path": None,
            "description": None,
        }


@router.get("/")
@version(1)
async def list_shells(
    request: Request,
    available_only: bool = Query(
        default=False, description="Filter to only available shells"
    ),
) -> dict[str, Any]:
    """List available shells with platform awareness."""
    try:
        service = ShellService()
        shells = service.get_available_shells()

        # Apply available_only filter if requested
        if available_only:
            shells = [shell for shell in shells if shell.get("available", False)]

        from ..core.context import get_current_context

        context = get_current_context()

        return {
            "shells": shells,
            "service_mode": context.service_mode.value if context else "local",
            "platform": service.get_platform_info().platform,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list shells: {e}")


@router.get("/{shell_name}")
@version(1)
async def get_shell_info(shell_name: str, request: Request) -> dict[str, Any]:
    """Get information about a specific shell with platform awareness."""
    try:
        service = ShellService()
        shell_info = service.get_shell_info(shell_name)

        from ..core.context import get_current_context

        context = get_current_context()
        shell_info["service_mode"] = context.service_mode.value if context else "local"
        shell_info["platform"] = service.get_platform_info().platform

        return shell_info
    except HTTPException:
        # Re-raise HTTPException (like 404) as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shell info: {e}")


@router.post("/{shell_name}/spawn")
async def spawn_shell(shell_name: str, env_id: str) -> None:
    """Spawn a shell in the specified environment."""
    # This would require more complex implementation with WebSocket or similar
    # for interactive shell sessions
    raise HTTPException(
        status_code=501, detail="Interactive shell spawning not implemented yet"
    )
