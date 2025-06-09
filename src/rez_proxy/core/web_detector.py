"""
Web environment detection for rez-proxy.

Provides functionality to detect if the application is running in a web environment
and determine appropriate security and access control measures.
"""

import logging
import os
import threading
from functools import lru_cache
from typing import Any

from rez_proxy.models.schemas import ServiceMode

logger = logging.getLogger(__name__)


class WebEnvironmentDetector:
    """Detects and manages web environment information."""

    def __init__(self) -> None:
        self._cache_lock = threading.Lock()
        self._detection_cache: bool | None = None
        self._forced_mode: ServiceMode | None = None

    def is_web_environment(self) -> bool:
        """
        Determine if the application is running in a web environment.

        Uses multiple detection methods:
        1. Environment variables
        2. HTTP headers (if available in context)
        3. Deployment context indicators
        4. Manual override settings

        Returns:
            bool: True if running in web environment, False otherwise
        """
        # Check for manual override first
        if self._forced_mode is not None:
            return self._forced_mode == ServiceMode.WEB

        # Use cached result if available
        if self._detection_cache is not None:
            return self._detection_cache

        with self._cache_lock:
            # Double-check pattern
            if self._detection_cache is not None:
                return self._detection_cache

            # Perform detection
            is_web = self._detect_web_environment()
            self._detection_cache = is_web
            return is_web

    def _detect_web_environment(self) -> bool:
        """Internal method to perform web environment detection."""
        detection_methods = [
            self._check_environment_variables,
            self._check_deployment_context,
            self._check_web_server_indicators,
            self._check_container_environment,
        ]

        # If any method indicates web environment, consider it web
        for method in detection_methods:
            try:
                if method():
                    return True
            except Exception as e:
                # Continue with other methods if one fails
                logger.debug(f"Web detection method failed: {e}")
                continue

        return False

    def _check_environment_variables(self) -> bool:
        """Check environment variables for web environment indicators."""
        # Check for explicit disable first - this should override any web indicators
        if os.environ.get("REZ_PROXY_FORCE_LOCAL", "").lower() in ("true", "1", "yes"):
            return False

        web_env_indicators = [
            # Explicit web environment markers
            "REZ_PROXY_WEB_MODE",
            "WEB_ENVIRONMENT",
            "IS_WEB_ENV",
            # Common web server environment variables
            "SERVER_SOFTWARE",
            "REQUEST_METHOD",
            "HTTP_HOST",
            "SCRIPT_NAME",
            # Cloud/container platform indicators
            "VERCEL",
            "NETLIFY",
            "HEROKU_APP_NAME",
            "AWS_LAMBDA_FUNCTION_NAME",
            "GOOGLE_CLOUD_PROJECT",
            "AZURE_FUNCTIONS_ENVIRONMENT",
            # Container orchestration
            "KUBERNETES_SERVICE_HOST",
            "DOCKER_CONTAINER",
        ]

        for var in web_env_indicators:
            if os.environ.get(var):
                return True

        return False

    def _check_deployment_context(self) -> bool:
        """Check deployment context indicators."""
        # Check for common web deployment paths (Unix-style paths)
        web_deployment_paths = [
            "/var/www",
            "/app",  # Common Docker web app path
            "/code",  # Another common container path
            "/workspace",  # Cloud IDE environments
        ]

        current_path = os.getcwd().replace("\\", "/")  # Normalize Windows paths
        for path in web_deployment_paths:
            if current_path.startswith(path):
                return True

        # Check for web-specific configuration files
        web_config_files = [
            "vercel.json",
            "netlify.toml",
            "Dockerfile",
            "docker-compose.yml",
            "kubernetes.yaml",
            "k8s.yaml",
        ]

        for config_file in web_config_files:
            if os.path.exists(config_file):
                return True

        return False

    def _check_web_server_indicators(self) -> bool:
        """Check for web server process indicators."""
        # Check if running under common web servers
        web_server_vars = [
            "UWSGI_VERSION",
            "GUNICORN_CMD_ARGS",
            "UVICORN_HOST",
            "HYPERCORN_CONFIG",
            "WAITRESS_LISTEN",
        ]

        for var in web_server_vars:
            if os.environ.get(var):
                return True

        return False

    def _check_container_environment(self) -> bool:
        """Check if running in a container environment."""
        container_indicators = [
            # Docker
            "/.dockerenv",
            "/proc/1/cgroup",  # Check if we can detect container cgroup
            # Kubernetes
            "/var/run/secrets/kubernetes.io",
            # Other container runtimes
            "/run/.containerenv",  # Podman
        ]

        for indicator in container_indicators:
            if os.path.exists(indicator):
                # Additional check for Docker cgroup
                if indicator == "/proc/1/cgroup":
                    try:
                        with open(indicator) as f:
                            content = f.read()
                            if "docker" in content or "containerd" in content:
                                return True
                    except OSError:
                        pass
                else:
                    return True

        return False

    def get_service_mode(self) -> ServiceMode:
        """
        Get the appropriate service mode based on environment detection.

        Returns:
            ServiceMode: WEB, REMOTE, or LOCAL based on detection
        """
        if self._forced_mode is not None:
            return self._forced_mode

        if self.is_web_environment():
            return ServiceMode.WEB

        # For now, default to LOCAL if not web
        # In the future, we might add more sophisticated REMOTE detection
        return ServiceMode.LOCAL

    def force_service_mode(self, mode: ServiceMode) -> None:
        """
        Manually override the detected service mode.

        Args:
            mode: ServiceMode to force
        """
        self._forced_mode = mode
        self._clear_cache()

    def clear_forced_mode(self) -> None:
        """Clear any manual service mode override."""
        self._forced_mode = None
        self._clear_cache()

    def _clear_cache(self) -> None:
        """Clear detection cache to force re-detection."""
        with self._cache_lock:
            self._detection_cache = None

    def get_detection_info(self) -> dict[str, Any]:
        """
        Get detailed information about the detection process.

        Returns:
            Dict containing detection details for debugging
        """
        return {
            "is_web_environment": self.is_web_environment(),
            "service_mode": self.get_service_mode().value,
            "forced_mode": self._forced_mode.value if self._forced_mode else None,
            "detection_methods": {
                "environment_variables": self._check_environment_variables(),
                "deployment_context": self._check_deployment_context(),
                "web_server_indicators": self._check_web_server_indicators(),
                "container_environment": self._check_container_environment(),
            },
            "relevant_env_vars": {
                key: value
                for key, value in os.environ.items()
                if any(
                    indicator in key.upper()
                    for indicator in [
                        "WEB",
                        "HTTP",
                        "SERVER",
                        "DOCKER",
                        "KUBERNETES",
                        "VERCEL",
                        "NETLIFY",
                        "HEROKU",
                        "AWS",
                        "GOOGLE",
                        "AZURE",
                        "REZ_PROXY",
                    ]
                )
            },
        }


# Global detector instance
_web_detector: WebEnvironmentDetector | None = None
_detector_lock = threading.Lock()


def get_web_detector() -> WebEnvironmentDetector:
    """Get the global web environment detector instance."""
    global _web_detector

    if _web_detector is None:
        with _detector_lock:
            if _web_detector is None:
                _web_detector = WebEnvironmentDetector()

    return _web_detector


@lru_cache(maxsize=1)
def is_web_environment() -> bool:
    """
    Check if running in web environment (cached).

    Returns:
        bool: True if web environment detected
    """
    return get_web_detector().is_web_environment()


def get_detected_service_mode() -> ServiceMode:
    """
    Get the detected service mode.

    Returns:
        ServiceMode: Detected service mode
    """
    return get_web_detector().get_service_mode()


def force_web_mode(enabled: bool = True) -> None:
    """
    Force web mode on or off.

    Args:
        enabled: True to force web mode, False to force local mode
    """
    detector = get_web_detector()
    if enabled:
        detector.force_service_mode(ServiceMode.WEB)
    else:
        detector.force_service_mode(ServiceMode.LOCAL)


def clear_detection_cache() -> None:
    """Clear web environment detection cache."""
    get_web_detector()._clear_cache()
    # Clear the lru_cache as well
    is_web_environment.cache_clear()
