"""
Version and requirement API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rez_proxy.core.rez_imports import rez_api, requires_rez

router = APIRouter()


class VersionRequest(BaseModel):
    """Version parsing request."""

    version: str


class VersionResponse(BaseModel):
    """Version parsing response."""

    version: str
    tokens: list[str]
    is_valid: bool


class RequirementRequest(BaseModel):
    """Requirement parsing request."""

    requirement: str


class RequirementResponse(BaseModel):
    """Requirement parsing response."""

    requirement: str
    name: str
    range: str | None
    is_valid: bool


class VersionCompareRequest(BaseModel):
    """Version comparison request."""

    version1: str
    version2: str


class VersionCompareResponse(BaseModel):
    """Version comparison response."""

    version1: str
    version2: str
    comparison: int  # -1, 0, 1
    equal: bool
    less_than: bool
    greater_than: bool


@router.post("/parse", response_model=VersionResponse)
@requires_rez
async def parse_version(request: VersionRequest) -> VersionResponse:
    """Parse a version string."""
    try:
        version = rez_api.create_version(request.version)

        return VersionResponse(
            version=str(version),
            tokens=[str(token) for token in getattr(version, "tokens", [])],
            is_valid=True,
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=500, detail=f"Rez version API not available: {e}"
        )
    except Exception:
        return VersionResponse(
            version=request.version,
            tokens=[],
            is_valid=False,
        )


@router.post("/compare", response_model=VersionCompareResponse)
@requires_rez
async def compare_versions(request: VersionCompareRequest) -> VersionCompareResponse:
    """Compare two versions."""
    try:
        v1 = rez_api.create_version(request.version1)
        v2 = rez_api.create_version(request.version2)

        if v1 < v2:
            comparison = -1
        elif v1 > v2:
            comparison = 1
        else:
            comparison = 0

        return VersionCompareResponse(
            version1=str(v1),
            version2=str(v2),
            comparison=comparison,
            equal=(comparison == 0),
            less_than=(comparison == -1),
            greater_than=(comparison == 1),
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=500, detail=f"Rez version API not available: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to compare versions: {e}")


@router.post("/requirements/parse", response_model=RequirementResponse)
@requires_rez
async def parse_requirement(request: RequirementRequest) -> RequirementResponse:
    """Parse a requirement string."""
    try:
        req = rez_api.create_requirement(request.requirement)

        return RequirementResponse(
            requirement=str(req),
            name=getattr(req, "name", ""),
            range=str(getattr(req, "range", None)) if hasattr(req, "range") and req.range else None,
            is_valid=True,
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=500, detail=f"Rez requirement API not available: {e}"
        )
    except Exception:
        return RequirementResponse(
            requirement=request.requirement,
            name="",
            range=None,
            is_valid=False,
        )


@router.post("/requirements/check")
@requires_rez
async def check_requirement_satisfaction(
    requirement: str,
    version: str,
) -> dict[str, str | bool]:
    """Check if a version satisfies a requirement."""
    try:
        req = rez_api.create_requirement(requirement)
        ver = rez_api.create_version(version)

        # Check if version satisfies requirement
        satisfies = False
        if hasattr(req, "range") and req.range:
            satisfies = ver in req.range
        elif hasattr(req, "name") and hasattr(ver, "name"):
            satisfies = (ver.name == req.name)

        return {
            "requirement": str(req),
            "version": str(ver),
            "satisfies": satisfies,
        }
    except AttributeError as e:
        raise HTTPException(
            status_code=500, detail=f"Rez version/requirement API not available: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to check requirement: {e}")


@router.get("/latest")
@requires_rez
async def get_latest_versions(
    packages: list[str],
    limit: int = 10,
) -> dict[str, dict[str, str | None]]:
    """Get latest versions of specified packages."""
    try:
        results = {}

        for package_name in packages[:limit]:  # Limit to prevent abuse
            try:
                # Use rez_api to iterate packages
                packages_iter = rez_api.iter_packages(package_name)
                latest_version = None

                for package in packages_iter:
                    if latest_version is None or (hasattr(package, "version") and package.version > latest_version):
                        latest_version = package.version
                    break  # iter_packages returns in descending order

                results[package_name] = str(latest_version) if latest_version else None
            except AttributeError as e:
                # Rez API not available
                results[package_name] = None
            except Exception:
                results[package_name] = None

        return {"latest_versions": results}
    except AttributeError as e:
        raise HTTPException(
            status_code=500, detail=f"Rez packages API not available: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get latest versions: {e}"
        )
