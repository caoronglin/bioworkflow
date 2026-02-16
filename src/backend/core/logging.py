"""
日志配置 - Python 3.14 优化版本

使用 Loguru 进行高性能日志记录
"""

import sys
from typing import Any

from loguru import logger

from backend.core.config import settings


def setup_logging() -> None:
    """配置日志系统"""

    # 移除默认处理器
    logger.remove()

    # 日志格式
    if settings.LOG_FORMAT == "json":
        # JSON 格式（用于生产环境）
        fmt = (
            "{{"
            '"timestamp": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>", '
            '"level": "<level>{level}</level>", '
            '"message": "{message}", '
            '"file": "{file}", '
            '"line": {line}, '
            '"function": "{function}"'
            "}}"
        )
    else:
        # 文本格式（用于开发环境）
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 控制台处理器
    logger.add(
        sys.stdout,
        format=fmt,
        level=settings.LOG_LEVEL,
        colorize=True,
        enqueue=True,  # 异步处理
    )

    # 文件处理器
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            format=fmt,
            level=settings.LOG_LEVEL,
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="zip",
            enqueue=True,
        )

    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}")


class StructuredLogger:
    """
    结构化日志记录器

    支持上下文信息和结构化数据
    """

    def __init__(self, name: str):
        self._name = name
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "StructuredLogger":
        """绑定上下文信息"""
        new_logger = StructuredLogger(self._name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _log(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """内部日志方法"""
        extra = {**self._context, **kwargs}
        logger.bind(**extra).log(level, f"[{self._name}] {message}")

    def debug(self, message: str, **kwargs: Any) -> None:
        """调试日志"""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """信息日志"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """警告日志"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """错误日志"""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """严重错误日志"""
        self._log("CRITICAL", message, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)
