# Rez Proxy

[![PyPI version](https://badge.fury.io/py/rez-proxy.svg)](https://badge.fury.io/py/rez-proxy)
[![Python Support](https://img.shields.io/pypi/pyversions/rez-proxy.svg)](https://pypi.org/project/rez-proxy/)
[![License](https://img.shields.io/github/license/loonghao/rez-proxy.svg)](https://github.com/loonghao/rez-proxy/blob/main/LICENSE)
[![Tests](https://github.com/loonghao/rez-proxy/workflows/Tests/badge.svg)](https://github.com/loonghao/rez-proxy/actions)
[![Release](https://github.com/loonghao/rez-proxy/workflows/Release/badge.svg)](https://github.com/loonghao/rez-proxy/actions)
[![codecov](https://codecov.io/gh/loonghao/rez-proxy/branch/main/graph/badge.svg)](https://codecov.io/gh/loonghao/rez-proxy)
[![Downloads](https://img.shields.io/pypi/dm/rez-proxy.svg)](https://pypi.org/project/rez-proxy/)

A RESTful API proxy for [Rez](https://github.com/AcademySoftwareFoundation/rez) package manager, built with FastAPI.

[中文文档](README_zh.md)

## Features

- 🚀 **RESTful API**: Complete REST interface for Rez operations
- 📦 **Package Management**: Search, query, and manage Rez packages
- 🔍 **Environment Resolution**: Resolve and create Rez environments
- 🌐 **TypeScript Ready**: Perfect for TypeScript/JavaScript integration
- ⚡ **Fast**: Built with FastAPI for high performance
- 🐍 **Easy Deployment**: Deploy with `uvx rez-proxy`
- 🔧 **Configurable**: Flexible configuration via environment variables
- 📚 **Auto-Generated Docs**: Interactive API documentation with Swagger UI
- 🔄 **Versioned API**: Support for API versioning with backward compatibility

## Quick Start

### Installation

```bash
# Install via pip
pip install rez-proxy

# Or install via uvx (recommended)
uvx install rez-proxy
```

### Usage

```bash
# Start the server
uvx rez-proxy

# Or with custom configuration
uvx rez-proxy --host 0.0.0.0 --port 8080

# With custom API paths
REZ_PROXY_API_DOCS_URL=/documentation uvx rez-proxy
```

The API will be available at:
- **API Base**: `http://localhost:8000/api/v1`
- **Documentation**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **API Info**: `http://localhost:8000/api/info`

## API Endpoints

### Package Operations
- `GET /api/v1/packages` - List all packages
- `GET /api/v1/packages/{name}` - Get package details
- `GET /api/v1/packages/{name}/versions` - Get package versions
- `POST /api/v1/packages/search` - Search packages

### Environment Operations
- `POST /api/v1/environments/resolve` - Resolve environment
- `GET /api/v1/environments/{id}` - Get environment details
- `POST /api/v1/environments/{id}/execute` - Execute command in environment
- `DELETE /api/v1/environments/{id}` - Delete environment

### Suite Management
- `POST /api/v1/suites` - Create new suite
- `GET /api/v1/suites` - List all suites
- `GET /api/v1/suites/{id}` - Get suite details
- `POST /api/v1/suites/{id}/contexts` - Add context to suite
- `POST /api/v1/suites/{id}/tools/alias` - Alias tool in suite
- `POST /api/v1/suites/{id}/save` - Save suite to disk
- `GET /api/v1/suites/{id}/tools` - Get suite tools
- `DELETE /api/v1/suites/{id}` - Delete suite

### System Operations
- `GET /api/v1/system/status` - Get system status
- `GET /api/v1/system/config` - Get Rez configuration

## Configuration

The server can be configured via environment variables or command line arguments:

### Server Configuration

```bash
# Basic server settings
export REZ_PROXY_API_HOST=0.0.0.0
export REZ_PROXY_API_PORT=8080
export REZ_PROXY_API_LOG_LEVEL=info
export REZ_PROXY_API_WORKERS=4

# API paths (customize documentation URLs)
export REZ_PROXY_API_API_PREFIX=/api/v1
export REZ_PROXY_API_DOCS_URL=/docs
export REZ_PROXY_API_REDOC_URL=/redoc

# Command line
uvx rez-proxy --host 0.0.0.0 --port 8080 --log-level debug
```

### Rez Configuration

```bash
# Rez-specific settings
export REZ_PROXY_API_REZ_CONFIG_FILE=/path/to/rezconfig.py
export REZ_PROXY_API_REZ_PACKAGES_PATH=/path/to/packages
export REZ_PROXY_API_REZ_LOCAL_PACKAGES_PATH=/path/to/local/packages
export REZ_PROXY_API_REZ_RELEASE_PACKAGES_PATH=/path/to/release/packages

# Cache settings
export REZ_PROXY_API_ENABLE_CACHE=true
export REZ_PROXY_API_CACHE_TTL=300
```

## Development

### Prerequisites

- Python 3.10+
- Rez package manager
- uv (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/loonghao/rez-proxy.git
cd rez-proxy

# Install dependencies
uvx nox -s dev

# Run tests
uvx nox -s pytest

# Start development server
uvx nox -s serve
```

### Testing

```bash
# Run all tests
uvx nox -s pytest

# Run with coverage
uvx nox -s pytest -- --cov

# Run specific tests
uvx nox -s pytest -- tests/test_api.py
```

## TypeScript Integration

```typescript
import axios from 'axios';

const rezApi = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});

// Search packages
const packages = await rezApi.post('/packages/search', {
  query: 'python',
  limit: 10
});

// Resolve environment
const environment = await rezApi.post('/environments/resolve', {
  packages: ['python-3.9', 'requests']
});
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Rez](https://github.com/AcademySoftwareFoundation/rez) - The amazing package manager
- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
