"""
Rez installation detection utilities.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List


def detect_rez_installation() -> Dict[str, Any]:
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
            info.update({
                "packages_path": config.packages_path,
                "local_packages_path": config.local_packages_path,
                "release_packages_path": config.release_packages_path,
                "config_file": getattr(config, 'config_file', None),
                "platform": config.platform.name,
                "arch": config.arch.name,
                "os": config.os.name,
            })
        except Exception as e:
            info["config_error"] = str(e)

        # Environment variables
        rez_env_vars = {
            key: value for key, value in os.environ.items()
            if key.startswith('REZ_')
        }
        info["environment_variables"] = rez_env_vars

        return info

    except ImportError as e:
        raise RuntimeError(f"Rez not found: {e}")
    except Exception as e:
        raise RuntimeError(f"Rez detection failed: {e}")


def validate_rez_environment() -> List[str]:
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
                if not os.access(path, os.R_OK):
                    warnings.append(f"No read access to packages path: {path}")

    except Exception as e:
        warnings.append(f"Environment validation failed: {e}")

    return warnings
