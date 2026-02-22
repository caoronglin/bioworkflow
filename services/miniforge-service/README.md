# Miniforge Service

A microservice for managing Miniforge/Mamba environments, providing a RESTful API for environment lifecycle management.

## Features

- 🚀 **Fast Package Resolution** - Uses Mamba for fast package solving
- 🐍 **Python Environment Management** - Create, update, and delete Python environments
- 📦 **Package Operations** - Install, remove, update, and search packages
- 🔍 **Environment Inspection** - View installed packages and environment details
- 🔄 **Clone & Export** - Clone environments and export configurations
- 📊 **Health Monitoring** - Built-in health checks and Prometheus metrics

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t miniforge-service .

# Run the container
docker run -p 8001:8001 miniforge-service
```

### Using Python

```bash
# Install dependencies
cd services/miniforge-service
pip install -e ".[dev]"

# Run the service
miniforge-service
```

The service will be available at `http://localhost:8001`.

## API Documentation

Once the service is running, you can access:

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`
- **Health Check**: `http://localhost:8001/health`

### Example API Usage

#### Create an Environment

```bash
curl -X POST "http://localhost:8001/api/v1/environments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "myenv",
    "python_version": "3.11",
    "packages": [
      {"name": "numpy"},
      {"name": "pandas", "version": "2.0"}
    ]
  }'
```

#### List Environments

```bash
curl "http://localhost:8001/api/v1/environments"
```

#### Search Packages

```bash
curl "http://localhost:8001/api/v1/packages/search?query=pandas&limit=10"
```

#### Install a Package

```bash
curl -X POST "http://localhost:8001/api/v1/packages/myenv/packages" \
  -H "Content-Type: application/json" \
  -d '[{"name": "scipy"}]'
```

## Configuration

The service can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8001` |
| `LOG_LEVEL` | Log level | `info` |
| `DEBUG` | Debug mode | `false` |
| `MINIFORGE_ROOT` | Miniforge installation path | auto-detected |
| `ENVS_DIR` | Environments directory | `{miniforge_root}/envs` |
| `METRICS_ENABLED` | Enable Prometheus metrics | `true` |
| `OTEL_ENABLED` | Enable OpenTelemetry tracing | `false` |

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=miniforge_service --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Run linter
ruff check src/ tests/
mypy src/

# Run all checks
pre-commit run --all-files
```

## Architecture

```
┌─────────────────────────────────────┐
│         FastAPI Application         │
├─────────────────────────────────────┤
│  Routers  │  Middleware  │  Models  │
├─────────────────────────────────────┤
│         MiniforgeManager            │
│   (Mamba/Conda command wrapper)     │
├─────────────────────────────────────┤
│         Miniforge Installation      │
│    (Mamba, Conda, Base Environment) │
└─────────────────────────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Miniforge](https://github.com/conda-forge/miniforge) - The minimal installer for Conda with Mamba
- [Mamba](https://github.com/mamba-org/mamba) - The fast cross-platform package manager
- [FastAPI](https://fastapi.tiangolo.com/) - The modern, fast web framework
