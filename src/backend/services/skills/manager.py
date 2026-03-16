"""
Skills Manager Service

Manages the lifecycle of skills including installation,
configuration, updates, and uninstallation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
from backend.models.skill import (
    Skill,
    SkillCategory,
    SkillStatus,
    SkillVisibility,
)

logger = logging.getLogger(__name__)


class InstanceStatus(str, Enum):
    """Skill instance status"""
    PENDING = "pending"
    INSTALLING = "installing"
    ACTIVE = "active"
    UPDATING = "updating"
    ERROR = "error"
    DISABLED = "disabled"
    UNINSTALLING = "uninstalling"


@dataclass
class SkillInstance:
    """Installed skill instance"""
    id: UUID = field(default_factory=uuid4)
    skill_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    version: str = "0.0.1"
    status: InstanceStatus = InstanceStatus.PENDING
    configuration: dict[str, Any] = field(default_factory=dict)
    auto_update: bool = True
    installed_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = None
    error_message: str | None = None
    
    # Relationships (populated on load)
    skill: Skill | None = None


class SkillsManager:
    """Manager for skill lifecycle operations"""
    
    _instance: SkillsManager | None = None
    _instances: dict[UUID, SkillInstance] = {}
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    async def get_instance(cls) -> SkillsManager:
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def install(
        self,
        skill_id: UUID,
        user_id: UUID,
        version: str | None = None,
        auto_update: bool = True,
        configuration: dict[str, Any] | None = None,
        db: AsyncSession | None = None,
    ) -> SkillInstance:
        """
        Install a skill.
        
        Args:
            skill_id: The skill to install
            user_id: The user installing
            version: Specific version or latest
            auto_update: Enable auto-updates
            configuration: Initial configuration
            db: Optional database session
            
        Returns:
            The installed skill instance
        """
        if db is None:
            db = await get_db_session()
        
        try:
            # Check if already installed
            existing = await self._get_instance(skill_id, user_id, db)
            if existing:
                raise ValueError(f"Skill {skill_id} is already installed")
            
            # Get skill details
            from backend.services.skills.registry import SkillsRegistry
            registry = await SkillsRegistry.get_instance()
            skill = await registry.get(skill_id, db)
            
            if not skill:
                raise ValueError(f"Skill {skill_id} not found")
            
            # Determine version
            install_version = version or skill.version
            
            # Create instance
            instance = SkillInstance(
                skill_id=skill_id,
                user_id=user_id,
                version=install_version,
                status=InstanceStatus.INSTALLING,
                configuration=configuration or {},
                auto_update=auto_update,
            )
            instance.skill = skill
            
            # Store in memory
            self._instances[instance.id] = instance
            
            # Perform installation steps
            await self._perform_installation(instance, db)
            
            # Save to database
            await self._save_instance(instance, db)
            
            instance.status = InstanceStatus.ACTIVE
            instance.updated_at = datetime.utcnow()
            
            self.logger.info(f"Installed skill: {skill.name} (instance: {instance.id})")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to install skill: {e}")
            raise
    
    async def uninstall(
        self,
        instance_id: UUID,
        user_id: UUID,
        remove_data: bool = False,
        force: bool = False,
        db: AsyncSession | None = None,
    ) -> None:
        """
        Uninstall a skill instance.
        
        Args:
            instance_id: The instance to uninstall
            user_id: The user performing the uninstall
            remove_data: Whether to remove associated data
            force: Force uninstall even if dependencies exist
            db: Optional database session
        """
        if db is None:
            db = await get_db_session()
        
        try:
            # Get instance
            instance = self._instances.get(instance_id)
            if not instance:
                raise ValueError(f"Instance {instance_id} not found")
            
            # Verify ownership
            if instance.user_id != user_id:
                raise PermissionError("You don't own this skill instance")
            
            # Update status
            instance.status = InstanceStatus.UNINSTALLING
            
            # Perform uninstallation steps
            await self._perform_uninstallation(instance, remove_data, db)
            
            # Remove from memory
            del self._instances[instance_id]
            
            # Remove from database
            await self._delete_instance(instance_id, db)
            
            self.logger.info(f"Uninstalled skill instance: {instance_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall skill: {e}")
            raise
    
    async def list_installed(
        self,
        user_id: UUID,
        status: Literal['active', 'inactive', 'all'] = 'active',
        category: SkillCategory | None = None,
        db: AsyncSession | None = None,
    ) -> list[SkillInstance]:
        """
        List installed skill instances for a user.
        
        Args:
            user_id: The user ID
            status: Filter by status
            category: Filter by category
            db: Optional database session
            
        Returns:
            List of skill instances
        """
        if db is None:
            db = await get_db_session()
        
        # Filter instances in memory
        instances = [
            inst for inst in self._instances.values()
            if inst.user_id == user_id
        ]
        
        if status == 'active':
            instances = [inst for inst in instances if inst.status == InstanceStatus.ACTIVE]
        elif status == 'inactive':
            instances = [inst for inst in instances if inst.status != InstanceStatus.ACTIVE]
        
        if category:
            # Need to load skill relationship
            instances = [
                inst for inst in instances
                if inst.skill and inst.skill.category == category
            ]
        
        return instances
    
    async def configure(
        self,
        instance_id: UUID,
        user_id: UUID,
        configuration: dict[str, Any],
        validate: bool = True,
        db: AsyncSession | None = None,
    ) -> SkillInstance:
        """
        Configure a skill instance.
        
        Args:
            instance_id: The instance ID
            user_id: The user ID
            configuration: New configuration
            validate: Whether to validate the configuration
            db: Optional database session
            
        Returns:
            The updated instance
        """
        if db is None:
            db = await get_db_session()
        
        # Get instance
        instance = self._instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        if instance.user_id != user_id:
            raise PermissionError("You don't own this skill instance")
        
        # Validate configuration if requested
        if validate and instance.skill:
            await self._validate_configuration(instance.skill, configuration)
        
        # Apply configuration
        instance.configuration.update(configuration)
        instance.updated_at = datetime.utcnow()
        
        # Save to database
        await self._save_instance(instance, db)
        
        self.logger.info(f"Configured skill instance: {instance_id}")
        return instance
    
    # Private helper methods
    
    async def _get_instance(
        self,
        skill_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> SkillInstance | None:
        """Get an existing instance"""
        for instance in self._instances.values():
            if instance.skill_id == skill_id and instance.user_id == user_id:
                return instance
        return None
    
    async def _perform_installation(
        self,
        instance: SkillInstance,
        db: AsyncSession,
    ) -> None:
        """Perform the actual installation steps"""
        # In a real implementation, this would:
        # 1. Download the skill package
        # 2. Verify checksums/signatures
        # 3. Extract to installation directory
        # 4. Run installation hooks
        # 5. Set up configuration
        
        self.logger.info(f"Installing skill: {instance.skill_id}")
        
        # Simulate installation delay
        import asyncio
        await asyncio.sleep(0.1)
        
        instance.status = InstanceStatus.ACTIVE
    
    async def _perform_uninstallation(
        self,
        instance: SkillInstance,
        remove_data: bool,
        db: AsyncSession,
    ) -> None:
        """Perform the actual uninstallation steps"""
        # In a real implementation, this would:
        # 1. Run pre-uninstallation hooks
        # 2. Stop any running processes
        # 3. Remove files
        # 4. Clean up data if requested
        # 5. Run post-uninstallation hooks
        
        self.logger.info(f"Uninstalling skill instance: {instance.id}")
        
        # Simulate uninstallation delay
        import asyncio
        await asyncio.sleep(0.1)
    
    async def _save_instance(
        self,
        instance: SkillInstance,
        db: AsyncSession,
    ) -> None:
        """Save instance to database"""
        # In a real implementation, this would persist to database
        pass
    
    async def _delete_instance(
        self,
        instance_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Delete instance from database"""
        # In a real implementation, this would remove from database
        pass
    
    async def _validate_configuration(
        self,
        skill: Skill,
        configuration: dict[str, Any],
    ) -> None:
        """Validate configuration against skill schema"""
        # In a real implementation, this would validate against JSON schema
        pass
