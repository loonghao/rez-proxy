"""
Test core platform detection functionality.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from rez_proxy.core.context import get_effective_platform_info
from rez_proxy.core.platform import (
    BuildSystemService,
    PlatformAwareService,
    RezConfigService,
    ShellService,
)
from rez_proxy.models.schemas import PlatformInfo


class TestPlatformAwareService:
    """Test PlatformAwareService class."""

    @patch("rez_proxy.core.platform.get_effective_platform_info")
    def test_get_platform_info(self, mock_get_platform):
        """Test getting platform info."""
        mock_platform = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )
        mock_get_platform.return_value = mock_platform

        service = PlatformAwareService()
        result = service.get_platform_info()

        assert result == mock_platform
        mock_get_platform.assert_called_once()

    @patch("rez_proxy.core.platform.get_effective_platform_info")
    def test_get_platform_specific_config(self, mock_get_platform):
        """Test getting platform-specific config."""
        mock_platform = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )
        mock_get_platform.return_value = mock_platform

        service = PlatformAwareService()
        config = service.get_platform_specific_config()

        assert config["platform"] == "linux"
        assert config["arch"] == "x86_64"
        assert config["os"] == "ubuntu-20.04"
        assert config["python_version"] == "3.9.0"
        assert config["rez_version"] == "3.2.1"

    @patch("rez_proxy.core.platform.get_effective_platform_info")
    def test_is_platform_compatible(self, mock_get_platform):
        """Test platform compatibility check."""
        mock_platform = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )
        mock_get_platform.return_value = mock_platform

        service = PlatformAwareService()

        # Test compatible platform
        assert service.is_platform_compatible("linux") is True

        # Test incompatible platform
        assert service.is_platform_compatible("windows") is False

        # Test no requirement
        assert service.is_platform_compatible(None) is True


class TestPlatformInfoModel:
    """Test PlatformInfo model."""

    def test_platform_info_creation(self):
        """Test PlatformInfo model creation."""
        info = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )

        assert info.platform == "linux"
        assert info.arch == "x86_64"
        assert info.os == "ubuntu-20.04"
        assert info.python_version == "3.9.0"
        assert info.rez_version == "3.2.1"

    def test_platform_info_serialization(self):
        """Test PlatformInfo serialization."""
        info = PlatformInfo(
            platform="linux",
            arch="x86_64",
            os="ubuntu-20.04",
            python_version="3.9.0",
            rez_version="3.2.1",
        )

        # Test dict conversion
        data = info.model_dump()
        expected = {
            "platform": "linux",
            "arch": "x86_64",
            "os": "ubuntu-20.04",
            "python_version": "3.9.0",
            "rez_version": "3.2.1",
        }
        assert data == expected

    def test_platform_info_from_dict(self):
        """Test PlatformInfo creation from dict."""
        data = {
            "platform": "windows",
            "arch": "x86_64",
            "os": "windows-10",
            "python_version": "3.8.0",
            "rez_version": "3.1.0",
        }

        info = PlatformInfo(**data)
        assert info.platform == "windows"
        assert info.arch == "x86_64"
        assert info.os == "windows-10"
        assert info.python_version == "3.8.0"
        assert info.rez_version == "3.1.0"


class TestRezConfigService:
    """Test RezConfigService class."""

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_packages_path_local_mode(self, mock_is_local):
        """Test getting packages path in local mode."""
        mock_is_local.return_value = True

        service = RezConfigService()

        with patch.object(
            service, "_get_local_packages_path", return_value=["/test/path"]
        ):
            result = service.get_packages_path()
            assert result == ["/test/path"]

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_packages_path_remote_mode(self, mock_is_local):
        """Test getting packages path in remote mode."""
        mock_is_local.return_value = False

        service = RezConfigService()
        result = service.get_packages_path()
        assert result == []

    def test_get_local_packages_path_success(self):
        """Test getting local packages path successfully."""
        service = RezConfigService()

        # Mock the import and config access
        with patch("builtins.__import__") as mock_import:
            mock_rez_config = MagicMock()
            mock_rez_config.config.packages_path = ["/path1", "/path2"]
            mock_import.return_value = mock_rez_config

            result = service._get_local_packages_path()
            assert result == ["/path1", "/path2"]

    def test_get_local_packages_path_string(self):
        """Test getting local packages path as string."""
        service = RezConfigService()

        with patch("builtins.__import__") as mock_import:
            mock_rez_config = MagicMock()
            mock_rez_config.config.packages_path = "/single/path"
            mock_import.return_value = mock_rez_config

            result = service._get_local_packages_path()
            assert result == ["/single/path"]

    def test_get_local_packages_path_empty(self):
        """Test getting local packages path when empty."""
        service = RezConfigService()

        with patch("builtins.__import__") as mock_import:
            mock_rez_config = MagicMock()
            mock_rez_config.config.packages_path = None
            mock_import.return_value = mock_rez_config

            result = service._get_local_packages_path()
            assert result == []

    def test_get_local_packages_path_exception(self):
        """Test getting local packages path with exception."""
        service = RezConfigService()

        with patch("builtins.__import__", side_effect=ImportError):
            result = service._get_local_packages_path()
            assert result == []

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_config_info_local_mode(self, mock_is_local):
        """Test getting config info in local mode."""
        mock_is_local.return_value = True

        service = RezConfigService()

        with patch.object(
            service, "get_platform_specific_config", return_value={"platform": "linux"}
        ):
            with patch("builtins.__import__") as mock_import:
                mock_rez_config = MagicMock()
                mock_rez_config.config.packages_path = ["/packages"]
                mock_rez_config.config.release_packages_path = ["/release"]
                mock_rez_config.config.local_packages_path = "/local"
                mock_rez_config.config.config_file = "/config"
                mock_import.return_value = mock_rez_config

                result = service.get_config_info()

                assert result["platform"] == "linux"
                assert result["packages_path"] == ["/packages"]
                assert result["release_packages_path"] == ["/release"]
                assert result["local_packages_path"] == "/local"
                assert result["config_file"] == "/config"

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_config_info_remote_mode(self, mock_is_local):
        """Test getting config info in remote mode."""
        mock_is_local.return_value = False

        service = RezConfigService()

        with patch.object(
            service, "get_platform_specific_config", return_value={"platform": "linux"}
        ):
            result = service.get_config_info()

            assert result["platform"] == "linux"
            assert result["packages_path"] == []
            assert "note" in result
            assert "remote mode" in result["note"].lower()

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_config_info_exception(self, mock_is_local):
        """Test getting config info with exception."""
        mock_is_local.return_value = True

        service = RezConfigService()

        with patch.object(
            service, "get_platform_specific_config", return_value={"platform": "linux"}
        ):
            with patch("builtins.__import__", side_effect=ImportError("Test error")):
                result = service.get_config_info()

                assert result["platform"] == "linux"
                assert result["config_error"] == "Test error"


class TestShellService:
    """Test ShellService class."""

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_available_shells_local_mode(self, mock_is_local):
        """Test getting available shells in local mode."""
        mock_is_local.return_value = True

        service = ShellService()

        with patch.object(
            service, "_get_local_shells", return_value=[{"name": "bash"}]
        ):
            result = service.get_available_shells()
            assert result == [{"name": "bash"}]

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_available_shells_remote_mode(self, mock_is_local):
        """Test getting available shells in remote mode."""
        mock_is_local.return_value = False

        service = ShellService()

        with patch.object(
            service, "_get_common_shells_for_platform", return_value=[{"name": "bash"}]
        ):
            result = service.get_available_shells()
            assert result == [{"name": "bash"}]

    def test_get_local_shells_success(self):
        """Test getting local shells successfully."""
        service = ShellService()

        mock_shell_class = MagicMock()
        mock_shell_class.name.return_value = "bash"
        mock_shell_class.executable = "bash"
        mock_shell_class.file_extension.return_value = ".sh"
        mock_shell_class.is_available.return_value = True
        mock_shell_class.executable_filepath.return_value = "/bin/bash"
        mock_shell_class.__doc__ = "Bash shell"

        with patch("builtins.__import__") as mock_import:
            mock_rez_shells = MagicMock()
            mock_rez_shells.get_shell_types.return_value = ["bash"]
            mock_rez_shells.get_shell_class.return_value = mock_shell_class
            mock_import.return_value = mock_rez_shells

            result = service._get_local_shells()

            assert len(result) == 1
            shell_info = result[0]
            assert shell_info["name"] == "bash"
            assert shell_info["executable"] == "bash"
            assert shell_info["file_extension"] == ".sh"
            assert shell_info["available"] is True
            assert shell_info["executable_path"] == "/bin/bash"
            assert shell_info["description"] == "Bash shell"

    def test_get_local_shells_exception(self):
        """Test getting local shells with exception."""
        service = ShellService()

        with patch("builtins.__import__") as mock_import:
            mock_rez_shells = MagicMock()
            mock_rez_shells.get_shell_types.return_value = ["bash"]
            mock_rez_shells.get_shell_class.side_effect = Exception
            mock_import.return_value = mock_rez_shells

            result = service._get_local_shells()

            assert len(result) == 1
            shell_info = result[0]
            assert shell_info["name"] == "bash"
            assert shell_info["available"] is False

    def test_get_common_shells_for_platform_linux(self):
        """Test getting common shells for Linux platform."""
        service = ShellService()

        with patch.object(service, "get_platform_info") as mock_get_platform:
            mock_platform = PlatformInfo(
                platform="linux",
                arch="x86_64",
                os="ubuntu-20.04",
                python_version="3.9.0",
            )
            mock_get_platform.return_value = mock_platform

            result = service._get_common_shells_for_platform()

            shell_names = [shell["name"] for shell in result]
            assert "bash" in shell_names
            assert "zsh" in shell_names
            assert "sh" in shell_names

    def test_get_common_shells_for_platform_windows(self):
        """Test getting common shells for Windows platform."""
        service = ShellService()

        with patch.object(service, "get_platform_info") as mock_get_platform:
            mock_platform = PlatformInfo(
                platform="windows",
                arch="x86_64",
                os="windows-10",
                python_version="3.9.0",
            )
            mock_get_platform.return_value = mock_platform

            result = service._get_common_shells_for_platform()

            shell_names = [shell["name"] for shell in result]
            assert "cmd" in shell_names
            assert "powershell" in shell_names
            assert "bash" in shell_names

            # Check Windows-specific shell info
            cmd_shell = next(s for s in result if s["name"] == "cmd")
            assert cmd_shell["executable"] == "cmd.exe"
            assert cmd_shell["file_extension"] == ".bat"

            ps_shell = next(s for s in result if s["name"] == "powershell")
            assert ps_shell["executable"] == "powershell.exe"
            assert ps_shell["file_extension"] == ".ps1"

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_shell_info_local_mode(self, mock_is_local):
        """Test getting shell info in local mode."""
        mock_is_local.return_value = True

        service = ShellService()

        with patch.object(
            service, "_get_local_shell_info", return_value={"name": "bash"}
        ):
            result = service.get_shell_info("bash")
            assert result == {"name": "bash"}

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_shell_info_remote_mode(self, mock_is_local):
        """Test getting shell info in remote mode."""
        mock_is_local.return_value = False

        service = ShellService()

        with patch.object(
            service, "_get_generic_shell_info", return_value={"name": "bash"}
        ):
            result = service.get_shell_info("bash")
            assert result == {"name": "bash"}

    def test_get_local_shell_info_success(self):
        """Test getting local shell info successfully."""
        service = ShellService()

        mock_shell_class = MagicMock()
        mock_shell_class.name.return_value = "bash"
        mock_shell_class.executable = "bash"
        mock_shell_class.file_extension.return_value = ".sh"
        mock_shell_class.is_available.return_value = True
        mock_shell_class.executable_filepath.return_value = "/bin/bash"
        mock_shell_class.__doc__ = "Bash shell"

        with patch("builtins.__import__") as mock_import:
            mock_rez_shells = MagicMock()
            mock_rez_shells.get_shell_class.return_value = mock_shell_class
            mock_import.return_value = mock_rez_shells

            result = service._get_local_shell_info("bash")

            assert result["name"] == "bash"
            assert result["executable"] == "bash"
            assert result["available"] is True
            assert result["executable_path"] == "/bin/bash"

    def test_get_local_shell_info_not_found(self):
        """Test getting local shell info for non-existent shell."""
        service = ShellService()

        with patch("builtins.__import__") as mock_import:
            mock_rez_shells = MagicMock()
            mock_rez_shells.get_shell_class.side_effect = Exception
            mock_import.return_value = mock_rez_shells

            with pytest.raises(HTTPException) as exc_info:
                service._get_local_shell_info("nonexistent")

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)

    def test_get_generic_shell_info_found(self):
        """Test getting generic shell info for existing shell."""
        service = ShellService()

        common_shells = [
            {"name": "bash", "executable": "bash"},
            {"name": "zsh", "executable": "zsh"},
        ]

        with patch.object(
            service, "_get_common_shells_for_platform", return_value=common_shells
        ):
            result = service._get_generic_shell_info("bash")
            assert result["name"] == "bash"

    def test_get_generic_shell_info_not_found(self):
        """Test getting generic shell info for non-existent shell."""
        service = ShellService()

        with patch.object(service, "_get_common_shells_for_platform", return_value=[]):
            with pytest.raises(HTTPException) as exc_info:
                service._get_generic_shell_info("nonexistent")

            assert exc_info.value.status_code == 404


class TestBuildSystemService:
    """Test BuildSystemService class."""

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_available_build_systems_local_mode(self, mock_is_local):
        """Test getting available build systems in local mode."""
        mock_is_local.return_value = True

        service = BuildSystemService()

        with patch.object(
            service,
            "_get_local_build_systems",
            return_value={"build_systems": {"cmake": {}}},
        ):
            result = service.get_available_build_systems()
            assert "build_systems" in result
            assert "cmake" in result["build_systems"]

    @patch("rez_proxy.core.platform.is_local_mode")
    def test_get_available_build_systems_remote_mode(self, mock_is_local):
        """Test getting available build systems in remote mode."""
        mock_is_local.return_value = False

        service = BuildSystemService()

        with patch.object(
            service,
            "_get_common_build_systems",
            return_value={"build_systems": {"cmake": {}}},
        ):
            result = service.get_available_build_systems()
            assert "build_systems" in result
            assert "cmake" in result["build_systems"]

    def test_get_local_build_systems_success(self):
        """Test getting local build systems successfully."""
        service = BuildSystemService()

        mock_cmake_class = MagicMock()
        mock_cmake_class.__doc__ = "CMake build system"
        mock_cmake_class.file_types = ["CMakeLists.txt"]

        mock_plugin_manager = MagicMock()
        mock_plugin_manager.get_plugins.return_value = {"cmake": mock_cmake_class}

        with patch("rez.plugin_managers.plugin_manager", mock_plugin_manager):
            result = service._get_local_build_systems()

            assert "build_systems" in result
            assert "cmake" in result["build_systems"]
            cmake_info = result["build_systems"]["cmake"]
            assert cmake_info["name"] == "cmake"
            assert cmake_info["description"] == "CMake build system"
            assert cmake_info["file_types"] == ["CMakeLists.txt"]

    def test_get_local_build_systems_exception(self):
        """Test getting local build systems with exception."""
        service = BuildSystemService()

        with patch("builtins.__import__", side_effect=ImportError("Test error")):
            result = service._get_local_build_systems()

            assert "error" in result
            assert result["error"] == "Test error"
            assert result["build_systems"] == {}

    def test_get_common_build_systems_linux(self):
        """Test getting common build systems for Linux."""
        service = BuildSystemService()

        with patch.object(service, "get_platform_info") as mock_get_platform:
            mock_platform = PlatformInfo(
                platform="linux",
                arch="x86_64",
                os="ubuntu-20.04",
                python_version="3.9.0",
            )
            mock_get_platform.return_value = mock_platform

            result = service._get_common_build_systems()

            assert "build_systems" in result
            assert "cmake" in result["build_systems"]
            assert "python" in result["build_systems"]
            assert "msbuild" not in result["build_systems"]

    def test_get_common_build_systems_windows(self):
        """Test getting common build systems for Windows."""
        service = BuildSystemService()

        with patch.object(service, "get_platform_info") as mock_get_platform:
            mock_platform = PlatformInfo(
                platform="windows",
                arch="x86_64",
                os="windows-10",
                python_version="3.9.0",
            )
            mock_get_platform.return_value = mock_platform

            result = service._get_common_build_systems()

            assert "build_systems" in result
            assert "cmake" in result["build_systems"]
            assert "python" in result["build_systems"]
            assert "msbuild" in result["build_systems"]

            msbuild_info = result["build_systems"]["msbuild"]
            assert msbuild_info["name"] == "msbuild"
            assert ".vcxproj" in msbuild_info["file_types"]


class TestPlatformIntegration:
    """Integration tests for platform detection."""

    def test_real_platform_detection(self):
        """Test platform detection with real system."""
        info = get_effective_platform_info()

        # Should return valid PlatformInfo
        assert isinstance(info, PlatformInfo)
        assert info.platform in ["linux", "windows", "osx"]
        assert info.arch in ["x86_64", "arm64", "i386", "AMD64"]
        assert info.python_version is not None
        assert len(info.python_version.split(".")) >= 2  # At least major.minor

        # OS should be non-empty
        assert info.os is not None
        assert len(info.os) > 0

        # Rez version should be string or None
        assert info.rez_version is None or isinstance(info.rez_version, str)

    def test_platform_consistency(self):
        """Test that platform detection is consistent."""
        info1 = get_effective_platform_info()
        info2 = get_effective_platform_info()

        # Should be identical
        assert info1.platform == info2.platform
        assert info1.arch == info2.arch
        assert info1.os == info2.os
        assert info1.python_version == info2.python_version
        assert info1.rez_version == info2.rez_version
