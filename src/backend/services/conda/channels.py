"""
Conda Channel 管理
支持换源配置和多 channel 管理
"""

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger


@dataclass
class ChannelConfig:
    """Channel 配置"""
    name: str
    url: str
    priority: int = 0


# 预定义的镜像源
MIRROR_SOURCES = {
    "tsinghua": {
        "name": "清华大学镜像",
        "channels": [
            "https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main",
            "https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free",
            "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge",
            "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda",
        ],
        "show_channel_urls": True,
    },
    "ustc": {
        "name": "中科大镜像",
        "channels": [
            "https://mirrors.ustc.edu.cn/anaconda/pkgs/main",
            "https://mirrors.ustc.edu.cn/anaconda/pkgs/free",
            "https://mirrors.ustc.edu.cn/anaconda/cloud/conda-forge",
            "https://mirrors.ustc.edu.cn/anaconda/cloud/bioconda",
        ],
        "show_channel_urls": True,
    },
    "aliyun": {
        "name": "阿里云镜像",
        "channels": [
            "https://mirrors.aliyun.com/anaconda/pkgs/main",
            "https://mirrors.aliyun.com/anaconda/pkgs/free",
            "https://mirrors.aliyun.com/anaconda/cloud/conda-forge",
            "https://mirrors.aliyun.com/anaconda/cloud/bioconda",
        ],
        "show_channel_urls": True,
    },
    "default": {
        "name": "官方源",
        "channels": [
            "defaults",
            "conda-forge",
            "bioconda",
        ],
        "show_channel_urls": True,
    },
}


class ChannelManager:
    """Conda Channel 管理器"""

    def __init__(self, condarc_path: Optional[Path] = None):
        """
        初始化 Channel 管理器
        
        Args:
            condarc_path: .condarc 文件路径，默认为用户目录
        """
        self.condarc_path = condarc_path or Path.home() / ".condarc"

    def get_current_config(self) -> dict:
        """获取当前 .condarc 配置"""
        if not self.condarc_path.exists():
            return {}
        
        try:
            with open(self.condarc_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"读取 .condarc 失败: {e}")
            return {}

    def get_channels(self) -> list[str]:
        """获取当前配置的 channels"""
        config = self.get_current_config()
        return config.get("channels", ["defaults"])

    def save_config(self, config: dict) -> None:
        """保存配置到 .condarc"""
        # 备份原有配置
        if self.condarc_path.exists():
            backup_path = self.condarc_path.parent / f"{self.condarc_path.name}.bak"
            import shutil
            shutil.copy2(self.condarc_path, backup_path)
            logger.info(f"已备份原配置到: {backup_path}")
        
        with open(self.condarc_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"配置已保存到: {self.condarc_path}")

    def set_mirror(self, mirror_name: str) -> dict:
        """
        设置镜像源
        
        Args:
            mirror_name: 镜像名称 (tsinghua, ustc, aliyun, default)
            
        Returns:
            新的配置内容
        """
        if mirror_name not in MIRROR_SOURCES:
            raise ValueError(f"未知的镜像源: {mirror_name}，可选: {list(MIRROR_SOURCES.keys())}")
        
        mirror = MIRROR_SOURCES[mirror_name]
        config = self.get_current_config()
        
        config["channels"] = mirror["channels"]
        config["show_channel_urls"] = mirror.get("show_channel_urls", True)
        
        self.save_config(config)
        logger.info(f"已切换到镜像源: {mirror['name']}")
        
        return config

    def add_channel(self, channel: str, priority: str = "highest") -> list[str]:
        """
        添加 channel
        
        Args:
            channel: channel 名称或 URL
            priority: 优先级 (highest, lowest)
            
        Returns:
            更新后的 channels 列表
        """
        config = self.get_current_config()
        channels = config.get("channels", ["defaults"])
        
        if channel in channels:
            logger.warning(f"Channel 已存在: {channel}")
            return channels
        
        if priority == "highest":
            channels.insert(0, channel)
        else:
            channels.append(channel)
        
        config["channels"] = channels
        self.save_config(config)
        
        return channels

    def remove_channel(self, channel: str) -> list[str]:
        """移除 channel"""
        config = self.get_current_config()
        channels = config.get("channels", ["defaults"])
        
        if channel not in channels:
            logger.warning(f"Channel 不存在: {channel}")
            return channels
        
        channels.remove(channel)
        config["channels"] = channels
        self.save_config(config)
        
        return channels

    def get_available_mirrors(self) -> dict:
        """获取可用的镜像源列表"""
        return {
            key: {"name": val["name"], "channels_count": len(val["channels"])}
            for key, val in MIRROR_SOURCES.items()
        }

    async def test_channel_speed(self, channel: str, timeout: int = 10) -> Optional[float]:
        """
        测试 channel 响应速度
        
        Args:
            channel: channel URL
            timeout: 超时时间（秒）
            
        Returns:
            响应时间（秒），失败返回 None
        """
        import aiohttp
        import time
        
        # 构建测试 URL
        if not channel.startswith("http"):
            test_url = f"https://conda.anaconda.org/{channel}/noarch/repodata.json"
        else:
            test_url = f"{channel}/noarch/repodata.json"
        
        try:
            start = time.time()
            client_timeout = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                async with session.head(test_url) as resp:
                    if resp.status == 200:
                        return time.time() - start
        except asyncio.TimeoutError:
            logger.debug(f"测试 channel {channel} 超时")
        except Exception as e:
            logger.debug(f"测试 channel {channel} 失败: {e}")
        
        return None

    async def test_all_mirrors(self) -> dict[str, Optional[float]]:
        """测试所有镜像源速度"""
        async def _test(name: str, url: str):
            return name, await self.test_channel_speed(url)

        tasks = []
        for name, mirror in MIRROR_SOURCES.items():
            if mirror["channels"]:
                tasks.append(_test(name, mirror["channels"][0]))

        results: dict[str, Optional[float]] = {}
        if tasks:
            done = await asyncio.gather(*tasks, return_exceptions=True)
            for item in done:
                if isinstance(item, Exception):
                    continue
                k, v = item
                results[k] = v
        return results


# 生物信息学常用 channels
BIOINFORMATICS_CHANNELS = {
    "bioconda": {
        "description": "生物信息学软件包",
        "url": "bioconda",
        "packages": ["bwa", "samtools", "bcftools", "bowtie2", "star", "hisat2"],
    },
    "conda-forge": {
        "description": "社区维护的通用包",
        "url": "conda-forge",
        "packages": ["numpy", "pandas", "scipy", "matplotlib", "scikit-learn"],
    },
    "r": {
        "description": "R 语言相关包",
        "url": "r",
        "packages": ["r-base", "r-ggplot2", "r-dplyr", "r-tidyverse"],
    },
}


def get_channel_manager() -> ChannelManager:
    """获取 Channel 管理器实例"""
    return ChannelManager()
