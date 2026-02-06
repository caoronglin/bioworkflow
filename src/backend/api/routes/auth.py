"""认证路由 - 用户登录、注册、Token 管理"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import create_access_token, decode_token
from backend.core.database import get_db
from backend.models.user import User

router = APIRouter()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic 模型
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        if len(v) < 3:
            raise ValueError('用户名至少3个字符')
        return v

    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少6个字符')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    last_login: Optional[str] = None
    created_at: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


# 辅助函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


@router.post("/register", response_model=MessageResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册

    - **username**: 用户名（3-50个字符，只能包含字母和数字）
    - **email**: 邮箱地址
    - **password**: 密码（至少6个字符）
    - **full_name**: 全名（可选）
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 检查邮箱是否已存在
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在",
        )

    # 创建新用户
    user = User(
        id=str(uuid4()),
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return MessageResponse(message="注册成功")


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回 JWT Token 用于后续请求认证
    """
    # 查找用户
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证密码
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已禁用",
        )

    # 更新最后登录时间
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    # 创建 JWT Token
    token = create_access_token(
        user_id=user.id,
        roles=["user"] if not user.is_superuser else ["user", "admin"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=30 * 60,  # 30分钟
    )


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """
    用户登出

    注意：JWT Token 是无状态的，登出需要在客户端删除 Token。
    服务端可以维护一个 Token 黑名单（可选实现）。
    """
    # TODO: 如果需要，可以将 Token 加入黑名单
    return MessageResponse(message="登出成功")


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前登录用户信息

    需要认证：Bearer Token
    """
    from fastapi import Depends as FastApiDepends
    from backend.auth.jwt import get_current_user_id

    user_id = await get_current_user_id(FastApiDepends())

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login=user.last_login.isoformat() if user.last_login else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    db: AsyncSession = Depends(get_db),
):
    """
    刷新访问令牌

    需要认证：Bearer Token（即将过期但未过期）
    返回新的 JWT Token
    """
    from fastapi import Depends as FastApiDepends
    from backend.auth.jwt import get_current_user_id

    user_id = await get_current_user_id(FastApiDepends())

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已禁用",
        )

    # 创建新的 Token
    token = create_access_token(
        user_id=user.id,
        roles=["user"] if not user.is_superuser else ["user", "admin"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=30 * 60,
    )
