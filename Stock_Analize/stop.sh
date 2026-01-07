#!/bin/bash

# 股票資訊儀表板停止腳本

echo "🛑 停止股票資訊儀表板系統..."

# 讀取 PID
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🛑 停止後端服務 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "✅ 後端已停止"
    else
        echo "⚠️  後端服務未運行"
    fi
    rm -f logs/backend.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🛑 停止前端服務 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "✅ 前端已停止"
    else
        echo "⚠️  前端服務未運行"
    fi
    rm -f logs/frontend.pid
fi

echo "✅ 所有服務已停止"

