#!/bin/bash
set -e

# BioWorkflow Docker 入口脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 等待服务就绪
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-60}

    log_info "等待 $service_name ($host:$port)..."

    for i in $(seq 1 $timeout); do
        if nc -z $host $port 2>/dev/null; then
            log_success "$service_name 已就绪"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    log_error "$service_name 在 ${timeout} 秒内未就绪"
    return 1
}

# 检查环境变量
check_env_vars() {
    log_info "检查环境变量..."

    # 必需的环境变量
    local required_vars=("SECRET_KEY")
    local missing=0

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "缺少必需的环境变量: $var"
            missing=1
        fi
    done

    if [ $missing -eq 1 ]; then
        log_warn "使用默认值或生成随机值..."
        export SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
    fi

    # 设置默认值
    export DEBUG=${DEBUG:-false}
    export HOST=${HOST:-0.0.0.0}
    export PORT=${PORT:-8000}
    export LOG_LEVEL=${LOG_LEVEL:-INFO}

    log_success "环境变量检查完成"
}

# 初始化目录结构
init_directories() {
    log_info "初始化目录结构..."

    local dirs=(
        "/app/data"
        "/app/workflows"
        "/app/conda_envs"
        "/app/knowledge_base"
        "/app/logs"
        "/app/temp"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        # 设置适当的权限
        chmod 755 "$dir"
    done

    # 创建空的日志文件
    touch /app/logs/bioworkflow.log
    chmod 644 /app/logs/bioworkflow.log

    log_success "目录初始化完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."

    # 检查数据库 URL
    if [[ "$DATABASE_URL" == sqlite* ]]; then
        log_info "使用 SQLite 数据库"
        # 确保目录存在
        mkdir -p "$(dirname "${DATABASE_URL#sqlite:///}")"
    fi

    # 可选：运行数据库迁移
    # alembic upgrade head

    log_success "数据库初始化完成"
}

# 显示启动信息
show_startup_info() {
    echo ""
    echo "================================================"
    echo "  BioWorkflow - 生物信息学工作流管理平台"
    echo "================================================"
    echo "  版本: ${VERSION:-0.1.0}"
    echo "  调试模式: ${DEBUG:-false}"
    echo "  监听地址: ${HOST:-0.0.0.0}:${PORT:-8000}"
    echo "  日志级别: ${LOG_LEVEL:-INFO}"
    echo "================================================"
    echo ""
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 检查 Python 环境
    if ! python --version > /dev/null 2>&1; then
        log_error "Python 环境异常"
        return 1
    fi

    # 检查关键依赖
    if ! python -c "import fastapi, uvicorn, sqlalchemy" 2>/dev/null; then
        log_error "关键 Python 依赖缺失"
        return 1
    fi

    # 检查目录权限
    if [ ! -w "/app/logs" ]; then
        log_error "日志目录无写入权限"
        return 1
    fi

    log_success "健康检查通过"
    return 0
}

# 主函数
main() {
    # 设置错误处理
    set -e
    trap 'log_error "脚本执行失败，退出代码: $?"' ERR

    log_info "启动 BioWorkflow 容器..."

    # 执行初始化步骤
    check_env_vars
    init_directories
    init_database

    # 执行健康检查
    if ! health_check; then
        log_error "健康检查失败，容器无法启动"
        exit 1
    fi

    # 显示启动信息
    show_startup_info

    # 处理不同的运行模式
    case "${1:-}" in
        "web"|"")
            log_info "启动 Web 服务..."
            exec uvicorn backend.main:app \
                --host "${HOST:-0.0.0.0}" \
                --port "${PORT:-8000}" \
                --log-level "${LOG_LEVEL,,}" \
                --access-log \
                --reload "${DEBUG:-false}"
            ;;
        "worker")
            log_info "启动 Celery Worker..."
            exec celery -A backend.tasks worker \
                --loglevel="${LOG_LEVEL:-INFO}" \
                --concurrency="${CELERY_CONCURRENCY:-4}"
            ;;
        "scheduler")
            log_info "启动 Celery Beat Scheduler..."
            exec celery -A backend.tasks beat \
                --loglevel="${LOG_LEVEL:-INFO}"
            ;;
        "migrate")
            log_info "执行数据库迁移..."
            exec alembic upgrade head
            ;;
        "shell")
            log_info "进入交互式 Shell..."
            exec /bin/bash
            ;;
        *)
            log_info "执行命令: $@"
            exec "$@"
            ;;
    esac
}

# 执行主函数
main "$@"
