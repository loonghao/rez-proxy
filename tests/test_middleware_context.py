"""
Test middleware context functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request, Response

from rez_proxy.middleware.context import ContextMiddleware
from rez_proxy.models.schemas import ClientContext, ServiceMode


class TestContextMiddleware:
    """Test ContextMiddleware class."""

    def test_init(self):
        """Test ContextMiddleware initialization."""
        app = Mock()
        middleware = ContextMiddleware(app)
        assert middleware.app == app

    @pytest.mark.asyncio
    async def test_dispatch_with_context_headers(self):
        """Test middleware dispatch with context headers."""
        app = Mock()
        middleware = ContextMiddleware(app)

        # Mock request with context headers
        request = Mock(spec=Request)
        request.headers = {
            "X-Client-ID": "test-client",
            "X-Session-ID": "test-session",
            "X-Platform": "linux",
            "X-Arch": "x86_64",
            "X-OS": "ubuntu-20.04",
            "X-Python-Version": "3.9.0",
            "X-Rez-Version": "3.2.1",
            "X-Service-Mode": "remote",
            "User-Agent": "test-agent",
            "X-Request-ID": "test-request",
        }
        request.url.path = "/api/v1/test"

        # Mock call_next
        call_next = AsyncMock()
        mock_response = Mock(spec=Response)
        call_next.return_value = mock_response

        with patch(
            "rez_proxy.middleware.context.context_manager"
        ) as mock_context_manager:
            # Execute middleware
            result = await middleware.dispatch(request, call_next)

            # Verify context was set
            mock_context_manager.set_current_context.assert_called()
            context_call = mock_context_manager.set_current_context.call_args[0][0]

            assert isinstance(context_call, ClientContext)
            assert context_call.client_id == "test-client"
            assert context_call.session_id == "test-session"
            assert context_call.platform_info.platform == "linux"
            assert context_call.platform_info.arch == "x86_64"
            assert context_call.service_mode == ServiceMode.REMOTE

            # Verify call_next was called
            call_next.assert_called_once_with(request)

            # Verify context was cleared
            assert mock_context_manager.set_current_context.call_count == 2
            clear_call = mock_context_manager.set_current_context.call_args_list[1][0][
                0
            ]
            assert clear_call is None

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_dispatch_without_context_headers(self):
        """Test middleware dispatch without context headers."""
        app = Mock()
        middleware = ContextMiddleware(app)

        # Mock request without context headers
        request = Mock(spec=Request)
        request.headers = {}
        request.url.path = "/api/v1/test"

        # Mock call_next
        call_next = AsyncMock()
        mock_response = Mock(spec=Response)
        call_next.return_value = mock_response

        with patch(
            "rez_proxy.middleware.context.context_manager"
        ) as mock_context_manager:
            # Execute middleware
            result = await middleware.dispatch(request, call_next)

            # Verify context was not set (no headers)
            mock_context_manager.set_current_context.assert_not_called()

            # Verify call_next was called
            call_next.assert_called_once_with(request)

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_dispatch_partial_context_headers(self):
        """Test middleware dispatch with partial context headers."""
        app = Mock()
        middleware = ContextMiddleware(app)

        # Mock request with only some context headers
        request = Mock(spec=Request)
        request.headers = {
            "X-Client-ID": "test-client",
            "X-Platform": "linux",
            "X-Arch": "x86_64",
            # Missing other required headers
        }
        request.url.path = "/api/v1/test"

        # Mock call_next
        call_next = AsyncMock()
        mock_response = Mock(spec=Response)
        call_next.return_value = mock_response

        with patch(
            "rez_proxy.middleware.context.context_manager"
        ) as mock_context_manager:
            # Execute middleware
            result = await middleware.dispatch(request, call_next)

            # Verify context was not set (incomplete headers)
            mock_context_manager.set_current_context.assert_not_called()

            # Verify call_next was called
            call_next.assert_called_once_with(request)

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_dispatch_with_exception(self):
        """Test middleware dispatch when call_next raises exception."""
        app = Mock()
        middleware = ContextMiddleware(app)

        # Mock request with context headers
        request = Mock(spec=Request)
        request.headers = {
            "X-Client-ID": "test-client",
            "X-Session-ID": "test-session",
            "X-Platform": "linux",
            "X-Arch": "x86_64",
            "X-OS": "ubuntu-20.04",
            "X-Python-Version": "3.9.0",
            "X-Rez-Version": "3.2.1",
            "X-Service-Mode": "remote",
            "User-Agent": "test-agent",
            "X-Request-ID": "test-request",
        }
        request.url.path = "/api/v1/test"

        # Mock call_next to raise exception
        call_next = AsyncMock()
        call_next.side_effect = Exception("Test exception")

        with patch(
            "rez_proxy.middleware.context.context_manager"
        ) as mock_context_manager:
            # Execute middleware and expect exception
            with pytest.raises(Exception, match="Test exception"):
                await middleware.dispatch(request, call_next)

            # Verify context was set and then cleared even with exception
            assert mock_context_manager.set_current_context.call_count == 2

            # First call should set context
            context_call = mock_context_manager.set_current_context.call_args_list[0][
                0
            ][0]
            assert isinstance(context_call, ClientContext)

            # Second call should clear context
            clear_call = mock_context_manager.set_current_context.call_args_list[1][0][
                0
            ]
            assert clear_call is None

    @pytest.mark.asyncio
    async def test_dispatch_non_api_path(self):
        """Test middleware dispatch for non-API paths."""
        app = Mock()
        middleware = ContextMiddleware(app)

        # Mock request to non-API path
        request = Mock(spec=Request)
        request.headers = {
            "X-Client-ID": "test-client",
            "X-Platform": "linux",
        }
        request.url.path = "/docs"  # Non-API path

        # Mock call_next
        call_next = AsyncMock()
        mock_response = Mock(spec=Response)
        call_next.return_value = mock_response

        with patch(
            "rez_proxy.middleware.context.context_manager"
        ) as mock_context_manager:
            # Execute middleware
            result = await middleware.dispatch(request, call_next)

            # Verify context was not processed for non-API paths
            mock_context_manager.set_current_context.assert_not_called()

            # Verify call_next was called
            call_next.assert_called_once_with(request)

            assert result == mock_response

    def test_extract_client_context_complete(self):
        """Test extracting complete client context from headers."""
        middleware = ContextMiddleware(Mock())

        headers = {
            "X-Client-ID": "test-client",
            "X-Session-ID": "test-session",
            "X-Platform": "linux",
            "X-Arch": "x86_64",
            "X-OS": "ubuntu-20.04",
            "X-Python-Version": "3.9.0",
            "X-Rez-Version": "3.2.1",
            "X-Service-Mode": "remote",
            "User-Agent": "test-agent",
            "X-Request-ID": "test-request",
        }

        context = middleware._extract_client_context(headers)

        assert isinstance(context, ClientContext)
        assert context.client_id == "test-client"
        assert context.session_id == "test-session"
        assert context.platform_info.platform == "linux"
        assert context.platform_info.arch == "x86_64"
        assert context.platform_info.os == "ubuntu-20.04"
        assert context.platform_info.python_version == "3.9.0"
        assert context.platform_info.rez_version == "3.2.1"
        assert context.service_mode == ServiceMode.REMOTE
        assert context.user_agent == "test-agent"
        assert context.request_id == "test-request"

    def test_extract_client_context_incomplete(self):
        """Test extracting incomplete client context from headers."""
        middleware = ContextMiddleware(Mock())

        # Missing required headers
        headers = {
            "X-Client-ID": "test-client",
            "X-Platform": "linux",
            # Missing other required headers
        }

        context = middleware._extract_client_context(headers)
        assert context is None

    def test_extract_client_context_invalid_service_mode(self):
        """Test extracting client context with invalid service mode."""
        middleware = ContextMiddleware(Mock())

        headers = {
            "X-Client-ID": "test-client",
            "X-Session-ID": "test-session",
            "X-Platform": "linux",
            "X-Arch": "x86_64",
            "X-OS": "ubuntu-20.04",
            "X-Python-Version": "3.9.0",
            "X-Rez-Version": "3.2.1",
            "X-Service-Mode": "invalid-mode",  # Invalid mode
            "User-Agent": "test-agent",
            "X-Request-ID": "test-request",
        }

        context = middleware._extract_client_context(headers)
        # Should default to LOCAL mode for invalid values
        assert context.service_mode == ServiceMode.LOCAL
