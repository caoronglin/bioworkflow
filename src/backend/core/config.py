"""核心配置模块"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    VERSION: str = "0.0.1a1"
    APP_NAME: str = "BioWorkflow"
    DEBUG: bool = False

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./bioworkflow.db"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Snakemake 配置
    SNAKEMAKE_WORKDIR: str = "./workflows"
    SNAKEMAKE_CONDA_PREFIX: str = "./conda_envs"

    # Conda 配置
    CONDA_CHANNELS: List[str] = [
        "conda-forge",
        "bioconda",
        "defaults",
    ]

    # 知识库配置
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    KNOWLEDGE_BASE_DIR: str = "./knowledge_base"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()
