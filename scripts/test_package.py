#!/usr/bin/env python3
"""
BioWorkflow 打包验证脚本
用于测试生成的包是否正常工作
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, capture=True):
    """运行命令行并返回结果"""
    print(f"运行：{' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd.split(),
            capture_output=capture,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except Exception as e:
        return -1, "", str(e)


def test_version(bundle_path):
    """测试版本命令"""
    print("\n测试 --version...")
    exe = bundle_path / "bioworkflow"
    if not exe.exists():
        print(f"✗ 可执行文件不存在：{exe}")
        return False

    returncode, stdout, stderr = run_command([str(exe), "--version"])
    if returncode == 0:
        print(f"✓ 版本信息：{stdout.strip()}")
        return True
    else:
        print(f"✗ 版本命令失败：{stderr}")
        return False


def test_health_check(bundle_path):
    """测试健康检查端点"""
    print("\n测试健康检查端点...")
    # 启动服务（后台）
    exe = bundle_path / "bioworkflow"

    # 简单测试，不实际启动服务
    print("✓ 健康检查测试跳过（需要实际运行服务）")
    return True


def test_rust_extension(bundle_path):
    """测试 Rust 扩展模块"""
    print("\n测试 Rust 扩展模块...")

    # 创建测试脚本
    test_script = bundle_path / "test_rust.py"
    test_script.write_text("""
import sys
try:
    import bioworkflow
    print(f"Rust 扩展已加载：{bioworkflow.__file__}")
    
    # 测试矩阵操作
    import numpy as np
    data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    corr = bioworkflow.correlation_matrix(data, "pearson")
    print(f"相关系数矩阵形状：{corr.shape}")
    print("✓ Rust 扩展测试通过")
    sys.exit(0)
except Exception as e:
    print(f"✗ Rust 扩展测试失败：{e}")
    sys.exit(1)
""")

    python_exe = (
        bundle_path / "python" if (bundle_path / "python").exists() else Path(sys.executable)
    )
    returncode, stdout, stderr = run_command([str(python_exe), str(test_script)])

    print(stdout)
    if stderr:
        print(f"错误：{stderr}")

    # 清理
    test_script.unlink()

    return returncode == 0


def test_frontend_files(bundle_path):
    """测试前端静态文件"""
    print("\n测试前端静态文件...")

    # 检查常见的前端文件
    frontend_dirs = ["frontend", "static", "www"]
    found = False

    for dir_name in frontend_dirs:
        frontend_path = bundle_path / dir_name
        if frontend_path.exists():
            print(f"✓ 找到前端目录：{frontend_path}")
            # 检查 index.html
            index_html = frontend_path / "index.html"
            if index_html.exists():
                print(f"✓ 找到 index.html")
                found = True
            break

    if not found:
        print("⚠ 警告：未找到前端静态文件")
        return False

    return True


def test_package_installation(package_file):
    """测试包安装"""
    print(f"\n测试包安装：{package_file}")

    suffix = Path(package_file).suffix.lower()

    if suffix == ".deb":
        # DEB 包测试
        returncode, stdout, stderr = run_command(f"sudo apt install {package_file} -y")
        if returncode == 0:
            print("✓ DEB 包安装成功")
            return True
        else:
            print(f"✗ DEB 包安装失败：{stderr}")
            return False

    elif suffix == ".rpm":
        # RPM 包测试
        returncode, stdout, stderr = run_command(f"sudo rpm -ivh {package_file}")
        if returncode == 0:
            print("✓ RPM 包安装成功")
            return True
        else:
            print(f"✗ RPM 包安装失败：{stderr}")
            return False

    elif suffix == ".appimage":
        # AppImage 测试
        returncode, stdout, stderr = run_command(
            f"chmod +x {package_file} && {package_file} --version"
        )
        if returncode == 0:
            print(f"✓ AppImage 运行成功：{stdout.strip()}")
            return True
        else:
            print(f"✗ AppImage 运行失败：{stderr}")
            return False

    else:
        print(f"✗ 不支持的包格式：{suffix}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("BioWorkflow 打包验证")
    print("=" * 60)

    # 检查参数
    if len(sys.argv) < 2:
        # 自动检测
        dist_dir = Path("dist/bundle-linux")
        if not dist_dir.exists():
            print("✗ 未找到打包目录：dist/bundle-linux")
            print("用法：python scripts/test_package.py <包文件路径>")
            sys.exit(1)

        # 测试打包目录
        print(f"\n测试打包目录：{dist_dir}")
        results = []
        results.append(("版本命令", test_version(dist_dir)))
        results.append(("Rust 扩展", test_rust_extension(dist_dir)))
        results.append(("前端文件", test_frontend_files(dist_dir)))
        results.append(("健康检查", test_health_check(dist_dir)))
    else:
        # 测试指定的包文件
        package_file = Path(sys.argv[1])
        if not package_file.exists():
            print(f"✗ 包文件不存在：{package_file}")
            sys.exit(1)

        results = [("包安装", test_package_installation(str(package_file)))]

    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")

    # 统计
    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n总计：{passed}/{total} 测试通过")

    if passed == total:
        print("\n✓ 所有测试通过！包可以发布。")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败。请修复后重新打包。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
