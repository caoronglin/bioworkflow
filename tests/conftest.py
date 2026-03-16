"""
测试配置 - Python 3.14 优化版本

提供测试夹具和配置
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
import httpx
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import Settings
from backend.core.database import get_db
from backend.main import app
from backend.models.base import Base

# 测试数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


# 创建测试引擎
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# 测试会话工厂
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def setup_test_database() -> AsyncGenerator[None, None]:
    """设置测试数据库 - 异步版本"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端"""

    # 覆盖依赖
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with LifespanManager(app):
        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> AsyncGenerator[TestClient, None]:
    """创建同步测试客户端"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_settings() -> Settings:
    """创建测试配置"""
    return Settings(
        DEBUG=True,
        DATABASE_URL=TEST_DATABASE_URL,
        SECRET_KEY="test-secret-key-for-testing-only",
    )


# 标记
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
]
