#!/bin/bash

# ============================================
# V4.1 部署到 AWS 腳本
# 包含：API_ERROR 處理 + GMT+8 時區
# ============================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
AWS_HOST="54.238.247.106"
AWS_USER="ubuntu"
SSH_KEY="$HOME/.ssh/globalping-checker-key.pem"
LOCAL_DIR="$HOME/Desktop/Project/GlobalpingChecker/v4.1"
REMOTE_DIR="/home/ubuntu/v4.1"

echo -e "${BLUE}========================================"
echo "V4.1 部署到 AWS"
echo "========================================${NC}"
echo "目標: $AWS_USER@$AWS_HOST"
echo "本地目錄: $LOCAL_DIR"
echo ""

# 步驟 1：打包代碼
echo -e "${GREEN}步驟 1/5: 打包 V4.1 代碼...${NC}"
cd "$LOCAL_DIR/.."
tar -czf v4.1-deploy.tar.gz \
    --exclude='v4.1/__pycache__' \
    --exclude='v4.1/app/__pycache__' \
    --exclude='v4.1/.env' \
    v4.1/

echo "✅ 打包完成: v4.1-deploy.tar.gz"
echo ""

# 步驟 2：上傳到 AWS
echo -e "${GREEN}步驟 2/5: 上傳到 AWS...${NC}"
scp -i "$SSH_KEY" v4.1-deploy.tar.gz "$AWS_USER@$AWS_HOST:~/"

if [ $? -eq 0 ]; then
    echo "✅ 上傳成功"
else
    echo -e "${RED}❌ 上傳失敗${NC}"
    exit 1
fi
echo ""

# 步驟 3：在 AWS 上部署
echo -e "${GREEN}步驟 3/5: 在 AWS 上部署...${NC}"
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
set -e

echo "📦 停止當前服務..."
cd ~/v4.1 2>/dev/null || true
docker-compose down 2>/dev/null || true

echo "💾 備份當前版本..."
cd ~
if [ -d "v4.1" ]; then
    mv v4.1 v4.1-backup-$(date +%Y%m%d-%H%M%S)
fi

echo "📂 解壓新版本..."
tar -xzf v4.1-deploy.tar.gz

echo "⚙️  配置環境變數..."
cd v4.1

# 檢查 .env 文件
if [ ! -f ".env" ]; then
    echo "創建 .env 文件..."
    cat > .env << 'EOF'
# Globalping API Token
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5

# PostgreSQL 密碼
POSTGRES_PASSWORD=globalping_secure_password

# 檢測間隔（分鐘）
CHECK_INTERVAL_MINUTES=90

# 異常區檢測時間（小時，24小時制）
ABNORMAL_CHECK_HOUR=1

# 正常區檢測時間（小時，24小時制）
NORMAL_CHECK_HOUR=9

# 最大迭代次數（異常區）
MAX_ITERATIONS=10
EOF
fi

echo "✅ 部署準備完成"
ENDSSH

echo "✅ 部署完成"
echo ""

# 步驟 4：啟動服務
echo -e "${GREEN}步驟 4/5: 啟動服務...${NC}"
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
cd ~/v4.1
echo "🚀 構建並啟動容器..."
docker-compose up -d --build

echo "⏳ 等待服務啟動..."
sleep 10

echo "📊 檢查服務狀態..."
docker-compose ps
ENDSSH

echo "✅ 服務已啟動"
echo ""

# 步驟 5：驗證部署
echo -e "${GREEN}步驟 5/5: 驗證部署...${NC}"
sleep 5

echo "測試 API..."
curl -s http://$AWS_HOST:8000/api/stats | python3 -m json.tool || echo "API 尚未就緒，請稍後再試"

echo ""
echo -e "${GREEN}========================================"
echo "✅ 部署完成！"
echo "========================================${NC}"
echo ""
echo "📊 Dashboard: http://$AWS_HOST:8000"
echo "📡 API Stats: http://$AWS_HOST:8000/api/stats"
echo ""
echo "查看日誌："
echo "  ssh -i $SSH_KEY $AWS_USER@$AWS_HOST"
echo "  cd v4.1 && docker-compose logs -f"
echo ""
echo "更新內容："
echo "  ✅ API_ERROR 自動等待 60 分鐘"
echo "  ✅ 時區設置為 GMT+8 (Asia/Taipei)"
echo "  ✅ 智能循環檢測系統"
echo ""
