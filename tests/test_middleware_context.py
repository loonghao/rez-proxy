"""
Test middleware context functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from rez_proxy.middleware.context import ContextMiddleware
from rez_proxy.models.schemas import ClientContext, PlatformInfo, ServiceMode


class TestContextMiddleware:
    """Test ContextMiddleware class."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return ContextMiddleware(app=MagicMock())

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.headers = Headers({})
        request.query_params = {}
        request.state = MagicMock()
        return request

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        response = MagicMock(spec=Response)
        response.headers = {}
        return response

    @pytest.mark.asyncio
    async def test_dispatch_basic(self, middleware, mock_request, mock_response):
        """Test basic dispatch functionality."""
        call_next = AsyncMock(return_value=mock_response)

        with patch("rez_proxy.middleware.context.get_context_manager") as mock_get_cm:
            mock_cm = MagicMock()
            mock_get_cm.return_value = mock_cm

            # Create a proper mock context with all required attributes
            mock_context = MagicMock(spec=ClientContext)
            mock_context.request_id = "test-request-id"
            mock_context.session_id = "test-session-id"
            mock_context.service_mode = MagicMock()
            mock_context.service_mode.value = "local"
            mock_context.platform_info = None
            mock_cm.create_context.return_value = mock_context

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            mock_cm.set_current_context.assert_called_once()
            call_next.assert_called_once_with(mock_request)

    def test_extract_context_from_request_basic(self, middleware, mock_request):
        """Test basic context extraction."""
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
            mock_cm.create_context.assert_called_once_with(
                client_id="test-client",
                session_id="test-session",
                platform_info=None,
                service_mode=ServiceMode.REMOTE,
                user_agent="test-agent",
                request_id="test-request",
            )

    def test_determine_service_mode_explicit_header(self, middleware, mock_request):
        """Test service mode determination with explicit header."""
        mock_request.headers = Headers({"X-Service-Mode": "local"})

        result = middleware._determine_service_mode(mock_request)
        assert result == ServiceMode.LOCAL

    def test_determine_service_mode_invalid_header(self, middleware, mock_request):
        """Test service mode determination with invalid header."""
        mock_request.headers = Headers({"X-Service-Mode": "invalid"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)
            assert result == ServiceMode.REMOTE

    def test_determine_service_mode_platform_info(self, middleware, mock_request):
        """Test service mode determination with platform info."""
        mock_request.headers = Headers({})

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

    def test_determine_service_mode_localhost_origin(self, middleware, mock_request):
        """Test service mode determination with localhost origin."""
        mock_request.headers = Headers({"Origin": "http://localhost:3000"})

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

    def test_determine_service_mode_default_remote(self, middleware, mock_request):
        """Test service mode determination defaults to remote."""
        mock_request.headers = Headers({"Host": "example.com"})

        with patch.object(
            middleware, "_has_platform_info_in_request", return_value=False
        ):
            result = middleware._determine_service_mode(mock_request)
            assert result == ServiceMode.REMOTE

    def test_has_platform_info_in_request_true(self, middleware, mock_request):
        """Test platform info detection when present."""
        mock_request.headers = Headers({"X-Platform": "linux"})

        result = middleware._has_platform_info_in_request(mock_request)
        assert result is True

    def test_has_platform_info_in_request_false(self, middleware, mock_request):
        """Test platform info detection when absent."""
        mock_request.headers = Headers({})

        result = middleware._has_platform_info_in_request(mock_request)
        assert result is False

    def test_extract_platform_info_from_headers(self, middleware, mock_request):
        """Test platform info extraction from headers."""
        mock_request.headers = Headers(
            {
                "X-Platform": "linux",
                "X-Platform-Arch": "x86_64",
                "X-Platform-OS": "ubuntu-20.04",
                "X-Python-Version": "3.9.0",
                "X-Rez-Version": "3.2.1",
            }
        )
        mock_request.query_params = {}

        result = middleware._extract_platform_info(mock_request)

        assert result is not None
        assert result.platform == "linux"
        assert result.arch == "x86_64"
        assert result.os == "ubuntu-20.04"
        assert result.python_version == "3.9.0"
        assert result.rez_version == "3.2.1"

    def test_extract_platform_info_from_query(self, middleware, mock_request):
        """Test platform info extraction from query parameters."""
        mock_request.headers = Headers({})
        mock_request.query_params = {
            "platform": "windows",
            "arch": "x86_64",
            "os": "windows-10",
            "python_version": "3.8.0",
        }

        result = middleware._extract_platform_info(mock_request)

        assert result is not None
        assert result.platform == "windows"
        assert result.arch == "x86_64"
        assert result.os == "windows-10"
        assert result.python_version == "3.8.0"
        assert result.rez_version is None

    def test_extract_platform_info_incomplete_headers(self, middleware, mock_request):
        """Test platform info extraction with incomplete headers."""
        mock_request.headers = Headers(
            {
                "X-Platform": "linux",
                "X-Platform-Arch": "x86_64",
                # Missing required fields
            }
        )
        mock_request.query_params = {}

        result = middleware._extract_platform_info(mock_request)
        assert result is None

    def test_extract_platform_info_none(self, middleware, mock_request):
        """Test platform info extraction when no info available."""
        mock_request.headers = Headers({})
        mock_request.query_params = {}

        result = middleware._extract_platform_info(mock_request)
        assert result is None

    def test_add_context_headers(self, middleware, mock_response):
        """Test adding context headers to response."""
        context = ClientContext(
            client_id="test-client",
            session_id="test-session",
            service_mode=ServiceMode.LOCAL,
            request_id="test-request",
            platform_info=PlatformInfo(
                platform="linux",
                arch="x86_64",
                os="ubuntu-20.04",
                python_version="3.9.0",
            ),
        )

        middleware._add_context_headers(mock_response, context)

        assert mock_response.headers["X-Request-ID"] == "test-request"
        assert mock_response.headers["X-Session-ID"] == "test-session"
        assert mock_response.headers["X-Service-Mode"] == "local"
        assert mock_response.headers["X-Platform-Used"] == "linux"
        assert mock_response.headers["X-Arch-Used"] == "x86_64"

    def test_add_context_headers_minimal(self, middleware, mock_response):
        """Test adding context headers with minimal context."""
        context = ClientContext(service_mode=ServiceMode.REMOTE)

        middleware._add_context_headers(mock_response, context)

        assert mock_response.headers["X-Service-Mode"] == "remote"
        assert "X-Request-ID" not in mock_response.headers
        assert "X-Session-ID" not in mock_response.headers
        assert "X-Platform-Used" not in mock_response.headers
