"""
Pydantic schemas for API requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PackageInfo(BaseModel):
    """Package information model."""
    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Package version")
    description: Optional[str] = Field(None, description="Package description")
    authors: Optional[List[str]] = Field(None, description="Package authors")
    requires: Optional[List[str]] = Field(None, description="Package requirements")
    variants: Optional[List[Dict[str, Any]]] = Field(None, description="Package variants")
    tools: Optional[List[str]] = Field(None, description="Package tools")
    commands: Optional[str] = Field(None, description="Package commands")
    uri: Optional[str] = Field(None, description="Package URI")


class PackageSearchRequest(BaseModel):
    """Package search request model."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=50, description="Maximum number of results")
    offset: int = Field(default=0, description="Result offset")
    include_prerelease: bool = Field(default=False, description="Include prerelease versions")


class PackageSearchResponse(BaseModel):
    """Package search response model."""
    packages: List[PackageInfo] = Field(..., description="Found packages")
    total: int = Field(..., description="Total number of packages found")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


class EnvironmentResolveRequest(BaseModel):
    """Environment resolve request model."""
    packages: List[str] = Field(..., description="List of package requirements")
    platform: Optional[str] = Field(None, description="Target platform")
    arch: Optional[str] = Field(None, description="Target architecture")
    os_name: Optional[str] = Field(None, description="Target OS")


class EnvironmentInfo(BaseModel):
    """Environment information model."""
    id: str = Field(..., description="Environment ID")
    packages: List[PackageInfo] = Field(..., description="Resolved packages")
    status: str = Field(..., description="Environment status")
    created_at: str = Field(..., description="Creation timestamp")
    platform: str = Field(..., description="Platform")
    arch: str = Field(..., description="Architecture")
    os_name: str = Field(..., description="Operating system")


class CommandExecuteRequest(BaseModel):
    """Command execution request model."""
    command: str = Field(..., description="Command to execute")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    timeout: Optional[int] = Field(default=300, description="Execution timeout in seconds")


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
    packages_path: List[str] = Field(..., description="Packages paths")
    active_environments: int = Field(..., description="Number of active environments")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")
