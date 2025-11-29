# Legion v2.2 Production Dockerfile with OS Integration

FROM python:3.14-slim

LABEL maintainer="legion14041981@gmail.com"
LABEL version="2.2.0"
LABEL description="Legion AI Multi-Agent Framework with OS Integration"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install --no-cache-dir playwright==1.45.0 && \
    playwright install-deps && \
    playwright install chromium firefox webkit

# Copy requirements
COPY requirements.txt requirements.in ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY pyproject.toml pytest.ini ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/workspaces

# Set environment variables
ENV PYTHONPATH=/app/src
ENV LEGION_MODE=production
ENV LEGION_OS_ENABLED=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from legion.core import LegionCore; print('OK')" || exit 1

# Expose ports
EXPOSE 8000 9090

# Default command
CMD ["python", "-m", "uvicorn", "legion.mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
