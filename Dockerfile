# Legion Framework - Production Dockerfile
# Multi-stage build for optimized image size

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LEGION_OS_ENABLED=true \
    ENVIRONMENT=production

# Create non-root user
RUN groupadd -r legion && useradd -r -g legion legion

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=legion:legion src/ ./src/
COPY --chown=legion:legion scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data && chown -R legion:legion /app/data

# Switch to non-root user
USER legion

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5).raise_for_status()" || exit 1

# Run application
CMD ["uvicorn", "src.legion.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
