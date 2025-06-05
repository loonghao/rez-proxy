"""
Rez Proxy configuration management.
"""

import os
from typing import List, Optional

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class RezProxyConfig(BaseSettings):
    """Rez Proxy configuration."""

    # Server configuration
    host: str = Field(default="localhost", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    reload: bool = Field(default=False, description="Enable auto-reload for development")
    log_level: str = Field(default="info", description="Log level")
    workers: int = Field(default=1, description="Number of worker processes")

    # CORS configuration
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

    # Rez configuration
    rez_config_file: Optional[str] = Field(default=None, description="Rez config file path")
    rez_packages_path: Optional[str] = Field(default=None, description="Rez packages path")

    # Cache configuration
    enable_cache: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    # Security configuration
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    max_concurrent_environments: int = Field(default=10, description="Max concurrent environments")
    max_command_timeout: int = Field(default=300, description="Max command timeout in seconds")

    model_config = ConfigDict(
        env_prefix="REZ_PROXY_",
        case_sensitive=False
    )


_config: Optional[RezProxyConfig] = None


def get_config() -> RezProxyConfig:
    """Get configuration instance."""
    global _config
    if _config is None:
        _config = RezProxyConfig()

        # Set Rez configuration from environment variables
        if _config.rez_config_file:
            os.environ['REZ_CONFIG_FILE'] = _config.rez_config_file
        if _config.rez_packages_path:
            os.environ['REZ_PACKAGES_PATH'] = _config.rez_packages_path

    return _config
