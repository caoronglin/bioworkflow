# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioWorkflow is a bioinformatics workflow management platform built on Snakemake. It features a FastAPI backend with a Vue 3 frontend, conda environment management, knowledge base integration, and MCP (Model Context Protocol) interfaces for AI tool integration.

## Common Development Commands

### Quick Start (Recommended)
```bash
# Start both backend and frontend in development mode
./dev-start.sh        # Linux/macOS
dev-start.bat         # Windows
```

### Backend Development
```bash
# Install dependencies (editable mode with dev dependencies)
pip install -e ".[dev]"

# Start backend server only
cd src/backend
python -m uvicorn main:app --reload --port 8000

# API documentation is auto-generated at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### Frontend Development
```bash
cd src/frontend
npm install
npm run dev        # Development server on http://localhost:5173
npm run build      # Production build
npm run lint       # Run ESLint
npm run format     # Run Prettier
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_health.py -v

# Run specific test function
pytest tests/test_health.py::test_health_status -v

# Run with coverage report
pytest tests/ --cov=src/backend --cov-report=html
```

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
ruff check src/ tests/
mypy src/backend

# Run pre-commit hooks on all files
pre-commit run --all-files
```

## Project Architecture

### Backend (FastAPI)

**Entry Point**: `src/backend/main.py`

The backend follows a modular architecture:

```
src/backend/
├── main.py                 # FastAPI application factory
├── core/                   # Core configuration and logging
│   ├── config.py         # Pydantic Settings (env vars)
│   └── logging.py        # Loguru configuration
├── api/                    # API layer
│   ├── __init__.py       # Router aggregation
│   └── routes/           # Endpoint handlers
│       ├── health.py
│       ├── auth.py
│       ├── pipelines.py
│       ├── conda.py
│       ├── knowledge.py
│       └── mcp.py
├── services/               # Business logic layer
│   ├── snakemake/        # Snakemake integration
│   ├── conda/            # Conda environment management
│   ├── pipeline/         # Pipeline execution logic
│   ├── knowledge/        # Knowledge base operations
│   └── mcp/              # MCP protocol implementation
├── models/                 # SQLAlchemy ORM models
├── tasks/                  # Celery background tasks
├── auth/                   # JWT authentication utilities
└── utils/                  # Shared utility functions
```

**Key Design Patterns**:
- **Dependency Injection**: Uses FastAPI's DI system for services
- **Pydantic Models**: Request/response validation via Pydantic v2
- **Settings Management**: `core/config.py` uses `pydantic-settings` with `.env` file support
- **Router Pattern**: API routes are modular and self-contained

### Frontend (Vue 3 + Vite)

**Entry Point**: `src/frontend/src/main.ts` (implied)

```
src/frontend/src/
├── components/           # Reusable Vue components
├── pages/              # Route-level page components
│   ├── Dashboard.vue
│   ├── Pipelines.vue
│   ├── PipelineDetail.vue
│   ├── CondaManager.vue
│   ├── Knowledge.vue
│   ├── MCPServices.vue
│   └── Settings.vue
├── stores/             # Pinia state management
├── api/                # API client functions
├── router.ts           # Vue Router configuration
└── styles/             # SCSS/CSS styles
```

**Key Technologies**:
- **Vue 3**: Composition API with `<script setup>` syntax
- **Vite**: Fast development server and build tool
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **Element Plus**: UI component library
- **Vue Flow**: Workflow visualization (for pipeline editor)

## Configuration

### Environment Variables (`.env`)

Key configuration in `.env` file:

```bash
# Application
DEBUG=true
VERSION=0.0.1a1

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./bioworkflow.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# JWT Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Snakemake
SNAKEMAKE_WORKDIR=./workflows
SNAKEMAKE_CONDA_PREFIX=./conda_envs

# Conda
CONDA_CHANNELS=conda-forge,bioconda,defaults

# Elasticsearch (Knowledge Base)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

## Testing Strategy

- **Unit Tests**: `pytest` for backend logic, run with `pytest tests/ -v`
- **API Tests**: Use `fastapi.testclient.TestClient` for endpoint testing
- **Test Configuration**: `conftest.py` contains shared fixtures

## Code Quality Standards

The project enforces code quality through:

- **Black**: Code formatting (line length: 100)
- **Ruff**: Fast Python linting
- **isort**: Import sorting
- **mypy**: Static type checking (strict mode)
- **pre-commit**: Git hooks for quality checks

## Git Workflow

- Follow **Conventional Commits** format:
  - `feat:` New features
  - `fix:` Bug fixes
  - `docs:` Documentation changes
  - `style:` Code style changes (formatting)
  - `refactor:` Code refactoring
  - `perf:` Performance improvements
  - `test:` Test changes
  - `chore:` Build/tooling changes

## Service Ports

When running locally:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:5173
- **Redis**: localhost:6379 (if used)
- **Elasticsearch**: localhost:9200 (if used)

## Common Development Tasks

### Adding a New API Endpoint

1. Create route handler in `src/backend/api/routes/`
2. Register router in `src/backend/api/__init__.py`
3. Add tests in `tests/`

### Adding a New Frontend Page

1. Create Vue component in `src/frontend/src/pages/`
2. Add route in `src/frontend/src/router.ts`
3. Add navigation link if needed

### Adding Dependencies

- **Python**: Edit `pyproject.toml` dependencies, then `pip install -e ".[dev]"`
- **Node**: `cd src/frontend && npm install <package>`
