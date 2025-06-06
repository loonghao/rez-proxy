# rez-proxy

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

## Development

This project uses [nox](https://nox.thea.codes/) for unified task management across local development and CI environments.

### 🚨 Important: Always Use Nox

**DO NOT** run tests directly with `uvx pytest` or `python -m pytest`. This will fail with import errors because dependencies are not installed globally.

**ALWAYS** use nox for consistent, isolated environments:

```bash
# ✅ Correct way
uvx nox -s test
make test

# ❌ Wrong way - will fail
uvx pytest
python -m pytest
```

### Quick Development Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install nox
uvx install nox

# Set up development environment
make install
# or
uvx nox -s dev

# Start development server
make serve
# or
uvx nox -s serve
```

### Testing & Quality

```bash
# Run all tests with coverage
make test
uvx nox -s test

# Run tests without coverage (faster)
make test-fast
uvx nox -s test_fast

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-routers       # Router tests only

# Generate coverage report
make coverage
make coverage-html      # Open HTML report in browser

# Code quality checks
make lint               # Linting
make format             # Code formatting
make mypy               # Type checking
make security           # Security scanning
make quality            # All quality checks

# Pre-commit checks
make pre-commit
uvx nox -s pre_commit
```

### CI/CD Pipeline

```bash
# Run full CI pipeline locally
make ci
uvx nox -s ci

# Run fast CI checks
make ci-fast
uvx nox -s ci_fast

# Release checks
make release-check
uvx nox -s release_check
```

### Available Commands

```bash
# See all available commands
make help
uvx nox -l

# Development servers
make serve              # Development server with auto-reload
make serve-debug        # Enhanced debugging
make serve-prod         # Production-like server
make serve-remote       # Remote access server

# Utilities
make demo               # Run API demo
make docs               # Show documentation info
make clean              # Clean build artifacts
make build              # Build package
```

### Git Hooks

```bash
# Install pre-commit hooks
make install-hooks

# Uninstall pre-commit hooks
make uninstall-hooks
```

The pre-commit hooks will automatically run `uvx nox -s pre_commit` before each commit, ensuring code quality.

## 核心文件实现

### 1. CLI 入口 (cli.py)
```python
#!/usr/bin/env python3
"""
Rez Proxy CLI - 命令行接口
"""

import os
import sys
import click
import uvicorn
from pathlib import Path

from .config import RezProxyConfig
from .utils.rez_detector import detect_rez_installation
from .main import create_app

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
    Rez Proxy - RESTful API server for Rez package manager
    """
    
    # 设置 Rez 配置文件
    if config_file:
        os.environ['REZ_CONFIG_FILE'] = config_file
    
    # 设置包路径
    if packages_path:
        os.environ['REZ_PACKAGES_PATH'] = packages_path
    
    # 检测 Rez 安装
    try:
        rez_info = detect_rez_installation()
        click.echo(f"✅ Found Rez {rez_info['version']}")
        click.echo(f"📁 Packages path: {rez_info['packages_path']}")
        click.echo(f"🐍 Python: {rez_info['python_path']}")
    except Exception as e:
        click.echo(f"❌ Rez detection failed: {e}", err=True)
        sys.exit(1)
    
    # 创建应用
    app = create_app()
    
    click.echo(f"🚀 Starting Rez Proxy on http://{host}:{port}")
    click.echo(f"📖 API docs: http://{host}:{port}/docs")
    click.echo(f"🔄 Reload: {reload}")
    
    # 启动服务器
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
```

### 2. 主应用 (main.py)
```python
"""
Rez Proxy - FastAPI 应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import get_config
from .routers import packages, environments, shells, system

def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    
    config = get_config()
    
    app = FastAPI(
        title="Rez Proxy",
        description="RESTful API for Rez package manager",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(system.router, prefix="/api/system", tags=["system"])
    app.include_router(packages.router, prefix="/api/packages", tags=["packages"])
    app.include_router(environments.router, prefix="/api/environments", tags=["environments"])
    app.include_router(shells.router, prefix="/api/shells", tags=["shells"])
    
    # 根路径重定向到文档
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")
    
    # 健康检查
    @app.get("/health", tags=["system"])
    async def health_check():
        return {"status": "healthy", "service": "rez-proxy"}
    
    return app

# 用于 uvicorn 直接运行
app = create_app()
```

### 3. 配置管理 (config.py)
```python
"""
Rez Proxy 配置管理
"""

import os
from typing import List, Optional
from pydantic import BaseSettings

class RezProxyConfig(BaseSettings):
    """Rez Proxy 配置"""
    
    # 服务器配置
    host: str = "localhost"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    workers: int = 1
    
    # CORS 配置
    cors_origins: List[str] = ["*"]
    
    # Rez 配置
    rez_config_file: Optional[str] = None
    rez_packages_path: Optional[str] = None
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # 安全配置
    api_key: Optional[str] = None
    max_concurrent_environments: int = 10
    max_command_timeout: int = 300  # 5 minutes
    
    class Config:
        env_prefix = "REZ_PROXY_"
        case_sensitive = False

_config: Optional[RezProxyConfig] = None

def get_config() -> RezProxyConfig:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = RezProxyConfig()
        
        # 从环境变量设置 Rez 配置
        if _config.rez_config_file:
            os.environ['REZ_CONFIG_FILE'] = _config.rez_config_file
        if _config.rez_packages_path:
            os.environ['REZ_PACKAGES_PATH'] = _config.rez_packages_path
    
    return _config
```

### 4. Rez 检测工具 (utils/rez_detector.py)
```python
"""
Rez 安装检测工具
"""

import os
import sys
from typing import Dict, Any, List
from pathlib import Path

def detect_rez_installation() -> Dict[str, Any]:
    """检测 Rez 安装信息"""
    
    try:
        import rez
        from rez import config
        
        # 基础信息
        info = {
            "version": rez.__version__,
            "rez_root": str(Path(rez.__file__).parent.parent),
            "python_path": sys.executable,
            "python_version": sys.version,
        }
        
        # 配置信息
        try:
            info.update({
                "packages_path": config.packages_path,
                "local_packages_path": config.local_packages_path,
                "release_packages_path": config.release_packages_path,
                "config_file": getattr(config, 'config_file', None),
                "platform": config.platform.name,
                "arch": config.arch.name,
                "os": config.os.name,
            })
        except Exception as e:
            info["config_error"] = str(e)
        
        # 环境变量
        rez_env_vars = {
            key: value for key, value in os.environ.items() 
            if key.startswith('REZ_')
        }
        info["environment_variables"] = rez_env_vars
        
        return info
        
    except ImportError as e:
        raise RuntimeError(f"Rez not found: {e}")
    except Exception as e:
        raise RuntimeError(f"Rez detection failed: {e}")

def validate_rez_environment() -> List[str]:
    """验证 Rez 环境，返回警告列表"""
    warnings = []
    
    try:
        info = detect_rez_installation()
        
        # 检查包路径
        if not info.get("packages_path"):
            warnings.append("No packages path configured")
        
        # 检查配置文件
        config_file = info.get("config_file")
        if config_file and not Path(config_file).exists():
            warnings.append(f"Config file not found: {config_file}")
        
        # 检查权限
        packages_path = info.get("packages_path", [])
        if isinstance(packages_path, list):
            for path in packages_path:
                if not os.access(path, os.R_OK):
                    warnings.append(f"No read access to packages path: {path}")
        
    except Exception as e:
        warnings.append(f"Environment validation failed: {e}")
    
    return warnings
```

### 5. pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "rez-proxy"
version = "1.0.0"
description = "RESTful API proxy for Rez package manager"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0",
    "pydantic>=2.0.0",
    "click>=8.0.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/your-org/rez-proxy"
Documentation = "https://github.com/your-org/rez-proxy#readme"
Repository = "https://github.com/your-org/rez-proxy.git"
Issues = "https://github.com/your-org/rez-proxy/issues"

[project.scripts]
rez-proxy = "rez_proxy.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## 使用场景

### 1. 开发环境
```bash
# 开发者本地启动
cd rez-proxy
pip install -e ".[dev]"
rez-proxy --reload --log-level debug
```

### 2. 生产环境
```bash
# 生产环境部署
pip install rez-proxy
export REZ_CONFIG_FILE=/path/to/production/config.py
export REZ_PACKAGES_PATH=/shared/packages:/local/packages
rez-proxy --host 0.0.0.0 --port 8080 --workers 4
```

### 3. Docker 部署
```dockerfile
FROM python:3.9-slim

# 安装 Rez 和 rez-proxy
RUN pip install rez rez-proxy

# 设置环境变量
ENV REZ_PACKAGES_PATH=/packages
ENV REZ_PROXY_HOST=0.0.0.0
ENV REZ_PROXY_PORT=8000

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["rez-proxy"]
```

### 4. 配置文件示例
```bash
# .env 文件
REZ_PROXY_HOST=localhost
REZ_PROXY_PORT=8000
REZ_PROXY_CORS_ORIGINS=["http://localhost:3000", "https://your-app.com"]
REZ_PROXY_ENABLE_CACHE=true
REZ_PROXY_MAX_CONCURRENT_ENVIRONMENTS=20

# Rez 配置
REZ_CONFIG_FILE=/path/to/rez/config.py
REZ_PACKAGES_PATH=/shared/packages:/local/packages
```

## 优势

1. **独立部署** - 可以单独安装和部署
2. **配置灵活** - 支持环境变量和配置文件
3. **生产就绪** - 支持多进程、缓存、监控
4. **易于维护** - 标准的 Python 包结构
5. **文档完整** - 自动生成 OpenAPI 文档

这样的设计让后端成为一个完全独立的服务，可以灵活部署和配置。
