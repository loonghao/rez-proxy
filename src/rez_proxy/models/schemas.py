"""
Pydantic schemas for API requests and responses.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PackageInfo(BaseModel):
    """Package information model."""

    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Package version")
    description: str | None = Field(None, description="Package description")
    authors: list[str] | None = Field(None, description="Package authors")
    requires: list[str] | None = Field(None, description="Package requirements")
    variants: list[dict[str, Any]] | None = Field(None, description="Package variants")
    tools: list[str] | None = Field(None, description="Package tools")
    commands: str | None = Field(None, description="Package commands")
    uri: str | None = Field(None, description="Package URI")


class PackageSearchRequest(BaseModel):
    """Package search request model."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=50, ge=1, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Result offset")
    include_prerelease: bool = Field(
        default=False, description="Include prerelease versions"
    )


class PackageSearchResponse(BaseModel):
    """Package search response model."""

    packages: list[PackageInfo] = Field(..., description="Found packages")
    total: int = Field(..., description="Total number of packages found")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


class EnvironmentResolveRequest(BaseModel):
    """Environment resolve request model."""

    packages: list[str] = Field(..., description="List of package requirements")
    platform: str | None = Field(None, description="Target platform")
    arch: str | None = Field(None, description="Target architecture")
    os_name: str | None = Field(None, description="Target OS")


class EnvironmentInfo(BaseModel):
    """Environment information model."""

    id: str = Field(..., description="Environment ID")
    packages: list[PackageInfo] = Field(..., description="Resolved packages")
    status: str = Field(..., description="Environment status")
    created_at: str = Field(..., description="Creation timestamp")
    platform: str = Field(..., description="Platform")
    arch: str = Field(..., description="Architecture")
    os_name: str = Field(..., description="Operating system")


class CommandExecuteRequest(BaseModel):
    """Command execution request model."""

    command: str = Field(..., description="Command to execute")
    args: list[str] | None = Field(None, description="Command arguments")
    timeout: int | None = Field(default=300, description="Execution timeout in seconds")


class CommandExecuteResponse(BaseModel):
    """Command execution response model."""

    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    return_code: int = Field(..., description="Return code")
    execution_time: float = Field(..., description="Execution time in seconds")


class SystemStatus(BaseModel):
    """System status model."""

    status: str = Field(..., description="System status")
    rez_version: str = Field(..., description="Rez version")
    python_version: str = Field(..., description="Python version")
    packages_path: list[str] = Field(..., description="Packages paths")
    active_environments: int = Field(..., description="Number of active environments")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Error details")
    code: str | None = Field(None, description="Error code")


class ServiceMode(str, Enum):
    """Service deployment mode."""

    LOCAL = "local"
    REMOTE = "remote"


class PlatformInfo(BaseModel):
    """Platform information model."""

    platform: str = Field(
        ..., description="Platform name (e.g., linux, windows, darwin)"
    )
    arch: str = Field(..., description="Architecture (e.g., x86_64, arm64)")
    os: str = Field(
        ..., description="Operating system (e.g., ubuntu-20.04, windows-10)"
    )
    python_version: str = Field(..., description="Python version")
    rez_version: str | None = Field(None, description="Rez version")


class ClientContext(BaseModel):
    """Client context information."""

    client_id: str | None = Field(None, description="Client identifier")
    session_id: str | None = Field(None, description="Session identifier")
    platform_info: PlatformInfo | None = Field(
        None, description="Client platform information"
    )
    service_mode: ServiceMode = Field(
        ServiceMode.LOCAL, description="Service deployment mode"
    )
    user_agent: str | None = Field(None, description="Client user agent")
    request_id: str | None = Field(None, description="Request identifier for tracing")
