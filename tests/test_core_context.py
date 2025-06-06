"""
Test core context management functionality.
"""

from unittest.mock import patch

from rez_proxy.core.context import ContextManager, context_manager
from rez_proxy.models.schemas import ClientContext, PlatformInfo, ServiceMode


class TestContextManager:
    """Test ContextManager class."""

    def test_init(self):
        """Test ContextManager initialization."""
        cm = ContextManager()
        assert cm._local_platform_info is None

    def test_set_get_current_context(self, mock_client_context):
        """Test setting and getting current context."""
        cm = ContextManager()

        # Initially no context
        assert cm.get_current_context() is None

        # Set context
        cm.set_current_context(mock_client_context)
        assert cm.get_current_context() == mock_client_context

    @patch("rez_proxy.core.context.ContextManager._detect_local_platform")
    def test_get_local_platform_info_cached(self, mock_detect):
        """Test local platform info caching."""
        cm = ContextManager()
        mock_platform = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )
        mock_detect.return_value = mock_platform

        # First call should fetch and cache
        result1 = cm.get_local_platform_info()
        assert result1 == mock_platform
        assert mock_detect.call_count == 1

        # Second call should use cache
        result2 = cm.get_local_platform_info()
        assert result2 == mock_platform
        assert mock_detect.call_count == 1  # Still 1, not called again

    def test_get_effective_platform_info_with_context(self, mock_client_context):
        """Test effective platform info when context is set."""
        cm = ContextManager()
        cm.set_current_context(mock_client_context)

        result = cm.get_effective_platform_info()
        assert result == mock_client_context.platform_info

    @patch("rez_proxy.core.context.ContextManager._detect_local_platform")
    def test_get_effective_platform_info_without_context(self, mock_detect):
        """Test effective platform info when no context is set."""
        cm = ContextManager()
        mock_platform = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )
        mock_detect.return_value = mock_platform

        result = cm.get_effective_platform_info()
        assert result == mock_platform
        mock_detect.assert_called_once()

    def test_is_remote_mode_with_context(self, mock_client_context):
        """Test remote mode detection with context."""
        cm = ContextManager()

        # Test local mode
        mock_client_context.service_mode = ServiceMode.LOCAL
        cm.set_current_context(mock_client_context)
        assert not cm.is_remote_mode()

        # Test remote mode
        mock_client_context.service_mode = ServiceMode.REMOTE
        assert cm.is_remote_mode()

    def test_is_remote_mode_without_context(self):
        """Test remote mode detection without context."""
        cm = ContextManager()
        # Should default to local mode when no context
        assert not cm.is_remote_mode()

    def test_create_context(self):
        """Test context creation."""
        cm = ContextManager()

        context = cm.create_context(
            client_id="test-client",
            session_id="test-session",
            service_mode=ServiceMode.REMOTE,
        )

        assert context.client_id == "test-client"
        assert context.session_id == "test-session"
        assert context.service_mode == ServiceMode.REMOTE
        assert context.request_id is not None

    def test_global_context_manager(self):
        """Test global context manager instance."""
        # Should be the same instance
        assert context_manager is not None
        assert isinstance(context_manager, ContextManager)


class TestContextManagerIntegration:
    """Integration tests for context manager."""

    @patch("rez_proxy.core.context.ContextManager._detect_local_platform")
    def test_full_workflow(self, mock_detect):
        """Test complete workflow with context management."""
        mock_platform = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )
        mock_detect.return_value = mock_platform

        cm = ContextManager()

        # Start with no context - should use local platform
        platform1 = cm.get_effective_platform_info()
        assert platform1 == mock_platform
        assert not cm.is_remote_mode()

        # Set remote context
        remote_platform = PlatformInfo(
            platform="windows",
            arch="x86_64",
            os="windows-10",
            python_version="3.8.0",
            rez_version="3.1.0",
        )
        remote_context = ClientContext(
            client_id="remote-client",
            session_id="remote-session",
            platform_info=remote_platform,
            service_mode=ServiceMode.REMOTE,
            user_agent="test-agent",
            request_id="test-request",
        )

        cm.set_current_context(remote_context)

        # Now should use remote platform
        platform2 = cm.get_effective_platform_info()
        assert platform2 == remote_platform
        assert cm.is_remote_mode()

    def test_clear_current_context(self):
        """Test clearing current context."""
        cm = ContextManager()

        # Set a context
        context = cm.create_context(
            client_id="test-client", service_mode=ServiceMode.LOCAL
        )
        cm.set_current_context(context)
        assert cm.get_current_context() is not None

        # Clear context
        cm.clear_current_context()
        assert cm.get_current_context() is None

    @patch("rez_proxy.core.context.ContextManager._detect_local_platform")
    def test_detect_local_platform_caching(self, mock_detect):
        """Test that local platform detection is cached."""
        mock_platform = PlatformInfo(
            platform="linux", arch="x86_64", os="ubuntu-20.04", python_version="3.9.0"
        )
        mock_detect.return_value = mock_platform

        cm = ContextManager()

        # Multiple calls should only detect once
        result1 = cm.get_local_platform_info()
        result2 = cm.get_local_platform_info()
        result3 = cm.get_local_platform_info()

        assert result1 == result2 == result3 == mock_platform
        assert mock_detect.call_count == 1

    def test_context_with_minimal_info(self):
        """Test context creation with minimal information."""
        cm = ContextManager()

        context = cm.create_context(service_mode=ServiceMode.LOCAL)

        assert context.service_mode == ServiceMode.LOCAL
        assert context.request_id is not None
        assert context.client_id is None
        assert context.session_id is not None  # session_id is auto-generated
        assert (
            context.platform_info is not None
        )  # platform_info is auto-detected in LOCAL mode

    def test_context_with_all_info(self):
        """Test context creation with all information."""
        cm = ContextManager()

        platform_info = PlatformInfo(
            platform="linux", arch="x86_64", os="ubuntu-20.04", python_version="3.9.0"
        )

        context = cm.create_context(
            client_id="test-client",
            session_id="test-session",
            platform_info=platform_info,
            service_mode=ServiceMode.REMOTE,
            user_agent="test-agent",
            request_id="custom-request-id",
        )

        assert context.client_id == "test-client"
        assert context.session_id == "test-session"
        assert context.platform_info == platform_info
        assert context.service_mode == ServiceMode.REMOTE
        assert context.user_agent == "test-agent"
        assert context.request_id == "custom-request-id"
