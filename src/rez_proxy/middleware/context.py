"""
Context middleware for rez-proxy.

Handles client context detection and management for each request.
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from rez_proxy.core.context import get_context_manager
from rez_proxy.models.schemas import ClientContext, PlatformInfo, ServiceMode


class EnvironmentManager:
    """Manages environment information for requests."""

    def get_environment(self) -> dict[str, str]:
        """Get current environment information."""
        import os

        # Return relevant environment variables for rez-proxy
        env_vars = {}

        # Common environment variables that might be relevant
        relevant_vars = [
            "REZ_PACKAGES_PATH",
            "REZ_LOCAL_PACKAGES_PATH",
            "REZ_RELEASE_PACKAGES_PATH",
            "REZ_CONFIG_FILE",
            "REZ_TMPDIR",
            "PATH",
            "PYTHONPATH",
            "HOME",
            "USER",
            "USERNAME",
        ]

        for var in relevant_vars:
            value = os.environ.get(var)
            if value is not None:
                env_vars[var] = value

        return env_vars


# Global environment manager instance
environment_manager = EnvironmentManager()


class ContextMiddleware(BaseHTTPMiddleware):
    """Middleware to handle client context for each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and set up context."""
        context_manager = get_context_manager()

        # Extract context information from request
        client_context = self._extract_context_from_request(request)

        # Set context for this request
        context_manager.set_current_context(client_context)

        # Add context info to request state for debugging
        request.state.client_context = client_context

        try:
            # Process the request
            response: Response = await call_next(request)

            # Add context headers to response
            self._add_context_headers(response, client_context)

            return response
        finally:
            # Clean up context (optional, as contextvars are request-scoped)
            pass

    def _extract_context_from_request(self, request: Request) -> ClientContext:
        """Extract client context from request headers and body."""
        context_manager = get_context_manager()

        # Extract headers
        client_id = request.headers.get("X-Client-ID")
        session_id = request.headers.get("X-Session-ID")
        user_agent = request.headers.get("User-Agent")
        request_id = request.headers.get("X-Request-ID")

        # Determine service mode
        service_mode = self._determine_service_mode(request)

        # Extract platform info if provided
        platform_info = self._extract_platform_info(request)

        return context_manager.create_context(
            client_id=client_id,
            session_id=session_id,
            platform_info=platform_info,
            service_mode=service_mode,
            user_agent=user_agent,
            request_id=request_id,
        )

    def _determine_service_mode(self, request: Request) -> ServiceMode:
        """Determine if this is a local or remote service call."""
        # Check explicit header
        mode_header = request.headers.get("X-Service-Mode")
        if mode_header:
            try:
                return ServiceMode(mode_header.lower())
            except ValueError:
                pass

        # Check if platform info is provided (indicates remote mode)
        if self._has_platform_info_in_request(request):
            return ServiceMode.REMOTE

        # Check host/origin to determine if it's local
        host = request.headers.get("Host", "")
        origin = request.headers.get("Origin", "")

        # Consider localhost, 127.0.0.1, and local IPs as local mode
        # Note: 0.0.0.0 is included for development purposes only
        local_indicators = ["localhost", "127.0.0.1", "0.0.0.0"]  # nosec B104

        if any(indicator in host for indicator in local_indicators):
            return ServiceMode.LOCAL

        if origin and any(indicator in origin for indicator in local_indicators):
            return ServiceMode.LOCAL

        # Default to remote mode for safety
        return ServiceMode.REMOTE

    def _has_platform_info_in_request(self, request: Request) -> bool:
        """Check if request contains platform information."""
        # Check headers
        platform_headers = [
            "X-Platform",
            "X-Platform-Arch",
            "X-Platform-OS",
            "X-Python-Version",
            "X-Rez-Version",
        ]

        return any(header in request.headers for header in platform_headers)

    def _extract_platform_info(self, request: Request) -> PlatformInfo | None:
        """Extract platform information from request."""
        # Try to get from headers first
        platform_info = self._extract_platform_from_headers(request)
        if platform_info:
            return platform_info

        # Try to get from query parameters
        platform_info = self._extract_platform_from_query(request)
        if platform_info:
            return platform_info

        return None

    def _extract_platform_from_headers(self, request: Request) -> PlatformInfo | None:
        """Extract platform info from request headers."""
        platform = request.headers.get("X-Platform")
        arch = request.headers.get("X-Platform-Arch")
        os_name = request.headers.get("X-Platform-OS")
        python_version = request.headers.get("X-Python-Version")
        rez_version = request.headers.get("X-Rez-Version")

        # All required fields must be present
        if platform and arch and os_name and python_version:
            return PlatformInfo(
                platform=platform,
                arch=arch,
                os=os_name,
                python_version=python_version,
                rez_version=rez_version,
            )

        return None

    def _extract_platform_from_query(self, request: Request) -> PlatformInfo | None:
        """Extract platform info from query parameters."""
        query_params = request.query_params

        platform = query_params.get("platform")
        arch = query_params.get("arch")
        os_name = query_params.get("os")
        python_version = query_params.get("python_version")
        rez_version = query_params.get("rez_version")

        # All required fields must be present
        if platform and arch and os_name and python_version:
            return PlatformInfo(
                platform=platform,
                arch=arch,
                os=os_name,
                python_version=python_version,
                rez_version=rez_version,
            )

        return None

    def _add_context_headers(self, response: Response, context: ClientContext) -> None:
        """Add context information to response headers."""
        if context.request_id:
            response.headers["X-Request-ID"] = context.request_id

        if context.session_id:
            response.headers["X-Session-ID"] = context.session_id

        response.headers["X-Service-Mode"] = context.service_mode.value

        # Add platform info if available
        if context.platform_info:
            response.headers["X-Platform-Used"] = context.platform_info.platform
            response.headers["X-Arch-Used"] = context.platform_info.arch
