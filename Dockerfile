# Multi-stage build for rez-proxy
FROM python:3.13-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ src/

# Install dependencies and build
RUN uv sync --frozen --no-dev
RUN uv build

# Production stage
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Create non-root user
RUN groupadd -r rez && useradd -r -g rez rez

# Set working directory
WORKDIR /app

# Copy built wheel from builder stage
COPY --from=builder /app/dist/*.whl ./

# Install the package
RUN uv pip install --system *.whl && rm *.whl

# Create directories for Rez
RUN mkdir -p /packages /config && \
    chown -R rez:rez /packages /config

# Switch to non-root user
USER rez

# Environment variables
ENV REZ_PROXY_HOST=0.0.0.0
ENV REZ_PROXY_PORT=8000
ENV REZ_PACKAGES_PATH=/packages

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["rez-proxy"]
