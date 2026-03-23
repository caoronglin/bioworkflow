#!/bin/bash
# Linux DEB/RPM 包安装后脚本

set -e

echo "BioWorkflow 安装后配置..."

# 1. 创建应用用户（如果不存在）
if ! id -u bioworkflow >/dev/null 2>&1; then
    echo "创建 bioworkflow 用户..."
    useradd --system --shell /usr/sbin/nologin --home-dir /var/lib/bioworkflow bioworkflow
fi

# 2. 创建必要的目录
echo "创建数据目录..."
mkdir -p /var/lib/bioworkflow/workflows
mkdir -p /var/log/bioworkflow
mkdir -p /etc/bioworkflow

# 3. 设置权限
chown -R bioworkflow:bioworkflow /var/lib/bioworkflow
chown -R bioworkflow:bioworkflow /var/log/bioworkflow
chown -R bioworkflow:bioworkflow /etc/bioworkflow
chmod 755 /var/lib/bioworkflow
chmod 755 /var/log/bioworkflow
chmod 755 /etc/bioworkflow

# 4. 创建默认配置文件（如果不存在）
if [ ! -f /etc/bioworkflow/config.yaml ]; then
    echo "创建默认配置文件..."
    cat > /etc/bioworkflow/config.yaml << 'EOF'
# BioWorkflow 配置文件
server:
  host: "0.0.0.0"
  port: 8000

database:
  url: "sqlite+aiosqlite:////var/lib/bioworkflow/bioworkflow.db"

logging:
  level: "INFO"
  file: "/var/log/bioworkflow/bioworkflow.log"

workflows:
  workdir: "/var/lib/bioworkflow/workflows"
EOF
    chown bioworkflow:bioworkflow /etc/bioworkflow/config.yaml
fi

# 5. 重载 systemd（如果存在 systemd 服务文件）
if [ -f /lib/systemd/system/bioworkflow.service ]; then
    echo "重载 systemd 配置..."
    systemctl daemon-reload
    
    # 如果服务未运行，则启动它
    if ! systemctl is-active --quiet bioworkflow; then
        echo "启动 bioworkflow 服务..."
        systemctl enable bioworkflow
        systemctl start bioworkflow
    else
        echo "重启 bioworkflow 服务..."
        systemctl restart bioworkflow
    fi
fi

# 6. 打印完成信息
echo ""
echo "=========================================="
echo "BioWorkflow 安装完成！"
echo "=========================================="
echo ""
echo "配置文件：/etc/bioworkflow/config.yaml"
echo "数据目录：/var/lib/bioworkflow"
echo "日志文件：/var/log/bioworkflow/bioworkflow.log"
echo ""
echo "启动服务：sudo systemctl start bioworkflow"
echo "查看状态：sudo systemctl status bioworkflow"
echo "访问界面：http://localhost:8000"
echo ""

exit 0
