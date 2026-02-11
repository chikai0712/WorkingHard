#!/bin/bash

# 🏰 爆米花王國 - 快速啟動腳本

echo "🏰 啟動爆米花王國..."
echo ""
echo "遊戲將在瀏覽器中打開"
echo "伺服器地址：http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止伺服器"
echo ""

# 啟動 Python HTTP 伺服器
python3 -m http.server 8000

