# ==============================================
# Legion AI System v2.0 - Production Dockerfile
# Multi-stage build for optimized image size
# ==============================================

# Stage 1: Builder - Install dependencies and build
FROM python:3.11-slim as builder

LABEL maintainer="legion14041981@gmail.com"
LABEL version="2.0.0"
LABEL description="Legion AI System - Multi-Agent Framework"

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY setup.py .
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim as runtime

# Create non-root user for security
RUN groupadd -r legion && useradd -r -g legion legion

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /build/src ./src
COPY --from=builder /build/setup.py .
COPY --from=builder /build/pyproject.toml .

# Create data directory
RUN mkdir -p /data/workspaces && chown -R legion:legion /data

# Switch to non-root user
USER legion

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    WORKSPACE_ROOT=/data/workspaces

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose MCP server port
EXPOSE 8001

# Expose Prometheus metrics port
EXPOSE 9090

# Volume for persistent data
VOLUME ["/data"]

# Default command
CMD ["python", "-m", "legion.mcp"]
