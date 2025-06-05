# Rez-Proxy Nox 开发命令

## 快速开始

### 🚀 一键启动

```bash
# 最快启动方式：安装依赖并启动服务器
uvx nox -s quick_start
```

### 📋 查看所有命令

```bash
uvx nox -l
```

## 开发服务器命令

### 基础开发服务器

```bash
# 标准开发服务器（自动重载）
uvx nox -s serve

# 增强调试模式（详细日志）
uvx nox -s serve_debug

# 生产模式（多进程，无重载）
uvx nox -s serve_prod

# 远程访问模式（绑定到 0.0.0.0）
uvx nox -s serve_remote
```

### 服务器特性

- **serve**: 标准开发模式，自动重载，localhost:8000
- **serve_debug**: 增强调试，详细日志，CORS 开放
- **serve_prod**: 生产模式，4个工作进程，无重载
- **serve_remote**: 远程访问，绑定所有IP地址

## 测试和检查命令

### 依赖和环境检查

```bash
# 检查所有依赖是否正确安装
uvx nox -s check_deps

# 安装开发依赖并显示使用说明
uvx nox -s dev
```

### API 测试

```bash
# 测试 API 端点（需要服务器运行）
uvx nox -s test_api

# 运行 API 演示
uvx nox -s demo
```

### 代码质量

```bash
# 代码风格检查
uvx nox -s lint

# 代码格式化
uvx nox -s format

# 类型检查
uvx nox -s mypy

# 运行单元测试
uvx nox -s pytest
```

## 文档和信息

```bash
# 显示 API 文档信息
uvx nox -s docs
```

## 构建和发布

```bash
# 构建包
uvx nox -s build

# 清理构建产物
uvx nox -s clean

# 发布检查
uvx nox -s release_check

# 干运行发布
uvx nox -s release_dry_run
```

## 使用示例

### 开发工作流

```bash
# 1. 设置开发环境
uvx nox -s dev

# 2. 检查依赖
uvx nox -s check_deps

# 3. 启动调试服务器
uvx nox -s serve_debug

# 4. 在另一个终端测试 API
uvx nox -s test_api
```

### 快速测试

```bash
# 一键启动并测试
uvx nox -s quick_start

# 在另一个终端运行演示
uvx nox -s demo
```

## 服务器访问地址

启动服务器后可访问：

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **健康检查**: http://localhost:8000/health
- **V1 API**: http://localhost:8000/api/v1/
- **最新 API**: http://localhost:8000/latest/

## 环境配置

### 开发配置文件

复制 `dev-config.env` 到 `.env` 进行自定义配置：

```bash
cp dev-config.env .env
```

### 常用环境变量

```bash
REZ_PROXY_HOST=localhost
REZ_PROXY_PORT=8000
REZ_PROXY_LOG_LEVEL=debug
REZ_PROXY_CORS_ORIGINS=["*"]
```

## 故障排除

### 常见问题

1. **依赖缺失**
   ```bash
   uvx nox -s dev
   ```

2. **端口被占用**
   ```bash
   # 修改 dev-config.env 中的端口
   REZ_PROXY_PORT=8001
   ```

3. **Rez 未安装**
   ```bash
   # 确保 Rez 已安装并可用
   rez --version
   ```

### 调试技巧

1. **查看详细日志**
   ```bash
   uvx nox -s serve_debug
   ```

2. **测试特定端点**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/system/status
   ```

3. **检查平台信息**
   ```bash
   curl http://localhost:8000/api/v1/system/platform
   ```

## 高级用法

### 自定义启动

如果需要更多控制，可以直接使用：

```bash
# 使用 Python 脚本启动
python start_dev_server.py

# 或直接使用 CLI
rez-proxy --reload --log-level debug
```

### 远程模式测试

```bash
# 设置远程平台上下文
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Service-Mode: remote" \
  -d '{"platform":"linux","arch":"x86_64","os":"ubuntu-20.04","python_version":"3.8.10"}' \
  http://localhost:8000/api/v1/system/context
```

## 贡献开发

1. **开发前检查**
   ```bash
   uvx nox -s lint
   uvx nox -s mypy
   uvx nox -s pytest
   ```

2. **提交前验证**
   ```bash
   uvx nox -s release_check
   ```

这些 nox 命令让 rez-proxy 的开发和调试变得非常简单和高效！
