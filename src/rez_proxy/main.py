"""
Rez Proxy - FastAPI application with versioning.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_versioning import VersionedFastAPI

from .config import get_config
from .middleware.context import ContextMiddleware
from .routers import (
    build,
    environments,
    package_ops,
    packages,
    repositories,
    resolver,
    rez_config,
    shells,
    system,
    versions,
)


def create_app() -> FastAPI:
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

    # Root path redirect to documentation
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Health check
    @app.get("/health", tags=["system"])
    async def health_check():
        return {"status": "healthy", "service": "rez-proxy"}

    # Create versioned app
    versioned_app = VersionedFastAPI(
        app,
        version_format="{major}",
        prefix_format="/api/v{major}",
        default_version=(1, 0),
        enable_latest=True,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    return versioned_app


# For uvicorn direct execution
app = create_app()
