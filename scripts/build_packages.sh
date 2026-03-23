#!/bin/bash
# 跨平台打包构建脚本
# 用法：./scripts/build_packages.sh [deb|rpm|appimage|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 版本提取
VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo '0.2.0-dev')}"
VERSION="${VERSION#v}"  # 移除前缀 v

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}BioWorkflow 打包构建脚本${NC}"
echo -e "${GREEN}版本：$VERSION${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 函数：检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"
    
    local missing=0
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python3 未安装${NC}"
        missing=1
    else
        echo -e "${GREEN}✓ Python3: $(python3 --version)${NC}"
    fi
    
    # 检查 PyInstaller
    if ! python3 -m pip show pyinstaller &> /dev/null; then
        echo -e "${YELLOW}⚠ PyInstaller 未安装，将尝试安装...${NC}"
        pip3 install pyinstaller
    else
        echo -e "${GREEN}✓ PyInstaller 已安装${NC}"
    fi
    
    # 检查 FPM (Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if ! command -v fpm &> /dev/null; then
            echo -e "${YELLOW}⚠ FPM 未安装 (用于 DEB/RPM 打包)${NC}"
            echo -e "${YELLOW}  安装：sudo gem install fpm${NC}"
        else
            echo -e "${GREEN}✓ FPM: $(fpm --version)${NC}"
        fi
    fi
    
    if [ $missing -eq 1 ]; then
        echo -e "${RED}错误：缺少必要依赖${NC}"
        exit 1
    fi
}

# 函数：构建 Python 包
build_python_bundle() {
    echo -e "${YELLOW}构建 Python 包...${NC}"
    
    # 清理旧的构建产物
    rm -rf dist/bundle-*
    
    # 构建前端
    if [ -d "src/frontend" ]; then
        echo "构建前端..."
        cd src/frontend
        pnpm install --frozen-lockfile
        pnpm build
        cd ../..
    fi
    
    # 使用 PyInstaller 打包
    cd packaging
    python3 -m PyInstaller bioworkflow.spec --noconfirm
    cd ..
    
    # 移动到输出目录
    mkdir -p dist/bundle-linux
    cp -r packaging/dist/bioworkflow/* dist/bundle-linux/
    
    echo -e "${GREEN}✓ Python 包构建完成${NC}"
    echo "  路径：dist/bundle-linux/"
    echo ""
}

# 函数：构建 DEB 包
build_deb() {
    echo -e "${YELLOW}构建 DEB 包...${NC}"
    
    if ! command -v fpm &> /dev/null; then
        echo -e "${RED}错误：FPM 未安装。请运行：sudo gem install fpm${NC}"
        exit 1
    fi
    
    if [ ! -d "dist/bundle-linux" ]; then
        echo -e "${YELLOW}Python 包不存在，先构建 Python 包...${NC}"
        build_python_bundle
    fi
    
    # 创建包结构
    mkdir -p .debpkg/usr/bin
    mkdir -p .debpkg/usr/lib/bioworkflow
    mkdir -p .debpkg/etc/bioworkflow
    
    # 复制文件
    cp dist/bundle-linux/bioworkflow .debpkg/usr/bin/
    cp -r dist/bundle-linux/* .debpkg/usr/lib/bioworkflow/
    
    # 构建 DEB
    fpm -s dir -t deb \
        -n bioworkflow \
        -v "$VERSION" \
        --description "BioWorkflow - Bioinformatics workflow platform" \
        --maintainer "BioWorkflow Team <team@bioworkflow.org>" \
        --url "https://github.com/${GITHUB_REPOSITORY:-bioworkflow-platform/bioworkflow}" \
        --license "MIT" \
        --vendor "BioWorkflow" \
        --deb-pre-depends "python3 (>= 3.10)" \
        --deb-pre-depends "libglib2.0-0" \
        --after-install packaging/linux/postinst.sh \
        --before-remove packaging/linux/prerm.sh \
        .debpkg/=/
    
    # 清理
    rm -rf .debpkg
    
    echo -e "${GREEN}✓ DEB 包构建完成${NC}"
    echo "  文件：bioworkflow_${VERSION}_*.deb"
    echo ""
}

# 函数：构建 RPM 包
build_rpm() {
    echo -e "${YELLOW}构建 RPM 包...${NC}"
    
    if ! command -v fpm &> /dev/null; then
        echo -e "${RED}错误：FPM 未安装。请运行：sudo gem install fpm${NC}"
        exit 1
    fi
    
    if [ ! -d "dist/bundle-linux" ]; then
        echo -e "${YELLOW}Python 包不存在，先构建 Python 包...${NC}"
        build_python_bundle
    fi
    
    # 创建包结构
    mkdir -p .rpmpkg/usr/bin
    mkdir -p .rpmpkg/usr/lib/bioworkflow
    mkdir -p .rpmpkg/etc/bioworkflow
    
    # 复制文件
    cp dist/bundle-linux/bioworkflow .rpmpkg/usr/bin/
    cp -r dist/bundle-linux/* .rpmpkg/usr/lib/bioworkflow/
    
    # 构建 RPM
    fpm -s dir -t rpm \
        -n bioworkflow \
        -v "$VERSION" \
        --description "BioWorkflow - Bioinformatics workflow platform" \
        --maintainer "BioWorkflow Team <team@bioworkflow.org>" \
        --url "https://github.com/${GITHUB_REPOSITORY:-bioworkflow-platform/bioworkflow}" \
        --license "MIT" \
        --vendor "BioWorkflow" \
        --rpm-os linux \
        --rpm-autoreqprov \
        .rpmpkg/=/
    
    # 清理
    rm -rf .rpmpkg
    
    echo -e "${GREEN}✓ RPM 包构建完成${NC}"
    echo "  文件：bioworkflow-${VERSION}-*.rpm"
    echo ""
}

# 函数：构建 AppImage
build_appimage() {
    echo -e "${YELLOW}构建 AppImage...${NC}"
    
    # 检查 appimagetool
    if ! command -v appimagetool &> /dev/null; then
        echo -e "${YELLOW}下载 appimagetool...${NC}"
        wget -q https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
        sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
    fi
    
    if [ ! -d "dist/bundle-linux" ]; then
        echo -e "${YELLOW}Python 包不存在，先构建 Python 包...${NC}"
        build_python_bundle
    fi
    
    # 创建 AppDir
    mkdir -p AppDir/usr/bin
    mkdir -p AppDir/usr/lib/bioworkflow
    mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
    mkdir -p AppDir/usr/share/applications
    
    # 复制应用
    cp dist/bundle-linux/bioworkflow AppDir/usr/bin/
    cp -r dist/bundle-linux/* AppDir/usr/lib/bioworkflow/
    
    # 创建 wrapper 脚本
    cat > AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/AppRun}
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/bioworkflow"
exec "${HERE}/usr/bin/bioworkflow" "$@"
EOF
    chmod +x AppDir/AppRun
    
    # 创建 desktop 文件
    cat > AppDir/usr/share/applications/bioworkflow.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=BioWorkflow
Comment=Bioinformatics workflow platform
Icon=bioworkflow
Exec=bioworkflow %F
Terminal=false
Categories=Science;Education;
EOF
    
    # 创建占位图标
    if [ ! -f "packaging/assets/icon.png" ]; then
        echo "创建占位图标..."
        convert -size 256x256 xc:blue AppDir/usr/share/icons/hicolor/256x256/apps/bioworkflow.png
    else
        cp packaging/assets/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/bioworkflow.png
    fi
    
    # 构建 AppImage
    appimagetool AppDir \
        -u "gh-releases-zsync|${GITHUB_REPOSITORY_OWNER:-bioworkflow-platform}|bioworkflow|latest|*x86_64.AppImage.zsync" \
        "bioworkflow-${VERSION}-x86_64.AppImage"
    
    # 清理
    rm -rf AppDir
    
    echo -e "${GREEN}✓ AppImage 构建完成${NC}"
    echo "  文件：bioworkflow-${VERSION}-x86_64.AppImage"
    echo ""
}

# 主函数
main() {
    check_dependencies
    
    case "${1:-all}" in
        deb)
            build_deb
            ;;
        rpm)
            build_rpm
            ;;
        appimage)
            build_appimage
            ;;
        all)
            build_python_bundle
            build_deb
            build_rpm
            build_appimage
            ;;
        *)
            echo "用法：$0 [deb|rpm|appimage|all]"
            echo ""
            echo "  deb       - 构建 DEB 包 (Debian/Ubuntu)"
            echo "  rpm       - 构建 RPM 包 (RHEL/CentOS/Fedora)"
            echo "  appimage  - 构建 AppImage (通用 Linux)"
            echo "  all       - 构建所有格式 (默认)"
            echo ""
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}所有包构建完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "产物位置:"
    ls -lh *.deb *.rpm *.AppImage 2>/dev/null || echo "无"
    echo ""
}

# 执行
main "$@"
