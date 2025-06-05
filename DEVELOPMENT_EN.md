# Development Guide

This guide explains how to set up and work with the rez-proxy development environment.

## 🚨 Important: Always Use Nox

**DO NOT** run tests directly with `uvx pytest` or `python -m pytest`. This will fail because dependencies are not installed in the global environment.

**ALWAYS** use nox for consistent, isolated environments:

```bash
# ✅ Correct way to run tests
uvx nox -s test
make test

# ❌ Wrong way - will fail with import errors
uvx pytest
python -m pytest
```

## Quick Start

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install nox**:
   ```bash
   uv tool install nox
   ```

3. **Set up development environment**:
   ```bash
   make install
   # or
   uvx nox -s dev
   ```

4. **Run tests**:
   ```bash
   make test
   # or
   uvx nox -s test
   ```

## Testing Commands

### Basic Testing
```bash
# Run all tests with coverage
make test
uvx nox -s test

# Run tests without coverage (faster)
make test-fast
uvx nox -s test_fast

# Run tests in watch mode (auto-rerun on file changes)
make test-watch
uvx nox -s test_watch
```

### Specific Test Categories
```bash
# Unit tests only
make test-unit
uvx nox -s test_unit

# Integration tests only
make test-integration
uvx nox -s test_integration

# Router tests only
make test-routers
uvx nox -s test_routers

# Test specific Python versions
uvx nox -s pytest-3.11
uvx nox -s pytest-3.12
```

### Coverage Reports
```bash
# Generate coverage report
make coverage
uvx nox -s coverage

# Generate and open HTML coverage report
make coverage-html
uvx nox -s coverage_html
```

## Code Quality

### Linting and Formatting
```bash
# Check code style
make lint
uvx nox -s lint

# Fix code style issues
make lint-fix
uvx nox -s lint_fix

# Format code
make format
uvx nox -s format

# Type checking
make mypy
uvx nox -s mypy
```

### Security and Safety
```bash
# Security scanning
make security
uvx nox -s security

# Check dependencies for vulnerabilities
make safety
uvx nox -s safety

# Run all quality checks
make quality
uvx nox -s quality
```

## Development Server

```bash
# Start development server with auto-reload
make serve
uvx nox -s serve

# Start with enhanced debugging
make serve-debug
uvx nox -s serve_debug

# Start production-like server
make serve-prod
uvx nox -s serve_prod

# Start server for remote access
make serve-remote
uvx nox -s serve_remote

# Start in tolerant mode (works with Rez config issues)
uvx nox -s serve_tolerant
```

## CI/CD Pipeline

### Local CI Testing
```bash
# Run full CI pipeline locally
make ci
uvx nox -s ci

# Run fast CI checks
make ci-fast
uvx nox -s ci_fast

# Pre-commit checks
make pre-commit
uvx nox -s pre_commit
```

### Release Process
```bash
# Release checks
make release-check
uvx nox -s release_check

# Build package
make build
uvx nox -s build
```

## Git Workflow

### Pre-commit Hooks
```bash
# Install pre-commit hooks
make install-hooks

# Manually run pre-commit checks
make pre-commit
uvx nox -s pre_commit

# Uninstall hooks
make uninstall-hooks
```

The pre-commit hooks will automatically run quality checks before each commit.

## Troubleshooting

### Common Issues

1. **Import errors when running pytest directly**:
   ```
   ModuleNotFoundError: No module named 'fastapi'
   ```
   **Solution**: Use nox instead of direct pytest:
   ```bash
   # ❌ Don't do this
   uvx pytest
   
   # ✅ Do this instead
   uvx nox -s test
   ```

2. **Nox not found**:
   ```bash
   # Install nox
   uv tool install nox
   
   # Add to PATH if needed (Windows)
   $env:PATH = "C:\Users\<username>\.local\bin;$env:PATH"
   ```

3. **Tests fail due to missing Rez**:
   - Tests are designed to work without Rez installed
   - They use mocks to simulate Rez functionality
   - If you see Rez-related errors, check the mock setup

### Environment Issues

If you encounter environment issues:

1. **Clean and rebuild**:
   ```bash
   make clean
   uvx nox -s clean
   ```

2. **Check dependencies**:
   ```bash
   uvx nox -s check_deps
   ```

3. **Validate configuration**:
   ```bash
   uvx nox -s validate_config
   ```

## Available Commands

Run `make help` or `uvx nox -l` to see all available commands:

```bash
# See all make targets
make help

# See all nox sessions
uvx nox -l

# Get development environment info
make dev
uvx nox -s dev
```

## Best Practices

1. **Always use nox** for testing and quality checks
2. **Run tests before committing** with `make pre-commit`
3. **Use make shortcuts** for common tasks
4. **Check coverage** regularly with `make coverage-html`
5. **Run full CI locally** before pushing with `make ci`

This ensures consistency between your local environment and CI/CD.
