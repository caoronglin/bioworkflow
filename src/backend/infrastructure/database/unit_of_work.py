"""
工作单元实现 - SQLAlchemy 版本

实现事务管理和仓储模式
"""

from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.interfaces import Repository, UnitOfWork
from backend.core.database import AsyncSessionLocal
from backend.models.base import Base

T = TypeVar("T", bound=Base)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy 工作单元实现"""

    def __init__(self):
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()
        self._session = None

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        if not self._session:
            raise RuntimeError("Unit of work not initialized")
        return self._session


class SQLAlchemyRepository(Repository[T]):
    """通用 SQLAlchemy 仓储实现"""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self._session = session
        self._model_class = model_class

    async def get_by_id(self, id: str) -> T | None:
        return await self._session.get(self._model_class, id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list[T]:
        from sqlalchemy import select

        query = select(self._model_class)

        if filters:
            for key, value in filters.items():
                if hasattr(self._model_class, key):
                    query = query.where(getattr(self._model_class, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def update(self, entity: T) -> T:
        await self._session.merge(entity)
        await self._session.flush()
        return entity

    async def delete(self, id: str) -> bool:
        entity = await self.get_by_id(id)
        if entity:
            await self._session.delete(entity)
            await self._session.flush()
            return True
        return False

    async def exists(self, id: str) -> bool:
        entity = await self.get_by_id(id)
        return entity is not None
