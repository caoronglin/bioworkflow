"""Miniforge environment manager."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from miniforge_service.core.models import (
    Environment,
    EnvironmentCreate,
    EnvironmentStatus,
    EnvironmentUpdate,
    Package,
    PackageChannel,
    PackageInstall,
    SystemInfo,
)

logger = logging.getLogger(__name__)


class MiniforgeManager:
    """Manager for Miniforge/Mamba environments.

    This class provides a high-level interface for managing Conda environments
    using the Miniforge distribution with Mamba for fast package resolution.
    """

    def __init__(
        self,
        root_prefix: Optional[Path] = None,
        envs_dir: Optional[Path] = None,
    ):
        """Initialize the manager.

        Args:
            root_prefix: Base Miniforge installation path
            envs_dir: Directory for environments (default: root_prefix/envs)
        """
        self._root_prefix = root_prefix or self._detect_root_prefix()
        self._envs_dir = envs_dir or (self._root_prefix / "envs")
        self._conda_exe = self._root_prefix / "bin" / "conda"
        self._mamba_exe = self._root_prefix / "bin" / "mamba"

        # Ensure executables exist
        if not self._mamba_exe.exists():
            raise RuntimeError(f"Mamba not found at {self._mamba_exe}")

    def _detect_root_prefix(self) -> Path:
        """Auto-detect Miniforge root prefix."""
        # Check common locations
        possible_paths = [
            Path.home() / "miniforge3",
            Path.home() / "mambaforge",
            Path("/opt/miniforge3"),
            Path("/opt/mambaforge"),
        ]

        # Check CONDA_PREFIX environment variable
        if "CONDA_PREFIX" in os.environ:
            conda_prefix = Path(os.environ["CONDA_PREFIX"])
            # If in an active environment, get base prefix
            if (conda_prefix / "conda-meta").exists():
                possible_paths.insert(0, conda_prefix)

        for path in possible_paths:
            if (path / "bin" / "mamba").exists() or (path / "bin" / "conda").exists():
                return path

        raise RuntimeError(
            "Could not detect Miniforge installation. "
            "Please set CONDA_PREFIX environment variable or install Miniforge."
        )

    async def _run_command(
        self,
        *args: str,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = 300,
    ) -> Tuple[int, str, str]:
        """Execute a shell command asynchronously.

        Args:
            *args: Command and arguments
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        cmd_str = " ".join(args)
        logger.debug(f"Running command: {cmd_str}")

        # Prepare environment
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        # Ensure PATH includes miniforge
        miniforge_bin = str(self._root_prefix / "bin")
        if miniforge_bin not in cmd_env.get("PATH", ""):
            cmd_env["PATH"] = f"{miniforge_bin}:{cmd_env.get('PATH', '')}"

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                    env=cmd_env,
                ),
                timeout=timeout,
            )

            stdout, stderr = await proc.communicate()

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                logger.warning(f"Command failed with exit code {proc.returncode}")
                logger.warning(f"stderr: {stderr_str[:500]}")

            return proc.returncode or 0, stdout_str, stderr_str

        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout}s: {cmd_str}")
            raise RuntimeError(f"Command timed out: {cmd_str}")
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            raise

    def _parse_environment_json(self, data: Dict[str, Any]) -> Environment:
        """Parse environment data from conda JSON output."""
        # Implementation...
        pass

    # ============== Public API ==============

    async def get_system_info(self) -> SystemInfo:
        """Get Miniforge system information."""
        # Get conda version
        _, conda_version, _ = await self._run_command(
            str(self._conda_exe), "--version"
        )
        conda_version = conda_version.strip().replace("conda ", "")

        # Get mamba version
        _, mamba_version, _ = await self._run_command(
            str(self._mamba_exe), "--version"
        )
        mamba_version = mamba_version.strip().split('\n')[0].replace("mamba ", "")

        # Detect platform
        import platform
        system = platform.system().lower()
        machine = platform.machine().lower()

        return SystemInfo(
            platform=system,
            architecture=machine,
            miniforge_version=conda_version,  # Use conda version as proxy
            conda_version=conda_version,
            mamba_version=mamba_version,
            base_prefix=self._root_prefix,
            envs_dirs=[self._envs_dir],
            pkgs_dirs=[self._root_prefix / "pkgs"],
        )

    async def list_environments(self) -> List[Environment]:
        """List all environments."""
        code, stdout, stderr = await self._run_command(
            str(self._conda_exe), "env", "list", "--json"
        )

        if code != 0:
            raise RuntimeError(f"Failed to list environments: {stderr}")

        import json
        data = json.loads(stdout)

        environments = []
        for env_data in data.get("envs", []):
            env = self._parse_environment_from_list(env_data)
            if env:
                environments.append(env)

        return environments

    def _parse_environment_from_list(self, data: Dict[str, Any]) -> Optional[Environment]:
        """Parse environment from conda list output."""
        import os

        name = data.get("name", "")
        path = Path(data.get("path", ""))
        is_active = data.get("is_active", False)

        # Skip base environment for now
        if name == "base":
            return None

        return Environment(
            id=f"env_{name}",  # Generate ID from name
            name=name,
            path=path,
            status=EnvironmentStatus.ACTIVE if is_active else EnvironmentStatus.INACTIVE,
            python_version=None,  # Would need to query
            packages=[],
            channels=[],
            size_bytes=None,
            created_at=datetime.now(),  # Would need to get from filesystem
            updated_at=datetime.now(),
            created_by=None,
            metadata={},
        )

    async def create_environment(self, request: EnvironmentCreate) -> Environment:
        """Create a new environment."""
        # Check if environment already exists
        existing = await self._get_environment_by_name(request.name)
        if existing:
            raise ValueError(f"Environment '{request.name}' already exists")

        # Build mamba create command
        cmd = [
            str(self._mamba_exe),
            "create",
            "-n", request.name,
            "-y",
        ]

        # Add channels
        for channel in request.channels:
            cmd.extend(["-c", channel.value])

        # Add Python if specified
        if request.python_version:
            cmd.append(f"python={request.python_version}")

        # Add packages
        for pkg in request.packages:
            pkg_spec = pkg.name
            if pkg.version:
                pkg_spec = f"{pkg.name}={pkg.version}"
            if pkg.build:
                pkg_spec = f"{pkg_spec}={pkg.build}"
            cmd.append(pkg_spec)

        # Execute creation
        code, stdout, stderr = await self._run_command(*cmd, timeout=600)

        if code != 0:
            raise RuntimeError(f"Failed to create environment: {stderr}")

        # Return created environment
        return await self.get_environment(request.name)

    async def _get_environment_by_name(self, name: str) -> Optional[Environment]:
        """Get environment by name if it exists."""
        try:
            return await self.get_environment(name)
        except Exception:
            return None

    async def get_environment(self, name: str) -> Environment:
        """Get environment by name."""
        # Get environment info using conda
        code, stdout, stderr = await self._run_command(
            str(self._conda_exe), "env", "export", "-n", name, "--json"
        )

        if code != 0:
            if "does not exist" in stderr:
                raise ValueError(f"Environment '{name}' not found")
            raise RuntimeError(f"Failed to get environment: {stderr}")

        import json
        env_data = json.loads(stdout)

        # Get environment path
        env_path = self._envs_dir / name

        # Get directory stats
        size_bytes = None
        created_at = datetime.now()
        if env_path.exists():
            try:
                stat = env_path.stat()
                created_at = datetime.fromtimestamp(stat.st_ctime)
                # Calculate size (this can be slow for large environments)
                # size_bytes = sum(f.stat().st_size for f in env_path.rglob('*') if f.is_file())
            except Exception:
                pass

        # Parse dependencies
        dependencies = env_data.get("dependencies", [])
        packages = []
        for dep in dependencies:
            if isinstance(dep, str):
                # Simple package specification
                parts = dep.split("=")
                pkg = Package(name=parts[0])
                if len(parts) > 1:
                    pkg = pkg.model_copy(update={"version": parts[1]})
                if len(parts) > 2:
                    pkg = pkg.model_copy(update={"build": parts[2]})
                packages.append(pkg)

        return Environment(
            id=f"env_{name}",
            name=name,
            path=env_path,
            status=EnvironmentStatus.ACTIVE,
            python_version=None,
            packages=packages,
            channels=[PackageChannel(c) for c in env_data.get("channels", [])],
            size_bytes=size_bytes,
            created_at=created_at,
            updated_at=datetime.now(),
            created_by=None,
            metadata={},
        )

    async def update_environment(
        self,
        name: str,
        request: EnvironmentUpdate
    ) -> Environment:
        """Update an environment."""
        # Verify environment exists
        await self.get_environment(name)

        # Update description if provided
        if request.description:
            # Note: Conda doesn't store descriptions, we'd need a separate metadata store
            pass

        # Install new packages
        if request.add_packages:
            await self.install_packages(name, request.add_packages)

        # Remove packages
        if request.remove_packages:
            await self.remove_packages(name, request.remove_packages)

        # Update packages
        if request.update_packages:
            await self.update_packages(name, request.update_packages)

        return await self.get_environment(name)

    async def delete_environment(self, name: str, force: bool = False) -> None:
        """Delete an environment."""
        # Verify environment exists
        await self.get_environment(name)

        # Cannot delete base environment
        if name == "base":
            raise ValueError("Cannot delete base environment")

        # Remove environment
        cmd = [str(self._conda_exe), "remove", "-n", name, "--all", "-y"]

        code, stdout, stderr = await self._run_command(*cmd, timeout=300)

        if code != 0:
            raise RuntimeError(f"Failed to delete environment: {stderr}")

    async def install_packages(
        self,
        env_name: str,
        packages: List[PackageInstall]
    ) -> None:
        """Install packages in an environment."""
        if not packages:
            return

        cmd = [str(self._mamba_exe), "install", "-n", env_name, "-y"]

        # Collect channels
        channels = set()
        for pkg in packages:
            if pkg.channel:
                channels.add(pkg.channel.value)

        for channel in channels:
            cmd.extend(["-c", channel])

        # Add package specifications
        for pkg in packages:
            spec = pkg.name
            if pkg.version:
                spec = f"{pkg.name}={pkg.version}"
            if pkg.build:
                spec = f"{spec}={pkg.build}"
            cmd.append(spec)

        code, stdout, stderr = await self._run_command(*cmd, timeout=600)

        if code != 0:
            raise RuntimeError(f"Failed to install packages: {stderr}")

    async def remove_packages(
        self,
        env_name: str,
        package_names: List[str]
    ) -> None:
        """Remove packages from an environment."""
        if not package_names:
            return

        cmd = [str(self._mamba_exe), "remove", "-n", env_name, "-y"]
        cmd.extend(package_names)

        code, stdout, stderr = await self._run_command(*cmd, timeout=300)

        if code != 0:
            raise RuntimeError(f"Failed to remove packages: {stderr}")

    async def update_packages(
        self,
        env_name: str,
        package_names: Optional[List[str]] = None
    ) -> None:
        """Update packages in an environment."""
        cmd = [str(self._mamba_exe), "update", "-n", env_name, "-y"]

        if package_names:
            cmd.extend(package_names)
        else:
            cmd.append("--all")

        code, stdout, stderr = await self._run_command(*cmd, timeout=600)

        if code != 0:
            raise RuntimeError(f"Failed to update packages: {stderr}")

    async def search_packages(
        self,
        query: str,
        channel: Optional[PackageChannel] = None,
        limit: int = 50
    ) -> List[Package]:
        """Search for packages."""
        cmd = [str(self._mamba_exe), "search", "--json"]

        if channel:
            cmd.extend(["-c", channel.value])

        cmd.append(query)

        code, stdout, stderr = await self._run_command(*cmd, timeout=60)

        if code != 0 and "No match found" not in stderr:
            raise RuntimeError(f"Failed to search packages: {stderr}")

        # Parse JSON output
        try:
            import json
            data = json.loads(stdout)
            packages = []

            # Mamba search output format
            for pkg_name, pkg_versions in data.items():
                for pkg_info in pkg_versions[:limit]:
                    packages.append(Package(
                        name=pkg_name,
                        version=pkg_info.get("version"),
                        channel=PackageChannel(pkg_info.get("channel", "conda-forge")),
                        build=pkg_info.get("build"),
                        size=pkg_info.get("size"),
                    ))

            return packages[:limit]

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse search results: {stdout[:500]}")
            return []

    async def get_system_info(self) -> SystemInfo:
        """Get system information."""
        # Get conda info
        code, stdout, stderr = await self._run_command(
            str(self._conda_exe), "info", "--json"
        )

        if code != 0:
            raise RuntimeError(f"Failed to get system info: {stderr}")

        import json
        data = json.loads(stdout)

        # Get mamba version
        _, mamba_version, _ = await self._run_command(
            str(self._mamba_exe), "--version"
        )
        mamba_version = mamba_version.strip().split('\n')[0].replace("mamba ", "")

        # Detect platform
        import platform

        return SystemInfo(
            platform=platform.system().lower(),
            architecture=platform.machine().lower(),
            miniforge_version=data.get("conda_version", "unknown"),
            conda_version=data.get("conda_version", "unknown"),
            mamba_version=mamba_version,
            base_prefix=Path(data.get("root_prefix", self._root_prefix)),
            envs_dirs=[Path(d) for d in data.get("envs_dirs", [self._envs_dir])],
            pkgs_dirs=[Path(d) for d in data.get("pkgs_dirs", [])],
        )
