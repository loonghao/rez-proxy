"""
Web environment compatibility management for rez-proxy APIs.

Provides decorators and utilities to manage API compatibility in web environments.
"""

import functools
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from rez_proxy.core.web_detector import get_web_detector
from rez_proxy.models.schemas import ServiceMode


class CompatibilityLevel(Enum):
    """API compatibility levels for web environments."""
    
    FULL = "full"  # Fully compatible with web environments
    PARTIAL = "partial"  # Partially compatible, some limitations
    LIMITED = "limited"  # Limited compatibility, major restrictions
    INCOMPATIBLE = "incompatible"  # Not compatible with web environments


class WebCompatibilityError(HTTPException):
    """Exception raised when API is not compatible with web environment."""
    
    def __init__(
        self,
        detail: str,
        compatibility_level: CompatibilityLevel,
        alternatives: Optional[List[str]] = None,
        documentation_url: Optional[str] = None,
    ):
        super().__init__(status_code=501, detail=detail)
        self.compatibility_level = compatibility_level
        self.alternatives = alternatives or []
        self.documentation_url = documentation_url


def web_compatible(
    level: CompatibilityLevel,
    reason: Optional[str] = None,
    alternatives: Optional[List[str]] = None,
    documentation_url: Optional[str] = None,
    allow_override: bool = False,
) -> Callable:
    """
    Decorator to mark API endpoints with web environment compatibility level.
    
    Args:
        level: Compatibility level for web environments
        reason: Reason for compatibility level (used in error messages)
        alternatives: List of alternative approaches for web environments
        documentation_url: URL to documentation about web compatibility
        allow_override: Whether to allow override via environment variable
        
    Returns:
        Decorated function that checks web compatibility before execution
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Check if we're in a web environment
            detector = get_web_detector()
            service_mode = detector.get_service_mode()
            
            # Skip check for local mode
            if service_mode == ServiceMode.LOCAL:
                return await func(*args, **kwargs)
            
            # Check for override
            if allow_override:
                import os
                if os.environ.get("REZ_PROXY_FORCE_WEB_COMPATIBILITY", "").lower() in ("true", "1", "yes"):
                    return await func(*args, **kwargs)
            
            # Handle different compatibility levels
            if level == CompatibilityLevel.INCOMPATIBLE:
                error_detail = _create_incompatible_error_detail(
                    func.__name__, reason, alternatives, documentation_url
                )
                raise WebCompatibilityError(
                    detail=error_detail,
                    compatibility_level=level,
                    alternatives=alternatives,
                    documentation_url=documentation_url,
                )
            
            elif level == CompatibilityLevel.LIMITED:
                # Add warning headers but allow execution
                response = await func(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers["X-Web-Compatibility"] = "limited"
                    response.headers["X-Web-Compatibility-Reason"] = reason or "Limited web compatibility"
                return response
            
            elif level == CompatibilityLevel.PARTIAL:
                # Add info headers
                response = await func(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers["X-Web-Compatibility"] = "partial"
                    if reason:
                        response.headers["X-Web-Compatibility-Info"] = reason
                return response
            
            # FULL compatibility - no restrictions
            return await func(*args, **kwargs)
        
        # Store compatibility metadata on the function
        wrapper._web_compatibility = {
            "level": level,
            "reason": reason,
            "alternatives": alternatives,
            "documentation_url": documentation_url,
            "allow_override": allow_override,
        }
        
        return wrapper
    return decorator


def _create_incompatible_error_detail(
    func_name: str,
    reason: Optional[str],
    alternatives: Optional[List[str]],
    documentation_url: Optional[str],
) -> str:
    """Create detailed error message for incompatible APIs."""
    detail_parts = [
        f"API endpoint '{func_name}' is not compatible with web environments."
    ]
    
    if reason:
        detail_parts.append(f"Reason: {reason}")
    
    if alternatives:
        detail_parts.append("Alternatives:")
        for alt in alternatives:
            detail_parts.append(f"  - {alt}")
    
    if documentation_url:
        detail_parts.append(f"Documentation: {documentation_url}")
    
    detail_parts.append(
        "This API requires local file system access, system permissions, or local Rez installation."
    )
    
    return " ".join(detail_parts)


def get_api_compatibility_info(func: Callable) -> Optional[Dict[str, Any]]:
    """Get compatibility information for a decorated function."""
    return getattr(func, '_web_compatibility', None)


def create_web_compatibility_response(
    message: str,
    compatibility_level: CompatibilityLevel,
    alternatives: Optional[List[str]] = None,
    documentation_url: Optional[str] = None,
) -> JSONResponse:
    """Create a standardized web compatibility response."""
    content = {
        "error": "web_compatibility_issue",
        "message": message,
        "compatibility_level": compatibility_level.value,
        "service_mode": get_web_detector().get_service_mode().value,
        "timestamp": _get_current_timestamp(),
    }
    
    if alternatives:
        content["alternatives"] = alternatives
    
    if documentation_url:
        content["documentation_url"] = documentation_url
    
    # Determine appropriate status code based on compatibility level
    status_code = {
        CompatibilityLevel.INCOMPATIBLE: 501,  # Not Implemented
        CompatibilityLevel.LIMITED: 206,       # Partial Content
        CompatibilityLevel.PARTIAL: 200,       # OK with warnings
        CompatibilityLevel.FULL: 200,          # OK
    }.get(compatibility_level, 501)
    
    return JSONResponse(content=content, status_code=status_code)


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


# Predefined compatibility decorators for common use cases
def web_incompatible(
    reason: str,
    alternatives: Optional[List[str]] = None,
    documentation_url: Optional[str] = None,
) -> Callable:
    """Decorator for APIs that are completely incompatible with web environments."""
    return web_compatible(
        level=CompatibilityLevel.INCOMPATIBLE,
        reason=reason,
        alternatives=alternatives,
        documentation_url=documentation_url,
    )


def web_limited(
    reason: str,
    alternatives: Optional[List[str]] = None,
) -> Callable:
    """Decorator for APIs with limited web compatibility."""
    return web_compatible(
        level=CompatibilityLevel.LIMITED,
        reason=reason,
        alternatives=alternatives,
    )


def web_partial(
    reason: Optional[str] = None,
) -> Callable:
    """Decorator for APIs with partial web compatibility."""
    return web_compatible(
        level=CompatibilityLevel.PARTIAL,
        reason=reason,
    )


def web_full() -> Callable:
    """Decorator for APIs with full web compatibility."""
    return web_compatible(level=CompatibilityLevel.FULL)


# Exception handler for web compatibility errors
async def web_compatibility_exception_handler(request: Request, exc: WebCompatibilityError) -> JSONResponse:
    """Handle web compatibility exceptions with detailed error responses."""
    return create_web_compatibility_response(
        message=exc.detail,
        compatibility_level=exc.compatibility_level,
        alternatives=exc.alternatives,
        documentation_url=exc.documentation_url,
    )
