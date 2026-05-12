#!/bin/bash

# Cursor 友好的部署腳本
# 自動在系統終端執行，避免代理問題

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 準備部署 Globalping Checker..."
echo ""
echo "由於 Cursor 代理限制，將在系統終端執行部署"
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
echo "Globalping Checker 部署"
echo "========================================"
echo ""

# 執行部署
./deploy-globalping-checker.sh

echo ""
echo "按 Enter 關閉此視窗..."
read
EOF

chmod +x "$TEMP_SCRIPT"

# 在新的終端視窗執行
osascript -e "tell application \"Terminal\" to do script \"$TEMP_SCRIPT\""

echo "✅ 已在系統終端開啟部署程序"
echo ""
echo "請在新開啟的終端視窗中："
echo "  1. 查看部署進度"
echo "  2. 選擇更新或重建實例"
echo "  3. 等待部署完成"
echo ""
