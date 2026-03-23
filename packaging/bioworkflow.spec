# PyInstaller 配置文件 - BioWorkflow
# 用于将 Python + Rust 混合应用打包成独立可执行文件

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata
import sys
import os
from pathlib import Path

# =============================================================================
# 路径配置
# =============================================================================
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / 'src'
BACKEND_DIR = SRC_DIR / 'backend'
FRONTEND_DIST = SRC_DIR / 'frontend' / 'dist'
RUST_EXT_NAME = 'bioworkflow'  # Rust 扩展模块名称

# =============================================================================
# 数据收集
# =============================================================================
datas = []
binaries = []
hiddenimports = []

# 1. 收集 Rust 扩展模块
print(f"Collecting Rust extension: {RUST_EXT_NAME}")
try:
    datas += collect_data_files(RUST_EXT_NAME)
    hiddenimports += collect_submodules(RUST_EXT_NAME)
    # 复制元数据（用于 pkg_resources）
    datas += copy_metadata(RUST_EXT_NAME)
    print(f"✓ Collected Rust extension files: {len(datas)} items")
except Exception as e:
    print(f"⚠ Warning collecting Rust extension: {e}")

# 2. 收集 FastAPI/Uvicorn 相关依赖
hiddenimports += [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi.middleware.cors',
    'fastapi.staticfiles',
    'pydantic_settings',
]

# 3. 收集科学计算栈
hiddenimports += [
    'numpy',
    'pandas',
    'scipy',
    'snakemake',
    'snakemake.logging',
]

# 4. 收集前端静态文件
if FRONTEND_DIST.exists():
    print(f"✓ Found frontend dist: {FRONTEND_DIST}")
    datas.append((str(FRONTEND_DIST), 'frontend'))
else:
    print(f"⚠ Warning: Frontend dist not found at {FRONTEND_DIST}")

# 5. 收集 Snakemake 资源
try:
    from snakemake import __file__ as snakemake_file
    snakemake_dir = Path(snakemake_file).parent
    print(f"✓ Found Snakemake at: {snakemake_dir}")
    
    # 收集 Snakemake 模板和规则文件
    for pattern in ['**/*.smk', '**/*.yaml', '**/*.yml', '**/*.json']:
        datas += collect_data_files('snakemake', include_datas=[pattern])
except Exception as e:
    print(f"⚠ Warning collecting Snakemake: {e}")

# =============================================================================
# 分析配置
# =============================================================================
block_cipher = None

a = Analysis(
    [str(BACKEND_DIR / 'main.py')],
    pathex=[str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(ROOT_DIR / 'packaging' / 'hooks')],
    hooksconfig={},
    runtime_hooks=[str(ROOT_DIR / 'packaging' / 'runtime_hook.py')],
    excludes=[
        'pytest',
        'pytest.*',
        'unittest',
        'test.*',
        'tests.*',
        'coverage',
        'mypy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# =============================================================================
# PYZ 配置
# =============================================================================
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# =============================================================================
# EXE 配置（开发模式 - 带控制台）
# =============================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='bioworkflow-dev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 开发模式显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT_DIR / 'packaging' / 'assets' / 'icon.ico')
)

# =============================================================================
# COLLECT 配置（onedir 模式）
# =============================================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bioworkflow',
)

# =============================================================================
# 说明
# =============================================================================
"""
打包模式说明：

1. onedir 模式（推荐）：
   - 生成一个目录，包含 exe 和所有依赖
   - 启动速度快
   - 方便调试
   - 命令：pyinstaller bioworkflow.spec

2. onefile 模式：
   - 生成单个 exe 文件
   - 便于分发
   - 启动时会解压到临时目录
   - 命令：pyinstaller --onefile bioworkflow.spec

打包后验证：
1. 测试 exe 启动：dist/bioworkflow/bioworkflow.exe
2. 检查 API 响应：curl http://localhost:8000/health
3. 验证 Rust 扩展：import bioworkflow; bioworkflow.correlation_matrix(...)
4. 检查前端静态文件是否正常服务

常见问题：
- Rust 扩展找不到：确保 spec 中 collect_data_files 和 collect_submodules
- 前端静态文件 404：检查 datas 配置和 FastAPI 的 StaticFiles 路径
- DLL 加载失败：检查 runtime_hook.py 中的 SetDllDirectory 调用
"""
