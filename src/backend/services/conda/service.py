"""Conda 服务 - 环境管理

提供 Conda 环境的生命周期管理，包括创建、删除、包管理等功能
"""

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class CondaEnvironment:
    """Conda 环境信息"""
    name: str
    path: str
    python_version: Optional[str] = None
    is_active: bool = False


@dataclass
class CondaPackage:
    """Conda 包信息"""
    name: str
    version: str
    channel: str
    build: Optional[str] = None


class CondaService:
    """Conda 服务"""

    def __init__(self, conda_path: str = "conda"):
        self.conda_path = conda_path
        self._lock = asyncio.Lock()

    async def _run_conda(
        self,
        args: list[str],
        cwd: Optional[Path] = None,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """运行 Conda 命令"""
        cmd = [self.conda_path] + args + ["--json"]

        logger.debug(f"Running: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError(f"Conda command timed out after {timeout}s")

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(f"Conda command failed: {error_msg}")

        # 解析 JSON 输出
        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError:
            return {"output": stdout.decode()}

    async def list_environments(self) -> list[CondaEnvironment]:
        """列出所有环境"""
        result = await self._run_conda(["env", "list"])

        envs = []
        for env_info in result.get("envs", []):
            name = Path(env_info).name if "/" in env_info or "\\" in env_info else env_info
            envs.append(CondaEnvironment(
                name=name,
                path=env_info,
                is_active="*" in str(result.get("active_prefix", "")),
            ))

        return envs

    async def create_environment(
        self,
        name: str,
        python_version: str = "3.10",
        packages: Optional[list[str]] = None,
    ) -> CondaEnvironment:
        """创建新环境"""
        async with self._lock:
            args = ["create", "-n", name, f"python={python_version}", "-y"]

            if packages:
                args.extend(packages)

            await self._run_conda(args, timeout=600)

            logger.info(f"Created environment: {name}")

            # 返回环境信息
            envs = await self.list_environments()
            for env in envs:
                if env.name == name:
                    return env

            raise RuntimeError(f"Environment created but not found: {name}")

    async def remove_environment(self, name: str) -> None:
        """删除环境"""
        async with self._lock:
            await self._run_conda(["env", "remove", "-n", name, "-y"])
            logger.info(f"Removed environment: {name}")

    async def list_packages(self, env_name: str) -> list[CondaPackage]:
        """列出环境中的包"""
        result = await self._run_conda(["list", "-n", env_name])

        packages = []
        pkg_list = result if isinstance(result, list) else result.get("packages", [])

        for pkg in pkg_list:
            if isinstance(pkg, dict):
                packages.append(CondaPackage(
                    name=pkg.get("name", ""),
                    version=pkg.get("version", ""),
                    channel=pkg.get("channel", ""),
                    build=pkg.get("build_string"),
                ))

        return packages

    async def install_packages(
        self,
        env_name: str,
        packages: list[str],
        channel: Optional[str] = None,
    ) -> None:
        """安装包"""
        async with self._lock:
            args = ["install", "-n", env_name, "-y"]

            if channel:
                args.extend(["-c", channel])

            args.extend(packages)

            await self._run_conda(args, timeout=600)
            logger.info(f"Installed packages in {env_name}: {packages}")

    async def remove_packages(
        self,
        env_name: str,
        packages: list[str],
    ) -> None:
        """卸载包"""
        async with self._lock:
            args = ["remove", "-n", env_name, "-y"] + packages
            await self._run_conda(args, timeout=600)
            logger.info(f"Removed packages from {env_name}: {packages}")

    async def search_packages(
        self,
        query: str,
        channel: Optional[str] = None,
        limit: int = 50,
    ) -> list[CondaPackage]:
        """搜索包"""
        args = ["search", query]
        if channel:
            args.extend(["-c", channel])

        result = await self._run_conda(args)

        packages = []
        for name, variants in result.items():
            for variant in variants[:limit]:
                packages.append(CondaPackage(
                    name=name,
                    version=variant.get("version", ""),
                    channel=variant.get("channel", ""),
                    build=variant.get("build", ""),
                ))

        return packages
