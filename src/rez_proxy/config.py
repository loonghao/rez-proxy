"""
Rez Proxy configuration management.
"""

import json
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

    # Create dummy classes for type hints when watchdog is not available
    class Observer:  # type: ignore
        pass

    class FileSystemEventHandler:  # type: ignore
        pass


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

    # Hot reload configuration
    enable_hot_reload: bool = Field(
        default=False, description="Enable configuration hot reload"
    )
    config_file_path: str = Field(
        default="config/rez_proxy.json", description="Configuration file path"
    )
    config_watch_interval: float = Field(
        default=1.0, description="Configuration file watch interval in seconds"
    )

    model_config = SettingsConfigDict(env_prefix="REZ_PROXY_API_", case_sensitive=False)

    @field_validator("port", mode="before")
    @classmethod
    def validate_port(cls, v: Any) -> int:
        """Validate port value and handle invalid strings."""
        if isinstance(v, str):
            # Handle common invalid values
            if v.lower() in ("invalid_port", "invalid", "none", "null", ""):
                return 8000  # Default port
            try:
                return int(v)
            except ValueError:
                # If conversion fails, use default
                return 8000
        if isinstance(v, int):
            return v
        # For any other type, convert to int or use default
        try:
            return int(v)
        except (ValueError, TypeError):
            return 8000


class ConfigChangeHandler(FileSystemEventHandler):
    """File system event handler for configuration changes."""

    def __init__(self, config_manager: "ConfigManager") -> None:
        self.config_manager = config_manager
        self.last_modified: dict[str, float] = {}

    def on_modified(self, event: Any) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path
        current_time = time.time()

        # Debounce rapid file changes
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < 0.5:
                return

        self.last_modified[file_path] = current_time

        # Check if this is a config file we're watching
        if self.config_manager.is_watched_file(file_path):
            self.config_manager.reload_config_from_file(file_path)


class ConfigManager:
    """Enhanced configuration manager with hot reload support."""

    def __init__(self) -> None:
        self._config: RezProxyConfig | None = None
        self._observers: list[Any] = []
        self._change_callbacks: list[Callable[[RezProxyConfig], None]] = []
        self._watched_files: dict[str, str] = {}  # file_path -> config_type
        self._lock = threading.RLock()

    def get_config(self) -> RezProxyConfig:
        """Get configuration instance with thread safety."""
        with self._lock:
            if self._config is None:
                self._config = RezProxyConfig()
                self._apply_rez_config(self._config)

                # Start hot reload if enabled
                if self._config.enable_hot_reload:
                    self._start_hot_reload()

            return self._config

    def reload_config(self) -> RezProxyConfig:
        """Reload configuration from environment and files."""
        with self._lock:
            old_config = self._config
            self._config = None
            new_config = self.get_config()

            # Notify callbacks of config change
            if old_config is not None:
                self._notify_config_change(new_config)

            return new_config

    def add_change_callback(self, callback: Callable[[RezProxyConfig], None]) -> None:
        """Add a callback to be called when configuration changes."""
        self._change_callbacks.append(callback)

    def remove_change_callback(
        self, callback: Callable[[RezProxyConfig], None]
    ) -> None:
        """Remove a configuration change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def _notify_config_change(self, new_config: RezProxyConfig) -> None:
        """Notify all callbacks of configuration change."""
        for callback in self._change_callbacks:
            try:
                callback(new_config)
            except Exception as e:
                print(f"⚠️ Error in config change callback: {e}")

    def _start_hot_reload(self) -> None:
        """Start file system monitoring for hot reload."""
        if not WATCHDOG_AVAILABLE:
            print("⚠️ Watchdog not available, hot reload disabled")
            return

        config = self._config
        if not config:
            return

        # Watch configuration file
        config_path = Path(config.config_file_path)
        if config_path.exists():
            self._watch_file(str(config_path), "main_config")

        # Watch additional config directories
        config_dir = config_path.parent
        if config_dir.exists():
            self._watch_directory(str(config_dir))

    def _watch_file(self, file_path: str, config_type: str) -> None:
        """Watch a specific file for changes."""
        self._watched_files[file_path] = config_type

        # Watch the directory containing the file
        directory = os.path.dirname(file_path)
        if directory and os.path.exists(directory):
            self._watch_directory(directory)

    def _watch_directory(self, directory: str) -> None:
        """Watch a directory for file changes."""
        if not WATCHDOG_AVAILABLE:
            return

        observer = Observer()
        event_handler = ConfigChangeHandler(self)
        observer.schedule(event_handler, directory, recursive=False)
        observer.start()
        self._observers.append(observer)
        print(f"📁 Watching directory for config changes: {directory}")

    def is_watched_file(self, file_path: str) -> bool:
        """Check if a file is being watched for configuration changes."""
        return file_path in self._watched_files

    def reload_config_from_file(self, file_path: str) -> None:
        """Reload configuration when a watched file changes."""
        config_type = self._watched_files.get(file_path)
        if not config_type:
            return

        print(f"🔄 Configuration file changed: {file_path}")

        try:
            if config_type == "main_config":
                self._reload_main_config(file_path)
            else:
                print(f"⚠️ Unknown config type: {config_type}")
        except Exception as e:
            print(f"❌ Error reloading config from {file_path}: {e}")

    def _reload_main_config(self, file_path: str) -> None:
        """Reload main configuration from JSON file."""
        try:
            with open(file_path) as f:
                config_data = json.load(f)

            # Update environment variables
            for key, value in config_data.items():
                if value is not None:
                    env_key = f"REZ_PROXY_API_{key.upper()}"
                    os.environ[env_key] = str(value)

            # Reload configuration
            self.reload_config()
            print(f"✅ Configuration reloaded from {file_path}")

        except Exception as e:
            print(f"❌ Error loading config file {file_path}: {e}")

    def save_config_to_file(
        self, config: RezProxyConfig, file_path: str | None = None
    ) -> None:
        """Save current configuration to a JSON file."""
        if file_path is None:
            file_path = config.config_file_path

        # Ensure directory exists
        config_dir = os.path.dirname(file_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        # Convert config to dict, excluding sensitive data
        config_dict = config.model_dump()

        # Remove sensitive fields
        sensitive_fields = ["api_key"]
        for field in sensitive_fields:
            config_dict.pop(field, None)

        try:
            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)
            print(f"💾 Configuration saved to {file_path}")
        except Exception as e:
            print(f"❌ Error saving config to {file_path}: {e}")

    def stop_hot_reload(self) -> None:
        """Stop all file system observers."""
        for observer in self._observers:
            observer.stop()
            observer.join()
        self._observers.clear()
        print("🛑 Hot reload stopped")

    def _apply_rez_config(self, config: RezProxyConfig) -> None:
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


# Global configuration manager instance
_config_manager = ConfigManager()


_config: RezProxyConfig | None = None


def get_config() -> RezProxyConfig:
    """Get configuration instance using the global config manager."""
    return _config_manager.get_config()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return _config_manager


def reload_config() -> RezProxyConfig:
    """Reload configuration using the config manager."""
    return _config_manager.reload_config()


def set_rez_config_from_dict(config_dict: dict) -> None:
    """Set Rez configuration from dictionary (useful for testing)."""
    for key, value in config_dict.items():
        if value is not None:
            env_key = f"REZ_PROXY_API_{key.upper()}"
            os.environ[env_key] = str(value)

    # Reload config to apply changes
    reload_config()


def add_config_change_callback(callback: Callable[[RezProxyConfig], None]) -> None:
    """Add a callback to be called when configuration changes."""
    _config_manager.add_change_callback(callback)


def remove_config_change_callback(callback: Callable[[RezProxyConfig], None]) -> None:
    """Remove a configuration change callback."""
    _config_manager.remove_change_callback(callback)


def save_config_to_file(
    config: RezProxyConfig | None = None, file_path: str | None = None
) -> None:
    """Save configuration to a JSON file."""
    if config is None:
        config = get_config()
    _config_manager.save_config_to_file(config, file_path)


def stop_config_hot_reload() -> None:
    """Stop configuration hot reload monitoring."""
    _config_manager.stop_hot_reload()
