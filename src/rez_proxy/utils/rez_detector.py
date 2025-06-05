"""
Rez installation detection utilities.
"""

import os
import sys
from pathlib import Path
from typing import Any


def detect_rez_installation() -> dict[str, Any]:
    """Detect Rez installation information."""

    try:
        import rez
        from rez import config

        # Basic information
        info = {
            "version": rez.__version__,
            "rez_root": str(Path(rez.__file__).parent.parent),
            "python_path": sys.executable,
            "python_version": sys.version,
        }

        # Configuration information
        try:
            # Access config attributes safely
            info.update(
                {
                    "packages_path": getattr(config, "packages_path", []),
                    "local_packages_path": getattr(config, "local_packages_path", None),
                    "release_packages_path": getattr(
                        config, "release_packages_path", []
                    ),
                    "config_file": getattr(config, "config_file", None),
                }
            )

            # Platform information
            try:
                from rez.system import system

                info.update(
                    {
                        "platform": str(system.platform),
                        "arch": str(system.arch),
                        "os": str(system.os),
                    }
                )
            except Exception:
                # Fallback platform detection
                import platform

                info.update(
                    {
                        "platform": platform.system().lower(),
                        "arch": platform.machine(),
                        "os": f"{platform.system().lower()}-{platform.release()}",
                    }
                )

        except Exception as e:
            info["config_error"] = str(e)

        # Environment variables
        rez_env_vars = {
            key: value for key, value in os.environ.items() if key.startswith("REZ_")
        }
        info["environment_variables"] = rez_env_vars

        return info

    except ImportError as e:
        raise RuntimeError(f"Rez not found: {e}")
    except Exception as e:
        raise RuntimeError(f"Rez detection failed: {e}")


def validate_rez_environment() -> list[str]:
    """Validate Rez environment, return list of warnings."""
    warnings = []

    try:
        info = detect_rez_installation()

        # Check packages path
        if not info.get("packages_path"):
            warnings.append("No packages path configured")

        # Check config file
        config_file = info.get("config_file")
        if config_file and not Path(config_file).exists():
            warnings.append(f"Config file not found: {config_file}")

        # Check permissions
        packages_path = info.get("packages_path", [])
        if isinstance(packages_path, list):
            for path in packages_path:
                if isinstance(path, str) and os.path.exists(path):
                    if not os.access(path, os.R_OK):
                        warnings.append(f"No read access to packages path: {path}")
                elif isinstance(path, str):
                    warnings.append(f"Packages path does not exist: {path}")

    except Exception as e:
        warnings.append(f"Environment validation failed: {e}")

    return warnings
