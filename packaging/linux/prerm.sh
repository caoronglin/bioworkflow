#!/bin/bash
# Linux DEB/RPM 包卸载前脚本

set -e

echo "BioWorkflow 卸载前清理..."

# 1. 停止并禁用服务
if [ -f /lib/systemd/system/bioworkflow.service ]; then
    echo "停止 bioworkflow 服务..."
    systemctl stop bioworkflow 2>/dev/null || true
    systemctl disable bioworkflow 2>/dev/null || true
fi

# 2. 备份用户数据（可选）
# 如果需要保留数据，取消以下注释：
# if [ -d /var/lib/bioworkflow ]; then
#     echo "备份用户数据到 /var/backups/bioworkflow-backup-$(date +%Y%m%d)..."
#     mkdir -p /var/backups
#     cp -r /var/lib/bioworkflow /var/backups/bioworkflow-backup-$(date +%Y%m%d)
# fi

# 3. 清理配置（保留用户数据）
echo "清理配置..."
rm -f /etc/bioworkflow/config.yaml 2>/dev/null || true

# 4. 打印信息
echo ""
echo "=========================================="
echo "BioWorkflow 已卸载"
echo "=========================================="
echo ""
echo "保留的数据目录：/var/lib/bioworkflow"
echo "保留的日志文件：/var/log/bioworkflow"
echo ""
echo "如需完全删除，请手动执行："
echo "  sudo rm -rf /var/lib/bioworkflow"
echo "  sudo rm -rf /var/log/bioworkflow"
echo "  sudo rm -rf /etc/bioworkflow"
echo "  sudo userdel bioworkflow"
echo ""

exit 0
