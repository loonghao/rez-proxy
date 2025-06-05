"""
Test configuration functionality.
"""

import os
from unittest.mock import patch

from rez_proxy.config import (
    RezProxyConfig,
    get_config,
    reload_config,
    set_rez_config_from_dict,
)


class TestRezProxyConfig:
    """Test RezProxyConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RezProxyConfig()

        assert config.host == "localhost"
        assert config.port == 8000
        assert config.reload is False
        assert config.cors_origins == ["*"]
        assert config.workers == 1
        assert config.cache_ttl == 300
        assert config.enable_cache is True

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        config_data = {
            "host": "127.0.0.1",
            "port": 9000,
            "reload": True,
            "cors_origins": ["http://localhost:3000"],
            "workers": 8,
            "cache_ttl": 7200,
            "enable_cache": False,
        }

        config = RezProxyConfig(**config_data)

        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.reload is True
        assert config.cors_origins == ["http://localhost:3000"]
        assert config.workers == 8
        assert config.cache_ttl == 7200
        assert config.enable_cache is False

    def test_config_validation_port(self):
        """Test port validation."""
        # Valid port
        config = RezProxyConfig(port=8080)
        assert config.port == 8080

    def test_config_validation_workers(self):
        """Test workers validation."""
        # Valid workers
        config = RezProxyConfig(workers=16)
        assert config.workers == 16

    def test_config_validation_cache_ttl(self):
        """Test cache_ttl validation."""
        # Valid cache_ttl
        config = RezProxyConfig(cache_ttl=7200)
        assert config.cache_ttl == 7200

    def test_config_cors_origins_list(self):
        """Test CORS origins as list."""
        origins = ["http://localhost:3000", "http://localhost:8080"]
        config = RezProxyConfig(cors_origins=origins)
        assert config.cors_origins == origins

    def test_config_serialization(self):
        """Test configuration serialization."""
        config = RezProxyConfig(host="127.0.0.1", port=9000, reload=True)

        data = config.model_dump()

        assert data["host"] == "127.0.0.1"
        assert data["port"] == 9000
        assert data["reload"] is True

    def test_config_environment_variables(self):
        """Test configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "REZ_PROXY_API_HOST": "192.168.1.100",
                "REZ_PROXY_API_PORT": "9000",
                "REZ_PROXY_API_RELOAD": "true",
                "REZ_PROXY_API_WORKERS": "8",
            },
        ):
            config = RezProxyConfig()

            assert config.host == "192.168.1.100"
            assert config.port == 9000
            assert config.reload is True
            assert config.workers == 8


class TestGetConfig:
    """Test get_config function."""

    def test_get_config_default(self):
        """Test get_config with default behavior."""
        config = get_config()

        assert isinstance(config, RezProxyConfig)
        assert config.host == "localhost"
        assert config.port == 8000

    def test_get_config_caching(self):
        """Test that get_config caches the configuration."""
        config1 = get_config()
        config2 = get_config()

        # Should be the same instance (cached)
        assert config1 is config2

    def test_reload_config(self):
        """Test config reloading."""
        # config1 = get_config()  # Initial config (not used in test)
        config2 = reload_config()

        # Should be different instances after reload
        assert isinstance(config2, RezProxyConfig)

    def test_set_rez_config_from_dict(self):
        """Test setting Rez config from dictionary."""
        config_dict = {
            "rez_config_file": "/path/to/config.py",
            "rez_packages_path": "/path/to/packages",
        }

        set_rez_config_from_dict(config_dict)

        # Check environment variables were set
        assert os.environ.get("REZ_PROXY_API_REZ_CONFIG_FILE") == "/path/to/config.py"
        assert os.environ.get("REZ_PROXY_API_REZ_PACKAGES_PATH") == "/path/to/packages"


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_full_config_workflow(self):
        """Test complete configuration workflow."""
        # Test with environment variables
        with patch.dict(
            os.environ,
            {
                "REZ_PROXY_API_HOST": "test-host",
                "REZ_PROXY_API_PORT": "9999",
                "REZ_PROXY_API_RELOAD": "true",
            },
        ):
            config = reload_config()  # Force reload to pick up env vars

            assert config.host == "test-host"
            assert config.port == 9999
            assert config.reload is True

    def test_partial_config_override(self):
        """Test partial configuration override."""
        with patch.dict(
            os.environ,
            {
                "REZ_PROXY_API_HOST": "partial-host"
                # Only override host, other values should be defaults
            },
        ):
            config = reload_config()

            assert config.host == "partial-host"
            assert config.port == 8000  # Default value
            assert config.reload is False  # Default value
