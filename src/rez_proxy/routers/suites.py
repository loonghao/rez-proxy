"""
Suite management API endpoints.
"""

import os
import tempfile
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi_versioning import version
from pydantic import BaseModel, Field

from rez_proxy.exceptions import handle_rez_exception

router = APIRouter()

# In-memory storage for suites (in production, use Redis or database)
_suites: dict[str, dict[str, Any]] = {}


class SuiteCreateRequest(BaseModel):
    """Request to create a new suite."""

    name: str = Field(..., description="Name of the suite")
    description: str | None = Field(None, description="Description of the suite")


class SuiteInfo(BaseModel):
    """Suite information."""

    id: str
    name: str
    description: str | None
    contexts: list[str]
    tools: dict[str, Any]
    created_at: str
    status: str


class SuiteAddContextRequest(BaseModel):
    """Request to add a context to a suite."""

    context_name: str = Field(..., description="Name for the context in the suite")
    environment_id: str = Field(
        ..., description="ID of the resolved environment to add"
    )
    prefix_char: str | None = Field(None, description="Prefix character for tools")


class SuiteToolAliasRequest(BaseModel):
    """Request to alias a tool in a suite."""

    context_name: str = Field(..., description="Context containing the tool")
    tool_name: str = Field(..., description="Original tool name")
    alias_name: str = Field(..., description="New alias name")


@router.post("/", response_model=SuiteInfo)
@version(1)
async def create_suite(request: SuiteCreateRequest) -> SuiteInfo:
    """Create a new suite."""
    try:
        from datetime import datetime

        from rez.suite import Suite

        # Create new suite
        suite = Suite()
        suite_id = str(uuid.uuid4())

        # Store suite info
        suite_info = {
            "suite": suite,
            "name": request.name,
            "description": request.description,
            "created_at": datetime.utcnow().isoformat(),
            "status": "created",
        }
        _suites[suite_id] = suite_info

        return SuiteInfo(
            id=suite_id,
            name=request.name,
            description=request.description,
            contexts=[],
            tools={},
            created_at=suite_info["created_at"],
            status="created",
        )
    except Exception as e:
        handle_rez_exception(e, "suite_creation")


@router.get("/{suite_id}", response_model=SuiteInfo)
@version(1)
async def get_suite(suite_id: str) -> SuiteInfo:
    """Get information about a specific suite."""
    if suite_id not in _suites:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

    try:
        suite_info = _suites[suite_id]
        suite = suite_info["suite"]

        # Get tools from suite
        tools = {}
        try:
            suite_tools = suite.get_tools()
            tools = {
                name: {"context": tool.context_name, "command": str(tool)}
                for name, tool in suite_tools.items()
            }
        except Exception:
            tools = {}

        return SuiteInfo(
            id=suite_id,
            name=suite_info["name"],
            description=suite_info["description"],
            contexts=suite.context_names,
            tools=tools,
            created_at=suite_info["created_at"],
            status=suite_info["status"],
        )
    except Exception as e:
        handle_rez_exception(e, "suite_retrieval")


@router.post("/{suite_id}/contexts")
@version(1)
async def add_context_to_suite(
    suite_id: str, request: SuiteAddContextRequest
) -> dict[str, str]:
    """Add a context to a suite."""
    if suite_id not in _suites:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

    try:
        # Import environments storage from environments router
        from rez_proxy.routers.environments import _environments

        if request.environment_id not in _environments:
            raise HTTPException(
                status_code=404,
                detail=f"Environment '{request.environment_id}' not found",
            )

        suite_info = _suites[suite_id]
        suite = suite_info["suite"]
        env_info = _environments[request.environment_id]
        context = env_info["context"]

        # Add context to suite
        suite.add_context(
            name=request.context_name, context=context, prefix_char=request.prefix_char
        )

        return {
            "message": f"Context '{request.context_name}' added to suite '{suite_id}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        handle_rez_exception(e, "suite_context_addition")


@router.post("/{suite_id}/tools/alias")
@version(1)
async def alias_tool_in_suite(
    suite_id: str, request: SuiteToolAliasRequest
) -> dict[str, str]:
    """Create an alias for a tool in a suite."""
    if suite_id not in _suites:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

    try:
        suite_info = _suites[suite_id]
        suite = suite_info["suite"]

        # Alias the tool
        suite.alias_tool(
            context_name=request.context_name,
            tool_name=request.tool_name,
            alias_name=request.alias_name,
        )

        return {
            "message": f"Tool '{request.tool_name}' aliased as '{request.alias_name}' in suite '{suite_id}'"
        }
    except Exception as e:
        handle_rez_exception(e, "suite_tool_aliasing")


@router.post("/{suite_id}/save")
@version(1)
async def save_suite(suite_id: str, path: str | None = None) -> dict[str, str]:
    """Save a suite to disk."""
    if suite_id not in _suites:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

    try:
        suite_info = _suites[suite_id]
        suite = suite_info["suite"]

        # Use provided path or create temporary directory
        if path is None:
            path = os.path.join(tempfile.gettempdir(), f"rez_suite_{suite_id}")

        # Validate suite before saving
        suite.validate()

        # Save suite
        suite.save(path, verbose=False)

        return {"message": f"Suite '{suite_id}' saved to '{path}'", "path": path}
    except Exception as e:
        handle_rez_exception(e, "suite_saving")


@router.get("/{suite_id}/tools")
@version(1)
async def get_suite_tools(suite_id: str) -> dict[str, Any]:
    """Get all tools available in a suite."""
    if suite_id not in _suites:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

    try:
        suite_info = _suites[suite_id]
        suite = suite_info["suite"]

        # Get tools and conflicts
        tools = suite.get_tools()
        conflicts = getattr(suite, "tool_conflicts", {})

        tools_info = {}
        for name, tool in tools.items():
            tools_info[name] = {
                "context": tool.context_name,
                "command": str(tool),
                "conflicted": name in conflicts,
            }

        return {
            "tools": tools_info,
            "conflicts": conflicts,
            "total_tools": len(tools),
        }
    except Exception as e:
        handle_rez_exception(e, "suite_tools_retrieval")


@router.delete("/{suite_id}")
@version(1)
async def delete_suite(suite_id: str) -> dict[str, str]:
    """Delete a suite."""
    if suite_id not in _suites:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

    del _suites[suite_id]
    return {"message": f"Suite '{suite_id}' deleted successfully"}


@router.get("/")
@version(1)
async def list_suites() -> dict[str, Any]:
    """List all suites."""
    suites = []
    for suite_id, suite_info in _suites.items():
        suite = suite_info["suite"]
        suites.append(
            {
                "id": suite_id,
                "name": suite_info["name"],
                "description": suite_info["description"],
                "contexts": suite.context_names,
                "created_at": suite_info["created_at"],
                "status": suite_info["status"],
            }
        )

    return {
        "suites": suites,
        "total": len(suites),
    }
