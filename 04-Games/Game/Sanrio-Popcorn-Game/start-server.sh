#!/bin/bash

# 三麗鷗爆米花大遊行 - 外部訪問伺服器啟動腳本

echo "🎀 啟動三麗鷗爆米花大遊行伺服器..."
echo ""

# 獲取本機 IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

echo "📡 本機 IP 位址: $LOCAL_IP"
echo "🌐 外部訪問網址: http://$LOCAL_IP:8888"
echo ""
echo "⚠️  請確保："
echo "   1. 防火牆允許 8888 端口"
echo "   2. 路由器已設置端口轉發（如需外網訪問）"
echo ""
echo "🎮 伺服器啟動中..."
echo "   按 Ctrl+C 停止伺服器"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 啟動 Python HTTP 伺服器，綁定到所有網路介面
cd "$(dirname "$0")"
python3 -m http.server 8888 --bind 0.0.0.0

