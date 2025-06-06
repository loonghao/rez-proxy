"""
Rez Proxy configuration management.
"""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RezProxyConfig(BaseSettings):
    """Rez Proxy configuration."""

    # Server configuration
    host: str = Field(default="localhost", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    reload: bool = Field(
        default=False, description="Enable auto-reload for development"
    )
    log_level: str = Field(default="info", description="Log level")
    workers: int = Field(default=1, description="Number of worker processes")

    # CORS configuration
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")

    # Rez configuration
    rez_config_file: str | None = Field(
        default=None, description="Rez config file path"
    )
    rez_packages_path: str | None = Field(
        default=None, description="Rez packages path (colon-separated)"
    )
    rez_local_packages_path: str | None = Field(
        default=None, description="Rez local packages path"
    )
    rez_release_packages_path: str | None = Field(
        default=None, description="Rez release packages path (colon-separated)"
    )
    rez_tmpdir: str | None = Field(default=None, description="Rez temporary directory")
    rez_cache_packages_path: str | None = Field(
        default=None, description="Rez package cache path"
    )
    rez_disable_home_config: bool = Field(
        default=False, description="Disable Rez home config"
    )
    rez_quiet: bool = Field(default=False, description="Enable Rez quiet mode")
    rez_debug: bool = Field(default=False, description="Enable Rez debug mode")

    # Cache configuration
    enable_cache: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    # API configuration
    api_prefix: str = Field(default="/api/v1", description="API prefix path")
    docs_url: str = Field(default="/docs", description="Documentation URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")

    # Security configuration
    api_key: str | None = Field(default=None, description="API key for authentication")
    max_concurrent_environments: int = Field(
        default=10, description="Max concurrent environments"
    )
    max_command_timeout: int = Field(
        default=300, description="Max command timeout in seconds"
    )

    model_config = SettingsConfigDict(env_prefix="REZ_PROXY_API_", case_sensitive=False)


_config: RezProxyConfig | None = None


def get_config() -> RezProxyConfig:
    """Get configuration instance."""
    global _config
    if _config is None:
        _config = RezProxyConfig()
        _apply_rez_config(_config)
    return _config


def _apply_rez_config(config: RezProxyConfig) -> None:
    """Apply Rez configuration to environment variables."""

    # Core Rez configuration
    if config.rez_config_file:
        os.environ["REZ_CONFIG_FILE"] = config.rez_config_file
        print(f"🔧 Using Rez config file: {config.rez_config_file}")

    # Packages paths
    if config.rez_packages_path:
        os.environ["REZ_PACKAGES_PATH"] = config.rez_packages_path
        print(f"📦 Using packages path: {config.rez_packages_path}")

    if config.rez_local_packages_path:
        os.environ["REZ_LOCAL_PACKAGES_PATH"] = config.rez_local_packages_path
        print(f"🏠 Using local packages path: {config.rez_local_packages_path}")

    if config.rez_release_packages_path:
        os.environ["REZ_RELEASE_PACKAGES_PATH"] = config.rez_release_packages_path
        print(f"🚀 Using release packages path: {config.rez_release_packages_path}")

    # Cache and temporary directories
    if config.rez_tmpdir:
        os.environ["REZ_TMPDIR"] = config.rez_tmpdir
        print(f"📁 Using temp directory: {config.rez_tmpdir}")

    if config.rez_cache_packages_path:
        os.environ["REZ_CACHE_PACKAGES_PATH"] = config.rez_cache_packages_path
        print(f"💾 Using cache path: {config.rez_cache_packages_path}")

    # Rez behavior flags
    if config.rez_disable_home_config:
        os.environ["REZ_DISABLE_HOME_CONFIG"] = "1"
        print("🚫 Disabled Rez home config")

    if config.rez_quiet:
        os.environ["REZ_QUIET"] = "1"
        print("🔇 Enabled Rez quiet mode")

    if config.rez_debug:
        os.environ["REZ_DEBUG"] = "1"
        print("🐛 Enabled Rez debug mode")


def reload_config() -> RezProxyConfig:
    """Reload configuration (useful for testing)."""
    global _config
    _config = None
    return get_config()


def set_rez_config_from_dict(config_dict: dict) -> None:
    """Set Rez configuration from dictionary (useful for testing)."""
    for key, value in config_dict.items():
        if value is not None:
            env_key = f"REZ_PROXY_API_{key.upper()}"
            os.environ[env_key] = str(value)

    # Reload config to apply changes
    reload_config()
