<<<<<<< HEAD
# ============================================
# Legion AI System v2.0 - Production Dockerfile
# Multi-stage build for optimized image size
# ============================================

# Stage 1: Builder - Install dependencies and build
FROM python:3.11-slim as builder

LABEL maintainer="legion14041981@gmail.com"
LABEL version="2.0.0"
LABEL description="Legion AI System - Multi-Agent Framework"

# Set working directory
WORKDIR /build

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to /install
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Install runtime dependencies (Playwright browsers need these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Process management
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash legion && \
    mkdir -p /app /data && \
    chown -R legion:legion /app /data

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=legion:legion src/ ./src/
COPY --chown=legion:legion setup.py ./
COPY --chown=legion:legion README.md ./
COPY --chown=legion:legion LICENSE ./
=======
# Multi-stage build for Legion AI v2.0
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 legion

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/legion/.local

# Copy application code
COPY --chown=legion:legion . .

# Set environment variables
ENV PATH=/home/legion/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535

# Switch to non-root user
USER legion

<<<<<<< HEAD
# Install Playwright browsers as non-root user
RUN playwright install chromium --with-deps

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/home/legion/.cache/ms-playwright \
    LOG_LEVEL=INFO \
    WORKSPACE_ROOT=/data/workspaces

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; from src.legion.core import LegionCore; sys.exit(0)"

# Expose MCP server port
EXPOSE 8001

# Expose Prometheus metrics port
EXPOSE 9090

# Volume for persistent data
VOLUME ["/data"]

# Default command
CMD ["python", "-m", "src.main"]
=======
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port
EXPOSE 8001

# Default command
CMD ["python", "-m", "legion.mcp"]
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
