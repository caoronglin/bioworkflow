# AGENTS.md - Agentic Coding Guidelines

## Build, Lint, and Test Commands

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_health.py -v

# Run a single test function
pytest tests/test_health.py::test_health_status -v

# Run tests with coverage
pytest tests/ --cov=src/backend --cov-report=html

# Run only unit tests (exclude slow/integration)
pytest tests/ -v -m "not slow and not integration"

# Run specific test markers
pytest tests/ -v -m "slow"          # Only slow tests
pytest tests/ -v -m "integration"   # Only integration tests
```

### Linting and Formatting
```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Run Ruff linter
ruff check src/ tests/

# Run Ruff with auto-fix
ruff check src/ tests/ --fix

# Type checking with mypy
mypy src/backend

# Run all quality checks
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/ && mypy src/backend

# Run pre-commit hooks on all files
pre-commit run --all-files
```

### Frontend Commands
```bash
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Production build
npm run build

# Run ESLint
npm run lint

# Run Prettier
npm run format

# Type check
npm run type-check
```

### Service-Specific Commands
```bash
# Workflow service
cd services/workflow-service
pip install -e ".[dev]"
pytest tests/ -v

# Miniforge service
cd services/miniforge-service
pip install -e ".[dev]"
pytest tests/ -v
```

### Docker Commands
```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild containers
docker-compose up -d --build

# Stop all services
docker-compose down
```

## Code Style Guidelines

### Python
- **Line length**: 100 characters max
- **Python version**: 3.12+ (use modern features like union types `X | Y`)
- **Formatter**: Black
- **Import sorting**: isort with `profile = "black"`
- **Linter**: Ruff with rules: E, F, W, I, N, UP, B, C4, SIM, PERF, FURB, RUF

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `WorkflowExecutionEngine`)
- **Functions/Variables**: `snake_case` (e.g., `get_pipeline_status`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`)
- **Private members**: Leading underscore (e.g., `_internal_helper`)

#### Type Hints
- Use Python 3.10+ union syntax: `str | None` instead of `Optional[str]`
- Use built-in generics: `list[str]` instead of `List[str]`
- Always type function parameters and return values
- Use `strict = true` in mypy configuration

#### Imports
```python
# Standard library imports
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

# Third-party imports
from fastapi import FastAPI, HTTPException, Request
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Local application imports (absolute imports preferred)
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.middleware import PerformanceMiddleware
```

#### Error Handling
- Use specific exceptions over generic ones
- Always catch specific exceptions first
- Use FastAPI's `HTTPException` for API errors
- Use custom exception classes for business logic
- Log exceptions with `logger.exception()` for unexpected errors

```python
# Good
try:
    result = await process_data(data)
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise HTTPException(status_code=400, detail="Invalid data format")
except PipelineExecutionError as e:
    logger.exception(f"Pipeline failed: {e}")
    raise HTTPException(status_code=500, detail="Pipeline execution failed")
```

#### Async/Await Patterns
- Use `async`/`await` for I/O-bound operations
- Use `asyncio.gather()` for concurrent operations
- Use `asyncio.Semaphore` for limiting concurrency

```python
async def fetch_multiple(urls: list[str]) -> list[dict]:
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
    
    async def fetch_with_limit(url: str) -> dict:
        async with semaphore:
            return await fetch_data(url)
    
    return await asyncio.gather(*[fetch_with_limit(url) for url in urls])
```

### Frontend (Vue 3 + TypeScript)
- Use Composition API with `<script setup>`
- Use TypeScript for all components
- Follow Vue 3 style guide
- Use `const` and `let`, never `var`

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `WorkflowEditor.vue`)
- **Composables**: `use` prefix + `camelCase` (e.g., `usePipelineStore`)
- **Types/Interfaces**: `PascalCase` with descriptive names

## Git Workflow

Follow **Conventional Commits**:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
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

## Project-Specific Notes

- **Python 3.12+**: Use modern syntax features like union types (`X | Y`)
- **FastAPI**: Uses dependency injection; leverage `Depends()` for services
- **SQLAlchemy 2.0**: Use `select()` syntax and async session patterns
- **Pydantic v2**: Use `field_validator` instead of deprecated `validator`
- **Snakemake 9.0+**: Workflow execution engine
- **MCP**: Model Context Protocol integration for AI tools
- **Vue 3**: Frontend uses Composition API with TypeScript
- **Rust**: Performance-critical components in `rust/` directory

## Architecture

```
src/backend/
├── api/routes/      # API endpoints
├── core/            # Config, database, interfaces
├── infrastructure/  # Cache, events, metrics, search
├── models/          # SQLAlchemy models
├── services/        # Business logic
└── middleware/      # Request/response middleware

src/frontend/
├── pages/           # Page components
├── components/      # Reusable components
├── stores/          # Pinia state management
└── api/             # API client modules
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `pytest tests/test_file.py::test_func -v` | Run single test |
| `black src/ tests/` | Format Python code |
| `ruff check src/ tests/ --fix` | Lint and auto-fix |
| `mypy src/backend` | Type check |
| `cd src/frontend && npm run dev` | Start frontend |
| `docker-compose up -d` | Start all services |
| `pre-commit run --all-files` | Run all hooks |