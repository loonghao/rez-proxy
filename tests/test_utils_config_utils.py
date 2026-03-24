"""
Tests for rez_proxy.utils.config_utils module.
"""

import json
import os
from unittest.mock import Mock, patch

from pyfakefs.fake_filesystem_unittest import TestCase

from rez_proxy.utils.config_utils import (
    apply_config_template,
    backup_config_file,
    create_default_config_file,
    get_config_diff,
    merge_config_files,
    restore_config_from_backup,
    validate_config_file,
    validate_config_file_data,
    watch_config_changes,
)


class TestCreateDefaultConfigFile(TestCase):
    """Test create_default_config_file function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_create_default_config_file_success(self):
        """Test creating default config file successfully."""
        config_path = "/test/config.json"

        with patch("builtins.print") as mock_print:
            create_default_config_file(config_path)

        # Check file was created
        self.assertTrue(os.path.exists(config_path))

        # Check file content
        with open(config_path) as f:
            config_data = json.load(f)

        # Should contain basic config fields but not sensitive ones
        self.assertIn("host", config_data)
        self.assertIn("port", config_data)
        self.assertNotIn("api_key", config_data)

        # Check print was called
        mock_print.assert_called_once()

    def test_create_default_config_file_creates_directory(self):
        """Test creating config file creates parent directories."""
        config_path = "/test/nested/dir/config.json"

        create_default_config_file(config_path)

        # Check directory was created
        self.assertTrue(os.path.exists("/test/nested/dir"))
        self.assertTrue(os.path.exists(config_path))

    def test_create_default_config_file_no_directory(self):
        """Test creating config file in current directory."""
        config_path = "config.json"

        create_default_config_file(config_path)

        self.assertTrue(os.path.exists(config_path))


class TestValidateConfigFile(TestCase):
    """Test validate_config_file function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_validate_config_file_not_found(self):
        """Test validation when config file doesn't exist."""
        result = validate_config_file("/nonexistent/config.json")

        self.assertFalse(result["valid"])
        self.assertIn("Configuration file not found", result["errors"][0])
        self.assertEqual(result["config"], None)

    def test_validate_config_file_invalid_json(self):
        """Test validation with invalid JSON."""
        config_path = "/test/config.json"
        self.fs.create_file(config_path, contents="invalid json {")

        result = validate_config_file(config_path)

        self.assertFalse(result["valid"])
        self.assertIn("Invalid JSON format", result["errors"][0])

    def test_validate_config_file_valid_config(self):
        """Test validation with valid configuration."""
        config_path = "/test/config.json"
        valid_config = {"host": "localhost", "port": 8000, "api_prefix": "/api"}
        self.fs.create_file(config_path, contents=json.dumps(valid_config))

        result = validate_config_file(config_path)

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIsNotNone(result["config"])

    def test_validate_config_file_unknown_fields(self):
        """Test validation with unknown fields."""
        config_path = "/test/config.json"
        config_with_unknown = {
            "host": "localhost",
            "port": 8000,
            "unknown_field": "value",
        }
        self.fs.create_file(config_path, contents=json.dumps(config_with_unknown))

        result = validate_config_file(config_path)

        self.assertTrue(result["valid"])
        self.assertIn("Unknown configuration fields", result["warnings"][0])

    def test_validate_config_file_missing_important_fields(self):
        """Test validation with missing important fields."""
        config_path = "/test/config.json"
        minimal_config = {"rez_debug": True}
        self.fs.create_file(config_path, contents=json.dumps(minimal_config))

        result = validate_config_file(config_path)

        self.assertTrue(result["valid"])
        self.assertIn("Missing important fields", result["warnings"][0])

    def test_validate_config_file_validation_error(self):
        """Test validation with schema validation error."""
        config_path = "/test/config.json"
        invalid_config = {
            "host": "localhost",
            "port": "invalid_port",  # Should be integer
        }
        self.fs.create_file(config_path, contents=json.dumps(invalid_config))

        result = validate_config_file(config_path)

        self.assertFalse(result["valid"])
        self.assertIn("Configuration validation error", result["errors"][0])


class TestValidateConfigFileData(TestCase):
    """Test validate_config_file_data function."""

    def test_validate_config_file_data_valid(self):
        """Test validation with valid config data."""
        config_data = {"host": "localhost", "port": 8000, "api_prefix": "/api"}

        result = validate_config_file_data(config_data)

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIsNotNone(result["config"])

    def test_validate_config_file_data_invalid(self):
        """Test validation with invalid config data."""
        config_data = {"host": "localhost", "port": "invalid_port"}

        result = validate_config_file_data(config_data)

        self.assertFalse(result["valid"])
        self.assertIn("Configuration validation error", result["errors"][0])

    def test_validate_config_file_data_unknown_fields(self):
        """Test validation with unknown fields."""
        config_data = {"host": "localhost", "port": 8000, "unknown_field": "value"}

        result = validate_config_file_data(config_data)

        self.assertTrue(result["valid"])
        self.assertIn("Unknown configuration fields", result["warnings"][0])


class TestMergeConfigFiles(TestCase):
    """Test merge_config_files function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_merge_config_files_success(self):
        """Test successful config file merging."""
        base_config = {"host": "localhost", "port": 8000, "rez_debug": False}
        override_config = {"port": 9000, "rez_debug": True, "workers": 4}

        base_path = "/test/base.json"
        override_path = "/test/override.json"
        output_path = "/test/merged.json"

        self.fs.create_file(base_path, contents=json.dumps(base_config))
        self.fs.create_file(override_path, contents=json.dumps(override_config))

        with patch("builtins.print") as mock_print:
            merge_config_files(base_path, override_path, output_path)

        # Check merged file was created
        self.assertTrue(os.path.exists(output_path))

        # Check merged content
        with open(output_path) as f:
            merged_data = json.load(f)

        expected = {
            "host": "localhost",  # from base
            "port": 9000,  # overridden
            "rez_debug": True,  # overridden
            "workers": 4,  # added
        }
        self.assertEqual(merged_data, expected)
        mock_print.assert_called_once()

    def test_merge_config_files_invalid_result(self):
        """Test merging that results in invalid configuration."""
        base_config = {"host": "localhost", "port": 8000}
        override_config = {"port": "invalid_port"}

        base_path = "/test/base.json"
        override_path = "/test/override.json"
        output_path = "/test/merged.json"

        self.fs.create_file(base_path, contents=json.dumps(base_config))
        self.fs.create_file(override_path, contents=json.dumps(override_config))

        with self.assertRaises(ValueError) as cm:
            merge_config_files(base_path, override_path, output_path)

        self.assertIn("Merged configuration is invalid", str(cm.exception))


class TestBackupConfigFile(TestCase):
    """Test backup_config_file function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_backup_config_file_success(self):
        """Test successful config file backup."""
        config_path = "/test/config.json"
        config_data = {"host": "localhost", "port": 8000}
        self.fs.create_file(config_path, contents=json.dumps(config_data))

        with patch("builtins.print") as mock_print:
            backup_path = backup_config_file(config_path)

        expected_backup = config_path + ".backup"
        self.assertEqual(backup_path, expected_backup)
        self.assertTrue(os.path.exists(backup_path))

        # Check backup content matches original
        with open(backup_path) as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data, config_data)
        mock_print.assert_called_once()

    def test_backup_config_file_not_found(self):
        """Test backup when config file doesn't exist."""
        with self.assertRaises(FileNotFoundError) as cm:
            backup_config_file("/nonexistent/config.json")

        self.assertIn("Configuration file not found", str(cm.exception))

    def test_backup_config_file_existing_backup(self):
        """Test backup when backup already exists."""
        config_path = "/test/config.json"
        backup_path = config_path + ".backup"

        config_data = {"host": "localhost", "port": 8000}
        self.fs.create_file(config_path, contents=json.dumps(config_data))
        self.fs.create_file(backup_path, contents="existing backup")

        with patch("time.time", return_value=1234567890):
            result_backup = backup_config_file(config_path)

        expected_backup = f"{config_path}.backup.1234567890"
        self.assertEqual(result_backup, expected_backup)
        self.assertTrue(os.path.exists(expected_backup))

    def test_backup_config_file_custom_suffix(self):
        """Test backup with custom suffix."""
        config_path = "/test/config.json"
        config_data = {"host": "localhost", "port": 8000}
        self.fs.create_file(config_path, contents=json.dumps(config_data))

        backup_path = backup_config_file(config_path, ".old")

        expected_backup = config_path + ".old"
        self.assertEqual(backup_path, expected_backup)
        self.assertTrue(os.path.exists(backup_path))


class TestRestoreConfigFromBackup(TestCase):
    """Test restore_config_from_backup function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_restore_config_from_backup_success(self):
        """Test successful config restoration."""
        backup_path = "/test/config.backup"
        target_path = "/test/config.json"

        backup_data = {"host": "localhost", "port": 8000}
        self.fs.create_file(backup_path, contents=json.dumps(backup_data))

        with patch("builtins.print") as mock_print:
            restore_config_from_backup(backup_path, target_path)

        self.assertTrue(os.path.exists(target_path))

        # Check restored content
        with open(target_path) as f:
            restored_data = json.load(f)
        self.assertEqual(restored_data, backup_data)
        mock_print.assert_called_once()

    def test_restore_config_from_backup_not_found(self):
        """Test restoration when backup doesn't exist."""
        with self.assertRaises(FileNotFoundError) as cm:
            restore_config_from_backup("/nonexistent/backup", "/test/config.json")

        self.assertIn("Backup file not found", str(cm.exception))

    def test_restore_config_from_backup_invalid(self):
        """Test restoration with invalid backup."""
        backup_path = "/test/config.backup"
        target_path = "/test/config.json"

        # Create invalid backup
        invalid_backup = {"port": "invalid_port"}
        self.fs.create_file(backup_path, contents=json.dumps(invalid_backup))

        with self.assertRaises(ValueError) as cm:
            restore_config_from_backup(backup_path, target_path)

        self.assertIn("Backup configuration is invalid", str(cm.exception))


class TestGetConfigDiff(TestCase):
    """Test get_config_diff function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_get_config_diff_success(self):
        """Test successful config diff."""
        config1 = {"host": "localhost", "port": 8000, "debug": False}
        config2 = {"host": "localhost", "port": 9000, "workers": 4}

        file1_path = "/test/config1.json"
        file2_path = "/test/config2.json"

        self.fs.create_file(file1_path, contents=json.dumps(config1))
        self.fs.create_file(file2_path, contents=json.dumps(config2))

        diff = get_config_diff(file1_path, file2_path)

        self.assertEqual(diff["unchanged"]["host"], "localhost")
        self.assertEqual(diff["changed"]["port"]["old"], 8000)
        self.assertEqual(diff["changed"]["port"]["new"], 9000)
        self.assertEqual(diff["removed"]["debug"], False)
        self.assertEqual(diff["added"]["workers"], 4)

    def test_get_config_diff_identical(self):
        """Test diff with identical configs."""
        config = {"host": "localhost", "port": 8000}

        file1_path = "/test/config1.json"
        file2_path = "/test/config2.json"

        self.fs.create_file(file1_path, contents=json.dumps(config))
        self.fs.create_file(file2_path, contents=json.dumps(config))

        diff = get_config_diff(file1_path, file2_path)

        self.assertEqual(diff["unchanged"], config)
        self.assertEqual(diff["added"], {})
        self.assertEqual(diff["removed"], {})
        self.assertEqual(diff["changed"], {})


class TestApplyConfigTemplate(TestCase):
    """Test apply_config_template function."""

    def setUp(self):
        """Set up test environment."""
        self.setUpPyfakefs()

    def test_apply_config_template_success(self):
        """Test successful template application."""
        template_content = """
        {
            "host": "${HOST}",
            "port": ${PORT},
            "rez_debug": ${DEBUG}
        }
        """

        template_path = "/test/template.json"
        output_path = "/test/config.json"

        self.fs.create_file(template_path, contents=template_content)

        variables = {"HOST": "localhost", "PORT": "8000", "DEBUG": "true"}

        with patch("builtins.print") as mock_print:
            apply_config_template(template_path, variables, output_path)

        self.assertTrue(os.path.exists(output_path))

        # Check output content
        with open(output_path) as f:
            config_data = json.load(f)

        expected = {"host": "localhost", "port": 8000, "rez_debug": True}
        self.assertEqual(config_data, expected)
        mock_print.assert_called_once()

    def test_apply_config_template_invalid_json(self):
        """Test template that results in invalid JSON."""
        template_content = """
        {
            "host": "${HOST}",
            "port": ${PORT}
        """  # Missing closing brace

        template_path = "/test/template.json"
        output_path = "/test/config.json"

        self.fs.create_file(template_path, contents=template_content)

        variables = {"HOST": "localhost", "PORT": "8000"}

        with self.assertRaises(ValueError) as cm:
            apply_config_template(template_path, variables, output_path)

        self.assertIn("Template resulted in invalid JSON", str(cm.exception))

    def test_apply_config_template_invalid_config(self):
        """Test template that results in invalid configuration."""
        template_content = """
        {
            "host": "${HOST}",
            "port": "${PORT}"
        }
        """

        template_path = "/test/template.json"
        output_path = "/test/config.json"

        self.fs.create_file(template_path, contents=template_content)

        variables = {"HOST": "localhost", "PORT": "invalid_port"}

        with self.assertRaises(ValueError) as cm:
            apply_config_template(template_path, variables, output_path)

        self.assertIn("Template configuration is invalid", str(cm.exception))


class TestWatchConfigChanges(TestCase):
    """Test watch_config_changes decorator."""

    def test_watch_config_changes_decorator(self):
        """Test the config changes decorator."""
        callback_func = Mock()
        mock_config_manager = Mock()

        with patch(
            "rez_proxy.utils.config_utils.get_config_manager",
            return_value=mock_config_manager,
        ):

            @watch_config_changes(callback_func)
            def test_function():
                return "test_result"

            result = test_function()

        self.assertEqual(result, "test_result")
        mock_config_manager.add_change_callback.assert_called_once_with(callback_func)
        mock_config_manager.remove_change_callback.assert_called_once_with(
            callback_func
        )

    def test_watch_config_changes_decorator_with_exception(self):
        """Test decorator when wrapped function raises exception."""
        callback_func = Mock()
        mock_config_manager = Mock()

        with patch(
            "rez_proxy.utils.config_utils.get_config_manager",
            return_value=mock_config_manager,
        ):

            @watch_config_changes(callback_func)
            def test_function():
                raise ValueError("Test error")

            with self.assertRaises(ValueError):
                test_function()

        # Should still remove callback even when exception occurs
        mock_config_manager.add_change_callback.assert_called_once_with(callback_func)
        mock_config_manager.remove_change_callback.assert_called_once_with(
            callback_func
        )
