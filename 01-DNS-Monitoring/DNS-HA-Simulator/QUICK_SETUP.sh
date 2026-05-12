#!/bin/bash
# ============================================
# DNS Port Forward 快速設定腳本
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
if [ "$EUID" -ne 0 ]; then
    log_error "此腳本需要 root 權限"
    echo ""
    echo "請執行: sudo $0"
    exit 1
fi

log_info "=========================================="
log_info "DNS Port Forward 設定"
log_info "=========================================="

# 步驟 1: 檢查 socat
if ! command -v socat &> /dev/null; then
    log_error "socat 未安裝"
    echo ""
    echo "請先執行: brew install socat"
    echo "然後再執行此腳本"
    exit 1
fi

log_success "socat 已安裝"

# 步驟 2: 檢查 53 端口
if lsof -i :53 -sTCP:LISTEN &> /dev/null; then
    log_warn "端口 53 已被占用"
    log_info "正在停止 mDNSResponder..."
    launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist 2>/dev/null || true
    sleep 2
    
    if lsof -i :53 -sTCP:LISTEN &> /dev/null; then
        log_error "無法釋放 53 端口"
        lsof -i :53 -sTCP:LISTEN
        exit 1
    fi
fi

log_success "端口 53 已釋放"

# 步驟 3: 檢查是否已有 port forward 在運行
if [ -f /tmp/dns-forward-udp.pid ]; then
    UDP_PID=$(cat /tmp/dns-forward-udp.pid)
    if kill -0 $UDP_PID 2>/dev/null; then
        log_warn "Port forward 已在運行 (PID: $UDP_PID)"
        log_info "正在停止舊的 port forward..."
        kill $UDP_PID 2>/dev/null || true
        rm -f /tmp/dns-forward-udp.pid
    fi
fi

if [ -f /tmp/dns-forward-tcp.pid ]; then
    TCP_PID=$(cat /tmp/dns-forward-tcp.pid)
    if kill -0 $TCP_PID 2>/dev/null; then
        kill $TCP_PID 2>/dev/null || true
        rm -f /tmp/dns-forward-tcp.pid
    fi
fi

# 步驟 4: 啟動 port forward
log_info "啟動 port forward (53 -> 127.0.0.1:5300)..."

# UDP
socat UDP4-LISTEN:53,fork,reuseaddr UDP4:127.0.0.1:5300 &
UDP_PID=$!
echo $UDP_PID > /tmp/dns-forward-udp.pid

# TCP
socat TCP4-LISTEN:53,fork,reuseaddr TCP4:127.0.0.1:5300 &
TCP_PID=$!
echo $TCP_PID > /tmp/dns-forward-tcp.pid

sleep 1

# 檢查是否成功啟動
if kill -0 $UDP_PID 2>/dev/null && kill -0 $TCP_PID 2>/dev/null; then
    log_success "Port forward 已啟動"
    log_info "UDP PID: $UDP_PID"
    log_info "TCP PID: $TCP_PID"
    echo ""
    log_info "=========================================="
    log_info "下一步："
    log_info "=========================================="
    log_info "1. 設定 macOS DNS:"
    log_info "   系統設定 > 網路 > Wi-Fi > 詳細資訊 > DNS"
    log_info "   新增: 127.0.0.1"
    log_info ""
    log_info "2. 清空 DNS cache:"
    log_info "   sudo killall -HUP mDNSResponder"
    log_info ""
    log_info "3. 測試 DNS:"
    log_info "   dig app.example.com"
    log_info ""
    log_info "4. 測試完成後恢復:"
    log_info "   sudo ./scripts/setup-dns-forward.sh stop"
    log_info "   sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist"
    log_info "=========================================="
else
    log_error "Port forward 啟動失敗"
    exit 1
fi

