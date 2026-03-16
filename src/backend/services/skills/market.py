"""
Skills Market Service

Provides skill discovery, distribution, and marketplace functionality.
Includes search, recommendations, reviews, and ratings.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
from backend.models.skill import (
    Skill,
    SkillCategory,
    SkillReview,
    SkillStatus,
    SkillVisibility,
)

logger = logging.getLogger(__name__)


class SkillsMarket:
    """Marketplace for skill discovery and distribution"""
    
    _instance: SkillsMarket | None = None
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    async def get_instance(cls) -> SkillsMarket:
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def search(
        self,
        query: str | None = None,
        category: SkillCategory | None = None,
        tags: list[str] | None = None,
        author: str | None = None,
        status: SkillStatus = SkillStatus.PUBLISHED,
        visibility: SkillVisibility | None = None,
        min_rating: float | None = None,
        sort_by: str = 'relevance',
        sort_order: str = 'desc',
        page: int = 1,
        page_size: int = 20,
        db: AsyncSession | None = None,
    ) -> Any:
        """
        Search skills with filters and sorting.
        
        Returns:
            Search results with pagination
        """
        if db is None:
            db = await get_db_session()
        
        # Build base query
        stmt = select(Skill).where(
            and_(
                Skill.status == status,
                Skill.visibility == SkillVisibility.PUBLIC
            )
        )
        
        # Apply filters
        if query:
            search_filter = or_(
                Skill.name.ilike(f"%{query}%"),
                Skill.description.ilike(f"%{query}%"),
                Skill.slug.ilike(f"%{query}%"),
            )
            stmt = stmt.where(search_filter)
        
        if category:
            stmt = stmt.where(Skill.category == category)
        
        if tags:
            stmt = stmt.where(Skill.tags.overlap(tags))
        
        if author:
            stmt = stmt.where(Skill.author['name'].astext == author)
        
        if min_rating is not None:
            # This would require a join with reviews or pre-calculated field
            pass
        
        # Apply sorting
        sort_column = {
            'relevance': Skill.updated_at,
            'downloads': Skill.metrics['downloads'],
            'rating': Skill.metrics['ratings_average'],
            'newest': Skill.created_at,
            'updated': Skill.updated_at,
        }.get(sort_by, Skill.updated_at)
        
        if sort_order == 'desc':
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0
        
        # Apply pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        # Execute
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size
        
        return type('SearchResult', (), {
            'items': list(items),
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        })()
    
    async def get_trending(
        self,
        limit: int = 10,
        db: AsyncSession | None = None,
    ) -> list[Skill]:
        """Get trending skills based on recent downloads and ratings"""
        if db is None:
            db = await get_db_session()
        
        # Get skills with high recent activity
        recent_date = datetime.utcnow() - timedelta(days=30)
        
        stmt = select(Skill).where(
            and_(
                Skill.status == SkillStatus.PUBLISHED,
                Skill.visibility == SkillVisibility.PUBLIC,
                Skill.updated_at >= recent_date,
            )
        ).order_by(
            desc(Skill.metrics['downloads']),
            desc(Skill.metrics['ratings_average']),
        ).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recommended(
        self,
        user_id: UUID,
        limit: int = 10,
        db: AsyncSession | None = None,
    ) -> list[Skill]:
        """Get personalized skill recommendations"""
        if db is None:
            db = await get_db_session()
        
        # This is a simplified recommendation algorithm
        # In production, you'd use ML-based recommendations
        
        # Get skills similar to what user has installed or viewed
        stmt = select(Skill).where(
            and_(
                Skill.status == SkillStatus.PUBLISHED,
                Skill.visibility == SkillVisibility.PUBLIC,
            )
        ).order_by(
            desc(Skill.metrics['ratings_average']),
            desc(Skill.metrics['downloads']),
        ).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_categories(
        self,
        db: AsyncSession | None = None,
    ) -> dict[SkillCategory, int]:
        """Get skill categories with counts"""
        if db is None:
            db = await get_db_session()
        
        stmt = select(
            Skill.category,
            func.count(Skill.id).label('count')
        ).where(
            Skill.status == SkillStatus.PUBLISHED
        ).group_by(Skill.category)
        
        result = await db.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
    
    async def submit_review(
        self,
        skill_id: UUID,
        user_id: UUID,
        rating: int,
        review: str | None = None,
        db: AsyncSession | None = None,
    ) -> SkillReview:
        """Submit a review for a skill"""
        if db is None:
            db = await get_db_session()
        
        # Check if user already reviewed this skill
        stmt = select(SkillReview).where(
            and_(
                SkillReview.skill_id == skill_id,
                SkillReview.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing review
            existing.rating = rating
            existing.content = review
            existing.updated_at = datetime.utcnow()
            review_obj = existing
        else:
            # Create new review
            review_obj = SkillReview(
                skill_id=skill_id,
                user_id=user_id,
                rating=rating,
                content=review,
            )
            db.add(review_obj)
        
        # Update skill metrics
        await self._update_skill_rating(skill_id, db)
        
        await db.commit()
        await db.refresh(review_obj)
        
        return review_obj
    
    async def get_reviews(
        self,
        skill_id: UUID,
        page: int = 1,
        page_size: int = 20,
        db: AsyncSession | None = None,
    ) -> list[SkillReview]:
        """Get reviews for a skill"""
        if db is None:
            db = await get_db_session()
        
        stmt = select(SkillReview).where(
            SkillReview.skill_id == skill_id
        ).order_by(
            desc(SkillReview.created_at)
        ).offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def _update_skill_rating(
        self,
        skill_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Update skill rating metrics based on reviews"""
        stmt = select(
            func.count(SkillReview.id).label('count'),
            func.avg(SkillReview.rating).label('average'),
        ).where(SkillReview.skill_id == skill_id)
        
        result = await db.execute(stmt)
        row = result.one()
        
        # Update skill metrics
        skill = await self.get(skill_id, db)
        if skill:
            skill.metrics.ratings_count = row.count or 0
            skill.metrics.ratings_average = float(row.average or 0)
            skill.updated_at = datetime.utcnow()
