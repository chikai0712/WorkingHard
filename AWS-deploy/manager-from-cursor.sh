#!/bin/bash

# Cursor 友好的管理界面
# 自動在系統終端執行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎛️  開啟 AWS 管理界面..."
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
./aws-manager.sh
EOF

chmod +x "$TEMP_SCRIPT"

# 在新的終端視窗執行
osascript -e "tell application \"Terminal\" to do script \"$TEMP_SCRIPT\""

echo "✅ 已在系統終端開啟管理界面"
echo ""
echo "在新視窗中可以："
echo "  • 部署新服務"
echo "  • 檢查狀態"
echo "  • 更新代碼"
echo "  • 管理實例"
echo ""
