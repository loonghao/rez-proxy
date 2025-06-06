"""
Context management for rez-proxy.

Handles client context, platform information, and service mode detection.
"""

import uuid
from contextvars import ContextVar

from rez_proxy.models.schemas import ClientContext, PlatformInfo, ServiceMode

# Context variables for request-scoped data
current_client_context: ContextVar[ClientContext | None] = ContextVar(
    "current_client_context", default=None
)


class ContextManager:
    """Manages client context and platform information."""

    def __init__(self) -> None:
        self._local_platform_info: PlatformInfo | None = None

    def get_local_platform_info(self) -> PlatformInfo:
        """Get local platform information (cached)."""
        if self._local_platform_info is None:
            self._local_platform_info = self._detect_local_platform()
        return self._local_platform_info

    def _detect_local_platform(self) -> PlatformInfo:
        """Detect local platform information."""
        try:
            import sys

            from rez.config import config
            from rez.system import system

            return PlatformInfo(
                platform=str(system.platform),
                arch=str(system.arch),
                os=str(system.os),
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                rez_version=getattr(config, "rez_version", None),
            )
        except Exception:
            # Fallback to basic platform detection
            import platform
            import sys

            return PlatformInfo(
                platform=platform.system().lower(),
                arch=platform.machine(),
                os=f"{platform.system().lower()}-{platform.release()}",
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                rez_version=None,
            )

    def create_context(
        self,
        client_id: str | None = None,
        session_id: str | None = None,
        platform_info: PlatformInfo | None = None,
        service_mode: ServiceMode = ServiceMode.LOCAL,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> ClientContext:
        """Create a new client context."""

        # Generate IDs if not provided
        if request_id is None:
            request_id = str(uuid.uuid4())

        if session_id is None:
            session_id = str(uuid.uuid4())

        # Use local platform info if not provided and in local mode
        if platform_info is None and service_mode == ServiceMode.LOCAL:
            platform_info = self.get_local_platform_info()

        return ClientContext(
            client_id=client_id,
            session_id=session_id,
            platform_info=platform_info,
            service_mode=service_mode,
            user_agent=user_agent,
            request_id=request_id,
        )

    def get_current_context(self) -> ClientContext | None:
        """Get the current client context."""
        return current_client_context.get()

    def set_current_context(self, context: ClientContext) -> None:
        """Set the current client context."""
        current_client_context.set(context)

    def clear_current_context(self) -> None:
        """Clear the current client context."""
        current_client_context.set(None)

    def get_effective_platform_info(self) -> PlatformInfo:
        """Get effective platform information based on current context."""
        context = self.get_current_context()

        if context and context.platform_info:
            # Use client-provided platform info (remote mode)
            return context.platform_info
        else:
            # Use local platform info (local mode)
            return self.get_local_platform_info()

    def is_remote_mode(self) -> bool:
        """Check if current context is in remote mode."""
        context = self.get_current_context()
        return context is not None and context.service_mode == ServiceMode.REMOTE

    def is_local_mode(self) -> bool:
        """Check if current context is in local mode."""
        return not self.is_remote_mode()


# Global context manager instance
context_manager = ContextManager()


def get_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    return context_manager


def get_current_context() -> ClientContext | None:
    """Get the current client context."""
    return context_manager.get_current_context()


def get_effective_platform_info() -> PlatformInfo:
    """Get effective platform information for current request."""
    return context_manager.get_effective_platform_info()


def is_remote_mode() -> bool:
    """Check if current request is in remote mode."""
    return context_manager.is_remote_mode()


def is_local_mode() -> bool:
    """Check if current request is in local mode."""
    return context_manager.is_local_mode()
