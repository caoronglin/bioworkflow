"""
Skills Registry Service

Manages the registration, storage, and retrieval of skills.
Provides CRUD operations and search capabilities.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from backend.core.database import get_db_session
from backend.models.skill import (
    Skill,
    SkillCategory,
    SkillConfiguration,
    SkillDependency,
    SkillPermission,
    SkillStatus,
    SkillVisibility,
)

logger = logging.getLogger(__name__)


class SkillsRegistry:
    """Registry for managing skills"""
    
    _instance: SkillsRegistry | None = None
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    async def get_instance(cls) -> SkillsRegistry:
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def register(
        self,
        skill: Skill,
        db: AsyncSession | None = None,
    ) -> Skill:
        """
        Register a new skill in the registry.
        
        Args:
            skill: The skill to register
            db: Optional database session
            
        Returns:
            The registered skill
        """
        if db is None:
            db = await get_db_session()
        
        try:
            # Check if slug already exists
            existing = await self._get_by_slug(skill.slug, db)
            if existing:
                raise ValueError(f"Skill with slug '{skill.slug}' already exists")
            
            # Set timestamps
            now = datetime.utcnow()
            skill.created_at = now
            skill.updated_at = now
            
            # Set initial version if not set
            if not skill.version:
                skill.version = "0.0.1"
            
            # Add to database
            db.add(skill)
            await db.commit()
            await db.refresh(skill)
            
            self.logger.info(f"Registered skill: {skill.name} ({skill.id})")
            return skill
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to register skill: {e}")
            raise
    
    async def get(
        self,
        skill_id: UUID,
        db: AsyncSession | None = None,
    ) -> Skill | None:
        """
        Get a skill by ID.
        
        Args:
            skill_id: The skill ID
            db: Optional database session
            
        Returns:
            The skill if found, None otherwise
        """
        if db is None:
            db = await get_db_session()
        
        result = await db.execute(
            select(Skill)
            .options(
                joinedload(Skill.author),
                selectinload(Skill.dependencies),
                selectinload(Skill.permissions),
            )
            .where(Skill.id == skill_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_by_slug(
        self,
        slug: str,
        db: AsyncSession,
    ) -> Skill | None:
        """Get a skill by slug"""
        result = await db.execute(
            select(Skill).where(Skill.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def update(
        self,
        skill_id: UUID,
        data: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> Skill:
        """
        Update a skill.
        
        Args:
            skill_id: The skill ID
            data: The data to update
            db: Optional database session
            
        Returns:
            The updated skill
        """
        if db is None:
            db = await get_db_session()
        
        try:
            skill = await self.get(skill_id, db)
            if not skill:
                raise ValueError(f"Skill with ID {skill_id} not found")
            
            # Update fields
            for key, value in data.items():
                if hasattr(skill, key):
                    setattr(skill, key, value)
            
            skill.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(skill)
            
            self.logger.info(f"Updated skill: {skill.name} ({skill.id})")
            return skill
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to update skill: {e}")
            raise
    
    async def delete(
        self,
        skill_id: UUID,
        db: AsyncSession | None = None,
    ) -> None:
        """
        Delete a skill (soft delete).
        
        Args:
            skill_id: The skill ID
            db: Optional database session
        """
        if db is None:
            db = await get_db_session()
        
        try:
            skill = await self.get(skill_id, db)
            if not skill:
                raise ValueError(f"Skill with ID {skill_id} not found")
            
            # Soft delete - update status
            skill.status = SkillStatus.ARCHIVED
            skill.updated_at = datetime.utcnow()
            
            await db.commit()
            
            self.logger.info(f"Deleted skill: {skill.name} ({skill.id})")
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to delete skill: {e}")
            raise
    
    async def search(
        self,
        query: str | None = None,
        category: SkillCategory | None = None,
        tags: list[str] | None = None,
        status: SkillStatus = SkillStatus.PUBLISHED,
        visibility: SkillVisibility | None = None,
        page: int = 1,
        page_size: int = 20,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Search skills with filters.
        
        Returns:
            Dict with items, total, page info
        """
        if db is None:
            db = await get_db_session()
        
        # Build query
        stmt = select(Skill).where(Skill.status == status)
        
        if query:
            stmt = stmt.where(
                or_(
                    Skill.name.ilike(f"%{query}%"),
                    Skill.description.ilike(f"%{query}%"),
                    Skill.slug.ilike(f"%{query}%"),
                )
            )
        
        if category:
            stmt = stmt.where(Skill.category == category)
        
        if tags:
            # PostgreSQL array overlap
            stmt = stmt.where(Skill.tags.overlap(tags))
        
        if visibility:
            stmt = stmt.where(Skill.visibility == visibility)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0
        
        # Add pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        # Execute
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": list(items),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
