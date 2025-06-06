"""
Package build and release API endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi_versioning import version
from pydantic import BaseModel

router = APIRouter()


class BuildRequest(BaseModel):
    """Package build request."""

    source_path: str
    build_args: list[str] | None = None
    install: bool = False
    clean: bool = False
    variants: list[int] | None = None


class ReleaseRequest(BaseModel):
    """Package release request."""

    source_path: str
    release_message: str | None = None
    skip_repo_errors: bool = False
    variants: list[int] | None = None


@router.post("/build")
@version(1)
async def build_package(request: BuildRequest) -> dict[str, Any]:
    """Build a package from source."""
    try:
        import os

        from rez.build_process import create_build_process
        from rez.developer_package import get_developer_package

        # Validate source path
        if not os.path.exists(request.source_path):
            raise HTTPException(
                status_code=404, detail=f"Source path not found: {request.source_path}"
            )

        # Get developer package
        dev_package = get_developer_package(request.source_path)
        if not dev_package:
            raise HTTPException(
                status_code=400, detail="No valid package found at source path"
            )

        # Create build process
        build_process = create_build_process(
            package=dev_package,
            build_args=request.build_args or [],
            verbose=True,
        )

        # Perform build
        build_result = build_process.build(
            clean=request.clean,
            install=request.install,
            variants=request.variants,
        )

        return {
            "success": True,
            "package": dev_package.name,
            "version": str(dev_package.version),
            "build_path": str(build_result.build_path)
            if hasattr(build_result, "build_path")
            else None,
            "install_path": str(build_result.install_path)
            if hasattr(build_result, "install_path")
            else None,
            "variants_built": request.variants or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build package: {e}")


@router.post("/release")
@version(1)
async def release_package(request: ReleaseRequest) -> dict[str, Any]:
    """Release a package."""
    try:
        import os

        from rez.developer_package import get_developer_package
        from rez.release_vcs import create_release_from_path

        # Validate source path
        if not os.path.exists(request.source_path):
            raise HTTPException(
                status_code=404, detail=f"Source path not found: {request.source_path}"
            )

        # Get developer package
        dev_package = get_developer_package(request.source_path)
        if not dev_package:
            raise HTTPException(
                status_code=400, detail="No valid package found at source path"
            )

        # Perform release
        release_result = create_release_from_path(
            path=request.source_path,
            message=request.release_message,
            skip_repo_errors=request.skip_repo_errors,
            variants=request.variants,
        )

        return {
            "success": True,
            "package": dev_package.name,
            "version": str(dev_package.version),
            "released_packages": [
                str(pkg.uri) for pkg in release_result.released_packages
            ]
            if hasattr(release_result, "released_packages")
            else [],
            "message": request.release_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to release package: {e}")


@router.get("/systems")
@version(1)
async def get_build_systems(request: Request) -> dict[str, Any]:
    """Get available build systems with platform awareness."""
    try:
        from ..core.context import get_current_context
        from ..core.platform import BuildSystemService

        service = BuildSystemService()
        build_systems = service.get_available_build_systems()

        context = get_current_context()
        build_systems["service_mode"] = (
            context.service_mode.value if context else "local"
        )
        build_systems["platform"] = service.get_platform_info().platform

        return build_systems
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get build systems: {e}")


@router.get("/status/{source_path:path}")
async def get_build_status(source_path: str) -> dict[str, Any]:
    """Get build status for a package source."""
    try:
        import os

        from rez.build_process import get_build_process_types
        from rez.developer_package import get_developer_package

        # Validate source path
        if not os.path.exists(source_path):
            raise HTTPException(
                status_code=404, detail=f"Source path not found: {source_path}"
            )

        # Get developer package
        dev_package = get_developer_package(source_path)
        if not dev_package:
            raise HTTPException(
                status_code=400, detail="No valid package found at source path"
            )

        # Check for build files
        build_files = {}
        build_types = get_build_process_types()

        for build_type in build_types:
            build_class = build_types[build_type]
            if hasattr(build_class, "file_types"):
                for file_type in build_class.file_types:
                    build_file_path = os.path.join(source_path, file_type)
                    if os.path.exists(build_file_path):
                        build_files[build_type] = file_type
                        break

        return {
            "package": dev_package.name,
            "version": str(dev_package.version),
            "source_path": source_path,
            "is_buildable": len(build_files) > 0,
            "build_systems": build_files,
            "variants": len(getattr(dev_package, "variants", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get build status: {e}")


@router.get("/variants/{source_path:path}")
async def get_package_variants(source_path: str) -> dict[str, Any]:
    """Get variants information for a package."""
    try:
        import os

        from rez.developer_package import get_developer_package

        # Validate source path
        if not os.path.exists(source_path):
            raise HTTPException(
                status_code=404, detail=f"Source path not found: {source_path}"
            )

        # Get developer package
        dev_package = get_developer_package(source_path)
        if not dev_package:
            raise HTTPException(
                status_code=400, detail="No valid package found at source path"
            )

        variants_info = []
        if hasattr(dev_package, "variants") and dev_package.variants:
            for i, variant in enumerate(dev_package.variants):
                variant_info = {
                    "index": i,
                    "requires": [str(req) for req in getattr(variant, "requires", [])],
                    "subpath": getattr(variant, "subpath", None),
                }
                variants_info.append(variant_info)

        return {
            "package": dev_package.name,
            "version": str(dev_package.version),
            "variants": variants_info,
            "total_variants": len(variants_info),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get package variants: {e}"
        )


@router.get("/dependencies/{source_path:path}")
async def get_build_dependencies(source_path: str) -> dict[str, Any]:
    """Get build dependencies for a package."""
    try:
        import os

        from rez.developer_package import get_developer_package

        # Validate source path
        if not os.path.exists(source_path):
            raise HTTPException(
                status_code=404, detail=f"Source path not found: {source_path}"
            )

        # Get developer package
        dev_package = get_developer_package(source_path)
        if not dev_package:
            raise HTTPException(
                status_code=400, detail="No valid package found at source path"
            )

        dependencies = {
            "requires": [str(req) for req in getattr(dev_package, "requires", [])],
            "build_requires": [
                str(req) for req in getattr(dev_package, "build_requires", [])
            ],
            "private_build_requires": [
                str(req) for req in getattr(dev_package, "private_build_requires", [])
            ],
        }

        return {
            "package": dev_package.name,
            "version": str(dev_package.version),
            "dependencies": dependencies,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get build dependencies: {e}"
        )
