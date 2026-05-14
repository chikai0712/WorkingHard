#!/bin/bash

# 股票資訊儀表板啟動腳本

echo "🚀 啟動股票資訊儀表板系統..."
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到 Python3，請先安裝 Python 3.10+"
    exit 1
fi

# 檢查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 錯誤: 未找到 Node.js，請先安裝 Node.js 16+"
    exit 1
fi

echo "✅ 環境檢查通過"
echo ""

# 啟動後端
echo "📦 啟動後端服務..."
cd backend

# matplotlib cache 目錄（避免權限警告）
export MPLCONFIGDIR=/tmp/mpl_cache
mkdir -p /tmp/mpl_cache

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "📦 建立 Python 虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴（如果還沒安裝）
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "📦 安裝後端依賴..."
    pip install -r requirements.txt
fi

# 檢查 .env 檔案
if [ ! -f ".env" ]; then
    echo "⚙️  建立 .env 檔案..."
    cp .env.example .env
    echo "✅ .env 檔案已建立，請編輯以調整設定（可選）"
fi

# 在背景啟動後端
echo "🚀 啟動後端服務 (http://localhost:8000)..."
python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 後端已啟動 (PID: $BACKEND_PID)"

cd ..

# 等待後端啟動
sleep 3

# 啟動前端
echo ""
echo "🎨 啟動前端服務..."
cd frontend

# 安裝依賴（如果還沒安裝）
if [ ! -d "node_modules" ]; then
    echo "📦 安裝前端依賴..."
    npm install
fi

# 檢查 .env 檔案
if [ ! -f ".env" ]; then
    echo "⚙️  建立 .env 檔案..."
    cp .env.example .env
fi

# 在背景啟動前端
echo "🚀 啟動前端服務 (http://localhost:5173)..."
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端已啟動 (PID: $FRONTEND_PID)"

cd ..

# 建立 logs 目錄
mkdir -p logs

# 儲存 PID
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ 股票資訊儀表板系統已啟動！"
echo ""
echo "📊 前端儀表板: http://localhost:5173"
echo "🔌 後端 API:   http://localhost:8000"
echo "📖 API 文件:   http://localhost:8000/docs"
echo ""
echo "🛑 停止服務: ./stop.sh"
echo "📋 查看日誌: tail -f logs/backend.log 或 logs/frontend.log"
echo "═══════════════════════════════════════════════════════"

