#!/bin/bash

# 修正資料庫連接問題

echo "🔧 修正資料庫連接設定..."

cd /Users/ckchiu/Desktop/Project/domain-monitoring-system

# 建立正確的 .env 檔案
cat > .env << 'EOF'
# Database Configuration (use 'postgres' as host in Docker)
DATABASE_URL=postgresql://dms_user:dms_password@postgres:5432/domain_monitoring

# Redis Configuration (use 'redis' as host in Docker)
REDIS_URL=redis://redis:6379/0

# SecurityTrails API
SECURITYTRAILS_API_KEY=your_api_key_here

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
CHECK_INTERVAL=300

# UptimeRobot (Optional)
UPTIMEROBOT_API_KEY=your_uptimerobot_key
EOF

echo "✅ .env 檔案已更新"

# 重啟服務
echo "🔄 重啟服務..."
docker-compose restart api celery-worker celery-beat

echo "⏳ 等待服務啟動..."
sleep 5

# 執行資料庫遷移
echo "📊 執行資料庫遷移..."
docker-compose exec -T api alembic upgrade head

# 初始化範例資料
echo "📝 初始化範例資料..."
docker-compose exec -T api python init_data.py

echo ""
echo "✅ 修正完成!"
echo "📍 訪問 API 文件: http://localhost:8000/docs"

