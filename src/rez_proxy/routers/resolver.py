"""
Advanced resolver API endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from rez_proxy.core.rez_imports import requires_rez, rez_api

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

    def model_post_init(self, __context: Any) -> None:
        """Validate packages list is not empty."""
        if not self.packages:
            raise ValueError("Packages list cannot be empty")


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

    def model_post_init(self, __context: Any) -> None:
        """Validate packages list is not empty."""
        if not self.packages:
            raise ValueError("Packages list cannot be empty")


@router.post("/resolve/advanced", response_model=ResolverResponse)
@requires_rez
async def advanced_resolve(request: ResolverRequest) -> ResolverResponse:
    """Perform advanced package resolution with detailed options."""
    try:
        import time

        start_time = time.time()

        # Create context with advanced options using rez_api
        try:
            context = rez_api.create_resolved_context(
                package_requests=request.packages,
                timestamp=request.timestamp,
                max_fails=request.max_fails,
                time_limit=request.time_limit,
                verbosity=request.verbosity,
            )
        except AttributeError as e:
            raise HTTPException(
                status_code=500, detail=f"Rez resolver API not available: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to create resolved context: {e}"
            )

        solve_time = time.time() - start_time

        # Extract resolution details with error handling
        resolved_packages = []
        try:
            if hasattr(context, "status") and hasattr(context, "resolved_packages"):
                # Check if resolution was successful
                status_name = getattr(context.status, "name", str(context.status))
                if status_name == "solved" or str(context.status) == "solved":
                    for package in context.resolved_packages:
                        pkg_info = {
                            "name": getattr(package, "name", "unknown"),
                            "version": str(getattr(package, "version", "unknown")),
                            "uri": getattr(package, "uri", None),
                        }
                        resolved_packages.append(pkg_info)
        except Exception:
            # Log error but continue with empty resolved_packages
            pass

        failed_packages = []
        if hasattr(context, "failed_packages"):
            try:
                failed_packages = [str(pkg) for pkg in context.failed_packages]
            except Exception:
                pass

        status_name = "unknown"
        if hasattr(context, "status"):
            status_name = getattr(context.status, "name", str(context.status))

        return ResolverResponse(
            status=status_name,
            resolved_packages=resolved_packages,
            failed_packages=failed_packages,
            solve_time=solve_time,
            num_solves=getattr(context, "num_solves", 0),
            graph_size=len(resolved_packages),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced resolution failed: {e}")


@router.post("/dependency-graph")
@requires_rez
async def get_dependency_graph(request: DependencyGraphRequest) -> dict[str, Any]:
    """Get dependency graph for packages."""
    try:

        def get_dependencies(
            package_name: str, depth: int, visited: set[str] | None = None
        ) -> dict[str, Any]:
            if visited is None:
                visited = set()

            if depth <= 0 or package_name in visited:
                return {}

            visited.add(package_name)

            # Get latest package using rez_api
            try:
                packages = rez_api.iter_packages(package_name)
                latest_package = None
                for package in packages:
                    latest_package = package
                    break
            except AttributeError as e:
                raise HTTPException(
                    status_code=500, detail=f"Rez packages API not available: {e}"
                )
            except Exception:
                # Package not found or other error
                return {}

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Dependency graph generation failed: {e}"
        )


@router.get("/conflicts")
@requires_rez
async def detect_conflicts(
    packages: list[str] = Query(..., min_length=1),
) -> dict[str, Any]:
    """Detect potential conflicts between packages."""

    try:
        # Try to resolve packages using rez_api
        try:
            context = rez_api.create_resolved_context(package_requests=packages)
        except AttributeError as e:
            raise HTTPException(
                status_code=500, detail=f"Rez resolver API not available: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to create resolved context: {e}"
            )

        conflicts = []
        status_name = "unknown"

        if hasattr(context, "status"):
            status_name = getattr(context.status, "name", str(context.status))

            # Check if resolution failed
            if status_name != "solved" and str(context.status) != "solved":
                # Analyze failure reasons
                failure_desc = getattr(
                    context, "failure_description", "Unknown conflict"
                )
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
            "resolution_status": status_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict detection failed: {e}")


@router.post("/validate")
@requires_rez
async def validate_package_list(packages: list[str]) -> dict[str, Any]:
    """Validate a list of package requirements."""
    # Validate packages list is not empty
    if not packages:
        raise HTTPException(status_code=422, detail="Packages list cannot be empty")

    try:
        validation_results = []

        for package_req in packages:
            try:
                # Use rez_api to create requirement
                req = rez_api.create_requirement(package_req)
                validation_results.append(
                    {
                        "requirement": package_req,
                        "valid": True,
                        "parsed_name": getattr(req, "name", None),
                        "parsed_range": str(getattr(req, "range", None))
                        if hasattr(req, "range") and req.range
                        else None,
                        "error": None,
                    }
                )
            except AttributeError as e:
                # Rez API not available
                validation_results.append(
                    {
                        "requirement": package_req,
                        "valid": False,
                        "parsed_name": None,
                        "parsed_range": None,
                        "error": f"Rez API not available: {e}",
                    }
                )
            except RuntimeError as e:
                # System errors should be raised as 500
                raise HTTPException(
                    status_code=500, detail=f"Package validation failed: {e}"
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
        raise HTTPException(status_code=500, detail=f"Package validation failed: {e}")
