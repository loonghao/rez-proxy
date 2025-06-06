"""
Rez Proxy - FastAPI application with versioning.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_versioning import VersionedFastAPI

from rez_proxy.config import get_config
from rez_proxy.exceptions import (
    RezProxyError,
    general_exception_handler,
    http_exception_handler,
    rez_proxy_exception_handler,
)
from rez_proxy.middleware.context import ContextMiddleware
from rez_proxy.routers import (
    build,
    environments,
    package_ops,
    packages,
    repositories,
    resolver,
    rez_config,
    shells,
    suites,
    system,
    versions,
)


def create_app() -> VersionedFastAPI:
    """Create FastAPI application with versioning."""

    config = get_config()

    # Create base app without versioning first
    app = FastAPI(
        title="Rez Proxy",
        description="RESTful API for Rez package manager",
        version="0.0.1",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Context middleware for platform awareness
    app.add_middleware(ContextMiddleware)

    # Register routers with versioning decorators
    # V1 API routers
    app.include_router(system.router, prefix="/system", tags=["system"])
    app.include_router(packages.router, prefix="/packages", tags=["packages"])
    app.include_router(
        environments.router, prefix="/environments", tags=["environments"]
    )
    app.include_router(shells.router, prefix="/shells", tags=["shells"])
    app.include_router(
        repositories.router, prefix="/repositories", tags=["repositories"]
    )
    app.include_router(versions.router, prefix="/versions", tags=["versions"])
    app.include_router(resolver.router, prefix="/resolver", tags=["resolver"])
    app.include_router(rez_config.router, prefix="/config", tags=["config"])
    app.include_router(
        package_ops.router, prefix="/package-ops", tags=["package-operations"]
    )
    app.include_router(build.router, prefix="/build", tags=["build"])
    app.include_router(suites.router, prefix="/suites", tags=["suites"])

    # Create versioned app first
    versioned_app = VersionedFastAPI(
        app,
        version_format="{major}",
        prefix_format="/api/v{major}",
        default_version=(1, 0),
        enable_latest=True,
        docs_url=config.docs_url,
        redoc_url=config.redoc_url,
    )

    # Register exception handlers
    versioned_app.add_exception_handler(RezProxyError, rez_proxy_exception_handler)
    versioned_app.add_exception_handler(HTTPException, http_exception_handler)
    versioned_app.add_exception_handler(Exception, general_exception_handler)

    # Add non-versioned endpoints to the versioned app
    # Root path redirect to documentation
    @versioned_app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url=config.docs_url)

    # Health check - non-versioned endpoint
    @versioned_app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "rez-proxy"}

    # API info endpoint - non-versioned
    @versioned_app.get("/api/info", tags=["system"])
    async def api_info() -> dict[str, str]:
        return {
            "name": "rez-proxy",
            "version": "0.0.1",
            "description": "RESTful API for Rez package manager",
            "api_version": "v1",
            "docs_url": config.docs_url,
            "redoc_url": config.redoc_url,
            "api_prefix": config.api_prefix,
        }

    return versioned_app


# For uvicorn direct execution
app = create_app()
