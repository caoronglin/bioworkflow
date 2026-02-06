# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioWorkflow is a modern bioinformatics workflow management platform based on Snakemake. It features a FastAPI backend with a Vue 3 frontend, conda environment management, knowledge base integration, and MCP (Model Context Protocol) interfaces for AI tool integration.

**Key Technologies:**
- Backend: FastAPI, SQLAlchemy 2.0, Pydantic v2, Snakemake 9.0+
- Frontend: Vue 3, Vite, TypeScript, Element Plus
- Database: SQLite (default), supports PostgreSQL/MySQL
- Task Queue: Celery with Redis
- Python: 3.13+ / 3.14 recommended

## Common Development Commands

### Quick Start (Both Backend and Frontend)

```bash
# Start both services (recommended for development)
./dev-start.sh        # Linux/macOS
dev-start.bat         # Windows

# Services will be available at:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Backend Development

```bash
# Install dependencies (editable mode with dev dependencies)
pip install -e ".[dev]"

# Start backend development server
cd src/backend
python -m uvicorn main:app --reload --port 8000

# Run database migrations (using Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head

# API documentation is auto-generated at:
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Frontend Development

```bash
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev        # http://localhost:5173

# Production build
npm run build

# Preview production build
npm run preview

# Code quality
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

# Run frontend tests
# cd src/frontend && npm test
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

### Backend Structure

```
src/backend/
├── main.py                 # FastAPI application factory
├── api/                    # API layer
│   ├── __init__.py         # Router aggregation
│   └── routes/             # Endpoint handlers
│       ├── health.py       # Health checks
│       ├── auth.py         # Authentication
│       ├── pipelines.py    # Pipeline management
│       ├── conda.py        # Conda management
│       ├── knowledge.py    # Knowledge base
│       └── mcp.py          # MCP interfaces
├── core/                   # Core infrastructure
│   ├── config.py           # Pydantic settings
│   ├── database.py         # SQLAlchemy setup
│   ├── dependencies.py     # DI container
│   ├── events.py           # Event bus
│   └── logging.py          # Loguru config
├── models/                 # SQLAlchemy ORM models
│   ├── base.py             # Base model
│   ├── user.py             # User model
│   ├── pipeline.py         # Pipeline models
│   └── knowledge.py        # Knowledge models
├── services/               # Business logic layer
│   ├── snakemake/          # Snakemake integration
│   ├── conda/              # Conda management
│   ├── pipeline/           # Pipeline execution
│   ├── knowledge/          # Knowledge base
│   ├── mcp/                # MCP protocol
│   └── cache.py            # Caching service
├── auth/                   # Authentication utilities
│   └── jwt.py              # JWT handling
├── tasks/                  # Celery background tasks
└── utils/                  # Shared utilities
```

### Frontend Structure

```
src/frontend/
├── package.json            # Node.js dependencies
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript config
├── index.html              # Entry HTML
└── src/
    ├── main.ts             # App entry point
    ├── App.vue             # Root component
    ├── router.ts           # Vue Router config
    ├── api/                # API client
    │   ├── client.ts       # Axios instance
    │   └── index.ts        # API methods
    ├── stores/             # Pinia stores
    │   └── app.ts          # App state
    ├── components/         # Reusable components
    │   └── workflow/       # Workflow editor
    ├── pages/              # Route pages
    │   ├── Dashboard.vue
    │   ├── Pipelines.vue
    │   ├── PipelineDetail.vue
    │   ├── CondaManager.vue
    │   ├── Knowledge.vue
    │   ├── MCPServices.vue
    │   └── Settings.vue
    └── styles/             # SCSS styles
        └── main.scss
```

## Key Design Patterns

1. **Dependency Injection**: Uses FastAPI's DI system and custom DI container for services
2. **Repository Pattern**: Database access through SQLAlchemy models
3. **Event-Driven Architecture**: Event bus for decoupled module communication
4. **Layered Architecture**: API → Services → Models clear separation
5. **Async/Await**: Full async support for high concurrency

## Configuration

Key environment variables in `.env`:

```bash
# Application
DEBUG=true
VERSION=0.0.1

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./bioworkflow.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
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

## Service Ports

When running locally:
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:5173
- **Redis**: localhost:6379 (if used)
- **Elasticsearch**: localhost:9200 (if used)

## Git Workflow

Follow **Conventional Commits** format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test changes
- `chore:` Build/tooling changes

Example commit message:
```
feat(pipelines): add async execution support

- Implement Snakemake async execution
- Add concurrency control with semaphore
- Support execution cancellation
```
