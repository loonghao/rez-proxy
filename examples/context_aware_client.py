"""
Example client for rez-proxy with context awareness.

Demonstrates both local and remote service modes.
"""

import requests
import json
from typing import Dict, Any, Optional


class RezProxyClient:
    """Client for rez-proxy API with context awareness."""
    
    def __init__(self, base_url: str = "http://localhost:8000", client_id: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.session = requests.Session()
        
        # Set default headers
        if self.client_id:
            self.session.headers.update({"X-Client-ID": self.client_id})
    
    def set_remote_mode(
        self,
        platform: str,
        arch: str,
        os: str,
        python_version: str,
        rez_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Set platform context for remote mode."""
        platform_info = {
            "platform": platform,
            "arch": arch,
            "os": os,
            "python_version": python_version,
        }
        
        if rez_version:
            platform_info["rez_version"] = rez_version
        
        # Set service mode to remote
        self.session.headers.update({"X-Service-Mode": "remote"})
        
        response = self.session.post(
            f"{self.base_url}/api/v1/system/context",
            json=platform_info
        )
        response.raise_for_status()
        return response.json()
    
    def set_local_mode(self) -> None:
        """Set client to local mode."""
        self.session.headers.update({"X-Service-Mode": "local"})
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information."""
        response = self.session.get(f"{self.base_url}/api/v1/system/platform")
        response.raise_for_status()
        return response.json()

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status."""
        response = self.session.get(f"{self.base_url}/api/v1/system/status")
        response.raise_for_status()
        return response.json()

    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        response = self.session.get(f"{self.base_url}/api/v1/system/config")
        response.raise_for_status()
        return response.json()

    def get_available_shells(self) -> Dict[str, Any]:
        """Get available shells."""
        response = self.session.get(f"{self.base_url}/api/v1/shells/")
        response.raise_for_status()
        return response.json()

    def list_packages(
        self,
        name_filter: Optional[str] = None,
        version_filter: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List packages."""
        params = {"limit": limit}
        if name_filter:
            params["name"] = name_filter
        if version_filter:
            params["version"] = version_filter

        response = self.session.get(f"{self.base_url}/api/v1/packages/", params=params)
        response.raise_for_status()
        return response.json()

    def get_package_info(self, package_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get package information."""
        params = {}
        if version:
            params["version"] = version

        response = self.session.get(
            f"{self.base_url}/api/v1/packages/{package_name}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_current_context(self) -> Dict[str, Any]:
        """Get current context information."""
        response = self.session.get(f"{self.base_url}/api/v1/system/context")
        response.raise_for_status()
        return response.json()

    def get_latest_api_version(self) -> Dict[str, Any]:
        """Get latest API version information."""
        response = self.session.get(f"{self.base_url}/latest/system/status")
        response.raise_for_status()
        return response.json()


def demo_local_mode():
    """Demonstrate local mode usage."""
    print("=== Local Mode Demo ===")
    
    client = RezProxyClient(client_id="demo-local-client")
    client.set_local_mode()
    
    # Get platform info (should use local system)
    platform_info = client.get_platform_info()
    print(f"Platform: {platform_info['platform']} {platform_info['arch']}")
    print(f"OS: {platform_info['os']}")
    print(f"Service Mode: {platform_info['service_mode']}")
    
    # Get system status
    status = client.get_system_status()
    print(f"System Status: {status['status']}")
    print(f"Rez Version: {status['rez_version']}")
    
    # List packages
    packages = client.list_packages(limit=3)
    print(f"Found {packages['total']} packages")
    for pkg in packages['packages'][:3]:
        print(f"  - {pkg['name']} {pkg['version']}")


def demo_remote_mode():
    """Demonstrate remote mode usage."""
    print("\n=== Remote Mode Demo ===")
    
    client = RezProxyClient(client_id="demo-remote-client")
    
    # Set platform context for remote mode
    context_result = client.set_remote_mode(
        platform="linux",
        arch="x86_64",
        os="ubuntu-20.04",
        python_version="3.8.10",
        rez_version="2.112.0"
    )
    print(f"Context Set: {context_result['status']}")
    
    # Get platform info (should use provided context)
    platform_info = client.get_platform_info()
    print(f"Platform: {platform_info['platform']} {platform_info['arch']}")
    print(f"Service Mode: {platform_info['service_mode']}")
    
    # Get current context
    current_context = client.get_current_context()
    print(f"Session ID: {current_context.get('session_id', 'N/A')}")
    
    # Get system config
    config = client.get_system_config()
    print(f"Config Mode: {config['context']['service_mode']}")


if __name__ == "__main__":
    try:
        demo_local_mode()
        demo_remote_mode()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to rez-proxy server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
