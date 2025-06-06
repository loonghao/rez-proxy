# rez-proxy

[![PyPI version](https://badge.fury.io/py/rez-proxy.svg)](https://badge.fury.io/py/rez-proxy)
[![Python Support](https://img.shields.io/pypi/pyversions/rez-proxy.svg)](https://pypi.org/project/rez-proxy/)
[![License](https://img.shields.io/github/license/loonghao/rez-proxy.svg)](https://github.com/loonghao/rez-proxy/blob/main/LICENSE)
[![Tests](https://github.com/loonghao/rez-proxy/workflows/Tests/badge.svg)](https://github.com/loonghao/rez-proxy/actions)
[![codecov](https://codecov.io/gh/loonghao/rez-proxy/branch/main/graph/badge.svg)](https://codecov.io/gh/loonghao/rez-proxy)

为 [Rez](https://github.com/AcademySoftwareFoundation/rez) 包管理器提供的 RESTful API 代理，基于 FastAPI 构建。

[English Documentation](README.md)

## 特性

- 🚀 **RESTful API**: 完整的 Rez 操作 REST 接口
- 📦 **包管理**: 搜索、查询和管理 Rez 包
- 🔍 **环境解析**: 解析和创建 Rez 环境
- 🌐 **TypeScript 就绪**: 完美支持 TypeScript/JavaScript 集成
- ⚡ **高性能**: 基于 FastAPI 构建，性能卓越
- 🐍 **简易部署**: 使用 `uvx rez-proxy` 一键部署

## 快速开始

### 安装

```bash
# 通过 pip 安装
pip install rez-proxy

# 或通过 uvx 安装（推荐）
uvx install rez-proxy
```

### 使用

```bash
# 启动服务器
uvx rez-proxy

# 或使用自定义配置
uvx rez-proxy --host 0.0.0.0 --port 8080
```

API 将在 `http://localhost:8000` 可用，交互式文档在 `http://localhost:8000/docs`。

## API 端点

### 包操作
- `GET /api/v1/packages` - 列出所有包
- `GET /api/v1/packages/{name}` - 获取包详情
- `GET /api/v1/packages/{name}/versions` - 获取包版本
- `POST /api/v1/packages/search` - 搜索包

### 环境操作
- `POST /api/v1/environments/resolve` - 解析环境
- `GET /api/v1/environments/{id}` - 获取环境详情
- `POST /api/v1/environments/{id}/execute` - 在环境中执行命令

### 系统操作
- `GET /api/v1/system/status` - 获取系统状态
- `GET /api/v1/system/config` - 获取 Rez 配置

## 开发

### 前置要求

- Python 3.8+
- Rez 包管理器
- uv（推荐）或 pip

### 设置

```bash
# 克隆仓库
git clone https://github.com/loonghao/rez-proxy.git
cd rez-proxy

# 安装依赖
uvx nox -s dev

# 运行测试
uvx nox -s pytest

# 启动开发服务器
uvx nox -s serve
```

### 测试

```bash
# 运行所有测试
uvx nox -s pytest

# 运行覆盖率测试
uvx nox -s pytest -- --cov

# 运行特定测试
uvx nox -s pytest -- tests/test_api.py
```

## 配置

服务器可以通过环境变量或命令行参数配置：

```bash
# 环境变量
export REZ_PROXY_HOST=0.0.0.0
export REZ_PROXY_PORT=8080
export REZ_PROXY_LOG_LEVEL=info

# 命令行
uvx rez-proxy --host 0.0.0.0 --port 8080 --log-level debug
```

## TypeScript 集成

```typescript
import axios from 'axios';

const rezApi = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});

// 搜索包
const packages = await rezApi.post('/packages/search', {
  query: 'python',
  limit: 10
});

// 解析环境
const environment = await rezApi.post('/environments/resolve', {
  packages: ['python-3.9', 'requests']
});
```

## 发布流程

项目使用 GitHub Actions 自动发布到 PyPI：

```bash
# 创建发布标签
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions 将自动构建并发布到 PyPI
```

## 贡献

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 许可证

本项目基于 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 致谢

- [Rez](https://github.com/AcademySoftwareFoundation/rez) - 出色的包管理器
- [FastAPI](https://fastapi.tiangolo.com/) - 使用的 Web 框架
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包安装器
