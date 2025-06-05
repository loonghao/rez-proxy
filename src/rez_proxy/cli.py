#!/usr/bin/env python3
"""
Rez Proxy CLI - Command line interface.
"""

import os
import sys

import click
import uvicorn

from .utils.rez_detector import detect_rez_installation


@click.command()
@click.option('--host', default='localhost', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--log-level', default='info', help='Log level')
@click.option('--config-file', help='Rez config file path')
@click.option('--packages-path', help='Override packages path')
@click.option('--workers', default=1, type=int, help='Number of worker processes')
def main(host, port, reload, log_level, config_file, packages_path, workers):
    """
    Rez Proxy - RESTful API server for Rez package manager.
    """

    # Set Rez configuration file
    if config_file:
        os.environ['REZ_CONFIG_FILE'] = config_file

    # Set packages path
    if packages_path:
        os.environ['REZ_PACKAGES_PATH'] = packages_path

    # Detect Rez installation
    try:
        rez_info = detect_rez_installation()
        click.echo(f"✅ Found Rez {rez_info['version']}")
        click.echo(f"📁 Packages path: {rez_info['packages_path']}")
        click.echo(f"🐍 Python: {rez_info['python_path']}")
    except Exception as e:
        click.echo(f"❌ Rez detection failed: {e}", err=True)
        sys.exit(1)

    # Create application (will be created by uvicorn factory)

    click.echo(f"🚀 Starting Rez Proxy on http://{host}:{port}")
    click.echo(f"📖 API docs: http://{host}:{port}/docs")
    click.echo(f"🔄 Reload: {reload}")

    # Start server
    uvicorn.run(
        "rez_proxy.main:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        workers=workers if not reload else 1
    )


if __name__ == "__main__":
    main()
