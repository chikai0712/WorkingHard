#!/bin/bash

# 寶可夢對戰遊戲 - 快速啟動腳本

cd "$(dirname "$0")"

# 檢查虛擬環境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虛擬環境不存在！"
    echo "請先執行: bash setup.sh"
    exit 1
fi

# 啟動虛擬環境
source venv/bin/activate

# 檢查 Pygame 是否已安裝
python -c "import pygame" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Pygame 未安裝！"
    echo "請先執行: bash setup.sh"
    exit 1
fi

# 運行遊戲
echo "🎮 啟動寶可夢對戰遊戲..."
echo ""
python main.py

# 遊戲結束後退出虛擬環境
deactivate

