"""日志配置模块"""

import sys
from loguru import logger


def setup_logging():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )

    # 添加文件处理器
    logger.add(
        "logs/bioworkflow.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="INFO",
        rotation="500 MB",
        retention="10 days",
    )

    return logger
