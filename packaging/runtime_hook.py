#!/usr/bin/env python3
"""
PyInstaller 运行时 Hook
用于设置正确的环境变量和路径配置
"""

import sys
import os
from pathlib import Path


def setup_environment():
    """设置运行时环境变量"""

    # 获取应用根目录
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的临时目录
        APP_ROOT = Path(sys._MEIPASS)
        print(f"[Runtime Hook] Running from PyInstaller bundle: {APP_ROOT}", file=sys.stderr)
    else:
        # 开发环境
        APP_ROOT = Path(__file__).parent.parent
        print(f"[Runtime Hook] Running in development mode: {APP_ROOT}", file=sys.stderr)

    # 设置环境变量
    os.environ.setdefault("APP_ROOT", str(APP_ROOT))

    # 前端静态文件路径
    if (APP_ROOT / "frontend").exists():
        FRONTEND_DIST = APP_ROOT / "frontend"
    elif (APP_ROOT / "src" / "frontend" / "dist").exists():
        FRONTEND_DIST = APP_ROOT / "src" / "frontend" / "dist"
    else:
        FRONTEND_DIST = APP_ROOT / "frontend"

    os.environ.setdefault("FRONTEND_DIST", str(FRONTEND_DIST))
    print(f"[Runtime Hook] Frontend dist: {FRONTEND_DIST}", file=sys.stderr)

    # Rust 扩展路径（如果需要）
    if (APP_ROOT / "bioworkflow").exists():
        # 打包后的 Rust 扩展
        rust_ext_path = APP_ROOT / "bioworkflow"
        if str(rust_ext_path) not in sys.path:
            sys.path.insert(0, str(rust_ext_path))
            print(f"[Runtime Hook] Added Rust extension path: {rust_ext_path}", file=sys.stderr)

    # Windows DLL 加载顺序修复
    if sys.platform == "win32":
        try:
            import ctypes

            # 恢复默认 DLL 加载顺序
            ctypes.windll.kernel32.SetDllDirectoryA(None)

            # 如果需要从特定目录加载 DLL
            if hasattr(sys, "_MEIPASS"):
                ctypes.windll.kernel32.SetDllDirectoryW(str(APP_ROOT))

            print("[Runtime Hook] Fixed Windows DLL loading order", file=sys.stderr)
        except Exception as e:
            print(f"[Runtime Hook] Warning fixing DLL loading: {e}", file=sys.stderr)

    # Snakemake 工作目录
    if not os.environ.get("SNAKEMAKE_WORKDIR"):
        snakemake_workdir = APP_ROOT / "workflows"
        snakemake_workdir.mkdir(exist_ok=True)
        os.environ["SNAKEMAKE_WORKDIR"] = str(snakemake_workdir)
        print(f"[Runtime Hook] Snakemake workdir: {snakemake_workdir}", file=sys.stderr)

    # 日志配置
    os.environ.setdefault("LOGURU_LEVEL", "INFO")

    print("[Runtime Hook] Environment setup complete", file=sys.stderr)


# 自动执行
setup_environment()
