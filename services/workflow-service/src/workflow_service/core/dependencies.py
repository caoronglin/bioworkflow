"""Dependency injection dependencies."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from .config import get_settings, Settings


def get_db_engine(settings: Settings = Depends(get_settings)):
    """Get database engine."""
    engine = create_async_engine(settings.DATABASE_URL)
    return engine


def get_session_maker(
    engine=Depends(get_db_engine),
):
    """Get session maker."""
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db_session(
    session_maker=Depends(get_session_maker),
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for request handling."""
    async with session_maker() as session:
        yield session


def get_workflow_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """Get workflow service instance."""
    from .service import WorkflowService

    return WorkflowService(session, settings)
