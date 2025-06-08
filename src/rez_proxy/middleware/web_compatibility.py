"""
Web compatibility middleware for rez-proxy.

Provides middleware to automatically handle web environment compatibility checks
and add appropriate headers to responses.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from rez_proxy.core.web_compatibility import (
    CompatibilityLevel,
    WebCompatibilityError,
    get_api_compatibility_info,
    create_web_compatibility_response,
)
from rez_proxy.core.web_detector import get_web_detector
from rez_proxy.models.schemas import ServiceMode


class WebCompatibilityMiddleware(BaseHTTPMiddleware):
    """Middleware to handle web environment compatibility."""
    
    def __init__(self, app, add_compatibility_headers: bool = True):
        super().__init__(app)
        self.add_compatibility_headers = add_compatibility_headers
        self.web_detector = get_web_detector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add compatibility information."""
        start_time = time.time()
        
        # Get service mode
        service_mode = self.web_detector.get_service_mode()
        
        try:
            # Call the next middleware/endpoint
            response = await call_next(request)
            
            # Add compatibility headers if enabled
            if self.add_compatibility_headers:
                self._add_compatibility_headers(response, service_mode, start_time)
            
            return response
            
        except WebCompatibilityError as exc:
            # Handle web compatibility errors
            return create_web_compatibility_response(
                message=exc.detail,
                compatibility_level=exc.compatibility_level,
                alternatives=exc.alternatives,
                documentation_url=exc.documentation_url,
            )
        
        except Exception as exc:
            # For other exceptions, still add headers if it's a Response
            response = await self._handle_exception(request, exc, call_next)
            if self.add_compatibility_headers and hasattr(response, 'headers'):
                self._add_compatibility_headers(response, service_mode, start_time)
            return response
    
    def _add_compatibility_headers(
        self, 
        response: Response, 
        service_mode: ServiceMode, 
        start_time: float
    ) -> None:
        """Add compatibility headers to response."""
        # Add service mode header
        response.headers["X-Rez-Proxy-Service-Mode"] = service_mode.value
        
        # Add processing time
        processing_time = time.time() - start_time
        response.headers["X-Rez-Proxy-Processing-Time"] = f"{processing_time:.3f}s"
        
        # Add web environment detection status
        if service_mode == ServiceMode.WEB:
            response.headers["X-Rez-Proxy-Web-Environment"] = "detected"
        else:
            response.headers["X-Rez-Proxy-Web-Environment"] = "not-detected"
        
        # Add compatibility information if available
        # Note: This would require access to the endpoint function to get compatibility info
        # For now, we'll add a general header
        response.headers["X-Rez-Proxy-Compatibility-Info"] = "available"
    
    async def _handle_exception(
        self, 
        request: Request, 
        exc: Exception, 
        call_next: Callable
    ) -> Response:
        """Handle exceptions that occur during request processing."""
        # Re-raise the exception to let FastAPI handle it
        raise exc


class WebCompatibilityInfoMiddleware(BaseHTTPMiddleware):
    """Middleware to add web compatibility information to API responses."""
    
    def __init__(self, app, include_compatibility_info: bool = True):
        super().__init__(app)
        self.include_compatibility_info = include_compatibility_info
        self.web_detector = get_web_detector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add compatibility information to responses."""
        response = await call_next(request)
        
        # Only add info for JSON responses and if enabled
        if (self.include_compatibility_info and 
            hasattr(response, 'headers') and
            response.headers.get('content-type', '').startswith('application/json')):
            
            # Add compatibility headers
            service_mode = self.web_detector.get_service_mode()
            
            # Add service mode information
            response.headers["X-API-Service-Mode"] = service_mode.value
            
            # Add web compatibility status
            if service_mode == ServiceMode.WEB:
                response.headers["X-API-Web-Compatible"] = "check-endpoint-docs"
            else:
                response.headers["X-API-Web-Compatible"] = "full"
            
            # Add documentation link
            response.headers["X-API-Compatibility-Docs"] = "/docs/web-environment-compatibility"
        
        return response


def create_web_compatibility_middleware(
    add_headers: bool = True,
    include_info: bool = True,
) -> list[tuple[type, dict]]:
    """
    Create web compatibility middleware stack.
    
    Args:
        add_headers: Whether to add compatibility headers
        include_info: Whether to include compatibility information
        
    Returns:
        List of middleware classes and their configurations
    """
    middleware_stack = []
    
    if add_headers:
        middleware_stack.append((
            WebCompatibilityMiddleware,
            {"add_compatibility_headers": True}
        ))
    
    if include_info:
        middleware_stack.append((
            WebCompatibilityInfoMiddleware,
            {"include_compatibility_info": True}
        ))
    
    return middleware_stack


# Utility functions for manual compatibility checking

def check_endpoint_compatibility(endpoint_func: Callable) -> dict:
    """
    Check the web compatibility of an endpoint function.
    
    Args:
        endpoint_func: The endpoint function to check
        
    Returns:
        Dictionary with compatibility information
    """
    compatibility_info = get_api_compatibility_info(endpoint_func)
    
    if compatibility_info is None:
        return {
            "compatible": True,
            "level": CompatibilityLevel.FULL.value,
            "reason": "No compatibility restrictions defined",
            "alternatives": [],
            "documentation_url": None,
        }
    
    return {
        "compatible": compatibility_info["level"] != CompatibilityLevel.INCOMPATIBLE,
        "level": compatibility_info["level"].value,
        "reason": compatibility_info.get("reason"),
        "alternatives": compatibility_info.get("alternatives", []),
        "documentation_url": compatibility_info.get("documentation_url"),
        "allow_override": compatibility_info.get("allow_override", False),
    }


def get_web_environment_summary() -> dict:
    """
    Get a summary of the current web environment detection status.
    
    Returns:
        Dictionary with web environment information
    """
    detector = get_web_detector()
    
    return {
        "is_web_environment": detector.is_web_environment(),
        "service_mode": detector.get_service_mode().value,
        "detection_details": detector.get_detection_details(),
        "compatibility_middleware_available": True,
    }


# Exception handler registration helper
def register_web_compatibility_handlers(app):
    """
    Register web compatibility exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    from rez_proxy.core.web_compatibility import web_compatibility_exception_handler
    
    app.add_exception_handler(WebCompatibilityError, web_compatibility_exception_handler)
