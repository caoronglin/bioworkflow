"""auth 包 - 认证与授权系统

提供 JWT Token 认证、权限检查和用户会话管理
支持高性能异步 Token 验证和刷新机制
"""

from .jwt import (
    TokenPayload,
    TokenResponse,
    create_access_token,
    decode_token,
    get_current_user_id,
    get_optional_user_id,
    RoleChecker,
)

__all__ = [
    "TokenPayload",
    "TokenResponse",
    "create_access_token",
    "decode_token",
    "get_current_user_id",
    "get_optional_user_id",
    "RoleChecker",
]
