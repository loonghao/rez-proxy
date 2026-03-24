"""
Comprehensive tests for rez_proxy.middleware.context module.

This test suite aims to achieve high coverage for the context middleware,
testing all major functionality including environment management, context
extraction, service mode determination, and platform info handling.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers, QueryParams

from rez_proxy.middleware.context import (
    ContextMiddleware,
    EnvironmentManager,
    environment_manager,
)
from rez_proxy.models.schemas import ClientContext, PlatformInfo, ServiceMode


class TestEnvironmentManager:
    """Test the EnvironmentManager class."""

    def test_get_environment_with_rez_vars(self):
        """Test getting environment with REZ variables present."""
        with patch.dict(
            os.environ,
            {
                "REZ_PACKAGES_PATH": "/path/to/packages",
                "REZ_CONFIG_FILE": "/path/to/config.py",
                "PATH": "/usr/bin:/bin",
                "HOME": "/home/user",
                "IRRELEVANT_VAR": "should_not_appear",
            },
        ):
            manager = EnvironmentManager()
            env = manager.get_environment()

            assert "REZ_PACKAGES_PATH" in env
            assert env["REZ_PACKAGES_PATH"] == "/path/to/packages"
            assert "REZ_CONFIG_FILE" in env
            assert "PATH" in env
            assert "HOME" in env
            assert "IRRELEVANT_VAR" not in env

    def test_get_environment_empty(self):
        """Test getting environment with no relevant variables."""
        with patch.dict(os.environ, {}, clear=True):
            manager = EnvironmentManager()
            env = manager.get_environment()

            assert env == {}

    def test_get_environment_partial(self):
        """Test getting environment with only some relevant variables."""
        with patch.dict(
            os.environ,
            {
                "REZ_PACKAGES_PATH": "/packages",
                "USER": "testuser",
                "UNRELATED": "value",
            },
            clear=True,
        ):
            manager = EnvironmentManager()
            env = manager.get_environment()

            assert len(env) == 2
            assert env["REZ_PACKAGES_PATH"] == "/packages"
            assert env["USER"] == "testuser"
            assert "UNRELATED" not in env

    def test_global_environment_manager(self):
        """Test the global environment manager instance."""
        assert environment_manager is not None
        assert isinstance(environment_manager, EnvironmentManager)


class TestContextMiddleware:
    """Test the ContextMiddleware class."""

    @pytest.fixture
    def middleware(self):
        """Create a ContextMiddleware instance."""
        return ContextMiddleware(app=MagicMock())

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.headers = Headers({})
        request.query_params = QueryParams("")
        request.state = MagicMock()
        return request

    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        response = MagicMock(spec=Response)
        response.headers = {}
        return response

    @pytest.mark.asyncio
    async def test_dispatch_basic_flow(self, middleware, mock_request, mock_response):
        """Test basic dispatch flow."""
        call_next = AsyncMock(return_value=mock_response)

        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm
            mock_context = MagicMock(spec=ClientContext)
            mock_context.request_id = "test-request-id"
            mock_context.session_id = "test-session-id"
            mock_context.service_mode = ServiceMode.LOCAL
            mock_context.platform_info = None
            mock_cm.create_context.return_value = mock_context

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            mock_cm.set_current_context.assert_called_once_with(mock_context)
            call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_with_exception(self, middleware, mock_request):
        """Test dispatch when call_next raises an exception."""
        call_next = AsyncMock(side_effect=Exception("Test error"))

        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm
            mock_context = MagicMock(spec=ClientContext)
            mock_cm.create_context.return_value = mock_context

            with pytest.raises(Exception, match="Test error"):
                await middleware.dispatch(mock_request, call_next)

            # Context should still be set even if exception occurs
            mock_cm.set_current_context.assert_called_once_with(mock_context)

    def test_extract_context_from_request_basic(self, middleware, mock_request):
        """Test extracting context from request with basic headers."""
        mock_request.headers = Headers(
            {
                "X-Client-ID": "test-client",
                "X-Session-ID": "test-session",
                "User-Agent": "test-agent",
                "X-Request-ID": "test-request",
            }
        )

        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm
            mock_context = MagicMock(spec=ClientContext)
            mock_cm.create_context.return_value = mock_context

            result = middleware._extract_context_from_request(mock_request)

            assert result == mock_context
            mock_cm.create_context.assert_called_once()
            call_args = mock_cm.create_context.call_args
            assert call_args.kwargs["client_id"] == "test-client"
            assert call_args.kwargs["session_id"] == "test-session"
            assert call_args.kwargs["user_agent"] == "test-agent"
            assert call_args.kwargs["request_id"] == "test-request"

    def test_extract_context_from_request_no_headers(self, middleware, mock_request):
        """Test extracting context from request with no headers."""
        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm
            mock_context = MagicMock(spec=ClientContext)
            mock_cm.create_context.return_value = mock_context

            result = middleware._extract_context_from_request(mock_request)

            assert result == mock_context
            call_args = mock_cm.create_context.call_args
            assert call_args.kwargs["client_id"] is None
            assert call_args.kwargs["session_id"] is None
            assert call_args.kwargs["user_agent"] is None
            assert call_args.kwargs["request_id"] is None

    def test_determine_service_mode_explicit_header_local(
        self, middleware, mock_request
    ):
        """Test service mode determination with explicit local header."""
        mock_request.headers = Headers({"X-Service-Mode": "local"})

        result = middleware._determine_service_mode(mock_request)

        assert result == ServiceMode.LOCAL

    def test_determine_service_mode_explicit_header_remote(
        self, middleware, mock_request
    ):
        """Test service mode determination with explicit remote header."""
        mock_request.headers = Headers({"X-Service-Mode": "remote"})

        result = middleware._determine_service_mode(mock_request)

        assert result == ServiceMode.REMOTE

    def test_determine_service_mode_invalid_header(self, middleware, mock_request):
        """Test service mode determination with invalid header value."""
        mock_request.headers = Headers({"X-Service-Mode": "invalid"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)

            # Should fall back to host-based detection
            assert result == ServiceMode.REMOTE  # Default when no local indicators

    def test_determine_service_mode_platform_info_present(
        self, middleware, mock_request
    ):
        """Test service mode determination when platform info is present."""
        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=True
        ):
            result = middleware._determine_service_mode(mock_request)

            assert result == ServiceMode.REMOTE

    def test_determine_service_mode_localhost_host(self, middleware, mock_request):
        """Test service mode determination with localhost host."""
        mock_request.headers = Headers({"Host": "localhost:8000"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)

            assert result == ServiceMode.LOCAL

    def test_determine_service_mode_127_host(self, middleware, mock_request):
        """Test service mode determination with 127.0.0.1 host."""
        mock_request.headers = Headers({"Host": "127.0.0.1:8000"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)

            assert result == ServiceMode.LOCAL

    def test_determine_service_mode_origin_localhost(self, middleware, mock_request):
        """Test service mode determination with localhost origin."""
        mock_request.headers = Headers({"Origin": "http://localhost:3000"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)

            assert result == ServiceMode.LOCAL

    def test_determine_service_mode_remote_default(self, middleware, mock_request):
        """Test service mode determination defaults to remote."""
        mock_request.headers = Headers({"Host": "example.com"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)

            assert result == ServiceMode.REMOTE

    def test_has_platform_info_in_request_true(self, middleware, mock_request):
        """Test platform info detection when headers are present."""
        mock_request.headers = Headers(
            {"X-Platform": "linux-x86_64", "X-Platform-Arch": "x86_64"}
        )

        result = middleware._has_platform_info_in_request(mock_request)

        assert result is True

    def test_has_platform_info_in_request_false(self, middleware, mock_request):
        """Test platform info detection when no headers are present."""
        result = middleware._has_platform_info_in_request(mock_request)

        assert result is False

    def test_extract_platform_info_from_headers(self, middleware, mock_request):
        """Test extracting platform info from headers."""
        with patch.object(
            middleware, "_extract_platform_from_headers"
        ) as mock_extract_headers:
            mock_platform = MagicMock(spec=PlatformInfo)
            mock_extract_headers.return_value = mock_platform

            result = middleware._extract_platform_info(mock_request)

            assert result == mock_platform
            mock_extract_headers.assert_called_once_with(mock_request)

    def test_extract_platform_info_from_query(self, middleware, mock_request):
        """Test extracting platform info from query when headers fail."""
        with patch.object(
            middleware, "_extract_platform_from_headers", return_value=None
        ):
            with patch.object(
                middleware, "_extract_platform_from_query"
            ) as mock_extract_query:
                mock_platform = MagicMock(spec=PlatformInfo)
                mock_extract_query.return_value = mock_platform

                result = middleware._extract_platform_info(mock_request)

                assert result == mock_platform
                mock_extract_query.assert_called_once_with(mock_request)

    def test_extract_platform_info_none(self, middleware, mock_request):
        """Test extracting platform info when none available."""
        with patch.object(
            middleware, "_extract_platform_from_headers", return_value=None
        ):
            with patch.object(
                middleware, "_extract_platform_from_query", return_value=None
            ):
                result = middleware._extract_platform_info(mock_request)

                assert result is None

    def test_extract_platform_from_headers_complete(self, middleware, mock_request):
        """Test extracting platform info from headers with all required fields."""
        mock_request.headers = Headers(
            {
                "X-Platform": "linux-x86_64",
                "X-Platform-Arch": "x86_64",
                "X-Platform-OS": "linux",
                "X-Python-Version": "3.9.0",
                "X-Rez-Version": "2.114.0",
            }
        )

        result = middleware._extract_platform_from_headers(mock_request)

        assert result is not None
        assert result.platform == "linux-x86_64"
        assert result.arch == "x86_64"
        assert result.os == "linux"
        assert result.python_version == "3.9.0"
        assert result.rez_version == "2.114.0"

    def test_extract_platform_from_headers_minimal(self, middleware, mock_request):
        """Test extracting platform info from headers with minimal required fields."""
        mock_request.headers = Headers(
            {
                "X-Platform": "linux-x86_64",
                "X-Platform-Arch": "x86_64",
                "X-Platform-OS": "linux",
                "X-Python-Version": "3.9.0",
                # X-Rez-Version is optional
            }
        )

        result = middleware._extract_platform_from_headers(mock_request)

        assert result is not None
        assert result.platform == "linux-x86_64"
        assert result.arch == "x86_64"
        assert result.os == "linux"
        assert result.python_version == "3.9.0"
        assert result.rez_version is None

    def test_extract_platform_from_headers_incomplete(self, middleware, mock_request):
        """Test extracting platform info from headers with missing required fields."""
        mock_request.headers = Headers(
            {
                "X-Platform": "linux-x86_64",
                "X-Platform-Arch": "x86_64",
                # Missing X-Platform-OS and X-Python-Version
            }
        )

        result = middleware._extract_platform_from_headers(mock_request)

        assert result is None

    def test_extract_platform_from_query_complete(self, middleware, mock_request):
        """Test extracting platform info from query parameters with all fields."""
        mock_request.query_params = QueryParams(
            "platform=linux-x86_64&arch=x86_64&os=linux&python_version=3.9.0&rez_version=2.114.0"
        )

        result = middleware._extract_platform_from_query(mock_request)

        assert result is not None
        assert result.platform == "linux-x86_64"
        assert result.arch == "x86_64"
        assert result.os == "linux"
        assert result.python_version == "3.9.0"
        assert result.rez_version == "2.114.0"

    def test_extract_platform_from_query_minimal(self, middleware, mock_request):
        """Test extracting platform info from query parameters with minimal fields."""
        mock_request.query_params = QueryParams(
            "platform=linux-x86_64&arch=x86_64&os=linux&python_version=3.9.0"
        )

        result = middleware._extract_platform_from_query(mock_request)

        assert result is not None
        assert result.platform == "linux-x86_64"
        assert result.rez_version is None

    def test_extract_platform_from_query_incomplete(self, middleware, mock_request):
        """Test extracting platform info from query parameters with missing fields."""
        mock_request.query_params = QueryParams("platform=linux-x86_64&arch=x86_64")

        result = middleware._extract_platform_from_query(mock_request)

        assert result is None

    def test_add_context_headers_complete(self, middleware, mock_response):
        """Test adding context headers with complete context."""
        mock_context = MagicMock(spec=ClientContext)
        mock_context.request_id = "test-request-123"
        mock_context.session_id = "test-session-456"
        mock_context.service_mode = ServiceMode.REMOTE

        mock_platform = MagicMock(spec=PlatformInfo)
        mock_platform.platform = "linux-x86_64"
        mock_platform.arch = "x86_64"
        mock_context.platform_info = mock_platform

        middleware._add_context_headers(mock_response, mock_context)

        assert mock_response.headers["X-Request-ID"] == "test-request-123"
        assert mock_response.headers["X-Session-ID"] == "test-session-456"
        assert mock_response.headers["X-Service-Mode"] == "remote"
        assert mock_response.headers["X-Platform-Used"] == "linux-x86_64"
        assert mock_response.headers["X-Arch-Used"] == "x86_64"

    def test_add_context_headers_minimal(self, middleware, mock_response):
        """Test adding context headers with minimal context."""
        mock_context = MagicMock(spec=ClientContext)
        mock_context.request_id = None
        mock_context.session_id = None
        mock_context.service_mode = ServiceMode.LOCAL
        mock_context.platform_info = None

        middleware._add_context_headers(mock_response, mock_context)

        # Only service mode should be added
        assert "X-Request-ID" not in mock_response.headers
        assert "X-Session-ID" not in mock_response.headers
        assert mock_response.headers["X-Service-Mode"] == "local"
        assert "X-Platform-Used" not in mock_response.headers
        assert "X-Arch-Used" not in mock_response.headers

    def test_add_context_headers_partial(self, middleware, mock_response):
        """Test adding context headers with partial context."""
        mock_context = MagicMock(spec=ClientContext)
        mock_context.request_id = "test-request-789"
        mock_context.session_id = None
        mock_context.service_mode = ServiceMode.REMOTE
        mock_context.platform_info = None

        middleware._add_context_headers(mock_response, mock_context)

        assert mock_response.headers["X-Request-ID"] == "test-request-789"
        assert "X-Session-ID" not in mock_response.headers
        assert mock_response.headers["X-Service-Mode"] == "remote"
        assert "X-Platform-Used" not in mock_response.headers


class TestContextMiddlewareIntegration:
    """Integration tests for ContextMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create a ContextMiddleware instance."""
        return ContextMiddleware(app=MagicMock())

    @pytest.mark.asyncio
    async def test_full_request_cycle_local_mode(self, middleware):
        """Test full request cycle in local mode."""
        # Create a realistic request
        request = MagicMock(spec=Request)
        request.headers = Headers(
            {
                "Host": "localhost:8000",
                "User-Agent": "test-client/1.0",
                "X-Request-ID": "req-123",
            }
        )
        request.query_params = QueryParams("")
        request.state = MagicMock()

        response = MagicMock(spec=Response)
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm

            # Create a realistic context
            mock_context = MagicMock(spec=ClientContext)
            mock_context.request_id = "req-123"
            mock_context.session_id = None
            mock_context.service_mode = ServiceMode.LOCAL
            mock_context.platform_info = None
            mock_cm.create_context.return_value = mock_context

            result = await middleware.dispatch(request, call_next)

            # Verify context was set
            mock_cm.set_current_context.assert_called_once_with(mock_context)

            # Verify request state was updated
            assert request.state.client_context == mock_context

            # Verify response headers were added
            assert response.headers["X-Request-ID"] == "req-123"
            assert response.headers["X-Service-Mode"] == "local"

            assert result == response

    @pytest.mark.asyncio
    async def test_full_request_cycle_remote_mode_with_platform(self, middleware):
        """Test full request cycle in remote mode with platform info."""
        request = MagicMock(spec=Request)
        request.headers = Headers(
            {
                "Host": "api.example.com",
                "X-Platform": "linux-x86_64",
                "X-Platform-Arch": "x86_64",
                "X-Platform-OS": "linux",
                "X-Python-Version": "3.9.0",
                "X-Client-ID": "client-456",
                "X-Session-ID": "session-789",
            }
        )
        request.query_params = QueryParams("")
        request.state = MagicMock()

        response = MagicMock(spec=Response)
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm

            # Create context with platform info
            mock_platform = MagicMock(spec=PlatformInfo)
            mock_platform.platform = "linux-x86_64"
            mock_platform.arch = "x86_64"

            mock_context = MagicMock(spec=ClientContext)
            mock_context.request_id = None
            mock_context.session_id = "session-789"
            mock_context.service_mode = ServiceMode.REMOTE
            mock_context.platform_info = mock_platform
            mock_cm.create_context.return_value = mock_context

            await middleware.dispatch(request, call_next)

            # Verify platform headers were added
            assert response.headers["X-Session-ID"] == "session-789"
            assert response.headers["X-Service-Mode"] == "remote"
            assert response.headers["X-Platform-Used"] == "linux-x86_64"
            assert response.headers["X-Arch-Used"] == "x86_64"
