"""
Test exception handling and custom exceptions.
"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from rez_proxy.exceptions import (
    RezConfigurationError,
    RezEnvironmentError,
    RezPackageError,
    RezProxyError,
    RezResolverError,
    create_error_response,
    general_exception_handler,
    handle_rez_exception,
    http_exception_handler,
    rez_proxy_exception_handler,
)


class TestRezProxyError:
    """Test the base RezProxyError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = RezProxyError("Test message")
        assert error.message == "Test message"
        assert error.error_code == "REZ_PROXY_ERROR"
        assert error.details == {}
        assert str(error) == "Test message"

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        details = {"key": "value", "number": 42}
        error = RezProxyError(
            message="Custom message", error_code="CUSTOM_ERROR", details=details
        )
        assert error.message == "Custom message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details

    def test_init_with_none_details(self):
        """Test initialization with None details."""
        error = RezProxyError("Test", details=None)
        assert error.details == {}


class TestRezConfigurationError:
    """Test RezConfigurationError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = RezConfigurationError("Config error")
        assert error.message == "Config error"
        assert error.error_code == "REZ_CONFIG_ERROR"
        assert error.details == {}

    def test_init_with_details(self):
        """Test initialization with details."""
        details = {"config_file": "/path/to/config"}
        error = RezConfigurationError("Config error", details=details)
        assert error.message == "Config error"
        assert error.error_code == "REZ_CONFIG_ERROR"
        assert error.details == details


class TestRezPackageError:
    """Test RezPackageError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = RezPackageError("Package error")
        assert error.message == "Package error"
        assert error.error_code == "REZ_PACKAGE_ERROR"
        assert error.details == {}

    def test_init_with_package_name(self):
        """Test initialization with package name."""
        error = RezPackageError("Package error", package_name="test_package")
        assert error.message == "Package error"
        assert error.error_code == "REZ_PACKAGE_ERROR"
        assert error.details == {"package_name": "test_package"}

    def test_init_with_package_name_and_details(self):
        """Test initialization with package name and additional details."""
        details = {"version": "1.0.0"}
        error = RezPackageError(
            "Package error", package_name="test_package", details=details
        )
        assert error.message == "Package error"
        assert error.error_code == "REZ_PACKAGE_ERROR"
        assert error.details == {"package_name": "test_package", "version": "1.0.0"}

    def test_init_with_empty_package_name(self):
        """Test initialization with empty package name."""
        error = RezPackageError("Package error", package_name="")
        assert error.details == {}


class TestRezResolverError:
    """Test RezResolverError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = RezResolverError("Resolver error")
        assert error.message == "Resolver error"
        assert error.error_code == "REZ_RESOLVER_ERROR"
        assert error.details == {}

    def test_init_with_packages(self):
        """Test initialization with packages."""
        packages = ["package1", "package2"]
        error = RezResolverError("Resolver error", packages=packages)
        assert error.message == "Resolver error"
        assert error.error_code == "REZ_RESOLVER_ERROR"
        assert error.details == {"packages": packages}

    def test_init_with_packages_and_details(self):
        """Test initialization with packages and additional details."""
        packages = ["package1", "package2"]
        details = {"platform": "linux"}
        error = RezResolverError("Resolver error", packages=packages, details=details)
        assert error.message == "Resolver error"
        assert error.error_code == "REZ_RESOLVER_ERROR"
        assert error.details == {"packages": packages, "platform": "linux"}

    def test_init_with_empty_packages(self):
        """Test initialization with empty packages list."""
        error = RezResolverError("Resolver error", packages=[])
        assert error.details == {}


class TestRezEnvironmentError:
    """Test RezEnvironmentError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = RezEnvironmentError("Environment error")
        assert error.message == "Environment error"
        assert error.error_code == "REZ_ENVIRONMENT_ERROR"
        assert error.details == {}

    def test_init_with_details(self):
        """Test initialization with details."""
        details = {"shell": "bash", "platform": "linux"}
        error = RezEnvironmentError("Environment error", details=details)
        assert error.message == "Environment error"
        assert error.error_code == "REZ_ENVIRONMENT_ERROR"
        assert error.details == details


class TestCreateErrorResponse:
    """Test create_error_response function."""

    def test_basic_error_response(self):
        """Test basic error response creation."""
        response = create_error_response(404, "Not found")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

        # Check response content structure by parsing the body
        import json

        response_data = json.loads(response.body.decode())
        assert "error" in response_data
        assert "code" in response_data["error"]
        assert "message" in response_data["error"]
        assert response_data["error"]["code"] == "UNKNOWN_ERROR"
        assert response_data["error"]["message"] == "Not found"
        assert response_data["error"]["details"] == {}
        assert (
            response.body.decode()
            == '{"error":{"code":"UNKNOWN_ERROR","message":"Not found","details":{}}}'
        )

    def test_error_response_with_all_params(self):
        """Test error response with all parameters."""
        details = {"field": "value", "number": 123}
        response = create_error_response(
            status_code=400,
            message="Validation error",
            error_code="VALIDATION_ERROR",
            details=details,
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_error_response_with_none_details(self):
        """Test error response with None details."""
        response = create_error_response(500, "Server error", details=None)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestHandleRezException:
    """Test handle_rez_exception function."""

    def test_handle_unrecognised_plugin_error(self):
        """Test handling of unrecognised package repository plugin error."""
        error = Exception("Unrecognised package repository plugin 'invalid_plugin'")

        with pytest.raises(RezConfigurationError) as exc_info:
            handle_rez_exception(error, "test context")

        assert (
            exc_info.value.message
            == "Invalid package repository plugin 'invalid_plugin' in Rez configuration"
        )
        assert exc_info.value.error_code == "REZ_CONFIG_ERROR"
        assert "original_error" in exc_info.value.details
        assert "context" in exc_info.value.details
        assert "solution" in exc_info.value.details
        assert "common_plugins" in exc_info.value.details

    def test_handle_unrecognised_plugin_error_no_quotes(self):
        """Test handling of unrecognised plugin error without quotes."""
        error = Exception("Unrecognised package repository plugin unknown")

        with pytest.raises(RezConfigurationError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "unknown" in exc_info.value.message

    def test_handle_package_not_found_error(self):
        """Test handling of package not found error."""
        error = Exception("No such package 'nonexistent'")

        with pytest.raises(RezPackageError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Package not found" in exc_info.value.message
        assert exc_info.value.error_code == "REZ_PACKAGE_ERROR"
        assert "original_error" in exc_info.value.details
        assert "context" in exc_info.value.details
        assert "solution" in exc_info.value.details

    def test_handle_package_not_found_error_variant(self):
        """Test handling of package not found error variant."""
        error = Exception("Package not found: test_package")

        with pytest.raises(RezPackageError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Package not found" in exc_info.value.message
        assert exc_info.value.error_code == "REZ_PACKAGE_ERROR"

    def test_handle_resolver_error(self):
        """Test handling of resolver error."""
        error = Exception("Failed to resolve packages due to conflict")

        with pytest.raises(RezResolverError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Package resolution failed" in exc_info.value.message
        assert exc_info.value.error_code == "REZ_RESOLVER_ERROR"
        assert "original_error" in exc_info.value.details
        assert "context" in exc_info.value.details
        assert "solution" in exc_info.value.details

    def test_handle_resolver_error_with_resolve_keyword(self):
        """Test handling of resolver error with 'resolve' keyword."""
        error = Exception("Cannot resolve dependencies")

        with pytest.raises(RezResolverError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Package resolution failed" in exc_info.value.message

    def test_handle_environment_error(self):
        """Test handling of environment error."""
        error = Exception("Environment setup failed")

        with pytest.raises(RezEnvironmentError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Environment operation failed" in exc_info.value.message
        assert exc_info.value.error_code == "REZ_ENVIRONMENT_ERROR"
        assert "original_error" in exc_info.value.details
        assert "context" in exc_info.value.details
        assert "solution" in exc_info.value.details

    def test_handle_environment_error_with_context_keyword(self):
        """Test handling of environment error with 'context' keyword."""
        error = Exception("Context creation failed")

        with pytest.raises(RezEnvironmentError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Environment operation failed" in exc_info.value.message

    def test_handle_generic_rez_error(self):
        """Test handling of generic Rez error."""
        error = Exception("Some other Rez error")

        with pytest.raises(RezProxyError) as exc_info:
            handle_rez_exception(error, "test context")

        assert "Rez operation failed" in exc_info.value.message
        assert exc_info.value.error_code == "REZ_OPERATION_ERROR"
        assert "original_error" in exc_info.value.details
        assert "context" in exc_info.value.details
        assert "type" in exc_info.value.details
        assert exc_info.value.details["type"] == "Exception"


class TestExceptionHandlers:
    """Test async exception handlers."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test/path"
        return request

    @pytest.mark.asyncio
    async def test_rez_proxy_exception_handler(self, mock_request):
        """Test RezProxyError exception handler."""
        details = {"key": "value"}
        error = RezProxyError(
            message="Test error", error_code="TEST_ERROR", details=details
        )

        response = await rez_proxy_exception_handler(mock_request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_http_exception_handler(self, mock_request):
        """Test HTTP exception handler."""
        error = HTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(mock_request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_general_exception_handler(self, mock_request):
        """Test general exception handler."""
        error = ValueError("Some unexpected error")

        response = await general_exception_handler(mock_request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_rez_proxy_exception_handler_minimal_error(self, mock_request):
        """Test RezProxyError handler with minimal error."""
        error = RezProxyError("Simple error")

        response = await rez_proxy_exception_handler(mock_request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_custom_status(self, mock_request):
        """Test HTTP exception handler with custom status code."""
        error = HTTPException(status_code=422, detail="Validation error")

        response = await http_exception_handler(mock_request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_general_exception_handler_with_different_exception_types(
        self, mock_request
    ):
        """Test general exception handler with different exception types."""
        # Test with RuntimeError
        error = RuntimeError("Runtime error occurred")
        response = await general_exception_handler(mock_request, error)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        # Test with KeyError
        error = KeyError("missing_key")
        response = await general_exception_handler(mock_request, error)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        # Test with custom exception
        class CustomError(Exception):
            pass

        error = CustomError("Custom error message")
        response = await general_exception_handler(mock_request, error)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestExceptionIntegration:
    """Test exception handling integration scenarios."""

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from RezProxyError."""
        assert issubclass(RezConfigurationError, RezProxyError)
        assert issubclass(RezPackageError, RezProxyError)
        assert issubclass(RezResolverError, RezProxyError)
        assert issubclass(RezEnvironmentError, RezProxyError)

    def test_exception_error_codes(self):
        """Test that each exception type has the correct error code."""
        config_error = RezConfigurationError("test")
        assert config_error.error_code == "REZ_CONFIG_ERROR"

        package_error = RezPackageError("test")
        assert package_error.error_code == "REZ_PACKAGE_ERROR"

        resolver_error = RezResolverError("test")
        assert resolver_error.error_code == "REZ_RESOLVER_ERROR"

        env_error = RezEnvironmentError("test")
        assert env_error.error_code == "REZ_ENVIRONMENT_ERROR"

    def test_handle_rez_exception_without_context(self):
        """Test handle_rez_exception without context parameter."""
        error = Exception("Generic error")

        with pytest.raises(RezProxyError) as exc_info:
            handle_rez_exception(error)

        assert exc_info.value.details["context"] == ""

    def test_complex_error_scenario(self):
        """Test complex error handling scenario."""
        # Create a nested exception scenario
        original_error = Exception("Original Rez error with resolve keyword")

        with pytest.raises(RezResolverError) as exc_info:
            handle_rez_exception(original_error, "complex scenario")

        resolver_error = exc_info.value
        assert "Package resolution failed" in resolver_error.message
        assert resolver_error.details["context"] == "complex scenario"
        assert resolver_error.details["original_error"] == str(original_error)
