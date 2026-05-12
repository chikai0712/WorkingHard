#!/bin/bash

# 一鍵開啟系統終端並執行檢查

echo "🚀 正在開啟系統終端..."
echo ""
echo "請在新開啟的終端視窗中查看結果"
echo ""

# 創建臨時腳本
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash

# 禁用所有代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

cd ~/Desktop/Project/AWS-deploy
./check-status.sh

echo ""
echo "按 Enter 關閉此視窗..."
read
EOF

chmod +x "$TEMP_SCRIPT"

# 在新的終端視窗執行
osascript <<END
tell application "Terminal"
    activate
    do script "$TEMP_SCRIPT"
end tell
END

echo "✅ 已開啟新終端視窗"
