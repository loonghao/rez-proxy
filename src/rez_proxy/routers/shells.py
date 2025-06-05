"""
Shell API endpoints.
"""


from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def list_shells():
    """List available shells."""
    try:
        from rez.shells import get_shell_types

        shell_types = get_shell_types()
        return {"shells": shell_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list shells: {e}")


@router.get("/{shell_name}")
async def get_shell_info(shell_name: str):
    """Get information about a specific shell."""
    try:
        from rez.shells import get_shell_class

        shell_class = get_shell_class(shell_name)

        # Get class-level information
        info = {
            "name": shell_class.name(),
            "executable": getattr(shell_class, 'executable', None),
            "file_extension": getattr(shell_class, 'file_extension', lambda: None)(),
            "is_available": shell_class.is_available(),
        }

        # Try to get executable filepath
        try:
            info["executable_filepath"] = shell_class.executable_filepath()
        except Exception:
            info["executable_filepath"] = None

        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shell info: {e}")


@router.post("/{shell_name}/spawn")
async def spawn_shell(shell_name: str, env_id: str):
    """Spawn a shell in the specified environment."""
    # This would require more complex implementation with WebSocket or similar
    # for interactive shell sessions
    raise HTTPException(
        status_code=501,
        detail="Interactive shell spawning not implemented yet"
    )
