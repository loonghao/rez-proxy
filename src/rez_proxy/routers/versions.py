"""
Version and requirement API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
async def parse_version(request: VersionRequest) -> VersionResponse:
    """Parse a version string."""
    try:
        from rez.version import Version

        version = Version(request.version)

        return VersionResponse(
            version=str(version),
            tokens=[str(token) for token in version.tokens],
            is_valid=True,
        )
    except Exception:
        return VersionResponse(
            version=request.version,
            tokens=[],
            is_valid=False,
        )


@router.post("/compare", response_model=VersionCompareResponse)
async def compare_versions(request: VersionCompareRequest) -> VersionCompareResponse:
    """Compare two versions."""
    try:
        from rez.version import Version

        v1 = Version(request.version1)
        v2 = Version(request.version2)

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
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to compare versions: {e}")


@router.post("/requirements/parse", response_model=RequirementResponse)
async def parse_requirement(request: RequirementRequest) -> RequirementResponse:
    """Parse a requirement string."""
    try:
        from rez.version import Requirement

        req = Requirement(request.requirement)

        return RequirementResponse(
            requirement=str(req),
            name=req.name,
            range=str(req.range) if req.range else None,
            is_valid=True,
        )
    except Exception:
        return RequirementResponse(
            requirement=request.requirement,
            name="",
            range=None,
            is_valid=False,
        )


@router.post("/requirements/check")
async def check_requirement_satisfaction(
    requirement: str,
    version: str,
) -> dict[str, str | bool]:
    """Check if a version satisfies a requirement."""
    try:
        from rez.version import Requirement, Version

        req = Requirement(requirement)
        ver = Version(version)

        satisfies = ver in req.range if req.range else (ver.name == req.name)

        return {
            "requirement": str(req),
            "version": str(ver),
            "satisfies": satisfies,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to check requirement: {e}")


@router.get("/latest")
async def get_latest_versions(
    packages: list[str],
    limit: int = 10,
) -> dict[str, dict[str, str | None]]:
    """Get latest versions of specified packages."""
    try:
        from rez.packages import iter_packages

        results = {}

        for package_name in packages[:limit]:  # Limit to prevent abuse
            try:
                latest_version = None
                for package in iter_packages(package_name):
                    if latest_version is None or package.version > latest_version:
                        latest_version = package.version
                    break  # iter_packages returns in descending order

                results[package_name] = str(latest_version) if latest_version else None
            except Exception:
                results[package_name] = None

        return {"latest_versions": results}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get latest versions: {e}"
        )
