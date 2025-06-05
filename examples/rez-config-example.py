"""
Example Rez configuration for rez-proxy.

This file demonstrates how to configure Rez for use with rez-proxy.
"""

# Basic package repositories
packages_path = [
    # Production packages
    "/shared/rez/packages/prod",
    
    # Development packages
    "/shared/rez/packages/dev",
    
    # Third-party packages
    "/shared/rez/packages/external",
]

# Local packages path (for development)
local_packages_path = "/home/user/rez/packages"

# Release packages (read-only, stable releases)
release_packages_path = [
    "/shared/rez/releases",
]

# Temporary directory for Rez operations
tmpdir = "/tmp/rez"

# Package cache settings
cache_packages_path = "/var/cache/rez/packages"
package_cache_max_variant_logs = 100
package_cache_clean_limit = 1000

# Platform configuration
platform_map = {
    "linux": "linux",
    "windows": "windows", 
    "darwin": "osx",
}

# Build system configuration
build_system = "cmake"

# Default shell
default_shell = "bash"

# Plugin configuration
plugins = [
    "rezgui",
    "rez_pip_boy",
]

# Logging configuration
quiet = False
debug = False

# Environment variable settings
set_prompt = True
prefix_prompt = True

# Package resolution settings
package_filter = []
package_orderers = ["version", "timestamp"]

# Build settings
build_directory = "{root}/build/{variant}"
install_directory = "{root}/install/{variant}"

# Custom settings for rez-proxy integration
rez_proxy_settings = {
    # Enable API-specific features
    "enable_api_cache": True,
    "api_cache_ttl": 300,
    
    # Concurrency limits
    "max_concurrent_environments": 10,
    "max_concurrent_builds": 5,
    
    # API behavior
    "allow_package_installation": False,
    "allow_environment_modification": True,
    
    # Security settings
    "restrict_shell_access": True,
    "allowed_shells": ["bash", "zsh", "cmd", "powershell"],
    
    # Performance settings
    "package_search_limit": 1000,
    "environment_timeout": 300,
}

# Custom package repositories for different environments
if os.environ.get("REZ_ENV") == "development":
    packages_path.insert(0, "/dev/rez/packages")
    debug = True

elif os.environ.get("REZ_ENV") == "production":
    # Production-specific settings
    quiet = True
    package_filter = ["!*-dev", "!*-debug"]

# Platform-specific configurations
import platform
if platform.system() == "Windows":
    default_shell = "cmd"
    tmpdir = "C:/temp/rez"
    
elif platform.system() == "Darwin":
    # macOS specific settings
    packages_path.append("/opt/rez/packages")

# Custom functions for rez-proxy
def get_custom_package_info(package_name):
    """Custom function to get additional package information."""
    return {
        "custom_metadata": f"Custom info for {package_name}",
        "api_version": "1.0",
    }

# Export configuration for rez-proxy
REZ_PROXY_CONFIG = {
    "packages_path": packages_path,
    "local_packages_path": local_packages_path,
    "release_packages_path": release_packages_path,
    "cache_path": cache_packages_path,
    "tmpdir": tmpdir,
    "settings": rez_proxy_settings,
    "custom_functions": {
        "get_package_info": get_custom_package_info,
    }
}
