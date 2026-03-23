#!/bin/bash
# 手动触发 GitHub Actions 工作流
# 需要安装 GitHub CLI: gh

set -e

echo "=========================================="
echo "BioWorkflow GitHub Actions 触发脚本"
echo "=========================================="
echo ""

# 检查 gh 是否安装
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) 未安装"
    echo ""
    echo "请先安装 GitHub CLI:"
    echo "  Ubuntu/Debian:"
    echo "    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    echo "    echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    echo "    sudo apt update && sudo apt install gh -y"
    echo ""
    echo "  macOS:"
    echo "    brew install gh"
    echo ""
    exit 1
fi

echo "✅ GitHub CLI 已安装：$(gh --version)"
echo ""

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "❌ 未登录到 GitHub"
    echo ""
    echo "请登录："
    echo "  gh auth login"
    echo ""
    exit 1
fi

echo "✅ 已登录到 GitHub"
echo ""

# 获取仓库信息
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || echo "crl4w/bioworkflow")
echo "📦 仓库：$REPO"
echo ""

# 选择要触发的工作流
echo "选择要触发的工作流:"
echo "  1) build-packages.yml - 跨平台打包"
echo "  2) deploy.yml - 部署"
echo "  3) ci.yml - CI 检查"
echo "  4) release.yml - 发布"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        WORKFLOW="build-packages.yml"
        echo "🚀 触发跨平台打包工作流..."
        echo ""
        
        # 输入版本号
        read -p "请输入版本号 (例如：0.2.0): " version
        read -p "是否上传到 Release? (y/n): " upload_release
        
        if [ "$upload_release" = "y" ]; then
            UPLOAD_RELEASE="true"
        else
            UPLOAD_RELEASE="false"
        fi
        
        # 触发工作流
        gh workflow run "$WORKFLOW" \
            --repo "$REPO" \
            --field version="$version" \
            --field upload_to_release="$UPLOAD_RELEASE"
        
        echo ""
        echo "✅ 工作流已触发！"
        echo ""
        echo "查看运行状态:"
        echo "  gh run list --repo $REPO"
        echo ""
        ;;
    
    2)
        WORKFLOW="deploy.yml"
        echo "🚀 触发部署工作流..."
        echo ""
        gh workflow run "$WORKFLOW" --repo "$REPO"
        echo ""
        echo "✅ 工作流已触发！"
        ;;
    
    3)
        WORKFLOW="ci.yml"
        echo "🚀 触发 CI 检查工作流..."
        echo ""
        gh workflow run "$WORKFLOW" --repo "$REPO"
        echo ""
        echo "✅ 工作流已触发！"
        ;;
    
    4)
        echo "🚀 发布需要通过打标签触发："
        echo ""
        read -p "请输入版本标签 (例如：v0.2.0): " tag
        echo ""
        git tag "$tag"
        git push origin "$tag"
        echo ""
        echo "✅ 标签已推送，将自动触发 release.yml 工作流"
        ;;
    
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "完成！"
echo "=========================================="
