#!/bin/bash
# ============================================
# DNS Port Forward 設定腳本
# 將 macOS 的 DNS 查詢轉發到 Docker DNS 服務器
# ============================================

set -e

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

# 檢查是否為 root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "此腳本需要 root 權限（使用 sudo）"
        exit 1
    fi
}

# 方法 1: 使用 socat 做 port forward（推薦）
setup_socat_forward() {
    log_info "設定方法 1: 使用 socat 做 port forward"
    
    # 檢查 socat 是否安裝
    if ! command -v socat &> /dev/null; then
        log_warn "socat 未安裝，正在安裝..."
        if command -v brew &> /dev/null; then
            brew install socat
        else
            log_error "請先安裝 Homebrew，然後執行: brew install socat"
            exit 1
        fi
    fi
    
    # 檢查 53 端口是否被占用
    if lsof -i :53 -sTCP:LISTEN &> /dev/null; then
        log_warn "端口 53 已被占用，正在檢查..."
        lsof -i :53 -sTCP:LISTEN
        log_warn "請先停止占用 53 端口的服務（例如 mDNSResponder）"
        log_info "可以執行: sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist"
        exit 1
    fi
    
    log_info "啟動 socat port forward (53 -> 127.0.0.1:5300)..."
    
    # 啟動 socat（UDP 和 TCP）
    socat UDP4-LISTEN:53,fork,reuseaddr UDP4:127.0.0.1:5300 &
    SOCAT_UDP_PID=$!
    echo $SOCAT_UDP_PID > /tmp/dns-forward-udp.pid
    
    socat TCP4-LISTEN:53,fork,reuseaddr TCP4:127.0.0.1:5300 &
    SOCAT_TCP_PID=$!
    echo $SOCAT_TCP_PID > /tmp/dns-forward-tcp.pid
    
    log_success "socat port forward 已啟動"
    log_info "UDP PID: $SOCAT_UDP_PID"
    log_info "TCP PID: $SOCAT_TCP_PID"
    log_info "PID 已保存到 /tmp/dns-forward-*.pid"
    
    # 測試
    sleep 1
    if dig @127.0.0.1 app.example.com +short &> /dev/null; then
        log_success "Port forward 測試成功！"
    else
        log_warn "Port forward 可能未正常工作，請檢查"
    fi
}

# 方法 2: 修改 docker-compose.yml 讓 DNS 直接監聽 53 端口
setup_docker_direct() {
    log_info "設定方法 2: 修改 Docker 配置讓 DNS 直接監聽 53 端口"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
    COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
    
    # 備份原始文件
    cp "${COMPOSE_FILE}" "${COMPOSE_FILE}.backup.$(date +%s)"
    
    # 修改 port mapping
    log_info "修改 docker-compose.yml..."
    sed -i '' 's/"5300:53\//"53:53\//g' "${COMPOSE_FILE}"
    
    log_success "docker-compose.yml 已修改"
    log_info "請執行: cd ${PROJECT_ROOT} && docker-compose up -d dns-secondary"
    log_warn "注意：53 端口需要 root 權限，Docker 可能需要特殊配置"
}

# 停止 port forward
stop_forward() {
    log_info "停止 port forward..."
    
    if [ -f /tmp/dns-forward-udp.pid ]; then
        UDP_PID=$(cat /tmp/dns-forward-udp.pid)
        if kill -0 $UDP_PID 2>/dev/null; then
            kill $UDP_PID
            log_success "已停止 UDP forward (PID: $UDP_PID)"
        fi
        rm -f /tmp/dns-forward-udp.pid
    fi
    
    if [ -f /tmp/dns-forward-tcp.pid ]; then
        TCP_PID=$(cat /tmp/dns-forward-tcp.pid)
        if kill -0 $TCP_PID 2>/dev/null; then
            kill $TCP_PID
            log_success "已停止 TCP forward (PID: $TCP_PID)"
        fi
        rm -f /tmp/dns-forward-tcp.pid
    fi
    
    # 殺掉所有 socat 進程（備用）
    pkill -f "socat.*53.*5300" 2>/dev/null && log_info "已清理所有相關 socat 進程"
}

# 主函數
main() {
    case "${1:-}" in
        start)
            check_root
            setup_socat_forward
            ;;
        stop)
            check_root
            stop_forward
            ;;
        docker)
            check_root
            setup_docker_direct
            ;;
        *)
            echo "用法: $0 {start|stop|docker}"
            echo ""
            echo "  start  - 使用 socat 啟動 port forward (53 -> 5300)"
            echo "  stop   - 停止 port forward"
            echo "  docker - 修改 docker-compose.yml 讓 DNS 直接監聽 53 端口"
            echo ""
            echo "推薦使用方法 1 (start)，較簡單且不影響 Docker 配置"
            exit 1
            ;;
    esac
}

main "$@"

