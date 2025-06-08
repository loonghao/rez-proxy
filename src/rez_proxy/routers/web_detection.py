"""
Web environment detection API endpoints.

Provides endpoints for checking and managing web environment detection.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from rez_proxy.core.web_detector import get_web_detector, clear_detection_cache
from rez_proxy.models.schemas import ServiceMode
from rez_proxy.core.web_compatibility import CompatibilityLevel


class WebDetectionInfo(BaseModel):
    """Web environment detection information."""
    
    is_web_environment: bool = Field(..., description="Whether web environment is detected")
    service_mode: ServiceMode = Field(..., description="Detected service mode")
    forced_mode: ServiceMode | None = Field(None, description="Manually forced service mode")
    detection_methods: Dict[str, bool] = Field(..., description="Results of individual detection methods")
    relevant_env_vars: Dict[str, str] = Field(..., description="Relevant environment variables")


class ForceServiceModeRequest(BaseModel):
    """Request to force a specific service mode."""
    
    mode: ServiceMode = Field(..., description="Service mode to force")
    reason: str | None = Field(None, description="Reason for forcing this mode")


class WebDetectionResponse(BaseModel):
    """Response for web detection operations."""
    
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: WebDetectionInfo | None = Field(None, description="Detection information")


router = APIRouter()


@router.get(
    "/detection-info",
    response_model=WebDetectionResponse,
    summary="Get web environment detection information",
    description="Returns detailed information about web environment detection including detection methods and results.",
)
async def get_web_detection_info() -> WebDetectionResponse:
    """
    Get comprehensive web environment detection information.
    
    This endpoint provides detailed information about:
    - Whether the application is running in a web environment
    - The detected service mode (LOCAL, REMOTE, WEB)
    - Results of individual detection methods
    - Relevant environment variables
    - Any manual overrides in effect
    
    Returns:
        WebDetectionResponse: Detailed detection information
    """
    try:
        detector = get_web_detector()
        detection_info = detector.get_detection_info()
        
        web_info = WebDetectionInfo(
            is_web_environment=detection_info["is_web_environment"],
            service_mode=ServiceMode(detection_info["service_mode"]),
            forced_mode=ServiceMode(detection_info["forced_mode"]) if detection_info["forced_mode"] else None,
            detection_methods=detection_info["detection_methods"],
            relevant_env_vars=detection_info["relevant_env_vars"],
        )
        
        return WebDetectionResponse(
            success=True,
            message="Web detection information retrieved successfully",
            data=web_info,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get web detection information: {str(e)}",
        ) from e


@router.get(
    "/is-web-environment",
    response_model=Dict[str, Any],
    summary="Check if running in web environment",
    description="Simple endpoint to check if the application is detected to be running in a web environment.",
)
async def check_web_environment() -> Dict[str, Any]:
    """
    Check if the application is running in a web environment.
    
    This is a simple endpoint that returns just the web environment detection result
    without detailed information.
    
    Returns:
        Dict containing is_web_environment boolean and service_mode
    """
    try:
        detector = get_web_detector()
        
        return {
            "is_web_environment": detector.is_web_environment(),
            "service_mode": detector.get_service_mode().value,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check web environment: {str(e)}",
        ) from e


@router.post(
    "/force-service-mode",
    response_model=WebDetectionResponse,
    summary="Force a specific service mode",
    description="Manually override the detected service mode. This affects all subsequent requests until cleared.",
)
async def force_service_mode(request: ForceServiceModeRequest) -> WebDetectionResponse:
    """
    Force a specific service mode.
    
    This endpoint allows manual override of the detected service mode.
    The override affects all subsequent requests until it is cleared.
    
    Args:
        request: Service mode to force and optional reason
        
    Returns:
        WebDetectionResponse: Updated detection information
    """
    try:
        detector = get_web_detector()
        detector.force_service_mode(request.mode)
        
        # Get updated detection info
        detection_info = detector.get_detection_info()
        
        web_info = WebDetectionInfo(
            is_web_environment=detection_info["is_web_environment"],
            service_mode=ServiceMode(detection_info["service_mode"]),
            forced_mode=ServiceMode(detection_info["forced_mode"]) if detection_info["forced_mode"] else None,
            detection_methods=detection_info["detection_methods"],
            relevant_env_vars=detection_info["relevant_env_vars"],
        )
        
        message = f"Service mode forced to {request.mode.value}"
        if request.reason:
            message += f" (Reason: {request.reason})"
        
        return WebDetectionResponse(
            success=True,
            message=message,
            data=web_info,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force service mode: {str(e)}",
        ) from e


@router.delete(
    "/force-service-mode",
    response_model=WebDetectionResponse,
    summary="Clear forced service mode",
    description="Remove any manual service mode override and return to automatic detection.",
)
async def clear_forced_service_mode() -> WebDetectionResponse:
    """
    Clear any forced service mode override.
    
    This endpoint removes any manual service mode override and returns
    to automatic detection based on environment indicators.
    
    Returns:
        WebDetectionResponse: Updated detection information
    """
    try:
        detector = get_web_detector()
        detector.clear_forced_mode()
        
        # Get updated detection info
        detection_info = detector.get_detection_info()
        
        web_info = WebDetectionInfo(
            is_web_environment=detection_info["is_web_environment"],
            service_mode=ServiceMode(detection_info["service_mode"]),
            forced_mode=ServiceMode(detection_info["forced_mode"]) if detection_info["forced_mode"] else None,
            detection_methods=detection_info["detection_methods"],
            relevant_env_vars=detection_info["relevant_env_vars"],
        )
        
        return WebDetectionResponse(
            success=True,
            message="Forced service mode cleared, using automatic detection",
            data=web_info,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear forced service mode: {str(e)}",
        ) from e


@router.post(
    "/clear-cache",
    response_model=Dict[str, Any],
    summary="Clear detection cache",
    description="Clear the web environment detection cache to force re-detection on next request.",
)
async def clear_web_detection_cache() -> Dict[str, Any]:
    """
    Clear the web environment detection cache.
    
    This endpoint clears the detection cache, forcing the system to
    re-evaluate the environment on the next detection request.
    
    Returns:
        Dict with success status and message
    """
    try:
        clear_detection_cache()
        
        return {
            "success": True,
            "message": "Web detection cache cleared successfully",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear detection cache: {str(e)}",
        ) from e


@router.get(
    "/detection-methods",
    response_model=Dict[str, Any],
    summary="Get available detection methods",
    description="Returns information about available web environment detection methods.",
)
async def get_detection_methods() -> Dict[str, Any]:
    """
    Get information about available detection methods.
    
    Returns:
        Dict containing information about detection methods
    """
    return {
        "detection_methods": {
            "environment_variables": {
                "description": "Checks for web-related environment variables",
                "indicators": [
                    "REZ_PROXY_WEB_MODE",
                    "SERVER_SOFTWARE",
                    "HTTP_HOST",
                    "VERCEL",
                    "NETLIFY",
                    "HEROKU_APP_NAME",
                    "AWS_LAMBDA_FUNCTION_NAME",
                    "KUBERNETES_SERVICE_HOST",
                ],
            },
            "deployment_context": {
                "description": "Checks deployment paths and configuration files",
                "indicators": [
                    "Web deployment paths (/var/www, /app, /code)",
                    "Configuration files (Dockerfile, vercel.json, netlify.toml)",
                ],
            },
            "web_server_indicators": {
                "description": "Checks for web server process indicators",
                "indicators": [
                    "UWSGI_VERSION",
                    "GUNICORN_CMD_ARGS",
                    "UVICORN_HOST",
                    "HYPERCORN_CONFIG",
                ],
            },
            "container_environment": {
                "description": "Checks for container runtime indicators",
                "indicators": [
                    "/.dockerenv",
                    "/proc/1/cgroup",
                    "/var/run/secrets/kubernetes.io",
                    "/run/.containerenv",
                ],
            },
        },
        "override_options": {
            "REZ_PROXY_WEB_MODE": "Force web mode detection",
            "REZ_PROXY_FORCE_LOCAL": "Force local mode (overrides web detection)",
            "X-Service-Mode header": "Per-request service mode override",
        },
    }


@router.get(
    "/compatibility",
    response_model=Dict[str, Any],
    summary="Get web environment compatibility information",
    description="Returns comprehensive information about API compatibility in web environments.",
)
async def get_web_compatibility_info() -> Dict[str, Any]:
    """
    Get comprehensive web environment compatibility information.

    Returns detailed information about which APIs are compatible with
    web environments and what limitations exist.

    Returns:
        Dict containing compatibility information for all API groups
    """
    detector = get_web_detector()
    service_mode = detector.get_service_mode()

    # Define API compatibility matrix
    api_compatibility = {
        "packages": {
            "level": CompatibilityLevel.FULL.value,
            "description": "Package query APIs are fully compatible with web environments",
            "endpoints": ["/api/v1/packages/*"]
        },
        "environments": {
            "level": CompatibilityLevel.FULL.value,
            "description": "Environment resolution APIs are fully compatible",
            "endpoints": ["/api/v1/environments/*"]
        },
        "repositories": {
            "level": CompatibilityLevel.FULL.value,
            "description": "Repository query APIs are fully compatible",
            "endpoints": ["/api/v1/repositories/*"]
        },
        "versions": {
            "level": CompatibilityLevel.FULL.value,
            "description": "Version management APIs are fully compatible",
            "endpoints": ["/api/v1/versions/*"]
        },
        "resolver": {
            "level": CompatibilityLevel.FULL.value,
            "description": "Dependency resolution APIs are fully compatible",
            "endpoints": ["/api/v1/resolver/*"]
        },
        "system": {
            "level": CompatibilityLevel.PARTIAL.value,
            "description": "System information APIs have partial compatibility",
            "endpoints": ["/api/v1/system/*"],
            "limitations": ["Local Rez installation detection", "Local environment variables"]
        },
        "suites": {
            "level": CompatibilityLevel.LIMITED.value,
            "description": "Suite management has limited compatibility",
            "endpoints": ["/api/v1/suites/*/save"],
            "limitations": ["File system write operations"]
        },
        "build": {
            "level": CompatibilityLevel.INCOMPATIBLE.value,
            "description": "Build APIs are not compatible with web environments",
            "endpoints": ["/api/v1/build/*"],
            "limitations": ["Local file system access", "Build tool execution", "Source code access"]
        },
        "package_ops": {
            "level": CompatibilityLevel.INCOMPATIBLE.value,
            "description": "Package operation APIs are not compatible with web environments",
            "endpoints": ["/api/v1/package-ops/*"],
            "limitations": ["Package repository write access", "System permissions"]
        },
        "shells": {
            "level": CompatibilityLevel.INCOMPATIBLE.value,
            "description": "Shell management APIs are not compatible with web environments",
            "endpoints": ["/api/v1/shells/*"],
            "limitations": ["Process creation", "Interactive terminal access"]
        }
    }

    # Count compatibility levels
    compatibility_stats = {
        "total_api_groups": len(api_compatibility),
        "full_compatible": len([api for api in api_compatibility.values()
                               if api["level"] == CompatibilityLevel.FULL.value]),
        "partial_compatible": len([api for api in api_compatibility.values()
                                  if api["level"] == CompatibilityLevel.PARTIAL.value]),
        "limited_compatible": len([api for api in api_compatibility.values()
                                  if api["level"] == CompatibilityLevel.LIMITED.value]),
        "incompatible": len([api for api in api_compatibility.values()
                            if api["level"] == CompatibilityLevel.INCOMPATIBLE.value])
    }

    return {
        "web_environment": {
            "detected": detector.is_web_environment(),
            "service_mode": service_mode.value,
            "detection_details": detector.get_detection_details()
        },
        "compatibility_overview": {
            "overall_compatibility": "partial" if service_mode == ServiceMode.WEB else "full",
            "web_ready_apis": compatibility_stats["full_compatible"],
            "total_api_groups": compatibility_stats["total_api_groups"],
            "compatibility_percentage": round(
                (compatibility_stats["full_compatible"] / compatibility_stats["total_api_groups"]) * 100, 1
            )
        },
        "api_compatibility": api_compatibility,
        "compatibility_statistics": compatibility_stats,
        "recommendations": {
            "for_web_deployment": [
                "Use only 'full' and 'partial' compatible APIs",
                "Set up local rez-proxy instance for incompatible operations",
                "Consider using remote build services for package operations",
                "Use web-based terminals for shell access needs"
            ],
            "for_local_deployment": [
                "All APIs are available without restrictions",
                "Full file system and system access available",
                "Optimal for development and administrative tasks"
            ]
        },
        "documentation": {
            "compatibility_guide": "/docs/web-environment-compatibility",
            "api_reference": "/docs",
            "deployment_guide": "/docs/deployment"
        }
    }
