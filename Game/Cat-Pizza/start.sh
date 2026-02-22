#!/bin/bash

# 貓咪披薩店 - 啟動腳本

echo "🐱🍕 啟動貓咪披薩店..."
echo ""

# 檢查是否有 Python
if command -v python3 &> /dev/null; then
    echo "使用 Python 啟動本地伺服器..."
    echo "遊戲網址: http://localhost:8000"
    echo "按 Ctrl+C 停止伺服器"
    echo ""
    python3 -m http.server 8000
# 檢查是否有 Node.js
elif command -v npx &> /dev/null; then
    echo "使用 Node.js 啟動本地伺服器..."
    echo "遊戲網址: http://localhost:8000"
    echo "按 Ctrl+C 停止伺服器"
    echo ""
    npx http-server -p 8000
else
    echo "❌ 找不到 Python 或 Node.js"
    echo "請直接在瀏覽器中打開 index.html"
    echo ""
    # 嘗試直接打開瀏覽器
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open index.html
    fi
fi

