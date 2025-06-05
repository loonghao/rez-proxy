"""
Package operations API endpoints (copy, move, remove, etc.).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class PackageCopyRequest(BaseModel):
    """Package copy request."""

    source_uri: str
    dest_repository: str
    force: bool = False


class PackageMoveRequest(BaseModel):
    """Package move request."""

    source_uri: str
    dest_repository: str
    force: bool = False


class PackageRemoveRequest(BaseModel):
    """Package remove request."""

    package_name: str
    version: str | None = None
    repository: str | None = None
    force: bool = False


@router.post("/copy")
async def copy_package(request: PackageCopyRequest):
    """Copy a package to another repository."""
    try:
        from rez.package_copy import copy_package
        from rez.package_repository import package_repository_manager

        # Get destination repository
        dest_repo = package_repository_manager.get_repository(request.dest_repository)
        if not dest_repo:
            raise HTTPException(
                status_code=404,
                detail=f"Destination repository not found: {request.dest_repository}",
            )

        # Perform copy
        result = copy_package(
            source_uri=request.source_uri,
            dest_repository=dest_repo,
            force=request.force,
        )

        return {
            "success": True,
            "source_uri": request.source_uri,
            "dest_repository": request.dest_repository,
            "copied_uri": getattr(result, "uri", None) if result else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy package: {e}")


@router.post("/move")
async def move_package(request: PackageMoveRequest):
    """Move a package to another repository."""
    try:
        from rez.package_move import move_package
        from rez.package_repository import package_repository_manager

        # Get destination repository
        dest_repo = package_repository_manager.get_repository(request.dest_repository)
        if not dest_repo:
            raise HTTPException(
                status_code=404,
                detail=f"Destination repository not found: {request.dest_repository}",
            )

        # Perform move
        result = move_package(
            source_uri=request.source_uri,
            dest_repository=dest_repo,
            force=request.force,
        )

        return {
            "success": True,
            "source_uri": request.source_uri,
            "dest_repository": request.dest_repository,
            "moved_uri": getattr(result, "uri", None) if result else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move package: {e}")


@router.delete("/remove")
async def remove_package(request: PackageRemoveRequest):
    """Remove a package or package version."""
    try:
        from rez.package_remove import remove_package, remove_package_family
        from rez.packages import get_package
        from rez.version import Version

        if request.version:
            # Remove specific version
            package = get_package(request.package_name, Version(request.version))
            if not package:
                raise HTTPException(
                    status_code=404,
                    detail=f"Package {request.package_name}-{request.version} not found",
                )

            remove_package(package, force=request.force)

            return {
                "success": True,
                "action": "removed_version",
                "package": request.package_name,
                "version": request.version,
            }
        else:
            # Remove entire package family
            from rez.packages import iter_packages

            # Check if package family exists
            packages = list(iter_packages(request.package_name))
            if not packages:
                raise HTTPException(
                    status_code=404,
                    detail=f"Package family {request.package_name} not found",
                )

            remove_package_family(request.package_name, force=request.force)

            return {
                "success": True,
                "action": "removed_family",
                "package": request.package_name,
                "versions_removed": len(packages),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove package: {e}")


@router.get("/uri/{package_uri:path}")
async def get_package_from_uri(package_uri: str):
    """Get package information from URI."""
    try:
        from rez.packages import get_package_from_uri

        package = get_package_from_uri(package_uri)
        if not package:
            raise HTTPException(
                status_code=404, detail=f"Package not found at URI: {package_uri}"
            )

        return {
            "name": package.name,
            "version": str(package.version),
            "uri": package_uri,
            "description": getattr(package, "description", None),
            "authors": getattr(package, "authors", None),
            "requires": [str(req) for req in getattr(package, "requires", [])],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get package from URI: {e}"
        )


@router.get("/variant/{variant_uri:path}")
async def get_variant_from_uri(variant_uri: str):
    """Get variant information from URI."""
    try:
        from rez.packages import get_variant_from_uri

        variant = get_variant_from_uri(variant_uri)
        if not variant:
            raise HTTPException(
                status_code=404, detail=f"Variant not found at URI: {variant_uri}"
            )

        return {
            "name": variant.parent.name,
            "version": str(variant.parent.version),
            "index": getattr(variant, "index", None),
            "subpath": getattr(variant, "subpath", None),
            "uri": variant_uri,
            "requires": [str(req) for req in getattr(variant, "requires", [])],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get variant from URI: {e}"
        )


@router.get("/help/{package_name}")
async def get_package_help(package_name: str, version: str | None = None):
    """Get help information for a package."""
    try:
        from rez.package_help import get_package_help
        from rez.packages import get_package, iter_packages
        from rez.version import Version

        if version:
            package = get_package(package_name, Version(version))
        else:
            # Get latest package
            package = None
            for pkg in iter_packages(package_name):
                package = pkg
                break

        if not package:
            raise HTTPException(
                status_code=404, detail=f"Package {package_name} not found"
            )

        help_text = get_package_help(package)

        return {
            "package": package_name,
            "version": str(package.version),
            "help": help_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get package help: {e}")


@router.get("/test/{package_name}")
async def get_package_tests(package_name: str, version: str | None = None):
    """Get test information for a package."""
    try:
        from rez.packages import get_package, iter_packages
        from rez.version import Version

        if version:
            package = get_package(package_name, Version(version))
        else:
            # Get latest package
            package = None
            for pkg in iter_packages(package_name):
                package = pkg
                break

        if not package:
            raise HTTPException(
                status_code=404, detail=f"Package {package_name} not found"
            )

        tests_info = {
            "package": package_name,
            "version": str(package.version),
            "has_tests": hasattr(package, "tests") and package.tests,
            "tests": getattr(package, "tests", {}),
        }

        return tests_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get package tests: {e}")
