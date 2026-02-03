"""数据库连接和会话管理 - 支持高并发"""

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

# 创建异步引擎 - 优化连接池以支持高并发
engine = create_async_engine(
    settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"),
    echo=settings.DEBUG,
    poolclass=NullPool,  # SQLite 使用 NullPool 避免并发问题
    # 对于 PostgreSQL/MySQL，使用以下配置：
    # pool_size=20,              # 基础连接数
    # max_overflow=30,           # 额外连接数
    # pool_pre_ping=True,        # 连接健康检查
    # pool_recycle=3600,         # 连接回收时间
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 避免过期问题，支持高并发
    autoflush=False,         # 手动控制 flush
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
    ```python
    async with get_session() as session:
        result = await session.execute(query)
    ```
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
    ```python
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
    ```
    """
    async with get_session() as session:
        yield session
