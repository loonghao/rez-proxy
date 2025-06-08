#!/usr/bin/env python3
"""
Rez Proxy CLI - Command line interface.
"""

import click
import uvicorn

from rez_proxy.config import get_config
from rez_proxy.utils.rez_detector import detect_rez_installation


@click.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--log-level", default="info", help="Log level")
@click.option("--workers", default=1, type=int, help="Number of worker processes")
# Rez configuration options
@click.option("--rez-config-file", help="Rez config file path")
@click.option("--rez-packages-path", help="Rez packages path (colon-separated)")
@click.option("--rez-local-packages-path", help="Rez local packages path")
@click.option(
    "--rez-release-packages-path", help="Rez release packages path (colon-separated)"
)
@click.option("--rez-tmpdir", help="Rez temporary directory")
@click.option("--rez-cache-path", help="Rez package cache path")
@click.option("--rez-disable-home-config", is_flag=True, help="Disable Rez home config")
@click.option("--rez-quiet", is_flag=True, help="Enable Rez quiet mode")
@click.option("--rez-debug", is_flag=True, help="Enable Rez debug mode")
def main(
    host: str,
    port: int,
    reload: bool,
    log_level: str,
    workers: int,
    rez_config_file: str | None,
    rez_packages_path: str | None,
    rez_local_packages_path: str | None,
    rez_release_packages_path: str | None,
    rez_tmpdir: str | None,
    rez_cache_path: str | None,
    rez_disable_home_config: bool,
    rez_quiet: bool,
    rez_debug: bool,
) -> None:
    """
    Rez Proxy - RESTful API server for Rez package manager.

    Configure Rez environment through command line options or environment variables.
    Environment variables use REZ_PROXY_API_ prefix (e.g., REZ_PROXY_API_REZ_CONFIG_FILE).
    """

    # Set Rez configuration environment variables
    rez_config = {
        "rez_config_file": rez_config_file,
        "rez_packages_path": rez_packages_path,
        "rez_local_packages_path": rez_local_packages_path,
        "rez_release_packages_path": rez_release_packages_path,
        "rez_tmpdir": rez_tmpdir,
        "rez_cache_packages_path": rez_cache_path,
        "rez_disable_home_config": rez_disable_home_config,
        "rez_quiet": rez_quiet,
        "rez_debug": rez_debug,
    }

    # Apply configuration
    from rez_proxy.config import set_rez_config_from_dict

    set_rez_config_from_dict(rez_config)

    click.echo("🔧 Rez Configuration Applied:")
    for key, value in rez_config.items():
        if value:
            click.echo(f"   {key}: {value}")

    # Detect Rez installation
    try:
        rez_info = detect_rez_installation()
        click.echo(f"✅ Found Rez {rez_info['version']}")

        # Show packages path if available
        packages_path = rez_info.get("packages_path", [])
        if packages_path:
            if isinstance(packages_path, list):
                click.echo(
                    f"📁 Packages path: {', '.join(str(p) for p in packages_path[:3])}"
                )
                if len(packages_path) > 3:
                    click.echo(f"   ... and {len(packages_path) - 3} more")
            else:
                click.echo(f"📁 Packages path: {packages_path}")
        else:
            click.echo("⚠️  No packages path configured")

        click.echo(f"🐍 Python: {rez_info['python_path']}")

        # Show any config errors as warnings
        if "config_error" in rez_info:
            click.echo(f"⚠️  Config warning: {rez_info['config_error']}")

    except Exception as e:
        click.echo(f"❌ Rez detection failed: {e}", err=True)
        click.echo("💡 Please ensure Rez is properly installed and configured.")
        raise click.ClickException(f"Rez detection failed: {e}")

    # Create application (will be created by uvicorn factory)

    # Get config for URLs
    config = get_config()

    click.echo(f"🚀 Starting Rez Proxy on http://{host}:{port}")
    click.echo(f"📖 API docs: http://{host}:{port}{config.docs_url}")
    click.echo(f"🔍 ReDoc docs: http://{host}:{port}{config.redoc_url}")
    click.echo(f"🔗 V1 API: http://{host}:{port}{config.api_prefix}/")
    click.echo(f"🔗 Latest API: http://{host}:{port}/latest/")
    click.echo(f"💡 API info: http://{host}:{port}/api/info")
    click.echo(f"🔄 Reload: {reload}")

    # Start server
    uvicorn.run(
        "rez_proxy.main:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        workers=workers if not reload else 1,
    )


# Configuration management commands
@click.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command()
@click.option(
    "--file", "-f", default="config/rez_proxy.json", help="Configuration file path"
)
def create_default(file: str) -> None:
    """Create a default configuration file."""
    from rez_proxy.utils.config_utils import create_default_config_file

    try:
        create_default_config_file(file)
        click.echo(f"✅ Default configuration created: {file}")
    except Exception as e:
        click.echo(f"❌ Failed to create configuration: {e}", err=True)
        raise click.ClickException(str(e))


@config.command()
@click.argument("file")
def validate(file: str) -> None:
    """Validate a configuration file."""
    from rez_proxy.utils.config_utils import validate_config_file

    try:
        result = validate_config_file(file)

        if result["valid"]:
            click.echo(f"✅ Configuration file is valid: {file}")

            if result["warnings"]:
                click.echo("⚠️  Warnings:")
                for warning in result["warnings"]:
                    click.echo(f"   {warning}")
        else:
            click.echo(f"❌ Configuration file is invalid: {file}")
            for error in result["errors"]:
                click.echo(f"   {error}")
            raise click.ClickException("Configuration validation failed")

    except Exception as e:
        click.echo(f"❌ Failed to validate configuration: {e}", err=True)
        raise click.ClickException(str(e))


@config.command()
@click.argument("file")
@click.option("--suffix", default=".backup", help="Backup file suffix")
def backup(file: str, suffix: str) -> None:
    """Create a backup of a configuration file."""
    from rez_proxy.utils.config_utils import backup_config_file

    try:
        backup_path = backup_config_file(file, suffix)
        click.echo(f"✅ Configuration backup created: {backup_path}")
    except Exception as e:
        click.echo(f"❌ Failed to create backup: {e}", err=True)
        raise click.ClickException(str(e))


@config.command()
@click.argument("backup_file")
@click.argument("target_file")
def restore(backup_file: str, target_file: str) -> None:
    """Restore configuration from backup."""
    from rez_proxy.utils.config_utils import restore_config_from_backup

    try:
        restore_config_from_backup(backup_file, target_file)
        click.echo(f"✅ Configuration restored: {backup_file} -> {target_file}")
    except Exception as e:
        click.echo(f"❌ Failed to restore configuration: {e}", err=True)
        raise click.ClickException(str(e))


@config.command()
@click.argument("file1")
@click.argument("file2")
def diff(file1: str, file2: str) -> None:
    """Show differences between two configuration files."""
    from rez_proxy.utils.config_utils import get_config_diff

    try:
        diff_result = get_config_diff(file1, file2)

        if diff_result["added"]:
            click.echo("➕ Added:")
            for key, value in diff_result["added"].items():
                click.echo(f"   {key}: {value}")

        if diff_result["removed"]:
            click.echo("➖ Removed:")
            for key, value in diff_result["removed"].items():
                click.echo(f"   {key}: {value}")

        if diff_result["changed"]:
            click.echo("🔄 Changed:")
            for key, change in diff_result["changed"].items():
                click.echo(f"   {key}: {change['old']} -> {change['new']}")

        if not any(
            [diff_result["added"], diff_result["removed"], diff_result["changed"]]
        ):
            click.echo("✅ No differences found")

    except Exception as e:
        click.echo(f"❌ Failed to compare configurations: {e}", err=True)
        raise click.ClickException(str(e))


# Create a multi-command CLI
@click.group()
def cli() -> None:
    """Rez Proxy - RESTful API server for Rez package manager."""
    pass


cli.add_command(main, name="serve")
cli.add_command(config)


if __name__ == "__main__":
    cli()
