"""JWT 认证模块 - 高性能 Token 处理"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.core.config import settings

# Token 黑名单（内存存储，生产环境应使用 Redis）
_token_blacklist: set[str] = set()
# JWT 配置
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 安全 Scheme
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str  # 用户ID
    exp: datetime
    iat: datetime
    type: str = "access"
    roles: list[str] = []


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    user_id: str,
    roles: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建 JWT 访问令牌

    Args:
        user_id: 用户 ID
        roles: 用户角色列表
        expires_delta: 过期时间增量，默认使用配置值

    Returns:
        JWT 令牌字符串
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": "access",
        "roles": roles or [],
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def blacklist_token(token: str) -> None:
    """将 Token 加入黑名单"""
    _token_blacklist.add(token)


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    解码并验证 JWT 令牌

    Args:
        token: JWT 令牌字符串

    Returns:
        解码后的 TokenPayload，如果无效则返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 检查黑名单
        if token in _token_blacklist:
            return None
        # 验证必要字段
        if "sub" not in payload or "exp" not in payload:
            return None

        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc) if "iat" in payload else datetime.now(timezone.utc),
            type=payload.get("type", "access"),
            roles=payload.get("roles", []),
        )
    except JWTError:
        return None
    except Exception:
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    获取当前用户 ID（FastAPI 依赖）

    Args:
        credentials: HTTP 认证凭证

    Returns:
        用户 ID

    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查过期
    if payload.exp < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload.sub


async def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str | None:
    """
    获取当前用户 ID（可选，不认证时返回 None）

    Args:
        credentials: HTTP 认证凭证

    Returns:
        用户 ID 或 None
    """
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload:
        return None

    # 检查过期
    if payload.exp < datetime.now(timezone.utc):
        return None

    return payload.sub


class RoleChecker:
    """角色权限检查器"""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> str:
        """检查用户角色权限"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证凭证",
            )

        payload = decode_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
            )

        # 检查过期
        if payload.exp < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证令牌已过期",
            )

        # 检查角色
        user_roles = set(payload.roles or [])
        if not any(role in self.allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )

        return payload.sub
