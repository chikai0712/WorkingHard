#!/bin/bash

# 寶可夢對戰遊戲 - 自動安裝腳本
# 此腳本會自動設置環境並安裝所需套件

echo "=========================================="
echo "🎮 寶可夢對戰遊戲 - 環境設置"
echo "=========================================="
echo ""

# 進入專案目錄
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
echo "📁 專案目錄: $PROJECT_DIR"
echo ""

# 檢查 Python 版本
echo "🔍 檢查 Python 版本..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "   $PYTHON_VERSION"
echo ""

# 創建虛擬環境
echo "📦 創建虛擬環境..."
if [ -d "venv" ]; then
    echo "   ⚠️  虛擬環境已存在，跳過創建"
else
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "   ✅ 虛擬環境創建成功"
    else
        echo "   ❌ 虛擬環境創建失敗"
        exit 1
    fi
fi
echo ""

# 啟動虛擬環境
echo "🚀 啟動虛擬環境..."
source venv/bin/activate
if [ $? -eq 0 ]; then
    echo "   ✅ 虛擬環境已啟動"
else
    echo "   ❌ 虛擬環境啟動失敗"
    exit 1
fi
echo ""

# 升級 pip
echo "⬆️  升級 pip..."
pip install --upgrade pip > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ pip 升級成功"
else
    echo "   ⚠️  pip 升級失敗，繼續安裝..."
fi
echo ""

# 安裝 Pygame
echo "🎮 安裝 Pygame..."
pip install pygame
if [ $? -eq 0 ]; then
    echo "   ✅ Pygame 安裝成功"
else
    echo "   ❌ Pygame 安裝失敗"
    exit 1
fi
echo ""

# 驗證安裝
echo "✅ 驗證安裝..."
python -c "import pygame; print('   Pygame 版本:', pygame.version.ver)"
if [ $? -eq 0 ]; then
    echo "   ✅ Pygame 可以正常使用"
else
    echo "   ❌ Pygame 無法正常使用"
    exit 1
fi
echo ""

# 創建資源目錄
echo "📁 創建資源目錄..."
mkdir -p assets/images
mkdir -p assets/audio
if [ $? -eq 0 ]; then
    echo "   ✅ 資源目錄創建成功"
    echo "   📂 assets/images/ - 請放入寶可夢圖片"
    echo "   📂 assets/audio/ - 請放入背景音樂"
else
    echo "   ❌ 資源目錄創建失敗"
fi
echo ""

# 檢查資源文件
echo "🔍 檢查資源文件..."
IMAGE_COUNT=$(ls -1 assets/images/*.png 2>/dev/null | wc -l | tr -d ' ')
AUDIO_COUNT=$(ls -1 assets/audio/*.mp3 2>/dev/null | wc -l | tr -d ' ')

echo "   圖片文件: $IMAGE_COUNT / 7"
echo "   音樂文件: $AUDIO_COUNT / 1"

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "   ⚠️  尚未放入圖片文件（遊戲仍可運行，會顯示灰色方塊）"
fi

if [ "$AUDIO_COUNT" -eq 0 ]; then
    echo "   ⚠️  尚未放入音樂文件（遊戲仍可運行，但沒有音樂）"
fi
echo ""

# 完成
echo "=========================================="
echo "✅ 環境設置完成！"
echo "=========================================="
echo ""
echo "📝 接下來的步驟："
echo ""
echo "1️⃣  啟動虛擬環境（每次運行遊戲前都要執行）："
echo "   source venv/bin/activate"
echo ""
echo "2️⃣  運行遊戲："
echo "   python main.py"
echo ""
echo "3️⃣  退出虛擬環境（遊戲結束後）："
echo "   deactivate"
echo ""
echo "💡 提示："
echo "   - 如果沒有圖片，遊戲會使用灰色方塊代替"
echo "   - 如果沒有音樂，遊戲會靜音運行"
echo "   - 遊戲邏輯不受影響，可以正常遊玩"
echo ""
echo "🎮 現在就可以運行遊戲了！"
echo "   python main.py"
echo ""

