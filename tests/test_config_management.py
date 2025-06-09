"""
Tests for configuration management functionality.
"""

import json
import os
import tempfile
import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rez_proxy.config import (
    ConfigChangeHandler,
    ConfigManager,
    RezProxyConfig,
    get_config,
    get_config_manager,
    reload_config,
    stop_config_hot_reload,
)
from rez_proxy.main import create_app
from rez_proxy.utils.config_utils import (
    apply_config_template,
    backup_config_file,
    create_default_config_file,
    get_config_diff,
    merge_config_files,
    restore_config_from_backup,
    validate_config_file,
)


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config_data = {
            "host": "localhost",
            "port": 8000,
            "log_level": "info",
            "enable_hot_reload": False,
        }
        json.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def config_manager():
    """Create a fresh config manager for testing."""
    return ConfigManager()


class TestConfigManager:
    """Test configuration manager functionality."""

    def test_get_config(self, config_manager):
        """Test getting configuration."""
        config = config_manager.get_config()
        assert isinstance(config, RezProxyConfig)
        assert config.host == "localhost"
        assert config.port == 8000

    def test_reload_config(self, config_manager):
        """Test configuration reload."""
        # Set environment variable
        os.environ["REZ_PROXY_API_HOST"] = "testhost"

        try:
            config = config_manager.reload_config()
            assert config.host == "testhost"
        finally:
            # Cleanup
            os.environ.pop("REZ_PROXY_API_HOST", None)

    def test_config_change_callback(self, config_manager):
        """Test configuration change callbacks."""
        callback_called = []

        def test_callback(config):
            callback_called.append(config)

        # Initialize config first
        config_manager.get_config()

        config_manager.add_change_callback(test_callback)

        # Trigger config reload
        config_manager.reload_config()

        assert len(callback_called) == 1
        assert isinstance(callback_called[0], RezProxyConfig)

        # Remove callback
        config_manager.remove_change_callback(test_callback)

        # Trigger another reload
        config_manager.reload_config()

        # Should still be 1 (callback removed)
        assert len(callback_called) == 1


class TestConfigUtils:
    """Test configuration utility functions."""

    def test_create_default_config_file(self):
        """Test creating default configuration file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            create_default_config_file(temp_path)

            assert os.path.exists(temp_path)

            with open(temp_path) as f:
                config_data = json.load(f)

            assert "host" in config_data
            assert "port" in config_data
            assert config_data["host"] == "localhost"
            assert config_data["port"] == 8000

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_validate_config_file(self, temp_config_file):
        """Test configuration file validation."""
        result = validate_config_file(temp_config_file)

        assert result["valid"] is True
        assert isinstance(result["config"], dict)
        assert len(result["errors"]) == 0

    def test_validate_invalid_config_file(self):
        """Test validation of invalid configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write invalid JSON
            f.write('{"invalid": json}')
            temp_path = f.name

        try:
            result = validate_config_file(temp_path)

            assert result["valid"] is False
            assert len(result["errors"]) > 0

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_backup_and_restore_config(self, temp_config_file):
        """Test configuration backup and restore."""
        # Create backup
        backup_path = backup_config_file(temp_config_file)

        assert os.path.exists(backup_path)

        # Modify original file
        with open(temp_config_file, "w") as f:
            json.dump({"host": "modified", "port": 9000}, f)

        # Restore from backup
        restore_config_from_backup(backup_path, temp_config_file)

        # Verify restoration
        with open(temp_config_file) as f:
            restored_config = json.load(f)

        assert restored_config["host"] == "localhost"
        assert restored_config["port"] == 8000

        # Cleanup backup
        if os.path.exists(backup_path):
            os.unlink(backup_path)

    def test_config_diff(self):
        """Test configuration file diff."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
            json.dump({"host": "localhost", "port": 8000, "workers": 1}, f1)
            file1_path = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
            json.dump({"host": "remotehost", "port": 8000, "log_level": "debug"}, f2)
            file2_path = f2.name

        try:
            diff = get_config_diff(file1_path, file2_path)

            assert "host" in diff["changed"]
            assert diff["changed"]["host"]["old"] == "localhost"
            assert diff["changed"]["host"]["new"] == "remotehost"

            assert "workers" in diff["removed"]
            assert "log_level" in diff["added"]
            assert "port" in diff["unchanged"]

        finally:
            for path in [file1_path, file2_path]:
                if os.path.exists(path):
                    os.unlink(path)


class TestConfigAPI:
    """Test configuration management API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    def test_get_current_config(self, client):
        """Test getting current configuration via API."""
        response = client.get("/api/v1/config-management/current")

        assert response.status_code == 200
        data = response.json()

        assert "config" in data
        assert "hot_reload_enabled" in data
        assert "config_file_path" in data

        config = data["config"]
        assert "host" in config
        assert "port" in config

    def test_update_config(self, client):
        """Test updating configuration via API."""
        update_data = {
            "config": {"log_level": "debug", "cache_ttl": 600},
            "save_to_file": False,
        }

        response = client.post("/api/v1/config-management/update", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "log_level" in data["updated_fields"]
        assert "cache_ttl" in data["updated_fields"]

    def test_update_config_invalid_field(self, client):
        """Test updating configuration with invalid field."""
        update_data = {"config": {"invalid_field": "value"}}

        response = client.post("/api/v1/config-management/update", json=update_data)

        assert response.status_code == 400
        assert "Invalid configuration fields" in response.json()["detail"]

    def test_reload_config(self, client):
        """Test reloading configuration via API."""
        response = client.post("/api/v1/config-management/reload")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "hot_reload_enabled" in data

    def test_get_config_schema(self, client):
        """Test getting configuration schema."""
        response = client.get("/api/v1/config-management/schema")

        assert response.status_code == 200
        data = response.json()

        assert "schema" in data
        assert "properties" in data["schema"]

        # Check that sensitive fields are removed
        assert "api_key" not in data["schema"]["properties"]

    def test_hot_reload_status(self, client):
        """Test getting hot reload status."""
        response = client.get("/api/v1/config-management/hot-reload/status")

        assert response.status_code == 200
        data = response.json()

        assert "enabled" in data
        assert "config_file_path" in data
        assert "watch_interval" in data
        assert "watched_files" in data
        assert "active_observers" in data


class TestConfigChangeHandler:
    """Test configuration change handler functionality."""

    def test_config_change_handler_init(self):
        """Test ConfigChangeHandler initialization."""
        config_manager = ConfigManager()
        handler = ConfigChangeHandler(config_manager)

        assert handler.config_manager is config_manager
        assert isinstance(handler.last_modified, dict)

    def test_on_modified_directory_event(self):
        """Test handling directory modification events."""
        config_manager = ConfigManager()
        handler = ConfigChangeHandler(config_manager)

        # Mock directory event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = "/some/directory"

        # Should not process directory events
        handler.on_modified(mock_event)

        # No files should be tracked
        assert len(handler.last_modified) == 0

    @patch("time.time")
    def test_on_modified_debouncing(self, mock_time):
        """Test file modification debouncing."""
        config_manager = ConfigManager()
        handler = ConfigChangeHandler(config_manager)

        # Mock file event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/config/test.json"

        # First modification
        mock_time.return_value = 1000.0
        handler.config_manager.is_watched_file = MagicMock(return_value=True)
        handler.config_manager.reload_config_from_file = MagicMock()

        handler.on_modified(mock_event)

        # Should process first modification
        assert handler.config_manager.reload_config_from_file.call_count == 1

        # Second modification within debounce period
        mock_time.return_value = 1000.3  # 0.3 seconds later
        handler.on_modified(mock_event)

        # Should not process due to debouncing
        assert handler.config_manager.reload_config_from_file.call_count == 1

        # Third modification after debounce period
        mock_time.return_value = 1001.0  # 1 second later
        handler.on_modified(mock_event)

        # Should process after debounce period
        assert handler.config_manager.reload_config_from_file.call_count == 2


class TestConfigManagerAdvanced:
    """Test advanced configuration manager functionality."""

    def test_config_manager_thread_safety(self):
        """Test configuration manager thread safety."""
        config_manager = ConfigManager()
        results = []
        errors = []

        def worker():
            try:
                for _ in range(10):
                    config = config_manager.get_config()
                    results.append(config.host)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0
        assert len(results) == 50  # 5 threads * 10 iterations
        assert all(host == "localhost" for host in results)

    def test_config_manager_callback_management(self):
        """Test configuration change callback management."""
        config_manager = ConfigManager()
        callback_calls = []

        def test_callback(config):
            callback_calls.append(config.host)

        # Initialize config first
        config_manager.get_config()

        # Add callback
        config_manager.add_change_callback(test_callback)

        # Trigger config reload
        config_manager.reload_config()

        assert len(callback_calls) == 1
        assert callback_calls[0] == "localhost"

        # Remove callback
        config_manager.remove_change_callback(test_callback)

        # Trigger another reload
        config_manager.reload_config()

        # Should still be 1 (callback removed)
        assert len(callback_calls) == 1

    def test_config_manager_save_config(self):
        """Test saving configuration to file."""
        config_manager = ConfigManager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            config = config_manager.get_config()
            config_manager.save_config_to_file(config, temp_path)

            assert os.path.exists(temp_path)

            with open(temp_path) as f:
                saved_config = json.load(f)

            assert "host" in saved_config
            assert "port" in saved_config
            assert saved_config["host"] == "localhost"
            assert saved_config["port"] == 8000

            # Sensitive fields should be removed
            assert "api_key" not in saved_config

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("rez_proxy.config.WATCHDOG_AVAILABLE", True)
    @patch("rez_proxy.config.Observer")
    def test_config_manager_hot_reload_start(self, mock_observer_class):
        """Test starting hot reload functionality."""
        mock_observer = MagicMock()
        mock_observer_class.return_value = mock_observer

        config_manager = ConfigManager()

        # Set up config with hot reload enabled
        os.environ["REZ_PROXY_API_ENABLE_HOT_RELOAD"] = "true"
        os.environ["REZ_PROXY_API_CONFIG_FILE_PATH"] = "config/test.json"

        try:
            # Create config directory
            os.makedirs("config", exist_ok=True)

            # Create config file
            with open("config/test.json", "w") as f:
                json.dump({"host": "localhost", "port": 8000}, f)

            # Get config (should start hot reload)
            config = config_manager.get_config()

            assert config.enable_hot_reload is True
            assert mock_observer.start.called
            assert len(config_manager._observers) > 0

        finally:
            # Cleanup
            config_manager.stop_hot_reload()
            os.environ.pop("REZ_PROXY_API_ENABLE_HOT_RELOAD", None)
            os.environ.pop("REZ_PROXY_API_CONFIG_FILE_PATH", None)
            if os.path.exists("config/test.json"):
                os.unlink("config/test.json")
            if os.path.exists("config"):
                import shutil

                shutil.rmtree("config", ignore_errors=True)

    def test_config_manager_stop_hot_reload(self):
        """Test stopping hot reload functionality."""
        config_manager = ConfigManager()

        # Mock observers
        mock_observer1 = MagicMock()
        mock_observer2 = MagicMock()
        config_manager._observers = [mock_observer1, mock_observer2]

        # Stop hot reload
        config_manager.stop_hot_reload()

        # Check that observers were stopped
        assert mock_observer1.stop.called
        assert mock_observer1.join.called
        assert mock_observer2.stop.called
        assert mock_observer2.join.called
        assert len(config_manager._observers) == 0


class TestConfigUtilsAdvanced:
    """Test advanced configuration utility functions."""

    def test_merge_config_files(self):
        """Test merging configuration files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
            json.dump({"host": "localhost", "port": 8000, "workers": 1}, f1)
            base_file = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
            json.dump({"host": "remotehost", "log_level": "debug"}, f2)
            override_file = f2.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f3:
            output_file = f3.name

        try:
            merge_config_files(base_file, override_file, output_file)

            with open(output_file) as f:
                merged_config = json.load(f)

            # Check merged values
            assert merged_config["host"] == "remotehost"  # Override
            assert merged_config["port"] == 8000  # Base
            assert merged_config["workers"] == 1  # Base
            assert merged_config["log_level"] == "debug"  # Override

        finally:
            for path in [base_file, override_file, output_file]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_apply_config_template(self):
        """Test applying variables to configuration template."""
        template_content = """
        {
            "host": "${HOST}",
            "port": ${PORT},
            "log_level": "${LOG_LEVEL}",
            "workers": ${WORKERS}
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
            f1.write(template_content)
            template_file = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
            output_file = f2.name

        try:
            variables = {
                "HOST": "production.example.com",
                "PORT": "9000",
                "LOG_LEVEL": "info",
                "WORKERS": "4",
            }

            apply_config_template(template_file, variables, output_file)

            with open(output_file) as f:
                config = json.load(f)

            assert config["host"] == "production.example.com"
            assert config["port"] == 9000
            assert config["log_level"] == "info"
            assert config["workers"] == 4

        finally:
            for path in [template_file, output_file]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_watch_config_changes_decorator(self):
        """Test configuration change watching decorator."""
        from rez_proxy.utils.config_utils import watch_config_changes

        callback_calls = []

        def config_change_callback(config):
            callback_calls.append(config.host)

        @watch_config_changes(config_change_callback)
        def test_function():
            # Initialize config first
            get_config()
            # Trigger config change while callback is registered
            reload_config()
            return "test_result"

        # Execute function
        result = test_function()

        assert result == "test_result"

        # Check that callback was called during function execution
        assert len(callback_calls) > 0


class TestConfigIntegrationAdvanced:
    """Test advanced configuration integration scenarios."""

    def test_config_hot_reload_integration(self):
        """Test complete hot reload integration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            initial_config = {
                "host": "localhost",
                "port": 8000,
                "enable_hot_reload": True,
                "config_file_path": f.name,
            }
            json.dump(initial_config, f)
            config_file = f.name

        try:
            # Set environment to use our test config
            os.environ["REZ_PROXY_API_CONFIG_FILE_PATH"] = config_file
            os.environ["REZ_PROXY_API_ENABLE_HOT_RELOAD"] = "true"

            # Get initial config
            config = get_config()
            assert config.host == "localhost"
            assert config.port == 8000

            # Modify config file
            updated_config = initial_config.copy()
            updated_config["host"] = "updated-host"
            updated_config["port"] = 9000

            with open(config_file, "w") as f:
                json.dump(updated_config, f)

            # Manually trigger reload from file (simulating file change)
            config_manager = get_config_manager()
            config_manager._reload_main_config(config_file)

            # Get updated config
            new_config = get_config()
            assert new_config.host == "updated-host"
            assert new_config.port == 9000

        finally:
            # Cleanup
            os.environ.pop("REZ_PROXY_API_CONFIG_FILE_PATH", None)
            os.environ.pop("REZ_PROXY_API_ENABLE_HOT_RELOAD", None)
            if os.path.exists(config_file):
                os.unlink(config_file)
            stop_config_hot_reload()

    def test_config_validation_integration(self):
        """Test configuration validation integration."""
        # Test valid config
        valid_config_data = {
            "host": "localhost",
            "port": 8000,
            "log_level": "info",
            "workers": 1,
        }

        # Create valid config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_config_data, f)
            temp_config_file = f.name

        try:
            result = validate_config_file(temp_config_file)
            assert result["valid"] is True
            assert len(result["errors"]) == 0

            # Test invalid config
            invalid_config_data = {
                "host": "localhost",
                "port": "invalid_port",  # Should be integer
                "workers": -1,  # Should be positive
                "invalid_field": "value",  # Should not exist
            }

            # Create invalid config file
            with open(temp_config_file, "w") as f:
                json.dump(invalid_config_data, f)

            result = validate_config_file(temp_config_file)
            assert result["valid"] is False
            assert len(result["errors"]) > 0

        finally:
            if os.path.exists(temp_config_file):
                os.unlink(temp_config_file)
