#!/bin/bash

# ============================================
# V4.1 部署到 AWS（SQLite 版本）
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
SSH_KEY="$HOME/.ssh/globalping-checker-key.pem"
LOCAL_DIR="$HOME/Desktop/Project/GlobalpingChecker/v4.1"

echo -e "${BLUE}========================================"
echo "V4.1 部署到 AWS (SQLite 版本)"
echo "========================================${NC}"
echo ""

# 檢測 SSH 用戶名
echo -e "${YELLOW}🔍 檢測 SSH 用戶名...${NC}"
if ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$AWS_HOST "echo 'ubuntu user works'" 2>/dev/null; then
    AWS_USER="ubuntu"
    echo -e "${GREEN}✅ 使用用戶: ubuntu${NC}"
elif ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$AWS_HOST "echo 'ec2-user works'" 2>/dev/null; then
    AWS_USER="ec2-user"
    echo -e "${GREEN}✅ 使用用戶: ec2-user${NC}"
else
    echo -e "${RED}❌ 無法連接到 AWS，請檢查：${NC}"
    echo "  1. SSH 密鑰路徑: $SSH_KEY"
    echo "  2. AWS IP: $AWS_HOST"
    echo "  3. 安全組是否允許 SSH (端口 22)"
    exit 1
fi

REMOTE_DIR="/home/$AWS_USER/globalping-v4.1"
echo "目標: $AWS_USER@$AWS_HOST"
echo "遠程目錄: $REMOTE_DIR"
echo ""

# 步驟 1：打包代碼
echo -e "${GREEN}步驟 1/6: 打包 V4.1 代碼...${NC}"
cd "$LOCAL_DIR"

# 創建臨時目錄
TEMP_DIR=$(mktemp -d)
echo "臨時目錄: $TEMP_DIR"

# 複製文件
cp -r app "$TEMP_DIR/"
cp -r templates "$TEMP_DIR/"
cp -r static "$TEMP_DIR/"
cp -r data "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"
cp domains.txt "$TEMP_DIR/"
cp .env "$TEMP_DIR/"

# 創建 Dockerfile（不使用 PostgreSQL）
cat > "$TEMP_DIR/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 設置時區為 GMT+8
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安裝依賴
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    tzdata \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴（移除 PostgreSQL）
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings \
    httpx apscheduler python-dotenv jinja2 aiohttp alembic

# 複製應用代碼
COPY . .

# 創建數據目錄
RUN mkdir -p /app/data && chmod 777 /app/data

# 創建非 root 用戶
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 創建 docker-compose.yml（僅 web 服務）
cat > "$TEMP_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  web:
    build: .
    container_name: globalping_v41_web
    environment:
      DATABASE_URL: sqlite:///./data/globalping_results.db
      GLOBALPING_TOKEN: ${GLOBALPING_TOKEN}
      CHECK_INTERVAL_MINUTES: ${CHECK_INTERVAL_MINUTES:-90}
      ABNORMAL_CHECK_HOUR: ${ABNORMAL_CHECK_HOUR:-1}
      NORMAL_CHECK_HOUR: ${NORMAL_CHECK_HOUR:-9}
      MAX_ITERATIONS: ${MAX_ITERATIONS:-10}
      DOMAINS_FILE: /app/domains.txt
      HOST: 0.0.0.0
      PORT: 8000
      TZ: Asia/Taipei
    volumes:
      - ./data:/app/data
      - ./domains.txt:/app/domains.txt:ro
      - ./templates:/app/templates:ro
      - ./static:/app/static:ro
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/stats"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

networks:
  default:
    name: globalping_v41_network
EOF

# 打包
cd "$TEMP_DIR/.."
tar -czf v4.1-sqlite-deploy.tar.gz $(basename "$TEMP_DIR")

echo "✅ 打包完成"
echo ""

# 步驟 2：上傳到 AWS
echo -e "${GREEN}步驟 2/6: 上傳到 AWS...${NC}"
scp -i "$SSH_KEY" "$TEMP_DIR/../v4.1-sqlite-deploy.tar.gz" "$AWS_USER@$AWS_HOST:~/"

if [ $? -eq 0 ]; then
    echo "✅ 上傳成功"
else
    echo -e "${RED}❌ 上傳失敗${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi
echo ""

# 清理臨時文件
rm -rf "$TEMP_DIR"
rm -f "$TEMP_DIR/../v4.1-sqlite-deploy.tar.gz"

# 步驟 3：備份數據庫並停止服務
echo -e "${GREEN}步驟 3/6: 備份數據庫並停止服務...${NC}"
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << ENDSSH
set -e

if [ -d "$REMOTE_DIR" ]; then
    echo "💾 備份數據庫..."
    
    # 創建備份目錄
    mkdir -p ~/db-backups
    
    # 備份數據庫
    if [ -f "$REMOTE_DIR/data/globalping_results.db" ]; then
        BACKUP_NAME="globalping_results.db.backup-\$(date +%Y%m%d-%H%M%S)"
        cp "$REMOTE_DIR/data/globalping_results.db" ~/db-backups/"\$BACKUP_NAME"
        echo "✅ 數據庫已備份到: ~/db-backups/\$BACKUP_NAME"
        
        # 保留最近 10 個備份
        cd ~/db-backups
        ls -t globalping_results.db.backup-* 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
        echo "📦 保留最近 10 個備份"
    else
        echo "⚠️  沒有現有數據庫"
    fi
    
    # 停止服務
    echo "🛑 停止服務..."
    cd "$REMOTE_DIR"
    docker-compose down 2>/dev/null || true
else
    echo "ℹ️  首次部署"
fi
ENDSSH

echo "✅ 備份完成"
echo ""

# 步驟 4：解壓並配置（保留數據庫）
echo -e "${GREEN}步驟 4/6: 解壓並配置...${NC}"
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << ENDSSH
set -e

cd ~
echo "📂 解壓新版本..."

# 備份舊數據庫（如果存在）
if [ -f "$REMOTE_DIR/data/globalping_results.db" ]; then
    echo "💾 臨時保存數據庫..."
    cp "$REMOTE_DIR/data/globalping_results.db" ~/temp_db_backup.db
    DB_BACKUP_EXISTS=true
else
    DB_BACKUP_EXISTS=false
fi

# 解壓新代碼
tar -xzf v4.1-sqlite-deploy.tar.gz

# 刪除舊目錄（如果存在）
rm -rf "$REMOTE_DIR"

# 移動新代碼
mv tmp.* "$REMOTE_DIR"

cd "$REMOTE_DIR"

# 恢復數據庫
if [ "\$DB_BACKUP_EXISTS" = true ]; then
    echo "♻️  恢復數據庫..."
    cp ~/temp_db_backup.db data/globalping_results.db
    rm ~/temp_db_backup.db
    echo "✅ 數據庫已恢復"
else
    echo "ℹ️  使用新數據庫"
fi

# 確保 .env 文件存在
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，請手動創建"
fi

# 設置數據目錄權限
chmod 777 data
chmod 666 data/globalping_results.db 2>/dev/null || true

echo "✅ 配置完成"
ENDSSH

echo "✅ 配置完成"
echo ""

# 步驟 5：啟動服務
echo -e "${GREEN}步驟 5/6: 啟動服務...${NC}"
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << ENDSSH
cd "$REMOTE_DIR"

echo "🚀 構建並啟動容器..."
docker-compose up -d --build

echo "⏳ 等待服務啟動..."
sleep 15

echo "📊 檢查服務狀態..."
docker-compose ps

echo "📋 查看日誌（最後 20 行）..."
docker-compose logs --tail=20
ENDSSH

echo "✅ 服務已啟動"
echo ""

# 步驟 6：驗證部署
echo -e "${GREEN}步驟 6/6: 驗證部署...${NC}"
sleep 5

echo "測試 API..."
if curl -s -f http://$AWS_HOST:8000/api/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API 響應正常${NC}"
    curl -s http://$AWS_HOST:8000/api/stats | python3 -m json.tool 2>/dev/null || echo "API 數據獲取成功"
else
    echo -e "${YELLOW}⚠️  API 尚未就緒，請稍後檢查${NC}"
fi

echo ""
echo -e "${GREEN}========================================"
echo "✅ 部署完成！"
echo "========================================${NC}"
echo ""
echo "📊 Dashboard: http://$AWS_HOST:8000"
echo "📡 API Stats: http://$AWS_HOST:8000/api/stats"
echo "📡 API Docs:  http://$AWS_HOST:8000/docs"
echo ""
echo "🔧 管理命令："
echo "  SSH 登入:"
echo "    ssh -i $SSH_KEY $AWS_USER@$AWS_HOST"
echo ""
echo "  查看日誌:"
echo "    cd $REMOTE_DIR && docker-compose logs -f"
echo ""
echo "  重啟服務:"
echo "    cd $REMOTE_DIR && docker-compose restart"
echo ""
echo "  停止服務:"
echo "    cd $REMOTE_DIR && docker-compose down"
echo ""
echo "📦 版本特性："
echo "  ✅ SQLite 數據庫（無需 PostgreSQL）"
echo "  ✅ 智能循環檢測系統"
echo "  ✅ 時區設置為 GMT+8 (Asia/Taipei)"
echo "  ✅ 自動重啟機制"
echo "  ✅ 健康檢查"
echo ""
