"""
Rez Proxy - FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import get_config
from .routers import build, environments, package_ops, packages, repositories, resolver, rez_config, shells, system, versions


def create_app() -> FastAPI:
    """Create FastAPI application."""

    config = get_config()

    app = FastAPI(
        title="Rez Proxy",
        description="RESTful API for Rez package manager",
        version="0.0.1",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
    app.include_router(packages.router, prefix="/api/v1/packages", tags=["packages"])
    app.include_router(environments.router, prefix="/api/v1/environments", tags=["environments"])
    app.include_router(shells.router, prefix="/api/v1/shells", tags=["shells"])
    app.include_router(repositories.router, prefix="/api/v1/repositories", tags=["repositories"])
    app.include_router(versions.router, prefix="/api/v1/versions", tags=["versions"])
    app.include_router(resolver.router, prefix="/api/v1/resolver", tags=["resolver"])
    app.include_router(rez_config.router, prefix="/api/v1/config", tags=["config"])
    app.include_router(package_ops.router, prefix="/api/v1/package-ops", tags=["package-operations"])
    app.include_router(build.router, prefix="/api/v1/build", tags=["build"])

    # Root path redirect to documentation
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Health check
    @app.get("/health", tags=["system"])
    async def health_check():
        return {"status": "healthy", "service": "rez-proxy"}

    return app


# For uvicorn direct execution
app = create_app()
