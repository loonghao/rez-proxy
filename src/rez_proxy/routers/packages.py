"""
Package API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.schemas import PackageInfo, PackageSearchRequest, PackageSearchResponse

router = APIRouter()


def _package_to_info(package) -> PackageInfo:
    """Convert Rez package to PackageInfo model."""
    return PackageInfo(
        name=package.name,
        version=str(package.version),
        description=getattr(package, 'description', None),
        authors=getattr(package, 'authors', None),
        requires=[str(req) for req in getattr(package, 'requires', [])],
        variants=getattr(package, 'variants', None),
        tools=getattr(package, 'tools', None),
        commands=getattr(package, 'commands', None),
        uri=getattr(package, 'uri', None),
    )


@router.get("/", response_model=List[PackageInfo])
async def list_packages(
    limit: int = Query(default=50, description="Maximum number of packages to return"),
    offset: int = Query(default=0, description="Number of packages to skip"),
    name_pattern: Optional[str] = Query(default=None, description="Package name pattern"),
):
    """List all available packages."""
    try:
        from rez.packages import iter_packages

        packages = []
        count = 0

        for package in iter_packages():
            if name_pattern and name_pattern not in package.name:
                continue

            if count < offset:
                count += 1
                continue

            if len(packages) >= limit:
                break

            packages.append(_package_to_info(package))
            count += 1

        return packages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list packages: {e}")


@router.get("/{package_name}", response_model=List[PackageInfo])
async def get_package_versions(package_name: str):
    """Get all versions of a specific package."""
    try:
        from rez.packages import iter_packages

        packages = []
        for package in iter_packages(package_name):
            packages.append(_package_to_info(package))

        if not packages:
            raise HTTPException(status_code=404, detail=f"Package '{package_name}' not found")

        # Sort by version (newest first)
        packages.sort(key=lambda p: p.version, reverse=True)
        return packages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get package versions: {e}")


@router.get("/{package_name}/{version}", response_model=PackageInfo)
async def get_package_info(package_name: str, version: str):
    """Get information about a specific package version."""
    try:
        from rez.packages import get_latest_package
        from rez.version import Version

        package = get_latest_package(package_name, Version(version))
        if not package:
            raise HTTPException(
                status_code=404,
                detail=f"Package '{package_name}' version '{version}' not found"
            )

        return _package_to_info(package)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get package info: {e}")


@router.post("/search", response_model=PackageSearchResponse)
async def search_packages(request: PackageSearchRequest):
    """Search for packages."""
    try:
        from rez.packages import iter_packages

        packages = []
        total_count = 0

        for package in iter_packages():
            # Simple search implementation
            if (request.query.lower() in package.name.lower() or
                (hasattr(package, 'description') and package.description and
                 request.query.lower() in package.description.lower())):

                total_count += 1

                if total_count > request.offset and len(packages) < request.limit:
                    packages.append(_package_to_info(package))

        return PackageSearchResponse(
            packages=packages,
            total=total_count,
            limit=request.limit,
            offset=request.offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search packages: {e}")
