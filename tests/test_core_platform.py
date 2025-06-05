"""
Test core platform detection functionality.
"""

from unittest.mock import patch

from rez_proxy.core.context import get_effective_platform_info
from rez_proxy.core.platform import PlatformAwareService
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
