"""
Advanced resolver API endpoints.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from rez_proxy.exceptions import handle_rez_exception

router = APIRouter()


class ResolverRequest(BaseModel):
    """Advanced resolver request."""

    packages: list[str]
    platform: str | None = None
    arch: str | None = None
    os_name: str | None = None
    timestamp: int | None = None
    max_fails: int = -1
    time_limit: int = -1
    verbosity: int = 0


class ResolverResponse(BaseModel):
    """Advanced resolver response."""

    status: str
    resolved_packages: list[dict]
    failed_packages: list[str]
    solve_time: float
    num_solves: int
    graph_size: int


class DependencyGraphRequest(BaseModel):
    """Dependency graph request."""

    packages: list[str]
    depth: int = 3


@router.post("/resolve/advanced", response_model=ResolverResponse)
async def advanced_resolve(request: ResolverRequest) -> ResolverResponse:
    """Perform advanced package resolution with detailed options."""
    try:
        import time

        from rez.resolved_context import ResolvedContext
        from rez.resolver import ResolverStatus

        start_time = time.time()

        # Create context with advanced options
        context = ResolvedContext(
            package_requests=request.packages,
            timestamp=request.timestamp,
            max_fails=request.max_fails,
            time_limit=request.time_limit,
            verbosity=request.verbosity,
        )

        solve_time = time.time() - start_time

        # Extract resolution details
        resolved_packages = []
        if context.status == ResolverStatus.solved:
            for package in context.resolved_packages:
                pkg_info = {
                    "name": package.name,
                    "version": str(package.version),
                    "uri": getattr(package, "uri", None),
                }
                resolved_packages.append(pkg_info)

        failed_packages = []
        if hasattr(context, "failed_packages"):
            failed_packages = [str(pkg) for pkg in context.failed_packages]

        return ResolverResponse(
            status=context.status.name,
            resolved_packages=resolved_packages,
            failed_packages=failed_packages,
            solve_time=solve_time,
            num_solves=getattr(context, "num_solves", 0),
            graph_size=len(resolved_packages),
        )
    except Exception as e:
        handle_rez_exception(e, "advanced_package_resolution")


@router.post("/dependency-graph")
async def get_dependency_graph(request: DependencyGraphRequest) -> dict[str, Any]:
    """Get dependency graph for packages."""
    try:
        from rez.packages import iter_packages

        def get_dependencies(
            package_name: str, depth: int, visited: set[str] | None = None
        ) -> dict[str, Any]:
            if visited is None:
                visited = set()

            if depth <= 0 or package_name in visited:
                return {}

            visited.add(package_name)

            # Get latest package
            latest_package = None
            for package in iter_packages(package_name):
                latest_package = package
                break

            if not latest_package:
                return {}

            dependencies = {}
            if hasattr(latest_package, "requires") and latest_package.requires:
                for req in latest_package.requires:
                    req_name = req.name if hasattr(req, "name") else str(req).split()[0]
                    dependencies[req_name] = {
                        "requirement": str(req),
                        "dependencies": get_dependencies(
                            req_name, depth - 1, visited.copy()
                        ),
                    }

            return dependencies

        graph = {}
        for package_name in request.packages:
            graph[package_name] = get_dependencies(package_name, request.depth)

        return {"dependency_graph": graph}
    except Exception as e:
        handle_rez_exception(e, "dependency_graph_generation")


@router.get("/conflicts")
async def detect_conflicts(packages: list[str]) -> dict[str, Any]:
    """Detect potential conflicts between packages."""
    try:
        from rez.resolved_context import ResolvedContext
        from rez.resolver import ResolverStatus

        # Try to resolve packages
        context = ResolvedContext(packages)

        conflicts = []
        if context.status != ResolverStatus.solved:
            # Analyze failure reasons
            failure_desc = getattr(context, "failure_description", "Unknown conflict")
            conflicts.append(
                {
                    "type": "resolution_failure",
                    "description": failure_desc,
                    "packages": packages,
                }
            )

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "resolution_status": context.status.name,
        }
    except Exception as e:
        handle_rez_exception(e, "conflict_detection")


@router.post("/validate")
async def validate_package_list(packages: list[str]) -> dict[str, Any]:
    """Validate a list of package requirements."""
    try:
        from rez.version import Requirement

        validation_results = []

        for package_req in packages:
            try:
                req = Requirement(package_req)
                validation_results.append(
                    {
                        "requirement": package_req,
                        "valid": True,
                        "parsed_name": req.name,
                        "parsed_range": str(req.range) if req.range else None,
                        "error": None,
                    }
                )
            except Exception as e:
                validation_results.append(
                    {
                        "requirement": package_req,
                        "valid": False,
                        "parsed_name": None,
                        "parsed_range": None,
                        "error": str(e),
                    }
                )

        all_valid = all(result["valid"] for result in validation_results)

        return {
            "all_valid": all_valid,
            "results": validation_results,
        }
    except Exception as e:
        handle_rez_exception(e, "package_validation")
