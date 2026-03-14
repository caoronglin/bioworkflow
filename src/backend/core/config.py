"""
核心配置模块 - Python 3.14 优化版本

使用 Pydantic v2 的严格类型验证和性能优化
"""

import os
import secrets
import warnings
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _generate_secret_key_if_dev() -> str:
    """生成或获取JWT密钥

    生产环境：必须从环境变量读取，否则抛出异常
    开发环境：如果未设置，生成临时密钥并发出警告

    Returns:
        JWT密钥字符串

    Raises:
        ValueError: 生产环境未设置SECRET_KEY环境变量
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    secret_key = os.getenv("SECRET_KEY")

    if env == "production":
        if not secret_key:
            raise ValueError(
                "🔴 安全错误: 生产环境必须设置 SECRET_KEY 环境变量！\n"
                "请执行以下操作之一:\n"
                "1. 设置环境变量: export SECRET_KEY=$(openssl rand -hex 32)\n"
                "2. 在 .env 文件中设置: SECRET_KEY=your-secret-key\n"
                "密钥要求: 至少32个字符的随机字符串"
            )
        if len(secret_key) < 32:
            raise ValueError(
                f"🔴 安全错误: SECRET_KEY 长度不足！\n"
                f"当前长度: {len(secret_key)} 字符\n"
                f"要求长度: 至少 32 字符\n"
                f"建议: 使用 64 字符的随机字符串"
            )
        return secret_key
    else:
        # 开发/测试环境
        if secret_key and len(secret_key) >= 32:
            return secret_key

        # 生成临时密钥
        temp_key = secrets.token_hex(32)
        warnings.warn(
            f"⚠️  安全警告: 开发环境使用自动生成的临时JWT密钥！\n"
            f"临时密钥: {temp_key[:8]}...{temp_key[-8:]}\n"
            f"此密钥仅在当前进程有效，重启后会重新生成。\n"
            f"建议: 在 .env 文件中设置固定的 SECRET_KEY 以避免会话失效。",
            RuntimeWarning,
            stacklevel=3,
        )
        return temp_key


class Settings(BaseSettings):
    """
    应用配置

    所有配置项都支持从环境变量读取，使用 Pydantic v2 进行验证
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 忽略未定义的环境变量
    )

    # 应用信息
    VERSION: str = Field(default="0.2.0", description="应用版本")
    APP_NAME: str = Field(default="BioWorkflow", description="应用名称")
    DEBUG: bool = Field(default=False, description="调试模式")
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = Field(
        default="development",
        description="运行环境",
    )

    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="监听地址")
    PORT: int = Field(default=8000, ge=1, le=65535, description="服务端口")
    WORKERS: int = Field(default=1, ge=1, description="工作进程数")

    # CORS 配置
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="允许的 CORS 来源",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="允许 CORS 凭证")
    CORS_ALLOW_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="允许的 HTTP 方法",
    )
    CORS_ALLOW_HEADERS: list[str] = Field(
        default=["*"],
        description="允许的 HTTP 头",
    )

    # 数据库配置
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./bioworkflow.db",
        description="数据库连接 URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, description="连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, ge=0, description="连接池溢出")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=0, description="连接回收时间")
    DATABASE_ECHO: bool = Field(default=False, description="SQL 语句回显")

    # Redis 配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接 URL",
    )
    REDIS_POOL_SIZE: int = Field(default=50, ge=1, description="Redis 连接池大小")

    # JWT 配置
    SECRET_KEY: str = Field(
        default_factory=_generate_secret_key_if_dev,
        min_length=32,
        description="JWT 密钥（生产环境必须通过环境变量设置）",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        description="访问令牌过期时间（分钟）",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        description="刷新令牌过期时间（天）",
    )

    # Snakemake 配置
    SNAKEMAKE_WORKDIR: str = Field(
        default="./workflows",
        description="Snakemake 工作目录",
    )
    SNAKEMAKE_CONDA_PREFIX: str = Field(
        default="./conda_envs",
        description="Conda 环境前缀",
    )
    SNAKEMAKE_MAX_CORES: int = Field(default=4, ge=1, description="最大 CPU 核心数")
    SNAKEMAKE_MAX_MEMORY_GB: float = Field(
        default=8.0,
        ge=0.1,
        description="最大内存（GB）",
    )

    # Conda 配置
    CONDA_CHANNELS: list[str] = Field(
        default=["conda-forge", "bioconda", "defaults"],
        description="Conda 频道",
    )
    CONDA_TIMEOUT: int = Field(default=600, ge=1, description="Conda 命令超时")

    # Elasticsearch 配置
    ELASTICSEARCH_HOST: str = Field(default="localhost", description="ES 主机")
    ELASTICSEARCH_PORT: int = Field(
        default=9200,
        ge=1,
        le=65535,
        description="ES 端口",
    )
    ELASTICSEARCH_INDEX_PREFIX: str = Field(
        default="bioworkflow",
        description="ES 索引前缀",
    )

    # 知识库配置
    KNOWLEDGE_BASE_DIR: str = Field(
        default="./knowledge_base",
        description="知识库目录",
    )

    # AI / AgentScope 配置
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key")
    OPENAI_BASE_URL: str | None = Field(default=None, description="OpenAI-compatible API base URL")
    AGENTSCOPE_EVAL_ENABLED: bool = Field(default=False, description="是否启用 AgentScope 评测")
    AGENTSCOPE_EVAL_RESULTS_DIR: str = Field(
        default="./artifacts/agentscope-eval",
        description="AgentScope 评测结果目录",
    )

    # 日志配置
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别",
    )
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="text",
        description="日志格式",
    )
    LOG_FILE: str | None = Field(default=None, description="日志文件路径")
    LOG_ROTATION: str = Field(default="1 day", description="日志轮转")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留")

    # 性能配置
    ENABLE_METRICS: bool = Field(default=True, description="启用指标收集")
    ENABLE_CACHE: bool = Field(default=True, description="启用缓存")
    CACHE_DEFAULT_TTL: int = Field(default=3600, ge=0, description="默认缓存 TTL")

    # 安全配置
    ENABLE_RATE_LIMIT: bool = Field(default=True, description="启用速率限制")
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1, description="速率限制请求数")
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1, description="速率限制窗口（秒）")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """解析 CORS 来源，支持逗号分隔的字符串"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("CONDA_CHANNELS", mode="before")
    @classmethod
    def parse_conda_channels(cls, v: str | list[str]) -> list[str]:
        """解析 Conda 频道，支持逗号分隔的字符串"""
        if isinstance(v, str):
            return [channel.strip() for channel in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"

    @property
    def database_async_url(self) -> str:
        """获取异步数据库 URL"""
        if self.DATABASE_URL.startswith("sqlite:///"):
            return self.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）

    使用 lru_cache 确保配置只加载一次
    """
    return Settings()


# 全局配置实例
settings = get_settings()
