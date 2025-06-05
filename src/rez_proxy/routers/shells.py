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
        from rez.shells import create_shell

        shell = create_shell(shell_name)
        return {
            "name": shell.name(),
            "executable": shell.executable,
            "file_extension": getattr(shell, 'file_extension', None),
            "startup_capabilities": getattr(shell, 'startup_capabilities', {}),
        }
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
