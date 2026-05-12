#!/bin/bash

# 快速啟動腳本

echo "🚀 啟動 Domain Monitoring System..."

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝,請先安裝 Docker"
    exit 1
fi

# 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "📝 建立 .env 檔案..."
    cp env.example .env
    echo "⚠️  請編輯 .env 檔案填入必要的 API Keys"
    echo "   - SECURITYTRAILS_API_KEY"
    echo "   - SLACK_WEBHOOK_URL"
    exit 1
fi

# 啟動服務
echo "🐳 啟動 Docker 容器..."
docker-compose up -d

# 等待資料庫啟動
echo "⏳ 等待資料庫啟動..."
sleep 10

# 執行資料庫遷移
echo "📊 初始化資料庫..."
docker-compose exec -T api alembic upgrade head

# 顯示服務狀態
echo ""
echo "✅ 服務啟動完成!"
echo ""
echo "📍 API 服務: http://localhost:8000"
echo "📍 API 文件: http://localhost:8000/docs"
echo ""
echo "查看日誌: docker-compose logs -f api"
echo "停止服務: docker-compose down"

