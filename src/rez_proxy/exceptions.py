"""
Custom exceptions and error handling for Rez Proxy.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class RezProxyException(Exception):
    """Base exception for Rez Proxy."""

    def __init__(
        self,
        message: str,
        error_code: str = "REZ_PROXY_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class RezConfigurationError(RezProxyException):
    """Rez configuration related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="REZ_CONFIG_ERROR",
            details=details,
        )


class RezPackageError(RezProxyException):
    """Package related errors."""

    def __init__(self, message: str, package_name: str = "", details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if package_name:
            details["package_name"] = package_name
        super().__init__(
            message=message,
            error_code="REZ_PACKAGE_ERROR",
            details=details,
        )


class RezResolverError(RezProxyException):
    """Resolver related errors."""

    def __init__(self, message: str, packages: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if packages:
            details["packages"] = packages
        super().__init__(
            message=message,
            error_code="REZ_RESOLVER_ERROR",
            details=details,
        )


class RezEnvironmentError(RezProxyException):
    """Environment related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="REZ_ENVIRONMENT_ERROR",
            details=details,
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response."""
    error_data = {
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        }
    }
    return JSONResponse(status_code=status_code, content=error_data)


def handle_rez_exception(e: Exception, context: str = "") -> HTTPException:
    """Convert Rez exceptions to appropriate HTTP exceptions with detailed error information."""
    
    # Handle known Rez configuration errors
    if "Unrecognised package repository plugin" in str(e):
        plugin_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
        raise RezConfigurationError(
            message=f"Invalid package repository plugin '{plugin_name}' in Rez configuration",
            details={
                "original_error": str(e),
                "context": context,
                "solution": "Check your Rez configuration file and ensure all repository plugins are properly installed",
                "common_plugins": ["filesystem", "memory", "rezgui"],
            }
        )
    
    # Handle package not found errors
    if "No such package" in str(e) or "Package not found" in str(e):
        raise RezPackageError(
            message=f"Package not found: {str(e)}",
            details={
                "original_error": str(e),
                "context": context,
                "solution": "Check package name and version, ensure package exists in configured repositories",
            }
        )
    
    # Handle resolver errors
    if "resolve" in str(e).lower() or "conflict" in str(e).lower():
        raise RezResolverError(
            message=f"Package resolution failed: {str(e)}",
            details={
                "original_error": str(e),
                "context": context,
                "solution": "Check package requirements and dependencies for conflicts",
            }
        )
    
    # Handle environment errors
    if "environment" in str(e).lower() or "context" in str(e).lower():
        raise RezEnvironmentError(
            message=f"Environment operation failed: {str(e)}",
            details={
                "original_error": str(e),
                "context": context,
                "solution": "Check environment configuration and package availability",
            }
        )
    
    # Generic Rez error
    raise RezProxyException(
        message=f"Rez operation failed: {str(e)}",
        error_code="REZ_OPERATION_ERROR",
        details={
            "original_error": str(e),
            "context": context,
            "type": type(e).__name__,
        }
    )


async def rez_proxy_exception_handler(request: Request, exc: RezProxyException) -> JSONResponse:
    """Global exception handler for RezProxyException."""
    return create_error_response(
        status_code=500,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Enhanced HTTP exception handler."""
    return create_error_response(
        status_code=exc.status_code,
        message=exc.detail,
        error_code="HTTP_ERROR",
        details={"status_code": exc.status_code},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """General exception handler for unexpected errors."""
    return create_error_response(
        status_code=500,
        message="An unexpected error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        details={
            "type": type(exc).__name__,
            "message": str(exc),
        },
    )
