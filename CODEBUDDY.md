# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

BioWorkflow is a modern bioinformatics workflow management platform based on Snakemake, built with Python 3.14+ and the latest tech stack. It features a FastAPI backend with Vue 3 frontend, conda environment management, knowledge base integration, and MCP interfaces for AI tool integration.

**Key Technologies:**
- Backend: FastAPI, SQLAlchemy 2.0, Pydantic v2, Snakemake 9.0+
- Frontend: Vue 3, Vite, TypeScript, Element Plus, ECharts
- Database: SQLite/PostgreSQL with async support
- Cache: Redis with connection pooling
- Task Queue: Celery with Redis
- Search: Elasticsearch
- Python: 3.14+ required

## Architecture

### Layered Architecture

```
API Layer (Routes, Schemas)
    ↓
Service Layer (Business Logic)
    ↓
Infrastructure Layer (Cache, DB, Search)
    ↓
Interface Layer (Abstract Interfaces)
```

### Key Design Patterns

1. **Dependency Injection**: Custom IoC container in `core/container.py`
2. **Repository Pattern**: Database access through abstract interfaces
3. **Event-Driven**: Event bus for decoupled communication
4. **Interface Segregation**: All services implement interfaces from `core/interfaces.py`

## Common Development Commands

### Quick Start

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
# Install dependencies (requires Python 3.14+)
pip install -e ".[dev]"

# Start backend development server
cd src/backend
python -m uvicorn main:app --reload --port 8000

# Run database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run tests
pytest tests/ -v
pytest tests/test_health.py::test_health_check -v

# Code quality
black src/ tests/
ruff check src/ tests/
mypy src/backend
pre-commit run --all-files
```

### Frontend Development

```bash
cd src/frontend

# Install dependencies (requires Node.js 20+)
npm install

# Start development server
npm run dev        # http://localhost:5173

# Production build
npm run build

# Code quality
npm run lint
npm run format
```

## Project Structure

### Backend

```
src/backend/
├── api/                    # API layer
│   ├── routes/            # Endpoint handlers
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── pipelines.py
│   │   ├── conda.py
│   │   ├── knowledge.py
│   │   ├── mcp.py
│   │   └── system.py      # Performance & metrics
│   └── __init__.py
├── core/                  # Core infrastructure
│   ├── interfaces.py      # Abstract interfaces (Repository, Cache, etc.)
│   ├── container.py       # Dependency injection container
│   ├── config.py          # Pydantic settings (Python 3.14)
│   ├── database.py        # SQLAlchemy async setup
│   ├── performance.py     # Caching, rate limiting, circuit breaker
│   ├── logging.py         # Structured logging
│   └── events.py          # Event bus
├── infrastructure/        # Interface implementations
│   ├── cache/            # Redis cache service
│   ├── database/         # Unit of work, repositories
│   ├── events/           # Event publisher
│   ├── metrics/          # Prometheus metrics
│   └── search/           # Elasticsearch service
├── models/               # SQLAlchemy ORM models
├── services/             # Business logic
│   ├── conda/manager.py       # PackageManager implementation
│   ├── snakemake/workflow_engine.py  # WorkflowEngine implementation
│   └── pipeline/
└── middleware/           # FastAPI middleware
    └── performance.py    # Performance monitoring
```

### Frontend

```
src/frontend/
├── src/
│   ├── api/              # API client
│   ├── components/       # Reusable components
│   ├── pages/            # Route pages
│   ├── stores/           # Pinia stores
│   └── styles/           # SCSS styles
├── package.json          # Dependencies
└── vite.config.ts
```

## Configuration

Key environment variables in `.env`:

```bash
# Application
DEBUG=true
VERSION=0.2.0
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./bioworkflow.db
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Snakemake
SNAKEMAKE_WORKDIR=./workflows
SNAKEMAKE_MAX_CORES=4

# Performance
ENABLE_METRICS=true
ENABLE_CACHE=true
CACHE_DEFAULT_TTL=3600
```

## Service Ports

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:5173
- **Redis**: localhost:6379
- **Elasticsearch**: localhost:9200

## Performance Optimization

### Caching

```python
from backend.core.performance import async_cache

@async_cache(maxsize=128, ttl=300)
async def expensive_operation(param: str) -> dict:
    # Result cached for 5 minutes
    return await fetch_data(param)
```

### Database Query Optimization

```python
from backend.core.performance import measure_performance

@measure_performance("db_query")
async def get_pipelines(db: AsyncSession):
    # Automatically measures and logs query time
    result = await db.execute(select(Pipeline))
    return result.scalars().all()
```

### Rate Limiting

```python
from backend.core.performance import RateLimiter

limiter = RateLimiter(rate=10, capacity=10)  # 10 requests per second

async def api_endpoint():
    await limiter.acquire()
    # Process request
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/backend --cov-report=html

# Run specific test
pytest tests/test_performance.py::test_async_lru_cache -v

# Run async tests
pytest tests/ -v --asyncio-mode=auto
```

## Git Workflow

Follow **Conventional Commits** format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test changes
- `chore:` Build/tooling changes

Example:
```
feat(pipelines): add async execution support

- Implement Snakemake async execution
- Add concurrency control with semaphore
- Support execution cancellation
```

## Important Notes

1. **Always use interfaces**: When creating new services, implement interfaces from `core/interfaces.py`
2. **Register in container**: Add new service implementations to `core/container.py`
3. **Use dependency injection**: Access services through `get_container().resolve(Interface)`
4. **Async everywhere**: All I/O operations should be async
5. **Type hints required**: Use Python 3.14+ type annotation syntax
6. **Performance matters**: Use caching, connection pooling, and batch processing where appropriate
