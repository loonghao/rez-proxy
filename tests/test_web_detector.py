"""
Tests for Web environment detection functionality.
"""

import os
import tempfile
from unittest.mock import patch, mock_open
import pytest

from rez_proxy.core.web_detector import (
    WebEnvironmentDetector,
    get_web_detector,
    is_web_environment,
    get_detected_service_mode,
    force_web_mode,
    clear_detection_cache,
)
from rez_proxy.models.schemas import ServiceMode


class TestWebEnvironmentDetector:
    """Test WebEnvironmentDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = WebEnvironmentDetector()

    def test_init(self):
        """Test detector initialization."""
        assert self.detector._detection_cache is None
        assert self.detector._forced_mode is None

    def test_force_service_mode(self):
        """Test manual service mode override."""
        # Test forcing web mode
        self.detector.force_service_mode(ServiceMode.WEB)
        assert self.detector.get_service_mode() == ServiceMode.WEB
        assert self.detector.is_web_environment() is True

        # Test forcing local mode
        self.detector.force_service_mode(ServiceMode.LOCAL)
        assert self.detector.get_service_mode() == ServiceMode.LOCAL
        assert self.detector.is_web_environment() is False

        # Test clearing forced mode
        self.detector.clear_forced_mode()
        assert self.detector._forced_mode is None

    @patch.dict(os.environ, {}, clear=True)
    def test_environment_variables_detection_clean(self):
        """Test environment variable detection with clean environment."""
        assert self.detector._check_environment_variables() is False

    @patch.dict(os.environ, {"REZ_PROXY_WEB_MODE": "true"}, clear=True)
    def test_environment_variables_detection_web_mode(self):
        """Test detection with REZ_PROXY_WEB_MODE."""
        assert self.detector._check_environment_variables() is True

    @patch.dict(os.environ, {"SERVER_SOFTWARE": "nginx/1.18"}, clear=True)
    def test_environment_variables_detection_server_software(self):
        """Test detection with SERVER_SOFTWARE."""
        assert self.detector._check_environment_variables() is True

    @patch.dict(os.environ, {"VERCEL": "1"}, clear=True)
    def test_environment_variables_detection_vercel(self):
        """Test detection with Vercel environment."""
        assert self.detector._check_environment_variables() is True

    @patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}, clear=True)
    def test_environment_variables_detection_kubernetes(self):
        """Test detection with Kubernetes environment."""
        assert self.detector._check_environment_variables() is True

    @patch.dict(os.environ, {"REZ_PROXY_FORCE_LOCAL": "true"}, clear=True)
    def test_environment_variables_force_local(self):
        """Test forcing local mode via environment variable."""
        # Even with web indicators, force local should override
        with patch.dict(os.environ, {"SERVER_SOFTWARE": "nginx", "REZ_PROXY_FORCE_LOCAL": "true"}):
            assert self.detector._check_environment_variables() is False

    @patch("os.getcwd")
    def test_deployment_context_detection_web_path(self, mock_getcwd):
        """Test deployment context detection with web paths."""
        mock_getcwd.return_value = "/var/www/html"
        assert self.detector._check_deployment_context() is True

        mock_getcwd.return_value = "/app/src"
        assert self.detector._check_deployment_context() is True

        mock_getcwd.return_value = "/home/user/project"
        assert self.detector._check_deployment_context() is False

    @patch("os.path.exists")
    def test_deployment_context_detection_config_files(self, mock_exists):
        """Test deployment context detection with config files."""
        # Test with Dockerfile
        mock_exists.side_effect = lambda path: path == "Dockerfile"
        assert self.detector._check_deployment_context() is True

        # Test with vercel.json
        mock_exists.side_effect = lambda path: path == "vercel.json"
        assert self.detector._check_deployment_context() is True

        # Test with no web config files
        mock_exists.return_value = False
        assert self.detector._check_deployment_context() is False

    @patch.dict(os.environ, {"UWSGI_VERSION": "2.0.18"}, clear=True)
    def test_web_server_indicators_uwsgi(self):
        """Test web server detection with uWSGI."""
        assert self.detector._check_web_server_indicators() is True

    @patch.dict(os.environ, {"GUNICORN_CMD_ARGS": "--bind 0.0.0.0:8000"}, clear=True)
    def test_web_server_indicators_gunicorn(self):
        """Test web server detection with Gunicorn."""
        assert self.detector._check_web_server_indicators() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_web_server_indicators_none(self):
        """Test web server detection with no indicators."""
        assert self.detector._check_web_server_indicators() is False

    @patch("os.path.exists")
    def test_container_environment_detection_docker(self, mock_exists):
        """Test container environment detection with Docker."""
        # Test .dockerenv file
        mock_exists.side_effect = lambda path: path == "/.dockerenv"
        assert self.detector._check_container_environment() is True

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="1:name=systemd:/docker/abc123")
    def test_container_environment_detection_cgroup(self, mock_file, mock_exists):
        """Test container environment detection with cgroup."""
        mock_exists.side_effect = lambda path: path == "/proc/1/cgroup"
        assert self.detector._check_container_environment() is True

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="1:name=systemd:/init.scope")
    def test_container_environment_detection_no_container(self, mock_file, mock_exists):
        """Test container environment detection without container."""
        mock_exists.side_effect = lambda path: path == "/proc/1/cgroup"
        assert self.detector._check_container_environment() is False

    @patch("os.path.exists")
    def test_container_environment_detection_kubernetes(self, mock_exists):
        """Test container environment detection with Kubernetes."""
        mock_exists.side_effect = lambda path: path == "/var/run/secrets/kubernetes.io"
        assert self.detector._check_container_environment() is True

    def test_caching_behavior(self):
        """Test that detection results are cached."""
        # Mock all detection methods to return False
        with patch.object(self.detector, '_detect_web_environment', return_value=False) as mock_detect:
            # First call should trigger detection
            result1 = self.detector.is_web_environment()
            assert result1 is False
            assert mock_detect.call_count == 1

            # Second call should use cache
            result2 = self.detector.is_web_environment()
            assert result2 is False
            assert mock_detect.call_count == 1  # No additional calls

    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Set up cache
        with patch.object(self.detector, '_detect_web_environment', return_value=True):
            self.detector.is_web_environment()
            assert self.detector._detection_cache is True

        # Clear cache
        self.detector._clear_cache()
        assert self.detector._detection_cache is None

    def test_get_detection_info(self):
        """Test getting detailed detection information."""
        info = self.detector.get_detection_info()
        
        assert "is_web_environment" in info
        assert "service_mode" in info
        assert "forced_mode" in info
        assert "detection_methods" in info
        assert "relevant_env_vars" in info
        
        # Check detection methods structure
        methods = info["detection_methods"]
        assert "environment_variables" in methods
        assert "deployment_context" in methods
        assert "web_server_indicators" in methods
        assert "container_environment" in methods


class TestWebDetectorGlobalFunctions:
    """Test global web detector functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear any cached state
        clear_detection_cache()

    def test_get_web_detector_singleton(self):
        """Test that get_web_detector returns singleton instance."""
        detector1 = get_web_detector()
        detector2 = get_web_detector()
        assert detector1 is detector2

    @patch.dict(os.environ, {"REZ_PROXY_WEB_MODE": "true"}, clear=True)
    def test_is_web_environment_cached(self):
        """Test cached web environment detection."""
        # Clear cache first
        clear_detection_cache()
        
        result1 = is_web_environment()
        result2 = is_web_environment()
        assert result1 is True
        assert result2 is True

    def test_get_detected_service_mode(self):
        """Test getting detected service mode."""
        mode = get_detected_service_mode()
        assert isinstance(mode, ServiceMode)

    def test_force_web_mode(self):
        """Test forcing web mode globally."""
        # Force web mode on
        force_web_mode(True)
        assert is_web_environment() is True
        assert get_detected_service_mode() == ServiceMode.WEB

        # Force web mode off
        force_web_mode(False)
        assert get_detected_service_mode() == ServiceMode.LOCAL

    def test_clear_detection_cache_global(self):
        """Test clearing detection cache globally."""
        # Set up some cached state
        is_web_environment()
        
        # Clear cache
        clear_detection_cache()
        
        # Should work without errors
        result = is_web_environment()
        assert isinstance(result, bool)


class TestWebDetectorIntegration:
    """Integration tests for web detector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = WebEnvironmentDetector()

    @patch.dict(os.environ, {"VERCEL": "1", "VERCEL_URL": "myapp.vercel.app"}, clear=True)
    @patch("os.path.exists", return_value=True)
    def test_vercel_environment_detection(self, mock_exists):
        """Test detection in Vercel environment."""
        assert self.detector.is_web_environment() is True
        assert self.detector.get_service_mode() == ServiceMode.WEB

    @patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}, clear=True)
    @patch("os.path.exists")
    def test_kubernetes_environment_detection(self, mock_exists):
        """Test detection in Kubernetes environment."""
        mock_exists.side_effect = lambda path: path == "/var/run/secrets/kubernetes.io"
        assert self.detector.is_web_environment() is True
        assert self.detector.get_service_mode() == ServiceMode.WEB

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.getcwd", return_value="/home/user/project")
    @patch("os.path.exists", return_value=False)
    def test_local_development_environment(self, mock_exists, mock_getcwd):
        """Test detection in local development environment."""
        assert self.detector.is_web_environment() is False
        assert self.detector.get_service_mode() == ServiceMode.LOCAL

    def test_mixed_indicators_priority(self):
        """Test behavior with mixed environment indicators."""
        # Test that explicit force local overrides web indicators
        with patch.dict(os.environ, {"VERCEL": "1", "REZ_PROXY_FORCE_LOCAL": "true"}):
            assert self.detector._check_environment_variables() is False
            assert self.detector.get_service_mode() == ServiceMode.LOCAL
