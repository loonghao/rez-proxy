# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


### Added
- Complete RESTful API for Rez package manager
- FastAPI-based web service with automatic OpenAPI documentation
- Comprehensive package management endpoints (search, query, versions)
- Environment resolution and creation capabilities
- Build system integration with Rez
- System information and diagnostics endpoints
- Configuration management and validation
- Context-aware platform detection (local/remote modes)
- CLI interface with `rez-proxy` command
- Docker support and deployment configurations
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- GoReleaser configuration for automated releases
- Type hints and mypy support
- Code quality tools (ruff, bandit, safety)
- Development tools and nox task runner
- Multi-language documentation (English/Chinese)

### Features
- **Package Operations**: Search, list, get details, and manage package versions
- **Environment Management**: Resolve dependencies and create Rez environments
- **Build Integration**: Package building and release management
- **System Integration**: Platform detection, configuration, and diagnostics
- **Remote Support**: Context-aware API for remote client integration
- **Security**: Input validation, error handling, and security scanning
- **Performance**: Async operations and efficient Rez integration
- **Monitoring**: Health checks, logging, and system status endpoints

[Unreleased]: https://github.com/loonghao/rez-proxy/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/loonghao/rez-proxy/releases/tag/v1.0.0

## v1.2.0 (2025-06-06)

### Feat

- add comprehensive error handling and Suite management API
- add configurable API documentation URLs and update README
- migrate from twine to uv publish for PyPI publishing

### Fix

- resolve lint issues in test files
- update unit tests to match actual API implementations
- resolve code quality issues and improve type safety
- rebuild Python packages after GoReleaser cleans dist directory
- clean up egg-info after build to prevent dirty git state
- resolve GoReleaser dist directory conflict

### Refactor

- remove legacy CLI parameters for cleaner interface

## v1.1.6 (2025-06-06)

### Fix

- rebuild Python packages after GoReleaser cleans dist directory

## v1.1.5 (2025-06-06)

### Fix

- clean up egg-info after build to prevent dirty git state

## v1.1.4 (2025-06-06)

### Fix

- resolve GoReleaser dist directory conflict

## v1.1.3 (2025-06-06)

### Feat

- migrate from twine to uv publish for PyPI publishing

## v1.1.2 (2025-06-06)

### Fix

- add type annotations for mypy compliance
- resolve unit test failures and adjust CI coverage threshold
- remove problematic middleware test file and update noxfile
- resolve mypy type annotation errors and remove problematic test files
- resolve PyPI publishing and type annotation issues

## v1.1.1 (2025-06-06)

### Fix

- add required value for uv publish trusted-publishing parameter

## v1.1.0 (2025-06-05)

### Feat

- configure PyPI trusted publishing and commitizen
- prepare v1.0.0 release - fix code formatting and update version
- add comprehensive RESTful API endpoints for complete Rez functionality
- implement rez-proxy RESTful API with GoReleaser

### Fix

- temporarily disable mypy check in GoReleaser
- resolve all package router test failures
- resolve all package router test failures
- resolve CLI test hanging issue
- correct Rez core API integration and improve package handling

### Refactor

- convert relative imports to absolute imports
