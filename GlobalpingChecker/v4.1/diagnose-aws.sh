#!/bin/bash

# 診斷 AWS 上的 GlobalpingChecker V4.1

echo "🔍 診斷 GlobalpingChecker V4.1"
echo "================================"
echo ""

AWS_HOST="54.238.247.106"
SSH_KEY="$HOME/.ssh/globalping-checker-key.pem"

# 檢測用戶名
if ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$AWS_HOST "echo 'test'" 2>/dev/null; then
    AWS_USER="ubuntu"
elif ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$AWS_HOST "echo 'test'" 2>/dev/null; then
    AWS_USER="ec2-user"
else
    echo "❌ 無法連接到 AWS"
    exit 1
fi

echo "✅ SSH 連接成功 (用戶: $AWS_USER)"
echo ""

# 執行診斷
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
echo "📊 檢查服務狀態..."
cd ~/globalping-v4.1 2>/dev/null || cd ~/v4.1 2>/dev/null || { echo "❌ 找不到應用目錄"; exit 1; }

echo ""
echo "1️⃣ Docker 容器狀態:"
docker-compose ps

echo ""
echo "2️⃣ 最近日誌 (最後 20 行):"
docker-compose logs --tail=20

echo ""
echo "3️⃣ 數據庫檢查:"
if [ -f "data/globalping_results.db" ]; then
    echo "✅ 數據庫文件存在"
    sqlite3 data/globalping_results.db << 'EOF'
.mode column
.headers on
SELECT COUNT(*) as batch_count FROM test_batches;
SELECT COUNT(*) as domain_count FROM domains;
SELECT COUNT(*) as result_count FROM domain_results;
EOF
else
    echo "❌ 數據庫文件不存在"
fi

echo ""
echo "4️⃣ API 測試:"
curl -s http://localhost:8000/api/stats | python3 -m json.tool 2>/dev/null || echo "❌ API 無響應"

ENDSSH

echo ""
echo "================================"
echo "診斷完成"
