"""
Conda 环境管理器
提供 Conda 环境的创建、激活、包管理等功能
"""

import asyncio
import json
import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from loguru import logger


class CondaError(Exception):
    """Conda 操作错误"""
    pass


class PackageSource(Enum):
    """包来源"""
    CONDA = "conda"
    CONDA_FORGE = "conda-forge"
    BIOCONDA = "bioconda"
    R = "r"


@dataclass
class CondaPackage:
    """Conda 包信息"""
    name: str
    version: str
    channel: str
    build: str = ""


@dataclass
class CondaEnvironment:
    """Conda 环境信息"""
    name: str
    path: str
    is_active: bool = False
    packages: list[CondaPackage] = field(default_factory=list)


class CondaManager:
    """Conda 环境管理器"""

    def __init__(self, conda_path: Optional[str] = None):
        """
        初始化 Conda 管理器（惰性校验，避免阻塞启动）
        
        Args:
            conda_path: Conda 可执行文件路径，默认自动检测
        """
        self.conda_path = conda_path
        self._validated = False

    def _detect_conda(self) -> str:
        """检测 Conda 安装路径"""
        # 尝试常见路径
        possible_paths = [
            "conda",  # 系统 PATH
            os.path.expanduser("~/miniconda3/bin/conda"),
            os.path.expanduser("~/anaconda3/bin/conda"),
            "/opt/conda/bin/conda",
            "C:\\ProgramData\\miniconda3\\Scripts\\conda.exe",
            "C:\\Users\\%USERNAME%\\miniconda3\\Scripts\\conda.exe",
        ]
        
        for path in possible_paths:
            expanded = os.path.expandvars(path)
            if os.path.isfile(expanded) or self._command_exists(expanded):
                return expanded
        
        raise CondaError("无法找到 Conda 安装，请确保 Conda 已安装并在 PATH 中")

    def _command_exists(self, cmd: str) -> bool:
        """检查命令是否存在"""
        try:
            subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                timeout=10
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _validate_conda(self) -> None:
        """验证 Conda 安装"""
        if self._validated:
            return
        if not self.conda_path:
            self.conda_path = self._detect_conda()
        try:
            result = subprocess.run(
                [self.conda_path, "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                raise CondaError(f"Conda 验证失败: {result.stderr}")
            logger.info(f"Conda 版本: {result.stdout.strip()}")
            self._validated = True
        except subprocess.TimeoutExpired:
            raise CondaError("Conda 验证超时")

    def _ensure_ready(self) -> None:
        """确保 Conda 可用（惰性检测与校验）"""
        if not self._validated:
            self._validate_conda()

    async def _run_conda_async(
        self, 
        args: list[str], 
        timeout: int = 300
    ) -> dict:
        """
        异步执行 Conda 命令
        
        Args:
            args: 命令参数列表
            timeout: 超时时间（秒）
            
        Returns:
            命令输出的 JSON 解析结果或文本
        """
        self._ensure_ready()
        cmd = [self.conda_path] + args + ["--json"]
        logger.debug(f"执行 Conda 命令: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise CondaError(f"Conda 命令失败: {error_msg}")
            
            output = stdout.decode()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"output": output}
                
        except asyncio.TimeoutError:
            raise CondaError(f"Conda 命令超时 ({timeout}s)")

    async def list_environments(self) -> list[CondaEnvironment]:
        """列出所有 Conda 环境"""
        result = await self._run_conda_async(["env", "list"])
        
        envs = []
        for env_info in result.get("envs", []):
            name = os.path.basename(env_info) if "/" in env_info or "\\" in env_info else env_info
            envs.append(CondaEnvironment(
                name=name,
                path=env_info,
                is_active="*" in str(result.get("active_prefix", ""))
            ))
        
        return envs

    async def create_environment(
        self,
        name: str,
        python_version: str = "3.10",
        packages: Optional[list[str]] = None
    ) -> CondaEnvironment:
        """
        创建新的 Conda 环境
        
        Args:
            name: 环境名称
            python_version: Python 版本
            packages: 初始安装的包列表
        """
        args = ["create", "-n", name, f"python={python_version}", "-y"]
        
        if packages:
            args.extend(packages)
        
        await self._run_conda_async(args, timeout=600)
        logger.info(f"创建环境成功: {name}")
        
        # 获取环境信息
        envs = await self.list_environments()
        for env in envs:
            if env.name == name:
                return env
        
        raise CondaError(f"环境创建后未找到: {name}")

    async def remove_environment(self, name: str) -> None:
        """删除 Conda 环境"""
        await self._run_conda_async(["env", "remove", "-n", name, "-y"])
        logger.info(f"删除环境成功: {name}")

    async def install_packages(
        self,
        env_name: str,
        packages: list[str],
        channel: Optional[str] = None
    ) -> list[CondaPackage]:
        """
        在指定环境中安装包
        
        Args:
            env_name: 环境名称
            packages: 包列表
            channel: 指定 channel（如 conda-forge, bioconda）
        """
        args = ["install", "-n", env_name, "-y"]
        
        if channel:
            args.extend(["-c", channel])
        
        args.extend(packages)
        
        await self._run_conda_async(args, timeout=600)
        logger.info(f"在环境 {env_name} 中安装包成功: {packages}")
        
        return await self.list_packages(env_name)

    async def remove_packages(
        self,
        env_name: str,
        packages: list[str],
    ) -> list[CondaPackage]:
        """在指定环境中卸载包"""
        args = ["remove", "-n", env_name, "-y"] + packages
        await self._run_conda_async(args, timeout=600)
        logger.info(f"在环境 {env_name} 中卸载包成功: {packages}")
        return await self.list_packages(env_name)

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
        args.append("--json")

        self._ensure_ready()
        process = await asyncio.create_subprocess_exec(
            self.conda_path,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise CondaError(f"Conda 搜索失败: {stderr.decode()}")
        try:
            result = json.loads(stdout.decode())
        except json.JSONDecodeError:
            raise CondaError("Conda 搜索结果解析失败")

        packages: list[CondaPackage] = []
        for name, variants in result.items():
            for variant in variants[:limit]:
                packages.append(
                    CondaPackage(
                        name=name,
                        version=variant.get("version", ""),
                        channel=variant.get("channel", ""),
                        build=variant.get("build", ""),
                    )
                )
        return packages

    async def list_packages(self, env_name: str) -> list[CondaPackage]:
        """列出环境中的所有包"""
        result = await self._run_conda_async(["list", "-n", env_name])
        
        packages = []
        # conda list --json 返回一个列表，或包含列表的字典
        pkg_list = result if isinstance(result, list) else result.get("packages", result.get("output", []))
        if isinstance(pkg_list, list):
            for pkg in pkg_list:
                if isinstance(pkg, dict):
                    packages.append(CondaPackage(
                        name=pkg.get("name", ""),
                        version=pkg.get("version", ""),
                        channel=pkg.get("channel", ""),
                        build=pkg.get("build_string", "")
                    ))
        
        return packages

    async def export_environment(
        self,
        env_name: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        导出环境配置为 YAML
        
        Args:
            env_name: 环境名称
            output_path: 输出文件路径，如不指定则返回内容
        """
        # 导出不使用 --json
        cmd = [self.conda_path, "env", "export", "-n", env_name]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise CondaError(f"导出环境失败: {stderr.decode()}")
        
        content = stdout.decode()
        
        if output_path:
            output_path.write_text(content)
            logger.info(f"环境配置已导出到: {output_path}")
        
        return content

    async def create_from_yaml(self, yaml_path: Path, name: Optional[str] = None) -> Optional[CondaEnvironment]:
        """
        从 YAML 文件创建环境
        
        Args:
            yaml_path: 环境配置文件路径
            name: 覆盖环境名称
            
        Returns:
            创建的环境对象，如果失败则返回 None
        """
        if not yaml_path.exists():
            raise CondaError(f"YAML 文件不存在: {yaml_path}")
        
        args = ["env", "create", "-f", str(yaml_path)]
        
        if name:
            args.extend(["-n", name])
        
        await self._run_conda_async(args, timeout=900)
        
        # 获取创建的环境名称
        target_name = name
        if not target_name:
            # 从 YAML 文件读取环境名称
            import yaml
            with open(yaml_path) as f:
                yaml_content = yaml.safe_load(f)
                target_name = yaml_content.get("name")
        
        # 查找创建的环境
        envs = await self.list_environments()
        for env in envs:
            if env.name == target_name:
                return env
        
        return envs[-1] if envs else None


# 全局实例
_conda_manager: Optional[CondaManager] = None


def get_conda_manager(conda_path: Optional[str] = None) -> CondaManager:
    """获取 Conda 管理器单例"""
    global _conda_manager
    if _conda_manager is None:
        _conda_manager = CondaManager(conda_path=conda_path)
    return _conda_manager
