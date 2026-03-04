"""
性能监控中间件

跟踪请求处理时间和资源使用
"""

import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.logging import get_logger
from backend.core.performance import performance_monitor
from backend.core.container import get_metrics_collector

logger = get_logger("performance")


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件

    记录请求处理时间、状态码等指标
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0,
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            status_code = response.status_code

            # 计算处理时间
            process_time = time.perf_counter() - start_time

            # 记录指标
            await performance_monitor.record("request_duration", process_time)

            # 记录到 Prometheus
            try:
                metrics = get_metrics_collector()
                metrics.record_histogram(
                    "http_request_duration_seconds",
                    process_time,
                    {"path": path, "method": method, "status": str(status_code)},
                )
                metrics.record_counter(
                    "http_requests_total",
                    1,
                    {"path": path, "method": method, "status": str(status_code)},
                )
            except Exception:
                pass  # 忽略指标记录错误

            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)

            # 记录慢请求
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {method} {path} took {process_time:.3f}s",
                    method=method,
                    path=path,
                    duration=process_time,
                    status_code=status_code,
                )

            return response

        except Exception as exc:
            process_time = time.perf_counter() - start_time
            logger.error(
                f"Request failed: {method} {path} after {process_time:.3f}s",
                method=method,
                path=path,
                duration=process_time,
                error=str(exc),
            )
            raise


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    缓存控制中间件

    为静态资源和 API 响应添加缓存头
    """

    def __init__(
        self,
        app: ASGIApp,
        static_max_age: int = 86400,  # 1天
        api_max_age: int = 0,  # 不缓存
    ):
        super().__init__(app)
        self.static_max_age = static_max_age
        self.api_max_age = api_max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        path = request.url.path

        # 静态资源
        if path.startswith("/static/") or "/assets/" in path:
            response.headers["Cache-Control"] = f"public, max-age={self.static_max_age}"
            response.headers["Expires"] = str(self.static_max_age)

        # API 响应
        elif path.startswith("/api/"):
            if self.api_max_age > 0:
                response.headers["Cache-Control"] = f"public, max-age={self.api_max_age}"
            else:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response


# CompressionMiddleware 已移除 —— 使用 FastAPI 内置的 GZipMiddleware 替代
# 原始实现将整个响应体加载到内存中，存在内存风险

class DatabaseQueryOptimizer:
    """
    数据库查询优化器

    提供查询优化建议和 N+1 检测
    """

    def __init__(self):
        self._query_count = 0
        self._query_times: list[float] = []

    def log_query(self, query: str, duration: float) -> None:
        """记录查询"""
        self._query_count += 1
        self._query_times.append(duration)

        # 检测慢查询
        if duration > 0.5:  # 500ms
            logger.warning(f"Slow query detected ({duration:.3f}s): {query[:200]}")

    def get_stats(self) -> dict[str, Any]:
        """获取查询统计"""
        if not self._query_times:
            return {"count": 0, "avg_time": 0, "max_time": 0}

        return {
            "count": self._query_count,
            "avg_time": sum(self._query_times) / len(self._query_times),
            "max_time": max(self._query_times),
            "total_time": sum(self._query_times),
        }

    def reset(self) -> None:
        """重置统计"""
        self._query_count = 0
        self._query_times.clear()


# 全局查询优化器实例
query_optimizer = DatabaseQueryOptimizer()
