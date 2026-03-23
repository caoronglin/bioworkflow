# Multi-Stage Dockerfile for Python + Rust + Vue Full-Stack Project
# Optimizes image size from ~3GB to ~200MB
#
# Reference:
# - Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
# - Rust optimization: https://www.docker.com/blog/faster-multi-platform-builds-dockerfile-cross-compilation-guide/

# ============================================
# STAGE 1: Rust Builder - Build native module
# ============================================
FROM rust:1.85-slim AS rust-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Cache dependencies by creating dummy project first
COPY rust/Cargo.toml rust/Cargo.lock ./
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Build actual code
COPY rust/src ./src
RUN touch src/main.rs && cargo build --release

# ============================================
# STAGE 2: Python Builder - Install dependencies
# ============================================
FROM python:3.12-slim AS python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml requirements*.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy and install the package
COPY src/backend ./src/backend
COPY --from=rust-builder /build/target/release/libnative_module.so ./src/backend/
RUN pip install --no-cache-dir -e .

# ============================================
# STAGE 3: Frontend Builder - Build Vue app
# ============================================
FROM node:25-alpine AS frontend-builder

WORKDIR /build

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Cache dependencies
COPY src/frontend/package.json src/frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Build application
COPY src/frontend ./
RUN pnpm build

# ============================================
# STAGE 4: Runtime - Minimal production image
# ============================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser src/backend ./backend
COPY --chown=appuser:appuser --from=frontend-builder /build/dist ./static

# Copy Rust native module
COPY --from=rust-builder /build/target/release/libnative_module.so ./backend/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]

# ============================================
# Alternative: Distroless image for maximum security
# ============================================
# FROM gcr.io/distroless/python3-debian12:latest AS runtime-distroless
# 
# WORKDIR /app
# COPY --from=python-builder /opt/venv /opt/venv
# COPY --chown=nonroot:nonroot src/backend ./backend
# COPY --chown=nonroot:nonroot --from=frontend-builder /build/dist ./static
# 
# ENV PATH="/opt/venv/bin:$PATH"
# EXPOSE 8000
# 
# CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]