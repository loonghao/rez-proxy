"""
Test core rez_config functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rez_proxy.core.rez_config import (
    RezConfigManager,
    RezEnvironmentInfo,
    get_rez_config_manager,
    rez_config_manager,
)


class TestRezEnvironmentInfo:
    """Test RezEnvironmentInfo dataclass."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        info = RezEnvironmentInfo()

        assert info.config_file is None
        assert info.packages_paths == []
        assert info.local_packages_path is None
        assert info.release_packages_paths == []
        assert info.tmpdir is None
        assert info.cache_path is None
        assert info.home_config_disabled is False
        assert info.quiet_mode is False
        assert info.debug_mode is False
        assert info.environment_variables == {}

    def test_init_with_values(self):
        """Test initialization with values."""
        info = RezEnvironmentInfo(
            config_file="/path/to/config",
            packages_paths=["/path1", "/path2"],
            local_packages_path="/local/path",
            release_packages_paths=["/release/path"],
            tmpdir="/tmp",
            cache_path="/cache",
            home_config_disabled=True,
            quiet_mode=True,
            debug_mode=True,
            environment_variables={"REZ_TEST": "value"},
        )

        assert info.config_file == "/path/to/config"
        assert info.packages_paths == ["/path1", "/path2"]
        assert info.local_packages_path == "/local/path"
        assert info.release_packages_paths == ["/release/path"]
        assert info.tmpdir == "/tmp"
        assert info.cache_path == "/cache"
        assert info.home_config_disabled is True
        assert info.quiet_mode is True
        assert info.debug_mode is True
        assert info.environment_variables == {"REZ_TEST": "value"}

    def test_post_init_none_lists(self):
        """Test post_init handles None lists."""
        info = RezEnvironmentInfo(
            packages_paths=None, release_packages_paths=None, environment_variables=None
        )

        assert info.packages_paths == []
        assert info.release_packages_paths == []
        assert info.environment_variables == {}


class TestRezConfigManager:
    """Test RezConfigManager class."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        with patch("rez_proxy.core.rez_config.get_config"):
            return RezConfigManager()

    def test_init(self, manager):
        """Test manager initialization."""
        assert manager._environment_info is None

    @patch.dict(
        os.environ,
        {
            "REZ_CONFIG_FILE": "/test/config",
            "REZ_PACKAGES_PATH": "/path1:/path2",
            "REZ_LOCAL_PACKAGES_PATH": "/local",
            "REZ_RELEASE_PACKAGES_PATH": "/release1:/release2",
            "REZ_TMPDIR": "/tmp",
            "REZ_CACHE_PACKAGES_PATH": "/cache",
            "REZ_DISABLE_HOME_CONFIG": "1",
            "REZ_QUIET": "1",
            "REZ_DEBUG": "1",
            "REZ_TEST_VAR": "test_value",
        },
    )
    def test_detect_environment_full(self, manager):
        """Test environment detection with full environment."""
        info = manager._detect_environment()

        assert info.config_file == "/test/config"
        assert info.packages_paths == ["/path1", "/path2"]
        assert info.local_packages_path == "/local"
        assert info.release_packages_paths == ["/release1", "/release2"]
        assert info.tmpdir == "/tmp"
        assert info.cache_path == "/cache"
        assert info.home_config_disabled is True
        assert info.quiet_mode is True
        assert info.debug_mode is True
        assert "REZ_TEST_VAR" in info.environment_variables
        assert info.environment_variables["REZ_TEST_VAR"] == "test_value"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_environment_empty(self, manager):
        """Test environment detection with empty environment."""
        info = manager._detect_environment()

        assert info.config_file is None
        assert info.packages_paths == []
        assert info.local_packages_path is None
        assert info.release_packages_paths == []
        assert info.tmpdir is None
        assert info.cache_path is None
        assert info.home_config_disabled is False
        assert info.quiet_mode is False
        assert info.debug_mode is False
        assert info.environment_variables == {}

    def test_parse_path_list_unix(self, manager):
        """Test path list parsing with Unix separators."""
        with patch("sys.platform", "linux"):
            result = manager._parse_path_list("/path1:/path2:/path3")
            assert result == ["/path1", "/path2", "/path3"]

    def test_parse_path_list_windows(self, manager):
        """Test path list parsing with Windows separators."""
        with patch("sys.platform", "win32"):
            result = manager._parse_path_list("C:\\path1;D:\\path2;E:\\path3")
            assert result == ["C:\\path1", "D:\\path2", "E:\\path3"]

    def test_parse_path_list_empty(self, manager):
        """Test path list parsing with empty string."""
        result = manager._parse_path_list("")
        assert result == []

    def test_parse_path_list_whitespace(self, manager):
        """Test path list parsing with whitespace."""
        with patch("sys.platform", "linux"):
            result = manager._parse_path_list(" /path1 : /path2 : /path3 ")
            assert result == ["/path1", "/path2", "/path3"]

    def test_get_environment_info_cached(self, manager):
        """Test environment info caching."""
        with patch.object(manager, "_detect_environment") as mock_detect:
            mock_info = MagicMock()
            mock_detect.return_value = mock_info

            # First call
            result1 = manager.get_environment_info()
            assert result1 == mock_info
            assert mock_detect.call_count == 1

            # Second call should use cache
            result2 = manager.get_environment_info()
            assert result2 == mock_info
            assert mock_detect.call_count == 1

    def test_validate_configuration_no_warnings(self, manager):
        """Test configuration validation with no warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.py"
            config_file.write_text("# test config")

            packages_path = Path(tmpdir) / "packages"
            packages_path.mkdir()

            local_path = Path(tmpdir) / "local"
            local_path.mkdir()

            release_path = Path(tmpdir) / "release"
            release_path.mkdir()

            cache_path = Path(tmpdir) / "cache"
            cache_path.mkdir()

            info = RezEnvironmentInfo(
                config_file=str(config_file),
                packages_paths=[str(packages_path)],
                local_packages_path=str(local_path),
                release_packages_paths=[str(release_path)],
                tmpdir=str(tmpdir),
                cache_path=str(cache_path),
            )

            manager._environment_info = info
            warnings = manager.validate_configuration()
            assert warnings == []

    def test_validate_configuration_missing_config_file(self, manager):
        """Test configuration validation with missing config file."""
        info = RezEnvironmentInfo(config_file="/nonexistent/config.py")
        manager._environment_info = info

        warnings = manager.validate_configuration()
        assert len(warnings) == 1
        assert "config file not found" in warnings[0].lower()

    def test_validate_configuration_no_packages_paths(self, manager):
        """Test configuration validation with no packages paths."""
        info = RezEnvironmentInfo(packages_paths=[])
        manager._environment_info = info

        warnings = manager.validate_configuration()
        assert any("no rez packages paths configured" in w.lower() for w in warnings)

    def test_validate_configuration_missing_packages_path(self, manager):
        """Test configuration validation with missing packages path."""
        info = RezEnvironmentInfo(packages_paths=["/nonexistent/path"])
        manager._environment_info = info

        warnings = manager.validate_configuration()
        assert any("packages path does not exist" in w for w in warnings)

    def test_get_configuration_summary(self, manager):
        """Test configuration summary generation."""
        info = RezEnvironmentInfo(
            config_file="/test/config",
            packages_paths=["/packages"],
            local_packages_path="/local",
            environment_variables={"REZ_TEST": "value"},
        )
        manager._environment_info = info

        with patch.object(manager, "validate_configuration", return_value=[]):
            summary = manager.get_configuration_summary()

            assert summary["config_file"] == "/test/config"
            assert summary["packages_paths"] == ["/packages"]
            assert summary["local_packages_path"] == "/local"
            assert summary["environment_variables"] == {"REZ_TEST": "value"}
            assert summary["warnings"] == []
            assert summary["is_valid"] is True

    def test_apply_configuration_from_dict(self, manager):
        """Test applying configuration from dictionary."""
        config_dict = {
            "config_file": "/new/config",
            "packages_path": "/new/packages",
            "local_packages_path": "/new/local",
            "quiet": True,
            "debug": False,
        }

        with patch.dict(os.environ, {}, clear=True):
            manager.apply_configuration_from_dict(config_dict)

            assert os.environ["REZ_CONFIG_FILE"] == "/new/config"
            assert os.environ["REZ_PACKAGES_PATH"] == "/new/packages"
            assert os.environ["REZ_LOCAL_PACKAGES_PATH"] == "/new/local"
            assert os.environ["REZ_QUIET"] == "1"
            assert os.environ["REZ_DEBUG"] == "0"

    def test_apply_configuration_resets_cache(self, manager):
        """Test that applying configuration resets cache."""
        manager._environment_info = MagicMock()

        manager.apply_configuration_from_dict({"quiet": True})

        assert manager._environment_info is None

    def test_create_rez_config_template(self, manager):
        """Test creating Rez config template."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            template_path = f.name

        try:
            manager.create_rez_config_template(template_path)

            with open(template_path) as f:
                content = f.read()

            assert "packages_path" in content
            assert "local_packages_path" in content
            assert "rez_proxy_settings" in content
        finally:
            os.unlink(template_path)


def test_get_rez_config_manager():
    """Test getting global config manager."""
    manager = get_rez_config_manager()
    assert manager is rez_config_manager
    assert isinstance(manager, RezConfigManager)
