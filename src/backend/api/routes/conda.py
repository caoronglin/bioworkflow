"""Conda 包管理路由"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.services.conda import (
    CondaEnvironment as CondaEnvModel,
    CondaPackage as CondaPkgModel,
    get_conda_manager,
    get_channel_manager,
)

router = APIRouter()


class CondaEnvironment(BaseModel):
    name: str
    path: str
    is_active: bool = False
    python_version: Optional[str] = None
    packages_count: int = 0


class CondaPackage(BaseModel):
    name: str
    version: str
    channel: str
    description: Optional[str] = None
    installed: bool


class ChannelConfig(BaseModel):
    channels: List[str]


@router.get("/envs", response_model=List[CondaEnvironment])
async def list_conda_environments():
    """
    列出系统中所有的 Conda 环境
    """
    manager = get_conda_manager()
    envs = await manager.list_environments()
    return [
        CondaEnvironment(
            name=e.name,
            path=e.path,
            is_active=e.is_active,
            packages_count=len(e.packages) if e.packages else 0,
        )
        for e in envs
    ]


@router.post("/envs")
async def create_conda_environment(
    name: str,
    packages: Optional[List[str]] = None,
):
    """
    创建新的 Conda 环境
    
    - **name**: 环境名称
    - **packages**: 要安装的包列表
    """
    manager = get_conda_manager()
    env = await manager.create_environment(name=name, packages=packages or [])
    return {"message": f"已创建环境: {name}", "environment": env.name}


@router.delete("/envs/{env_name}")
async def delete_conda_environment(env_name: str):
    """删除 Conda 环境"""
    manager = get_conda_manager()
    await manager.remove_environment(env_name)
    return {"message": f"环境 {env_name} 已删除"}


@router.get("/envs/{env_name}/packages", response_model=List[CondaPackage])
async def list_environment_packages(env_name: str):
    """列出特定环境中已安装的包"""
    manager = get_conda_manager()
    packages = await manager.list_packages(env_name)
    return [
        CondaPackage(
            name=p.name,
            version=p.version,
            channel=p.channel,
            installed=True,
        )
        for p in packages
    ]


@router.get("/packages", response_model=List[CondaPackage])
async def search_packages(
    query: str,
    channel: Optional[str] = "bioconda",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    搜索 Conda 包
    
    - **query**: 搜索关键词
    - **channel**: 搜索的频道
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    manager = get_conda_manager()
    results = await manager.search_packages(query=query, channel=channel, limit=limit + skip)
    sliced = results[skip : skip + limit]
    return [
        CondaPackage(
            name=p.name,
            version=p.version,
            channel=p.channel,
            installed=False,
        )
        for p in sliced
    ]


@router.post("/packages/install")
async def install_package(
    package_name: str,
    version: Optional[str] = None,
    environment: Optional[str] = "base",
):
    """
    安装 Conda 包
    
    - **package_name**: 包名称
    - **version**: 包版本（可选）
    - **environment**: 目标环境
    """
    manager = get_conda_manager()
    pkg_spec = f"{package_name}={version}" if version else package_name
    await manager.install_packages(env_name=environment, packages=[pkg_spec])
    return {
        "message": f"正在安装包: {pkg_spec}",
        "package": package_name,
        "environment": environment,
    }


@router.post("/packages/uninstall")
async def uninstall_package(
    package_name: str,
    environment: Optional[str] = "base",
):
    """卸载 Conda 包"""
    manager = get_conda_manager()
    await manager.remove_packages(env_name=environment, packages=[package_name])
    return {
        "message": f"已卸载包: {package_name}",
        "package": package_name,
        "environment": environment,
    }


@router.get("/channels")
async def get_conda_channels():
    """获取当前配置的 Conda 频道"""
    cm = get_channel_manager()
    return {"channels": cm.get_channels(), "available_mirrors": cm.get_available_mirrors()}


@router.post("/channels")
async def configure_channels(config: ChannelConfig):
    """
    配置 Conda 频道
    
    支持在 Web 界面中切换频道源
    """
    cm = get_channel_manager()
    cm.save_config({"channels": config.channels, "show_channel_urls": True})
    return {"message": "频道已更新", "channels": config.channels}


@router.get("/config")
async def get_conda_config():
    """获取完整的 Conda 配置信息"""
    cm = get_channel_manager()
    channels = cm.get_channels()
    manager = get_conda_manager()
    try:
        manager._ensure_ready()
        version_info = subprocess.run(
            [manager.conda_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = version_info.stdout.strip()
    except Exception:
        version = "unknown"

    return {
        "conda_root": manager.conda_path,
        "version": version,
        "channels": channels,
    }
