"""
Shell API endpoints with context awareness.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi_versioning import version

from ..core.platform import ShellService

router = APIRouter()


@router.get("/")
@version(1)
async def list_shells(request: Request) -> dict[str, Any]:
    """List available shells with platform awareness."""
    try:
        service = ShellService()
        shells = service.get_available_shells()

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
