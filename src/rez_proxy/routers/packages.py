"""
Package API endpoints with context awareness.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi_versioning import version

from rez_proxy.core.context import get_current_context, is_local_mode
from rez_proxy.core.platform import PlatformAwareService
from rez_proxy.models.schemas import (
    PackageInfo,
    PackageSearchRequest,
    PackageSearchResponse,
)

router = APIRouter()


class PackageService(PlatformAwareService):
    """Platform-aware package service."""

    def list_packages(
        self,
        name_filter: str | None = None,
        version_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List packages based on current platform context."""
        if is_local_mode():
            return self._list_local_packages(name_filter, version_filter, limit, offset)
        else:
            return self._list_remote_packages(
                name_filter, version_filter, limit, offset
            )

    def _list_local_packages(
        self,
        name_filter: str | None = None,
        version_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List packages from local Rez installation."""
        try:
            from rez.packages import iter_package_families, iter_packages
            from rez.version import Version

            packages: list[dict[str, Any]] = []
            count = 0
            total_count = 0

            # Iterate through package families
            for family in iter_package_families():
                if name_filter and name_filter.lower() not in family.name.lower():
                    continue

                try:
                    for package in iter_packages(family.name):
                        total_count += 1

                        # Apply version filter
                        if version_filter:
                            try:
                                if not Version(str(package.version)).in_range(
                                    version_filter
                                ):
                                    continue
                            except (ValueError, TypeError, AttributeError):
                                # Skip packages with invalid version format
                                continue  # nosec B112

                        # Apply offset
                        if count < offset:
                            count += 1
                            continue

                        # Check limit
                        if len(packages) >= limit:
                            break

                        package_info = self._package_to_dict(package)
                        packages.append(package_info)
                        count += 1
                        break  # Only get latest from each family
                except (AttributeError, TypeError, ImportError):
                    # Skip packages that can't be processed
                    continue  # nosec B112

                if len(packages) >= limit:
                    break

            return {
                "packages": packages,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "platform_compatible": True,
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to list local packages: {e}"
            )

    def _list_remote_packages(
        self,
        name_filter: str | None = None,
        version_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List packages for remote mode (placeholder)."""
        # In remote mode, we would typically need the client to provide
        # package information or connect to a remote Rez repository
        return {
            "packages": [
                {
                    "name": "example-package",
                    "version": "1.0.0",
                    "description": "Example package for remote mode",
                    "note": "Remote mode: actual packages depend on client configuration",
                    "platform_compatible": None,
                }
            ],
            "total": 1,
            "limit": limit,
            "offset": offset,
            "platform_compatible": None,
        }

    def _package_to_dict(self, package: Any) -> dict[str, Any]:
        """Convert Rez package to dictionary."""
        # Handle both Package and Variant objects
        if hasattr(package, "parent"):
            pkg = package.parent
            variant_info = {
                "index": getattr(package, "index", None),
                "subpath": getattr(package, "subpath", None),
            }
        else:
            pkg = package
            variant_info = None

        # Extract package information safely
        requires = []
        if hasattr(pkg, "requires") and pkg.requires:
            try:
                requires = [str(req) for req in pkg.requires]
            except (TypeError, AttributeError):
                requires = []

        tools = []
        if hasattr(pkg, "tools") and pkg.tools:
            try:
                tools = list(pkg.tools)
            except (TypeError, AttributeError):
                tools = []

        package_info = {
            "name": pkg.name,
            "version": str(pkg.version),
            "description": getattr(pkg, "description", None),
            "authors": getattr(pkg, "authors", None),
            "requires": requires,
            "tools": tools,
            "commands": getattr(pkg, "commands", None),
            "uri": str(getattr(pkg, "uri", "")),
            "platform_info": self.get_platform_specific_config(),
        }

        # Add variant information
        if variant_info:
            package_info["variants"] = [variant_info]
        elif hasattr(pkg, "variants") and pkg.variants:
            platform_info = self.get_platform_info()
            variants_info = []

            for variant in pkg.variants:
                variant_dict = {
                    "index": getattr(variant, "index", None),
                    "requires": [str(req) for req in getattr(variant, "requires", [])],
                    "platform_compatible": self._is_variant_compatible(
                        variant, platform_info.platform
                    ),
                }
                variants_info.append(variant_dict)

            package_info["variants"] = variants_info

        return package_info

    def _is_variant_compatible(self, variant: Any, platform: str) -> bool:
        """Check if variant is compatible with platform."""
        if not hasattr(variant, "index"):
            return True

        variant_index = str(variant.index)
        return platform in variant_index or "any" in variant_index.lower()


def _package_to_info(package: Any) -> PackageInfo:
    """Convert Rez package to PackageInfo model."""
    # Handle both Package and Variant objects
    if hasattr(package, "parent"):
        # This is a Variant, get the parent Package
        pkg = package.parent
        variant_info = {
            "index": getattr(package, "index", None),
            "subpath": getattr(package, "subpath", None),
        }
    else:
        # This is a Package
        pkg = package
        variant_info = None

    # Extract package information safely
    requires = []
    if hasattr(pkg, "requires") and pkg.requires:
        try:
            requires = [str(req) for req in pkg.requires]
        except (TypeError, AttributeError):
            requires = []

    # Get tools list
    tools = []
    if hasattr(pkg, "tools") and pkg.tools:
        try:
            tools = list(pkg.tools)
        except (TypeError, AttributeError):
            tools = []

    return PackageInfo(
        name=pkg.name,
        version=str(pkg.version),
        description=getattr(pkg, "description", None),
        authors=getattr(pkg, "authors", None),
        requires=requires,
        variants=[variant_info] if variant_info else getattr(pkg, "variants", None),
        tools=tools,
        commands=getattr(pkg, "commands", None),
        uri=getattr(pkg, "uri", None),
    )


@router.get("/")
@version(1)
async def list_packages(
    request: Request,
    limit: int = Query(default=50, description="Maximum number of packages to return"),
    offset: int = Query(default=0, description="Number of packages to skip"),
    name: str | None = Query(default=None, description="Filter by package name"),
    version: str | None = Query(default=None, description="Filter by version range"),
) -> dict[str, Any]:
    """List all available packages with platform awareness."""
    try:
        service = PackageService()
        result = service.list_packages(name, version, limit, offset)

        context = get_current_context()
        result["context"] = {
            "service_mode": context.service_mode.value if context else "local",
            "platform": service.get_platform_info().platform,
            "has_platform_filter": context.platform_info is not None
            if context
            else False,
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list packages: {e}")


@router.get("/{package_name}")
@version(1)
async def get_package_info(
    package_name: str,
    request: Request,
    version: str | None = Query(None, description="Specific version"),
) -> dict[str, Any]:
    """Get detailed package information with context awareness."""
    try:
        service = PackageService()

        if is_local_mode():
            if version:
                # Get specific version
                from rez.packages import get_package
                from rez.version import Version

                package = get_package(package_name, Version(version))
                if not package:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Package '{package_name}' version '{version}' not found",
                    )

                package_info = service._package_to_dict(package)
            else:
                # Get latest version
                from rez.packages import iter_packages

                packages = list(iter_packages(package_name))
                if not packages:
                    raise HTTPException(
                        status_code=404, detail=f"Package '{package_name}' not found"
                    )

                # Get the first (latest) package
                package_info = service._package_to_dict(packages[0])
        else:
            # Remote mode placeholder
            package_info = {
                "name": package_name,
                "version": version or "unknown",
                "description": f"Package {package_name} information for remote mode",
                "note": "Remote mode: actual package info depends on client configuration",
                "platform_info": service.get_platform_specific_config(),
            }

        context = get_current_context()
        package_info["context"] = {
            "service_mode": context.service_mode.value if context else "local",
            "platform": service.get_platform_info().platform,
        }

        return package_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get package info: {e}")


@router.get("/{package_name}/versions")
@version(1)
async def get_package_versions(
    package_name: str,
    request: Request,
    limit: int = Query(50, description="Maximum number of versions to return"),
) -> dict[str, Any]:
    """Get available versions for a package."""
    try:
        service = PackageService()

        if is_local_mode():
            from rez.packages import iter_packages

            versions: list[dict[str, Any]] = []
            for package in iter_packages(package_name):
                if len(versions) >= limit:
                    break

                version_info = {
                    "version": str(package.version),
                    "uri": str(getattr(package, "uri", "")),
                    "timestamp": getattr(package, "timestamp", None),
                    "description": getattr(package, "description", None),
                }
                versions.append(version_info)

            # Sort by version (newest first)
            versions.sort(key=lambda x: str(x["version"]), reverse=True)
        else:
            # Remote mode placeholder
            versions = [
                {
                    "version": "1.0.0",
                    "note": "Remote mode: actual versions depend on client configuration",
                }
            ]

        context = get_current_context()

        return {
            "package": package_name,
            "versions": versions,
            "total": len(versions),
            "context": {
                "service_mode": context.service_mode.value if context else "local",
                "platform": service.get_platform_info().platform,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get package versions: {e}"
        )


@router.get("/{package_name}/variants")
@version(1)
async def get_package_variants(
    package_name: str,
    request: Request,
    version: str | None = Query(None, description="Specific version"),
    platform_filter: bool = Query(
        True, description="Filter variants by current platform"
    ),
) -> dict[str, Any]:
    """Get package variants with platform filtering."""
    try:
        service = PackageService()

        if is_local_mode():
            if version:
                from rez.packages import get_package
                from rez.version import Version

                package = get_package(package_name, Version(version))
            else:
                from rez.packages import iter_packages

                packages = list(iter_packages(package_name))
                package = packages[0] if packages else None

            if not package:
                raise HTTPException(
                    status_code=404, detail=f"Package '{package_name}' not found"
                )

            variants = []
            if hasattr(package, "variants") and package.variants:
                platform_info = service.get_platform_info()

                for variant in package.variants:
                    variant_info = {
                        "index": getattr(variant, "index", None),
                        "requires": [
                            str(req) for req in getattr(variant, "requires", [])
                        ],
                        "platform_compatible": service._is_variant_compatible(
                            variant, platform_info.platform
                        ),
                    }

                    # Apply platform filtering if requested
                    if not platform_filter or variant_info["platform_compatible"]:
                        variants.append(variant_info)
        else:
            # Remote mode placeholder
            variants = [
                {
                    "index": 0,
                    "requires": [],
                    "platform_compatible": None,
                    "note": "Remote mode: actual variants depend on client configuration",
                }
            ]

        context = get_current_context()

        return {
            "package": package_name,
            "version": version,
            "variants": variants,
            "total": len(variants),
            "platform_filtered": platform_filter,
            "context": {
                "service_mode": context.service_mode.value if context else "local",
                "platform": service.get_platform_info().platform,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get package variants: {e}"
        )


@router.post("/search", response_model=PackageSearchResponse)
async def search_packages(request: PackageSearchRequest) -> PackageSearchResponse:
    """Search for packages."""
    try:
        from rez.packages import iter_package_families, iter_packages

        packages: list[PackageInfo] = []
        total_count = 0

        # Search through package families
        for family in iter_package_families():
            # Check if family name matches query
            if request.query.lower() in family.name.lower():
                # Get packages from this family
                try:
                    for package in iter_packages(family.name):
                        # Check description if available
                        matches_description = (
                            hasattr(package, "description")
                            and package.description
                            and request.query.lower() in package.description.lower()
                        )

                        if (
                            request.query.lower() in package.name.lower()
                            or matches_description
                        ):
                            total_count += 1

                            if (
                                total_count > request.offset
                                and len(packages) < request.limit
                            ):
                                packages.append(_package_to_info(package))

                            if len(packages) >= request.limit:
                                break
                except (AttributeError, TypeError, ImportError, OSError):
                    # Skip families that can't be iterated due to filesystem or import issues
                    continue  # nosec B112

            if len(packages) >= request.limit:
                break

        return PackageSearchResponse(
            packages=packages,
            total=total_count,
            limit=request.limit,
            offset=request.offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search packages: {e}")
