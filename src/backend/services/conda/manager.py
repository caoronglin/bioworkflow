"""
Conda 包管理器实现

实现 PackageManager 接口
"""

import asyncio
import json
from typing import Any

from loguru import logger

from backend.core.interfaces import PackageManager


class CondaPackageManager(PackageManager):
    """Conda 包管理器实现"""

    def __init__(self, conda_path: str = "conda"):
        self._conda_path = conda_path
        self._lock = asyncio.Lock()

    async def _run_conda(
        self,
        args: list[str],
        timeout: int = 300,
    ) -> dict[str, Any]:
        """运行 Conda 命令"""
        cmd = [self._conda_path] + args + ["--json"]

        logger.debug(f"Running conda: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError:
            return {"output": stdout.decode()}

    async def list_environments(self) -> list[dict[str, Any]]:
        """列出所有环境"""
        result = await self._run_conda(["env", "list"])

        envs = []
        for env_info in result.get("envs", []):
            from pathlib import Path

            name = Path(env_info).name if "/" in env_info else env_info
            envs.append({
                "name": name,
                "path": env_info,
                "is_active": "*" in str(result.get("active_prefix", "")),
            })

        return envs

    async def create_environment(
        self,
        name: str,
        python_version: str,
        packages: list[str] | None = None,
    ) -> dict[str, Any]:
        """创建新环境"""
        async with self._lock:
            args = ["create", "-n", name, f"python={python_version}", "-y"]

            if packages:
                args.extend(packages)

            await self._run_conda(args, timeout=600)

            logger.info(f"Created conda environment: {name}")

            # 返回环境信息
            envs = await self.list_environments()
            for env in envs:
                if env["name"] == name:
                    return env

            raise RuntimeError(f"Environment created but not found: {name}")

    async def remove_environment(self, name: str) -> bool:
        """删除环境"""
        async with self._lock:
            try:
                await self._run_conda(["env", "remove", "-n", name, "-y"])
                logger.info(f"Removed conda environment: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to remove environment: {e}")
                return False

    async def list_packages(self, env_name: str) -> list[dict[str, Any]]:
        """列出环境中的包"""
        result = await self._run_conda(["list", "-n", env_name])

        packages = []
        pkg_list = result if isinstance(result, list) else result.get("packages", [])

        for pkg in pkg_list:
            if isinstance(pkg, dict):
                packages.append({
                    "name": pkg.get("name", ""),
                    "version": pkg.get("version", ""),
                    "channel": pkg.get("channel", ""),
                    "build": pkg.get("build_string"),
                })

        return packages

    async def install_packages(
        self,
        env_name: str,
        packages: list[str],
    ) -> bool:
        """安装包"""
        async with self._lock:
            try:
                args = ["install", "-n", env_name, "-y"] + packages
                await self._run_conda(args, timeout=600)
                logger.info(f"Installed packages in {env_name}: {packages}")
                return True
            except Exception as e:
                logger.error(f"Failed to install packages: {e}")
                return False

    async def remove_packages(
        self,
        env_name: str,
        packages: list[str],
    ) -> bool:
        """卸载包"""
        async with self._lock:
            try:
                args = ["remove", "-n", env_name, "-y"] + packages
                await self._run_conda(args, timeout=600)
                logger.info(f"Removed packages from {env_name}: {packages}")
                return True
            except Exception as e:
                logger.error(f"Failed to remove packages: {e}")
                return False

    async def search_packages(
        self,
        query: str,
        channel: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """搜索包"""
        args = ["search", query]
        if channel:
            args.extend(["-c", channel])

        result = await self._run_conda(args)

        packages = []
        for name, variants in result.items():
            for variant in variants[:limit]:
                packages.append({
                    "name": name,
                    "version": variant.get("version", ""),
                    "channel": variant.get("channel", ""),
                    "build": variant.get("build", ""),
                })

        return packages


# 全局实例
_conda_manager: CondaPackageManager | None = None


def get_conda_manager() -> CondaPackageManager:
    """获取 Conda 包管理器实例"""
    global _conda_manager
    if _conda_manager is None:
        _conda_manager = CondaPackageManager()
    return _conda_manager
