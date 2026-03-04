"""
速率限制中间件 - 基于Redis的分布式速率限制

提供多维度速率限制：
1. 全局限制：所有请求的统一限制
2. 路由限制：特定路径的单独限制
3. 用户限制：基于用户ID的限制
4. IP限制：基于客户端IP的限制
"""

import time
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from redis.asyncio import Redis
from jose import jwt as jose_jwt, JWTError

from backend.core.logging import get_logger
from backend.core.config import settings
logger = get_logger("rate_limiter")


class RateLimitStrategy(str, Enum):
    """速率限制策略"""
    FIXED_WINDOW = "fixed_window"  # 固定窗口
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口
    TOKEN_BUCKET = "token_bucket"  # 令牌桶


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    requests: int = 100  # 请求次数
    window: int = 60  # 时间窗口（秒）
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    key_prefix: str = "ratelimit"  # Redis键前缀
    block_duration: int = 300  # 触发限制后的封禁时长（秒）


# 预定义的路由限制配置
ROUTE_LIMITS = {
    # 认证相关 - 更严格的限制
    "/api/auth/login": RateLimitConfig(
        requests=5,
        window=60,
        strategy=RateLimitStrategy.FIXED_WINDOW,
        block_duration=600  # 10分钟
    ),
    "/api/auth/register": RateLimitConfig(
        requests=3,
        window=3600,  # 1小时
        strategy=RateLimitStrategy.FIXED_WINDOW,
        block_duration=3600
    ),
    "/api/auth/refresh": RateLimitConfig(
        requests=10,
        window=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ),

    # 敏感操作 - 中等限制
    "/api/pipelines/": RateLimitConfig(
        requests=20,
        window=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    "/api/conda/": RateLimitConfig(
        requests=15,
        window=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ),

    # 默认配置
    "default": RateLimitConfig(
        requests=100,
        window=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
}


class RateLimiter:
    """
    速率限制器 - 基于Redis的实现

    支持策略：
    1. 滑动窗口(Sliding Window): 最精确，推荐用于生产
    2. 固定窗口(Fixed Window): 简单，适合严格限制场景
    3. 令牌桶(Token Bucket): 支持突发流量，适合API接口
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
        self._local_cache = {}  # 降级时的本地缓存

    async def is_allowed(
        self,
        key: str,
        config: RateLimitConfig,
        redis: Optional[Redis] = None
    ) -> tuple[bool, dict]:
        """
        检查是否允许请求

        Args:
            key: 限制键（如 IP:path 或 user_id:path）
            config: 速率限制配置
            redis: Redis客户端

        Returns:
            (是否允许, 响应头信息)
        """
        redis_client = redis or self.redis

        if not redis_client:
            # 降级到本地模式（仅单实例有效）
            return await self._check_local(key, config)

        # 根据策略执行不同的限制逻辑
        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_check(key, config, redis_client)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window_check(key, config, redis_client)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_check(key, config, redis_client)
        else:
            # 默认使用滑动窗口
            return await self._sliding_window_check(key, config, redis_client)

    async def _sliding_window_check(
        self,
        key: str,
        config: RateLimitConfig,
        redis: Redis
    ) -> tuple[bool, dict]:
        """滑动窗口算法 - 最精确"""
        now = time.time()
        window_start = now - config.window

        pipe = redis.pipeline()

        # 清理过期请求
        pipe.zremrangebyscore(f"{config.key_prefix}:{key}", 0, window_start)

        # 获取当前窗口内的请求数
        pipe.zcard(f"{config.key_prefix}:{key}")

        # 记录当前请求
        pipe.zadd(f"{config.key_prefix}:{key}", {str(now): now})

        # 设置过期时间
        pipe.expire(f"{config.key_prefix}:{key}", config.window + 1)

        results = await pipe.execute()
        current_count = results[1]  # zcard 的结果

        allowed = current_count < config.requests
        remaining = max(0, config.requests - current_count - 1)
        reset_time = int(now + config.window)

        # 如果触发限制，添加到封禁列表
        if not allowed and config.block_duration > 0:
            await redis.setex(
                f"{config.key_prefix}:block:{key}",
                config.block_duration,
                "1"
            )

        return allowed, {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Window": str(config.window),
        }

    async def _fixed_window_check(
        self,
        key: str,
        config: RateLimitConfig,
        redis: Redis
    ) -> tuple[bool, dict]:
        """固定窗口算法 - 简单但可能有突发流量"""
        now = int(time.time())
        window_key = now // config.window
        key = f"{config.key_prefix}:{key}:{window_key}"

        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, config.window * 2)  # 保留2个窗口时间
        results = await pipe.execute()

        current_count = results[0]
        allowed = current_count <= config.requests
        remaining = max(0, config.requests - current_count)
        reset_time = (window_key + 1) * config.window

        return allowed, {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

    async def _token_bucket_check(
        self,
        key: str,
        config: RateLimitConfig,
        redis: Redis
    ) -> tuple[bool, dict]:
        """令牌桶算法 - 支持突发流量"""
        key = f"{config.key_prefix}:bucket:{key}"
        now = time.time()

        pipe = redis.pipeline()

        # 获取当前桶状态
        pipe.hmget(key, ["tokens", "last_update"])
        pipe.exists(key)
        results = await pipe.execute()

        tokens_data = results[0]
        key_exists = results[1]

        if not key_exists:
            # 初始化桶
            tokens = config.requests - 1  # 当前请求消耗1个令牌
            await redis.hmset(key, {
                "tokens": tokens,
                "last_update": now
            })
            await redis.expire(key, config.window)
            return True, {
                "X-RateLimit-Limit": str(config.requests),
                "X-RateLimit-Remaining": str(tokens),
            }

        # 计算令牌添加
        current_tokens = float(tokens_data[0] or 0)
        last_update = float(tokens_data[1] or now)
        time_passed = now - last_update
        tokens_to_add = (time_passed / config.window) * config.requests

        new_tokens = min(current_tokens + tokens_to_add, config.requests)

        if new_tokens >= 1:
            # 允许请求，消耗令牌
            new_tokens -= 1
            await redis.hmset(key, {
                "tokens": new_tokens,
                "last_update": now
            })
            return True, {
                "X-RateLimit-Limit": str(config.requests),
                "X-RateLimit-Remaining": str(int(new_tokens)),
            }
        else:
            # 拒绝请求
            return False, {
                "X-RateLimit-Limit": str(config.requests),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(int(config.window)),
            }

    async def _check_local(
        self,
        key: str,
        config: RateLimitConfig
    ) -> tuple[bool, dict]:
        """本地模式检查（无Redis时的降级方案）"""
        now = time.time()
        window_start = now - config.window

        if key not in self._local_cache:
            self._local_cache[key] = []

        # 清理过期请求
        self._local_cache[key] = [
            ts for ts in self._local_cache[key] if ts > window_start
        ]

        current_count = len(self._local_cache[key])
        allowed = current_count < config.requests

        if allowed:
            self._local_cache[key].append(now)

        remaining = max(0, config.requests - current_count - 1)

        return allowed, {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Window": str(config.window),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    为API请求提供多维度速率限制保护
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_client: Optional[Redis] = None,
        default_config: Optional[RateLimitConfig] = None,
        whitelist: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.redis = redis_client
        self.default_config = default_config or ROUTE_LIMITS["default"]
        self.whitelist = set(whitelist or [])
        self.limiter = RateLimiter(redis_client)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否在白名单中
        client_ip = self._get_client_ip(request)
        if client_ip in self.whitelist:
            return await call_next(request)

        # 从 app.state 获取 Redis 客户端（lifespan 中注入）
        redis_client = self.redis or getattr(request.app.state, "redis_client", None)

        # 确定使用的配置
        config = self._get_config_for_path(request.url.path)

        # 构建限制键
        key = self._build_limit_key(request, config)

        # 检查是否被封禁
        if redis_client:
            is_blocked = await redis_client.exists(
                f"{config.key_prefix}:block:{key}"
            )
            if is_blocked:
                return self._create_blocked_response(config)

        # 执行速率限制检查
        allowed, headers = await self.limiter.is_allowed(key, config, redis_client)

        if not allowed:
            return self._create_rate_limit_response(headers)

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制响应头
        for header, value in headers.items():
            response.headers[header] = value

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 优先从X-Forwarded-For获取（代理场景）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 其次从X-Real-IP获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 最后使用直接连接的客户端IP
        return request.client.host if request.client else "unknown"

    def _get_config_for_path(self, path: str) -> RateLimitConfig:
        """根据路径获取对应的限制配置"""
        # 精确匹配
        if path in ROUTE_LIMITS:
            return ROUTE_LIMITS[path]

        # 前缀匹配
        for route_prefix, config in ROUTE_LIMITS.items():
            if route_prefix != "default" and path.startswith(route_prefix):
                return config

        # 使用默认配置
        return ROUTE_LIMITS["default"]

    def _build_limit_key(self, request: Request, config: RateLimitConfig) -> str:
        """
        构建速率限制键

        组合多个维度：
        - 客户端IP
        - 用户ID（从JWT Authorization header提取）
        - 请求路径
        """
        client_ip = self._get_client_ip(request)

        # 从 Authorization header 提取用户ID
        user_id = self._extract_user_id_from_jwt(request)

        if user_id:
            # 已认证用户：使用用户ID作为限制键
            return f"user:{user_id}:{request.url.path}"
        else:
            # 未认证用户：使用IP作为限制键
            return f"ip:{client_ip}:{request.url.path}"

    @staticmethod
    def _extract_user_id_from_jwt(request: Request) -> str | None:
        """
        从 Authorization header 中提取用户ID

        直接解码JWT而不依赖 request.state（中间件在路由处理前执行）
        """
        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header[7:]  # 去掉 'Bearer ' 前缀
        try:
            payload = jose_jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            return payload.get("sub")
        except JWTError:
            return None
        except Exception:
            return None

    def _create_rate_limit_response(self, headers: dict) -> JSONResponse:
        """创建速率限制响应"""
        retry_after = headers.get("Retry-After", "60")

        return JSONResponse(
            status_code=429,
            content={
                "detail": "请求过于频繁，请稍后再试",
                "code": "rate_limit_exceeded",
                "retry_after": int(retry_after),
            },
            headers={
                **headers,
                "Retry-After": retry_after,
            }
        )

    def _create_blocked_response(self, config: RateLimitConfig) -> JSONResponse:
        """创建封禁响应"""
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"请求被临时封禁，请 {config.block_duration} 秒后重试",
                "code": "rate_limit_blocked",
                "block_duration": config.block_duration,
            },
            headers={
                "Retry-After": str(config.block_duration),
            }
        )


class RateLimitExceeded(Exception):
    """速率限制异常"""
    pass
