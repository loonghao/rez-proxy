"""
Package repository API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.schemas import ErrorResponse

router = APIRouter()


@router.get("/")
async def list_repositories():
    """List all configured package repositories."""
    try:
        from rez.package_repository import package_repository_manager
        
        repositories = []
        for repo in package_repository_manager.get_repositories():
            repo_info = {
                "name": repo.name(),
                "location": repo.location,
                "type": repo.__class__.__name__,
                "uid": getattr(repo, 'uid', None),
            }
            repositories.append(repo_info)
        
        return {"repositories": repositories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {e}")


@router.get("/{repo_location:path}")
async def get_repository_info(repo_location: str):
    """Get information about a specific repository."""
    try:
        from rez.package_repository import package_repository_manager
        
        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_location}' not found")
        
        return {
            "name": repo.name(),
            "location": repo.location,
            "type": repo.__class__.__name__,
            "uid": getattr(repo, 'uid', None),
            "package_count": len(list(repo.iter_package_families())),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repository info: {e}")


@router.get("/{repo_location:path}/families")
async def list_repository_families(
    repo_location: str,
    limit: int = Query(default=50, description="Maximum number of families to return"),
    offset: int = Query(default=0, description="Number of families to skip"),
):
    """List package families in a specific repository."""
    try:
        from rez.package_repository import package_repository_manager
        
        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_location}' not found")
        
        families = []
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
        raise HTTPException(status_code=500, detail=f"Failed to list repository families: {e}")


@router.get("/{repo_location:path}/packages/{package_name}")
async def get_repository_package(repo_location: str, package_name: str):
    """Get a specific package from a repository."""
    try:
        from rez.package_repository import package_repository_manager
        
        repo = package_repository_manager.get_repository(repo_location)
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{repo_location}' not found")
        
        family = repo.get_package_family(package_name)
        if not family:
            raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found in repository")
        
        packages = []
        for package in family.iter_packages():
            package_info = {
                "name": package.name,
                "version": str(package.version),
                "repository": repo_location,
                "uri": getattr(package, 'uri', None),
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
        raise HTTPException(status_code=500, detail=f"Failed to get repository package: {e}")
