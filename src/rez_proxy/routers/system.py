"""
System API endpoints.
"""

from fastapi import APIRouter, HTTPException

from ..models.schemas import SystemStatus
from ..utils.rez_detector import detect_rez_installation, validate_rez_environment

router = APIRouter()


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status and Rez information."""
    try:
        rez_info = detect_rez_installation()
        warnings = validate_rez_environment()

        # Determine status based on warnings
        status = "healthy" if not warnings else "warning"

        return SystemStatus(
            status=status,
            rez_version=rez_info.get("version", "unknown"),
            python_version=rez_info.get("python_version", "unknown"),
            packages_path=rez_info.get("packages_path", []),
            active_environments=0,  # TODO: Implement environment tracking
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {e}")


@router.get("/config")
async def get_rez_config():
    """Get Rez configuration information."""
    try:
        rez_info = detect_rez_installation()
        return {
            "config_file": rez_info.get("config_file"),
            "packages_path": rez_info.get("packages_path"),
            "local_packages_path": rez_info.get("local_packages_path"),
            "release_packages_path": rez_info.get("release_packages_path"),
            "platform": rez_info.get("platform"),
            "arch": rez_info.get("arch"),
            "os": rez_info.get("os"),
            "environment_variables": rez_info.get("environment_variables", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Rez config: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rez-proxy"}
