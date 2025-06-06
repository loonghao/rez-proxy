"""
Environment API endpoints.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from rez_proxy.exceptions import handle_rez_exception

from ..models.schemas import (
    CommandExecuteRequest,
    CommandExecuteResponse,
    EnvironmentInfo,
    EnvironmentResolveRequest,
    PackageInfo,
)

router = APIRouter()

# In-memory storage for environments (in production, use Redis or database)
_environments: dict[str, dict[str, Any]] = {}


def _package_to_info(package: Any) -> PackageInfo:
    """Convert Rez package to PackageInfo model."""
    return PackageInfo(
        name=package.name,
        version=str(package.version),
        description=getattr(package, "description", None),
        authors=getattr(package, "authors", None),
        requires=[str(req) for req in getattr(package, "requires", [])],
        variants=getattr(package, "variants", None),
        tools=getattr(package, "tools", None),
        commands=getattr(package, "commands", None),
        uri=getattr(package, "uri", None),
    )


@router.post("/resolve", response_model=EnvironmentInfo)
async def resolve_environment(request: EnvironmentResolveRequest) -> EnvironmentInfo:
    """Resolve a new environment with specified packages."""
    try:
        from rez.resolved_context import ResolvedContext

        # Create resolved context
        context = ResolvedContext(request.packages)

        # Check if resolution was successful
        from rez.resolver import ResolverStatus

        if context.status != ResolverStatus.solved:
            failure_desc = getattr(
                context, "failure_description", "Unknown resolution failure"
            )
            raise HTTPException(
                status_code=400, detail=f"Failed to resolve environment: {failure_desc}"
            )

        # Generate environment ID
        env_id = str(uuid.uuid4())

        # Convert resolved packages to PackageInfo
        packages = [_package_to_info(pkg) for pkg in context.resolved_packages]

        # Store environment info
        from rez.system import system

        env_info = {
            "context": context,
            "packages": packages,
            "created_at": datetime.utcnow().isoformat(),
            "platform": str(getattr(context, "platform", system.platform)),
            "arch": str(getattr(context, "arch", system.arch)),
            "os_name": str(getattr(context, "os", system.os)),
        }
        _environments[env_id] = env_info

        return EnvironmentInfo(
            id=env_id,
            packages=packages,
            status="resolved",
            created_at=env_info["created_at"],
            platform=env_info["platform"],
            arch=env_info["arch"],
            os_name=env_info["os_name"],
        )
    except HTTPException:
        raise
    except Exception as e:
        handle_rez_exception(e, "environment_resolution")


@router.get("/{env_id}", response_model=EnvironmentInfo)
async def get_environment(env_id: str) -> EnvironmentInfo:
    """Get information about a specific environment."""
    if env_id not in _environments:
        raise HTTPException(status_code=404, detail=f"Environment '{env_id}' not found")

    env_info = _environments[env_id]
    return EnvironmentInfo(
        id=env_id,
        packages=env_info["packages"],
        status="resolved",
        created_at=env_info["created_at"],
        platform=env_info["platform"],
        arch=env_info["arch"],
        os_name=env_info["os_name"],
    )


@router.post("/{env_id}/execute", response_model=CommandExecuteResponse)
async def execute_command(
    env_id: str, request: CommandExecuteRequest
) -> CommandExecuteResponse:
    """Execute a command in the specified environment."""
    if env_id not in _environments:
        raise HTTPException(status_code=404, detail=f"Environment '{env_id}' not found")

    try:
        env_info = _environments[env_id]
        context = env_info["context"]

        # Build command
        cmd_args = [request.command]
        if request.args:
            cmd_args.extend(request.args)

        # Execute command in the resolved context
        import time

        start_time = time.time()

        # Use context.execute_command if available, otherwise use subprocess
        try:
            result = context.execute_command(cmd_args, timeout=request.timeout)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            return_code = result.get("return_code", 0)
        except AttributeError:
            # Fallback to subprocess execution
            import subprocess  # nosec B404

            # Get environment variables from context
            env_vars = context.get_environ()

            # Validate command arguments to prevent injection
            if not cmd_args or not all(isinstance(arg, str) for arg in cmd_args):
                raise HTTPException(status_code=400, detail="Invalid command arguments")

            process = subprocess.run(  # nosec B603
                cmd_args,
                capture_output=True,
                text=True,
                timeout=request.timeout,
                env=env_vars,
                shell=False,  # Explicitly disable shell to prevent injection
            )
            stdout = process.stdout
            stderr = process.stderr
            return_code = process.returncode

        execution_time = time.time() - start_time

        return CommandExecuteResponse(
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Command execution timed out")
    except Exception as e:
        handle_rez_exception(e, "command_execution")


@router.delete("/{env_id}")
async def delete_environment(env_id: str) -> dict[str, str]:
    """Delete an environment."""
    if env_id not in _environments:
        raise HTTPException(status_code=404, detail=f"Environment '{env_id}' not found")

    del _environments[env_id]
    return {"message": f"Environment '{env_id}' deleted successfully"}
