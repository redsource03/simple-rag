# Multi-stage Dockerfile for RAG Agent MCP Server
# Stage 1: Build stage
FROM python:3.14-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build setuptools wheel

# Copy application structure
COPY pyproject.toml ./
COPY src/ ./src/

# Build and install the package
RUN pip install --no-cache-dir .

# Stage 2: Runtime stage
FROM python:3.14-slim as runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy application code
COPY src/ /app/src/

# Create logs directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Switch to non-root user
USER appuser

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "rag_agent.main"]
