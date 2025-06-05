"""
Nox configuration for rez-proxy.
"""

import os
import nox


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"])
def pytest(session):
    """Run tests with pytest."""
    session.install("-e", ".[dev]")
    session.run("pytest", *session.posargs)


@nox.session
def lint(session):
    """Run linting with ruff."""
    session.install("ruff")
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")


@nox.session
def format(session):
    """Format code with ruff."""
    session.install("ruff")
    session.run("ruff", "format", "src", "tests")
    session.run("ruff", "check", "--fix", "src", "tests")


@nox.session
def mypy(session):
    """Run type checking with mypy."""
    session.install("-e", ".[dev]")
    session.run("mypy", "src/rez_proxy")


@nox.session
def serve(session):
    """Start development server."""
    session.install("-e", ".[dev]")
    session.run("rez-proxy", "--reload", "--log-level", "debug")


@nox.session
def dev(session):
    """Install development dependencies."""
    session.install("-e", ".[dev]")
    session.log("Development environment ready!")
    session.log("Run 'uvx nox -s serve' to start the development server")


@nox.session
def build(session):
    """Build the package."""
    session.install("build")
    session.run("python", "-m", "build")


@nox.session
def docs(session):
    """Generate API documentation."""
    session.install("-e", ".[dev]")
    # This would generate OpenAPI docs - placeholder for now
    session.log("API documentation available at /docs when server is running")


@nox.session
def release_check(session):
    """Run release checks (used by GoReleaser)."""
    session.install("-e", ".[dev]")

    # Run all checks
    session.run("uvx", "nox", "-s", "lint")
    session.run("uvx", "nox", "-s", "mypy")
    session.run("uvx", "nox", "-s", "pytest")

    session.log("✅ Release checks passed!")


@nox.session
def release_dry_run(session):
    """Run GoReleaser in dry-run mode."""
    session.install("-e", ".[dev]")

    # Check if goreleaser is available
    try:
        session.run("goreleaser", "--version", external=True)
    except Exception:
        session.error("GoReleaser not found. Install it with: go install github.com/goreleaser/goreleaser/v2@latest")

    # Run dry run
    session.run("goreleaser", "release", "--snapshot", "--clean", "--skip=publish", external=True)
    session.log("🔍 Dry run completed - check dist/ folder for artifacts")


@nox.session
def release(session):
    """Create a release using GoReleaser."""
    session.install("-e", ".[dev]")

    # Check if goreleaser is available
    try:
        session.run("goreleaser", "--version", external=True)
    except Exception:
        session.error("GoReleaser not found. Install it with: go install github.com/goreleaser/goreleaser/v2@latest")

    session.log("🚀 This will create a real release!")
    session.log("Make sure you have:")
    session.log("  1. Updated the version in pyproject.toml")
    session.log("  2. Created and pushed a git tag")
    session.log("  3. Set PYPI_TOKEN environment variable")

    # Run release
    session.run("goreleaser", "release", "--clean", external=True)
    session.log("🎉 Release completed!")


@nox.session
def release_test(session):
    """Release to Test PyPI."""
    session.install("-e", ".[dev]")
    session.install("twine")

    # Run release checks first
    session.run("uvx", "nox", "-s", "release")

    # Upload to Test PyPI
    session.run("twine", "upload", "--repository", "testpypi", "dist/*")
    session.log("📦 Package uploaded to Test PyPI!")


@nox.session
def clean(session):
    """Clean build artifacts."""
    import shutil

    dirs_to_clean = ["dist", "build", "*.egg-info", ".pytest_cache", ".coverage", "htmlcov"]

    for dir_pattern in dirs_to_clean:
        if "*" in dir_pattern:
            import glob
            for path in glob.glob(dir_pattern):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    session.log(f"Removed {path}")
        else:
            if os.path.exists(dir_pattern):
                if os.path.isdir(dir_pattern):
                    shutil.rmtree(dir_pattern)
                else:
                    os.remove(dir_pattern)
                session.log(f"Removed {dir_pattern}")
