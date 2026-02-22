# Miniforge Service Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM condaforge/miniforge:latest AS builder

# Install Python and build dependencies
RUN mamba install -y \
    python=3.11 \
    pip \
    && mamba clean -afy

# Set up build directory
WORKDIR /build

# Copy requirements first for better caching
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM condaforge/miniforge:latest AS runtime

# Install runtime dependencies only
RUN mamba install -y \
    python=3.11 \
    && mamba clean -afy

# Create non-root user
RUN groupadd -r miniforge && \
    useradd -r -g miniforge -s /bin/false miniforge

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/

# Install the application
RUN pip install --no-cache-dir -e .

# Change ownership to non-root user
RUN chown -R miniforge:miniforge /app

# Switch to non-root user
USER miniforge

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MINIFORGE_SERVICE_HOST=0.0.0.0 \
    MINIFORGE_SERVICE_PORT=8001

# Run the application
CMD ["miniforge-service"]
