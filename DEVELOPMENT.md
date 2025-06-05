# Rez-Proxy 开发指南

## 🚨 重要：始终使用 Nox

**不要** 直接使用 `uvx pytest` 或 `python -m pytest` 运行测试。这会失败，因为依赖没有安装在全局环境中。

**始终** 使用 nox 来确保一致的隔离环境：

```bash
# ✅ 正确的测试运行方式
uvx nox -s test
make test

# ❌ 错误的方式 - 会出现导入错误
uvx pytest
python -m pytest
```

## 快速开始

### 1. 一键启动开发服务器

```bash
# 安装依赖并启动服务器
uvx nox -s quick_start
```

### 2. 常用开发命令

```bash
# 开发服务器（自动重载）
uvx nox -s serve

# 调试模式（增强日志）
uvx nox -s serve_debug

# 生产模式（多进程）
uvx nox -s serve_prod

# 远程访问模式
uvx nox -s serve_remote
```

### 3. 测试和检查

```bash
# 测试 API 端点
uvx nox -s test_api

# 检查依赖
uvx nox -s check_deps

# 运行演示
uvx nox -s demo

# 查看所有可用命令
uvx nox -l
```

## 开发环境设置

### 1. 安装开发依赖

```bash
uvx nox -s dev
```

### 2. 配置环境变量

复制 `dev-config.env` 到 `.env` 并根据需要修改：

```bash
cp dev-config.env .env
```

### 3. 验证安装

```bash
uvx nox -s check_deps
```

## API 访问

### 开发服务器启动后可访问：

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **V1 API**: http://localhost:8000/api/v1/
- **最新 API**: http://localhost:8000/latest/

### API 版本

- `/api/v1/*` - 版本 1 API
- `/latest/*` - 最新版本 API
- `/docs` - 所有版本的文档

## 开发工作流

### 1. 启动开发服务器

```bash
uvx nox -s serve_debug
```

### 2. 测试 API

```bash
# 在另一个终端
uvx nox -s test_api
```

### 3. 查看日志

服务器会显示详细的调试日志，包括：
- 请求上下文信息
- 平台检测结果
- 中间件处理过程

### 4. 代码检查

```bash
uvx nox -s lint    # 代码风格检查
uvx nox -s mypy    # 类型检查
uvx nox -s pytest # 运行测试
```

## 调试技巧

### 1. 上下文调试

启用上下文调试模式：

```bash
export REZ_PROXY_CONTEXT_DEBUG=true
uvx nox -s serve_debug
```

### 2. 平台信息调试

查看平台检测结果：

```bash
curl http://localhost:8000/api/v1/system/platform
```

### 3. 远程模式测试

```bash
# 设置平台上下文
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Service-Mode: remote" \
  -d '{"platform":"linux","arch":"x86_64","os":"ubuntu-20.04","python_version":"3.8.10"}' \
  http://localhost:8000/api/v1/system/context
```

## 常见问题

### 1. 服务器启动失败

检查 Rez 安装：
```bash
rez --version
```

### 2. 依赖缺失

重新安装依赖：
```bash
uvx nox -s dev
```

### 3. 端口被占用

使用不同端口：
```bash
rez-proxy --port 8001
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 运行测试：`uvx nox -s pytest`
4. 检查代码：`uvx nox -s lint`
5. 提交 PR

## 有用的链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [FastAPI Versioning](https://github.com/DeanWay/fastapi-versioning)
- [Rez 文档](https://rez.readthedocs.io/)
- [Uvicorn 文档](https://www.uvicorn.org/)
