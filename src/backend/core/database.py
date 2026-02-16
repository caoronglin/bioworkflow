"""
数据库连接和会话管理 - Python 3.14 优化版本

支持高并发和连接池管理
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.core.config import settings
from backend.models.base import Base

# 创建异步引擎
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite 使用 NullPool 避免并发问题
    engine = create_async_engine(
        settings.database_async_url,
        echo=settings.DATABASE_ECHO,
        poolclass=NullPool,
    )
else:
    # PostgreSQL/MySQL 使用连接池
    engine = create_async_engine(
        settings.database_async_url,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """初始化数据库 - 创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的上下文管理器

    使用示例:
        async with get_session() as session:
            result = await session.execute(query)
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# FastAPI 依赖注入使用
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖 - 获取数据库会话

    使用示例:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with get_session() as session:
        yield session
