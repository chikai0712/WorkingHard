#!/bin/bash
# ============================================
# 修復 DNS Port Forward 問題
# 強制停止 mDNSResponder 並重新啟動 port forward
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
if [ "$EUID" -ne 0 ]; then
    log_error "此腳本需要 root 權限"
    echo ""
    echo "請執行: sudo $0"
    exit 1
fi

log_info "=========================================="
log_info "修復 DNS Port Forward"
log_info "=========================================="

# 步驟 1: 停止所有現有的 port forward
log_info "步驟 1: 停止現有的 port forward..."
if [ -f /tmp/dns-forward-udp.pid ]; then
    UDP_PID=$(cat /tmp/dns-forward-udp.pid)
    kill $UDP_PID 2>/dev/null && log_success "已停止 UDP forward (PID: $UDP_PID)" || log_warn "UDP forward 進程不存在"
    rm -f /tmp/dns-forward-udp.pid
fi

if [ -f /tmp/dns-forward-tcp.pid ]; then
    TCP_PID=$(cat /tmp/dns-forward-tcp.pid)
    kill $TCP_PID 2>/dev/null && log_success "已停止 TCP forward (PID: $TCP_PID)" || log_warn "TCP forward 進程不存在"
    rm -f /tmp/dns-forward-tcp.pid
fi

# 殺掉所有相關的 socat 進程
pkill -f "socat.*53.*5300" 2>/dev/null && log_info "已清理所有相關 socat 進程" || true
sleep 1

# 步驟 2: 強制停止 mDNSResponder
log_info "步驟 2: 停止 mDNSResponder..."
launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist 2>/dev/null || true
killall mDNSResponder 2>/dev/null || true
killall mDNSResponderHelper 2>/dev/null || true
sleep 3

# 步驟 3: 檢查並強制釋放 53 端口
log_info "步驟 3: 檢查並釋放 53 端口..."

# 函數：強制釋放 53 端口
force_release_port() {
    local retry=0
    local max_retries=10
    local quiet=${1:-false}  # 可選參數：是否靜默輸出
    
    while [ $retry -lt $max_retries ]; do
        # 檢查所有占用 53 端口的進程（TCP 和 UDP）
        local pids=$(lsof -i :53 2>/dev/null | awk 'NR>1 {print $2}' | sort -u)
        
        if [ -z "$pids" ]; then
            [ "$quiet" != "true" ] && log_success "端口 53 已釋放"
            return 0  # 端口已釋放
        fi
        
        if [ "$quiet" != "true" ]; then
            log_warn "檢測到占用 53 端口的進程: $pids"
        fi
        
        # 強制殺掉所有占用端口的進程
        echo "$pids" | xargs kill -9 2>/dev/null || true
        
        # 再次檢查 mDNSResponder 並停止
        killall mDNSResponder 2>/dev/null || true
        killall mDNSResponderHelper 2>/dev/null || true
        launchctl unload -w /System/Library/LaunchDaemons/com.apple.mDNSResponder.plist 2>/dev/null || true
        
        sleep 1
        retry=$((retry + 1))
    done
    
    # 最後檢查
    if lsof -i :53 2>/dev/null | grep -q .; then
        if [ "$quiet" != "true" ]; then
            log_error "無法完全釋放 53 端口："
            lsof -i :53 2>/dev/null
        fi
        return 1
    fi
    
    [ "$quiet" != "true" ] && log_success "端口 53 已釋放"
    return 0
}

# 執行強制釋放
force_release_port || exit 1

log_success "端口 53 已釋放"

# 步驟 4: 啟動 port forward（啟動前再次檢查並強制釋放）
log_info "步驟 4: 啟動 port forward (53 -> 127.0.0.1:5300)..."

# 啟動前最後一次檢查並強制釋放
log_info "啟動前最後檢查 53 端口..."
force_release_port || {
    log_error "無法釋放 53 端口，詳細信息："
    lsof -i :53 2>/dev/null
    exit 1
}

# 啟動 UDP forward（使用重試機制）
log_info "啟動 UDP forward..."
UDP_STARTED=false
for retry in {1..5}; do
    # 每次重試前都強制釋放端口
    if [ $retry -gt 1 ]; then
        log_warn "重試啟動 UDP forward (嘗試 $retry/5)..."
        force_release_port
        sleep 1
    fi
    
    # 啟動前最後檢查
    if lsof -i :53 2>/dev/null | grep -q .; then
        log_warn "檢測到端口仍被占用，強制釋放..."
        force_release_port
        sleep 1
    fi
    
    # 嘗試啟動
    nohup socat UDP4-LISTEN:53,fork,reuseaddr UDP4:127.0.0.1:5300 > /tmp/socat-udp.log 2>&1 &
    UDP_PID=$!
    sleep 1
    
    # 檢查是否成功啟動
    if kill -0 $UDP_PID 2>/dev/null; then
        # 驗證端口是否真的被我們占用
        sleep 0.5
        PORT_CHECK=$(lsof -i :53 -sUDP:LISTEN 2>/dev/null | grep -E "socat|$UDP_PID" | head -1)
        if [ -n "$PORT_CHECK" ]; then
            echo $UDP_PID > /tmp/dns-forward-udp.pid
            UDP_STARTED=true
            log_success "UDP forward 啟動成功 (PID: $UDP_PID)"
            break
        else
            log_warn "UDP forward 進程存在但未占用端口，清理並重試..."
            kill $UDP_PID 2>/dev/null || true
            force_release_port
        fi
    else
        log_warn "UDP forward 啟動失敗，查看錯誤："
        cat /tmp/socat-udp.log 2>/dev/null | tail -3 || true
        force_release_port
    fi
done

if [ "$UDP_STARTED" != "true" ]; then
    log_error "UDP forward 啟動失敗（已重試 5 次）"
    log_error "錯誤日誌："
    cat /tmp/socat-udp.log 2>/dev/null || true
    log_error "當前端口占用情況："
    lsof -i :53 2>/dev/null || true
    exit 1
fi

# 啟動 TCP forward（使用重試機制）
log_info "啟動 TCP forward..."
TCP_STARTED=false
for retry in {1..5}; do
    # 每次重試前都強制釋放端口
    if [ $retry -gt 1 ]; then
        log_warn "重試啟動 TCP forward (嘗試 $retry/5)..."
        force_release_port
        sleep 1
    fi
    
    # 啟動前最後檢查
    if lsof -i :53 2>/dev/null | grep -q .; then
        log_warn "檢測到端口仍被占用，強制釋放..."
        force_release_port
        sleep 1
    fi
    
    # 嘗試啟動
    nohup socat TCP4-LISTEN:53,fork,reuseaddr TCP4:127.0.0.1:5300 > /tmp/socat-tcp.log 2>&1 &
    TCP_PID=$!
    sleep 1
    
    # 檢查是否成功啟動
    if kill -0 $TCP_PID 2>/dev/null; then
        # 驗證端口是否真的被我們占用
        sleep 0.5
        PORT_CHECK=$(lsof -i :53 -sTCP:LISTEN 2>/dev/null | grep -E "socat|$TCP_PID" | head -1)
        if [ -n "$PORT_CHECK" ]; then
            echo $TCP_PID > /tmp/dns-forward-tcp.pid
            TCP_STARTED=true
            log_success "TCP forward 啟動成功 (PID: $TCP_PID)"
            break
        else
            log_warn "TCP forward 進程存在但未占用端口，清理並重試..."
            kill $TCP_PID 2>/dev/null || true
            force_release_port
        fi
    else
        log_warn "TCP forward 啟動失敗，查看錯誤："
        cat /tmp/socat-tcp.log 2>/dev/null | tail -3 || true
        force_release_port
    fi
done

if [ "$TCP_STARTED" != "true" ]; then
    log_error "TCP forward 啟動失敗（已重試 5 次）"
    log_error "錯誤日誌："
    cat /tmp/socat-tcp.log 2>/dev/null || true
    log_error "當前端口占用情況："
    lsof -i :53 2>/dev/null || true
    # 清理已啟動的 UDP
    kill $UDP_PID 2>/dev/null || true
    rm -f /tmp/dns-forward-udp.pid
    exit 1
fi

sleep 2

# 驗證端口是否被我們的進程占用
log_info "驗證端口占用情況..."
PORT_OWNER=$(lsof -i :53 2>/dev/null | awk 'NR>1 {print $2}' | sort -u)
if [ -n "$PORT_OWNER" ]; then
    # 檢查是否都是我們的進程
    for pid in $PORT_OWNER; do
        if [ "$pid" != "$UDP_PID" ] && [ "$pid" != "$TCP_PID" ]; then
            log_warn "檢測到其他進程占用 53 端口 (PID: $pid)，嘗試清理..."
            kill -9 $pid 2>/dev/null || true
            sleep 1
        fi
    done
fi

# 步驟 5: 驗證
log_info "步驟 5: 驗證 port forward..."
if kill -0 $UDP_PID 2>/dev/null && kill -0 $TCP_PID 2>/dev/null; then
    log_success "Port forward 已啟動"
    log_info "UDP PID: $UDP_PID"
    log_info "TCP PID: $TCP_PID"
    
    # 測試連接
    log_info "測試 DNS 查詢..."
    if dig @127.0.0.1 -p 53 app.example.com +time=2 +tries=1 +short 2>&1 | grep -q "172.20.0"; then
        log_success "DNS 查詢測試成功！"
    else
        log_warn "DNS 查詢測試失敗，但 port forward 已啟動"
        log_info "請手動測試: dig app.example.com"
    fi
else
    log_error "Port forward 啟動失敗"
    exit 1
fi

echo ""
log_info "=========================================="
log_info "修復完成！"
log_info "=========================================="
log_info "請確保 macOS DNS 設定為 127.0.0.1"
log_info "然後執行: sudo killall -HUP mDNSResponder"
log_info "測試: dig app.example.com"
log_info "=========================================="

