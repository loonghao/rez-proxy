"""
Package repository API endpoints.
"""

import fnmatch
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


def _repository_to_info(repo: Any) -> dict[str, Any]:
    """Convert repository object to info dictionary."""
    # Handle both callable and attribute access for name
    repo_name = repo.name() if callable(repo.name) else repo.name
    return {
        "name": repo_name,
        "location": repo.location,
        "type": repo.__class__.__name__,
    }


def _get_repository_stats(repo: Any) -> dict[str, Any]:
    """Get repository statistics."""
    package_count = len(list(repo.iter_packages()))
    # Handle both callable and attribute access for name
    repo_name = repo.name() if callable(repo.name) else repo.name
    return {
        "name": repo_name,
        "location": repo.location,
        "package_count": package_count,
    }


def _search_repository_packages(
    repo: Any, pattern: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Search packages in repository by pattern."""
    packages = []
    count = 0

    # Handle both callable and attribute access for name
    repo_name = repo.name() if callable(repo.name) else repo.name

    for package in repo.iter_packages():
        if pattern.lower() in package.name.lower():
            packages.append(
                {
                    "name": package.name,
                    "version": str(package.version),
                    "repository": repo_name,
                    "uri": getattr(package, "uri", None),
                }
            )
            count += 1
            if count >= limit:
                break

    return packages


def _filter_packages_by_pattern(
    packages: list[dict[str, Any]], pattern: str
) -> list[dict[str, Any]]:
    """Filter packages by name pattern using fnmatch."""
    return [pkg for pkg in packages if fnmatch.fnmatch(pkg["name"], pattern)]


@router.get("/")
async def list_repositories() -> dict[str, list[dict[str, Any]]]:
    """List all configured package repositories."""
    try:
        from rez.package_repository import package_repository_manager

        repositories = []
        for repo in package_repository_manager.repositories:
            # Handle both callable and attribute access for name
            repo_name = repo.name() if callable(repo.name) else repo.name
            # Handle uid attribute safely
            uid = getattr(repo, "uid", None)
            if uid is not None and hasattr(uid, "__call__"):
                try:
                    uid = uid()
                except Exception:
                    uid = None

            repo_info = {
                "name": repo_name,
                "location": repo.location,
                "type": repo.__class__.__name__,
                "uid": uid,
            }
            repositories.append(repo_info)

        return {"repositories": repositories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {e}")


# More specific routes first
@router.get("/{repo_location:path}/families")
async def list_repository_families(
    repo_location: str,
    limit: int = Query(default=50, description="Maximum number of families to return"),
    offset: int = Query(default=0, description="Number of families to skip"),
) -> dict[str, Any]:
    """List package families in a specific repository."""
    try:
        from rez.package_repository import package_repository_manager

        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(
                status_code=404, detail=f"Repository '{repo_location}' not found"
            )

        families: list[dict[str, Any]] = []
        count = 0

        for family in repo.iter_package_families():
            if count < offset:
                count += 1
                continue

            if len(families) >= limit:
                break

            family_info = {
                "name": family.name,
                "package_count": len(list(family.iter_packages())),
                "repository": repo_location,
            }
            families.append(family_info)
            count += 1

        return {
            "families": families,
            "total": count,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list repository families: {e}"
        )


@router.get("/{repo_location:path}/packages/{package_name}")
async def get_repository_package(
    repo_location: str, package_name: str
) -> dict[str, Any]:
    """Get a specific package from a repository."""
    try:
        from rez.package_repository import package_repository_manager

        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(
                status_code=404, detail=f"Repository '{repo_location}' not found"
            )

        family = repo.get_package_family(package_name)
        if not family:
            raise HTTPException(
                status_code=404,
                detail=f"Package '{package_name}' not found in repository",
            )

        packages = []
        for package in family.iter_packages():
            package_info = {
                "name": package.name,
                "version": str(package.version),
                "repository": repo_location,
                "uri": getattr(package, "uri", None),
            }
            packages.append(package_info)

        return {
            "name": package_name,
            "repository": repo_location,
            "packages": packages,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get repository package: {e}"
        )


@router.get("/{repo_location:path}/packages")
async def get_repository_packages(
    repo_location: str,
    name_pattern: str = Query(
        default=None, description="Filter packages by name pattern"
    ),
    limit: int = Query(default=50, description="Maximum number of packages to return"),
    offset: int = Query(default=0, description="Number of packages to skip"),
) -> dict[str, Any]:
    """Get packages from a specific repository."""
    try:
        from rez.package_repository import package_repository_manager

        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(
                status_code=404, detail=f"Repository '{repo_location}' not found"
            )

        packages: list[dict[str, Any]] = []
        count = 0

        for package in repo.iter_packages():
            # Apply name pattern filter if provided
            if name_pattern and not fnmatch.fnmatch(package.name, name_pattern):
                continue

            if count < offset:
                count += 1
                continue

            if len(packages) >= limit:
                break

            package_info = {
                "name": package.name,
                "version": str(package.version),
                "repository": repo_location,
                "uri": getattr(package, "uri", None),
            }
            packages.append(package_info)
            count += 1

        return {
            "packages": packages,
            "total": count,
            "limit": limit,
            "offset": offset,
            "repository": repo_location,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get repository packages: {e}"
        )


@router.get("/{repo_location:path}/stats")
async def get_repository_stats(repo_location: str) -> dict[str, Any]:
    """Get statistics for a specific repository."""
    try:
        from rez.package_repository import package_repository_manager

        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(
                status_code=404, detail=f"Repository '{repo_location}' not found"
            )

        stats = _get_repository_stats(repo)
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get repository stats: {e}"
        )


# General repository info route - must be last
@router.get("/{repo_location:path}")
async def get_repository_info(repo_location: str) -> dict[str, Any]:
    """Get information about a specific repository."""
    try:
        from rez.package_repository import package_repository_manager

        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(
                status_code=404, detail=f"Repository '{repo_location}' not found"
            )

        # Handle both callable and attribute access for name
        repo_name = repo.name() if callable(repo.name) else repo.name

        # Handle uid attribute safely
        uid = getattr(repo, "uid", None)
        if uid is not None and hasattr(uid, "__call__"):
            try:
                uid = uid()
            except Exception:
                uid = None

        return {
            "name": repo_name,
            "location": repo.location,
            "type": repo.__class__.__name__,
            "uid": uid,
            "package_count": len(list(repo.iter_package_families())),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get repository info: {e}"
        )


@router.post("/search")
async def search_repositories(search_request: dict[str, Any]) -> dict[str, Any]:
    """Search for packages across multiple repositories."""
    try:
        from rez.package_repository import package_repository_manager

        # Validate request
        if "query" not in search_request:
            raise HTTPException(status_code=422, detail="Missing required field: query")

        query = search_request["query"]
        repo_names = search_request.get("repositories", [])
        limit = search_request.get("limit", 50)

        results = []
        repositories_searched = []

        # Get repositories to search
        if repo_names:
            repos_to_search = []
            for repo_name in repo_names:
                repo = package_repository_manager.get_repository(repo_name)
                if repo:
                    repos_to_search.append(repo)
                    repositories_searched.append(repo_name)
        else:
            repos_to_search = package_repository_manager.repositories
            repositories_searched = [
                repo.name() if callable(repo.name) else repo.name
                for repo in repos_to_search
            ]

        # Search each repository
        for repo in repos_to_search:
            repo_results = _search_repository_packages(repo, query, limit=limit)
            results.extend(repo_results)

        return {
            "results": results[:limit],
            "repositories_searched": repositories_searched,
            "query": query,
            "total_results": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search repositories: {e}"
        )
