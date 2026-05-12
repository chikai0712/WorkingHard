#!/bin/bash
# ============================================
# DNS Port Forward 修復腳本（簡化版）
# 自動處理 sudo 權限緩存
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

# 檢查並緩存 sudo 權限
check_sudo() {
    log_info "檢查 sudo 權限..."
    
    # 嘗試緩存 sudo 權限（有效期約 5 分鐘）
    if sudo -v 2>/dev/null; then
        log_success "sudo 權限已緩存（5 分鐘內有效）"
        return 0
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_warn "⚠️  需要輸入密碼以獲取 sudo 權限"
    echo ""
    log_info "請在下方輸入您的 macOS 用戶密碼："
    echo "  （輸入時不會顯示，這是正常的安全機制）"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if sudo -v; then
        echo ""
        log_success "✅ sudo 權限已獲取並緩存（5 分鐘內有效）"
        return 0
    else
        echo ""
        log_error "❌ 無法獲取 sudo 權限"
        log_error "   請確認密碼輸入正確，或按 Ctrl+C 取消"
        exit 1
    fi
}

# 保持 sudo 權限有效（在後台運行）
keep_sudo_alive() {
    while true; do
        sleep 60
        sudo -v 2>/dev/null || break
    done
}

log_info "=========================================="
log_info "DNS Port Forward 修復工具"
log_info "=========================================="
echo ""

# 檢查並獲取 sudo 權限
check_sudo

# 在背景保持 sudo 權限有效
keep_sudo_alive &
KEEP_ALIVE_PID=$!

# 清理函數
cleanup() {
    kill $KEEP_ALIVE_PID 2>/dev/null || true
}
trap cleanup EXIT

echo ""
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "開始執行修復操作..."
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 執行實際的修復腳本
# 注意：如果 sudo 權限過期，這裡可能會再次要求輸入密碼
exec sudo "$SCRIPT_DIR/fix-dns-port.sh"

