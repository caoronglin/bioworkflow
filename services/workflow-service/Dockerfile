FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for pyo3)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ /app/src/

# Install the package
RUN pip install --no-cache-dir -e .[dev]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:${WORKFLOW_PORT}/health || exit 1

# Expose port
EXPOSE 8001

# Command
CMD ["python", "-m", "workflow_service", "run"]
