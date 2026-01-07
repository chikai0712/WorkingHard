#!/bin/bash
# ============================================
# DNS HA Simulator - 快速啟動腳本
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker Desktop for Mac."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    log_success "Docker is ready"
}

# 檢查 Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed."
        exit 1
    fi
    
    log_success "Docker Compose is ready"
}

# 設定權限
setup_permissions() {
    log_info "Setting up permissions..."
    chmod +x "${SCRIPT_DIR}"/*.sh 2>/dev/null || true
    log_success "Permissions set"
}

# 啟動服務
start_services() {
    log_info "Starting DNS HA Simulator..."
    cd "${PROJECT_ROOT}"
    
    docker-compose up -d
    
    log_success "Services started"
    log_info "Waiting for services to be ready (15 seconds)..."
    sleep 15
    
    # 檢查容器狀態
    log_info "Checking container status..."
    docker-compose ps
}

# 顯示使用說明
show_usage() {
    echo ""
    log_info "=========================================="
    log_info "DNS HA Simulator is ready!"
    log_info "=========================================="
    echo ""
    echo "To monitor the system, open two terminal windows:"
    echo ""
    echo "  Terminal A (Controller):"
    echo "    docker logs -f dns-controller"
    echo ""
    echo "  Terminal B (Client):"
    echo "    docker logs -f dns-client"
    echo ""
    echo "To simulate failure:"
    echo "    docker stop service-main"
    echo ""
    echo "To recover:"
    echo "    docker start service-main"
    echo ""
    echo "To stop all services:"
    echo "    docker-compose down"
    echo ""
    log_info "=========================================="
}

# 主函數
main() {
    log_info "DNS HA Simulator - Quick Start"
    log_info "=========================================="
    
    check_docker
    check_docker_compose
    setup_permissions
    start_services
    show_usage
}

# 執行主函數
main "$@"

