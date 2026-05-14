#!/bin/bash

# Cursor 友好的狀態檢查 - 簡化版

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 檢查 AWS 狀態..."
echo ""

# 創建臨時腳本
TEMP_SCRIPT="$SCRIPT_DIR/.temp_check_status.sh"
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

cd "$(dirname "$0")"
./check-status.sh

echo ""
echo "按 Enter 關閉此視窗..."
read
EOF

chmod +x "$TEMP_SCRIPT"

# 使用 open 命令在新終端執行
open -a Terminal "$TEMP_SCRIPT"

echo "✅ 已在系統終端開啟狀態檢查"
echo ""
echo "請查看新開啟的終端視窗"
echo ""
