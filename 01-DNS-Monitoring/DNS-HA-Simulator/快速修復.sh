#!/bin/bash
# ============================================
# DNS Port Forward 快速修復（一鍵執行）
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "DNS Port Forward 快速修復"
echo "=========================================="
echo ""
echo "此腳本將："
echo "  1. 停止現有的 port forward"
echo "  2. 停止 mDNSResponder"
echo "  3. 重新啟動 port forward"
echo ""
echo "⚠️  需要輸入您的 macOS 用戶密碼"
echo ""
read -p "按 Enter 繼續，或 Ctrl+C 取消..."

exec "$SCRIPT_DIR/scripts/fix-dns-port-easy.sh"

