"""
Platform information management for rez-proxy.

Provides platform-aware functionality that works in both local and remote modes.
"""

from typing import Any

from fastapi import HTTPException

from rez_proxy.core.context import get_effective_platform_info, is_local_mode
from rez_proxy.models.schemas import PlatformInfo


class PlatformAwareService:
    """Base class for platform-aware services."""

    def get_platform_info(self) -> PlatformInfo:
        """Get platform information for current context."""
        return get_effective_platform_info()

    def get_platform_specific_config(self) -> dict[str, Any]:
        """Get platform-specific configuration."""
        platform_info = self.get_platform_info()

        config = {
            "platform": platform_info.platform,
            "arch": platform_info.arch,
            "os": platform_info.os,
            "python_version": platform_info.python_version,
        }

        if platform_info.rez_version:
            config["rez_version"] = platform_info.rez_version

        return config

    def is_platform_compatible(self, required_platform: str | None = None) -> bool:
        """Check if current platform is compatible with requirements."""
        if not required_platform:
            return True

        platform_info = self.get_platform_info()
        return platform_info.platform == required_platform


class RezConfigService(PlatformAwareService):
    """Platform-aware Rez configuration service."""

    def get_packages_path(self) -> list[str]:
        """Get packages path based on current platform context."""
        if is_local_mode():
            return self._get_local_packages_path()
        else:
            # In remote mode, we might need to handle this differently
            # For now, return empty list as remote client should provide this info
            return []

    def _get_local_packages_path(self) -> list[str]:
        """Get local packages path."""
        try:
            from rez.config import config

            packages_path = getattr(config, "packages_path", [])
            # Ensure we return a list of strings
            if isinstance(packages_path, list):
                return [str(p) for p in packages_path]
            elif packages_path:
                return [str(packages_path)]
            else:
                return []
        except Exception:
            return []

    def get_config_info(self) -> dict[str, Any]:
        """Get comprehensive configuration information."""
        base_config = self.get_platform_specific_config()

        if is_local_mode():
            # Add local-specific config
            try:
                from rez.config import config

                packages_path = getattr(config, "packages_path", [])
                release_packages_path = getattr(config, "release_packages_path", [])

                # Ensure paths are strings
                if isinstance(packages_path, list):
                    packages_path = [str(p) for p in packages_path]
                elif packages_path:
                    packages_path = [str(packages_path)]
                else:
                    packages_path = []

                if isinstance(release_packages_path, list):
                    release_packages_path = [str(p) for p in release_packages_path]
                elif release_packages_path:
                    release_packages_path = [str(release_packages_path)]
                else:
                    release_packages_path = []

                base_config.update(
                    {
                        "packages_path": packages_path,
                        "local_packages_path": getattr(
                            config, "local_packages_path", None
                        ),
                        "release_packages_path": release_packages_path,
                        "config_file": getattr(config, "config_file", None),
                    }
                )
            except Exception as e:
                base_config["config_error"] = str(e)
        else:
            # In remote mode, indicate that client should provide these
            base_config.update(
                {
                    "packages_path": [],
                    "note": "Remote mode: client should provide configuration",
                }
            )

        return base_config


class ShellService(PlatformAwareService):
    """Platform-aware shell service."""

    def get_available_shells(self) -> list[dict[str, Any]]:
        """Get available shells for current platform."""
        if is_local_mode():
            return self._get_local_shells()
        else:
            # In remote mode, return common shells for the platform
            return self._get_common_shells_for_platform()

    def _get_local_shells(self) -> list[dict[str, Any]]:
        """Get locally available shells."""
        from rez.shells import get_shell_class, get_shell_types

        shell_types = get_shell_types()
        shells = []

        for shell_name in shell_types:
            try:
                shell_class = get_shell_class(shell_name)
                shell_info = {
                    "name": shell_class.name(),
                    "executable": getattr(shell_class, "executable", None),
                    "file_extension": getattr(
                        shell_class, "file_extension", lambda: None
                    )(),
                    "available": shell_class.is_available(),
                    "executable_path": None,
                    "description": getattr(shell_class, "__doc__", None),
                }

                try:
                    shell_info["executable_path"] = shell_class.executable_filepath()
                except Exception:
                    shell_info["executable_path"] = None

                shells.append(shell_info)
            except Exception:
                # Add basic info for shells that can't be loaded
                shells.append(
                    {
                        "name": shell_name,
                        "executable": shell_name,
                        "file_extension": ".sh",
                        "available": False,
                        "executable_path": None,
                        "description": None,
                    }
                )

        return shells

    def _get_common_shells_for_platform(self) -> list[dict[str, Any]]:
        """Get common shells for current platform."""
        platform_info = self.get_platform_info()

        shells = []
        if platform_info.platform == "windows":
            shell_names = ["cmd", "powershell", "bash"]
        elif platform_info.platform in ["linux", "darwin"]:
            shell_names = ["bash", "zsh", "sh", "csh", "tcsh"]
        else:
            shell_names = ["bash", "sh"]

        for shell_name in shell_names:
            shell_info = {
                "name": shell_name,
                "executable": shell_name,
                "file_extension": ".sh",
                "available": True,  # Assume available in remote mode
                "executable_path": f"/bin/{shell_name}",
                "description": f"{shell_name.upper()} shell",
            }

            # Platform-specific adjustments
            if platform_info.platform == "windows":
                if shell_name == "cmd":
                    shell_info.update(
                        {
                            "executable": "cmd.exe",
                            "file_extension": ".bat",
                            "executable_path": "C:\\Windows\\System32\\cmd.exe",
                        }
                    )
                elif shell_name == "powershell":
                    shell_info.update(
                        {
                            "executable": "powershell.exe",
                            "file_extension": ".ps1",
                            "executable_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                        }
                    )

            shells.append(shell_info)

        return shells

    def get_shell_info(self, shell_name: str) -> dict[str, Any]:
        """Get information about a specific shell."""
        if is_local_mode():
            return self._get_local_shell_info(shell_name)
        else:
            return self._get_generic_shell_info(shell_name)

    def _get_local_shell_info(self, shell_name: str) -> dict[str, Any]:
        """Get local shell information."""
        try:
            from rez.shells import get_shell_class

            shell_class = get_shell_class(shell_name)

            info = {
                "name": shell_class.name(),
                "executable": getattr(shell_class, "executable", None),
                "file_extension": getattr(
                    shell_class, "file_extension", lambda: None
                )(),
                "available": shell_class.is_available(),
                "executable_path": None,
                "description": getattr(shell_class, "__doc__", None),
            }

            try:
                info["executable_path"] = shell_class.executable_filepath()
            except Exception:
                info["executable_path"] = None

            return info
        except Exception:
            # Return 404-like response for missing shells
            raise HTTPException(
                status_code=404, detail=f"Shell '{shell_name}' not found"
            )

    def _get_generic_shell_info(self, shell_name: str) -> dict[str, Any]:
        """Get generic shell information for remote mode."""
        # Check if shell is in common shells list
        common_shells = self._get_common_shells_for_platform()
        for shell in common_shells:
            if shell["name"] == shell_name:
                return shell

        # If not found, raise 404
        raise HTTPException(status_code=404, detail=f"Shell '{shell_name}' not found")


class BuildSystemService(PlatformAwareService):
    """Platform-aware build system service."""

    def get_available_build_systems(self) -> dict[str, Any]:
        """Get available build systems for current platform."""
        if is_local_mode():
            return self._get_local_build_systems()
        else:
            return self._get_common_build_systems()

    def _get_local_build_systems(self) -> dict[str, Any]:
        """Get locally available build systems."""
        try:
            from rez.plugin_managers import plugin_manager

            build_systems = plugin_manager.get_plugins("build_system")

            systems_info = {}
            for name, system_class in build_systems.items():
                systems_info[name] = {
                    "name": name,
                    "description": getattr(system_class, "__doc__", ""),
                    "file_types": getattr(system_class, "file_types", []),
                }

            return {"build_systems": systems_info}
        except Exception as e:
            return {"error": str(e), "build_systems": {}}

    def _get_common_build_systems(self) -> dict[str, Any]:
        """Get common build systems for remote mode."""
        platform_info = self.get_platform_info()

        # Common build systems across platforms
        common_systems = {
            "cmake": {
                "name": "cmake",
                "description": "CMake build system",
                "file_types": ["CMakeLists.txt"],
            },
            "python": {
                "name": "python",
                "description": "Python setuptools build system",
                "file_types": ["setup.py", "pyproject.toml"],
            },
        }

        # Platform-specific additions
        if platform_info.platform == "windows":
            common_systems["msbuild"] = {
                "name": "msbuild",
                "description": "Microsoft Build Engine",
                "file_types": [".vcxproj", ".sln"],
            }

        return {
            "build_systems": common_systems,
            "note": "Remote mode: actual availability depends on client system",
        }
