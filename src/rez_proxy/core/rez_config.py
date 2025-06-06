"""
Rez configuration management for rez-proxy.

Handles Rez environment setup and configuration validation.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import get_config


@dataclass
class RezEnvironmentInfo:
    """Information about the current Rez environment."""

    config_file: str | None = None
    packages_paths: list[str] | None = None
    local_packages_path: str | None = None
    release_packages_paths: list[str] | None = None
    tmpdir: str | None = None
    cache_path: str | None = None
    home_config_disabled: bool = False
    quiet_mode: bool = False
    debug_mode: bool = False
    environment_variables: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.packages_paths is None:
            self.packages_paths = []
        if self.release_packages_paths is None:
            self.release_packages_paths = []
        if self.environment_variables is None:
            self.environment_variables = {}


class RezConfigManager:
    """Manages Rez configuration for rez-proxy."""

    def __init__(self) -> None:
        self._config = get_config()
        self._environment_info: RezEnvironmentInfo | None = None

    def get_environment_info(self) -> RezEnvironmentInfo:
        """Get current Rez environment information."""
        if self._environment_info is None:
            self._environment_info = self._detect_environment()
        return self._environment_info

    def _detect_environment(self) -> RezEnvironmentInfo:
        """Detect current Rez environment configuration."""

        # Get Rez environment variables
        rez_env_vars = {
            key: value for key, value in os.environ.items() if key.startswith("REZ_")
        }

        # Parse paths
        packages_paths = self._parse_path_list(os.environ.get("REZ_PACKAGES_PATH", ""))
        release_packages_paths = self._parse_path_list(
            os.environ.get("REZ_RELEASE_PACKAGES_PATH", "")
        )

        return RezEnvironmentInfo(
            config_file=os.environ.get("REZ_CONFIG_FILE"),
            packages_paths=packages_paths,
            local_packages_path=os.environ.get("REZ_LOCAL_PACKAGES_PATH"),
            release_packages_paths=release_packages_paths,
            tmpdir=os.environ.get("REZ_TMPDIR"),
            cache_path=os.environ.get("REZ_CACHE_PACKAGES_PATH"),
            home_config_disabled=os.environ.get("REZ_DISABLE_HOME_CONFIG") == "1",
            quiet_mode=os.environ.get("REZ_QUIET") == "1",
            debug_mode=os.environ.get("REZ_DEBUG") == "1",
            environment_variables=rez_env_vars,
        )

    def _parse_path_list(self, path_string: str) -> list[str]:
        """Parse colon-separated path string into list."""
        if not path_string:
            return []

        # Handle both Unix (:) and Windows (;) path separators
        separator = ";" if sys.platform == "win32" else ":"
        paths = [p.strip() for p in path_string.split(separator) if p.strip()]
        return paths

    def validate_configuration(self) -> list[str]:
        """Validate Rez configuration and return warnings."""
        warnings = []
        env_info = self.get_environment_info()

        # Check config file
        if env_info.config_file:
            config_path = Path(env_info.config_file)
            if not config_path.exists():
                warnings.append(f"Rez config file not found: {env_info.config_file}")
            elif not config_path.is_file():
                warnings.append(
                    f"Rez config path is not a file: {env_info.config_file}"
                )

        # Check packages paths
        if not env_info.packages_paths:
            warnings.append("No Rez packages paths configured")
        else:
            for path in env_info.packages_paths:
                path_obj = Path(path)
                if not path_obj.exists():
                    warnings.append(f"Packages path does not exist: {path}")
                elif not path_obj.is_dir():
                    warnings.append(f"Packages path is not a directory: {path}")
                elif not os.access(path, os.R_OK):
                    warnings.append(f"No read access to packages path: {path}")

        # Check local packages path
        if env_info.local_packages_path:
            local_path = Path(env_info.local_packages_path)
            if not local_path.exists():
                warnings.append(
                    f"Local packages path does not exist: {env_info.local_packages_path}"
                )
            elif not os.access(env_info.local_packages_path, os.W_OK):
                warnings.append(
                    f"No write access to local packages path: {env_info.local_packages_path}"
                )

        # Check release packages paths
        if env_info.release_packages_paths:
            for path in env_info.release_packages_paths:
                path_obj = Path(path)
                if not path_obj.exists():
                    warnings.append(f"Release packages path does not exist: {path}")
                elif not path_obj.is_dir():
                    warnings.append(f"Release packages path is not a directory: {path}")

        # Check temporary directory
        if env_info.tmpdir:
            tmp_path = Path(env_info.tmpdir)
            if not tmp_path.exists():
                warnings.append(
                    f"Temporary directory does not exist: {env_info.tmpdir}"
                )
            elif not os.access(env_info.tmpdir, os.W_OK):
                warnings.append(
                    f"No write access to temporary directory: {env_info.tmpdir}"
                )

        # Check cache path
        if env_info.cache_path:
            cache_path = Path(env_info.cache_path)
            if not cache_path.exists():
                warnings.append(
                    f"Cache directory does not exist: {env_info.cache_path}"
                )
            elif not os.access(env_info.cache_path, os.W_OK):
                warnings.append(
                    f"No write access to cache directory: {env_info.cache_path}"
                )

        return warnings

    def get_configuration_summary(self) -> dict[str, Any]:
        """Get a summary of current Rez configuration."""
        env_info = self.get_environment_info()
        warnings = self.validate_configuration()

        return {
            "config_file": env_info.config_file,
            "packages_paths": env_info.packages_paths,
            "local_packages_path": env_info.local_packages_path,
            "release_packages_paths": env_info.release_packages_paths,
            "tmpdir": env_info.tmpdir,
            "cache_path": env_info.cache_path,
            "flags": {
                "home_config_disabled": env_info.home_config_disabled,
                "quiet_mode": env_info.quiet_mode,
                "debug_mode": env_info.debug_mode,
            },
            "environment_variables": env_info.environment_variables,
            "warnings": warnings,
            "is_valid": len(warnings) == 0,
        }

    def apply_configuration_from_dict(self, config_dict: dict[str, Any]) -> None:
        """Apply Rez configuration from dictionary."""

        # Map configuration keys to environment variables
        env_mapping = {
            "config_file": "REZ_CONFIG_FILE",
            "packages_path": "REZ_PACKAGES_PATH",
            "local_packages_path": "REZ_LOCAL_PACKAGES_PATH",
            "release_packages_path": "REZ_RELEASE_PACKAGES_PATH",
            "tmpdir": "REZ_TMPDIR",
            "cache_path": "REZ_CACHE_PACKAGES_PATH",
            "disable_home_config": "REZ_DISABLE_HOME_CONFIG",
            "quiet": "REZ_QUIET",
            "debug": "REZ_DEBUG",
        }

        for key, value in config_dict.items():
            if value is not None and key in env_mapping:
                env_key = env_mapping[key]
                if isinstance(value, bool):
                    os.environ[env_key] = "1" if value else "0"
                else:
                    os.environ[env_key] = str(value)

        # Reset cached environment info
        self._environment_info = None

    def create_rez_config_template(self, output_path: str) -> None:
        """Create a template Rez configuration file."""

        template_content = '''"""
Rez configuration template for rez-proxy.

This file can be used as a starting point for your Rez configuration.
Modify the paths and settings according to your environment.
"""

# Package repositories
packages_path = [
    "/path/to/your/packages",
    "/shared/packages",
]

# Local packages (for development)
local_packages_path = "/path/to/local/packages"

# Release packages
release_packages_path = [
    "/path/to/release/packages",
]

# Temporary directory
tmpdir = "/tmp/rez"

# Cache settings
cache_packages_path = "/path/to/cache"
package_cache_max_variant_logs = 100

# Platform settings
platform_map = {}

# Build settings
build_system = "cmake"

# Environment settings
default_shell = "bash"

# Logging
quiet = False
debug = False

# Plugin settings
plugins = []

# Custom settings for rez-proxy
rez_proxy_settings = {
    "enable_api_cache": True,
    "api_cache_ttl": 300,
    "max_concurrent_environments": 10,
}
'''

        with open(output_path, "w") as f:
            f.write(template_content)


# Global instance
rez_config_manager = RezConfigManager()


def get_rez_config_manager() -> RezConfigManager:
    """Get the global Rez configuration manager."""
    return rez_config_manager
