#!/bin/bash

# Cursor 友好的更新腳本
# 自動在系統終端執行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 準備更新 Globalping Checker..."
echo ""

# 創建臨時腳本
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << EOF
#!/bin/bash

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

cd "$SCRIPT_DIR"

echo "========================================"
echo "更新 Globalping Checker 代碼"
echo "========================================"
echo ""

./update-globalping-code.sh

echo ""
echo "按 Enter 關閉此視窗..."
read
EOF

chmod +x "$TEMP_SCRIPT"

# 在新的終端視窗執行
osascript -e "tell application \"Terminal\" to do script \"$TEMP_SCRIPT\""

echo "✅ 已在系統終端開啟更新程序"
echo ""
