#!/bin/bash

# ============================================
# V4.1 自動部署腳本 - 適用於系統終端
# 請在 Terminal.app 或 iTerm 中執行
# ============================================

set -e

# 禁用代理
export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""
export no_proxy="*"
export NO_PROXY="*"

# 配置
AWS_IP="54.238.247.106"
KEY_FILE="$HOME/.ssh/globalping-checker-key.pem"
PROJECT_DIR="$HOME/Desktop/Project/GlobalpingChecker"
PACKAGE_FILE="$PROJECT_DIR/v4.1-update.tar.gz"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================"
echo "V4.1 自動部署到 AWS"
echo "========================================${NC}"
echo "目標: $AWS_IP"
echo "區域: ap-northeast-1 (東京)"
echo ""

# 檢查是否在 Cursor 環境中
if [ -n "$CURSOR_SESSION_ID" ] || [ -n "$__CURSOR_SANDBOX_ENV_RESTORE" ]; then
    echo -e "${RED}❌ 檢測到 Cursor 環境${NC}"
    echo ""
    echo "請在系統終端執行此腳本："
    echo "  1. 打開 Terminal.app 或 iTerm"
    echo "  2. 執行: bash $0"
    echo ""
    exit 1
fi

# 步驟 1：檢查文件
echo -e "${GREEN}步驟 1/6: 檢查文件...${NC}"
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ SSH 密鑰不存在: $KEY_FILE${NC}"
    exit 1
fi
echo "✅ SSH 密鑰存在"

if [ ! -f "$PACKAGE_FILE" ]; then
    echo -e "${YELLOW}⚠️  打包文件不存在，正在創建...${NC}"
    cd "$PROJECT_DIR"
    tar -czf v4.1-update.tar.gz \
        --exclude='v4.1/__pycache__' \
        --exclude='v4.1/app/__pycache__' \
        --exclude='v4.1/.env' \
        v4.1/
    echo "✅ 打包完成"
else
    echo "✅ 打包文件存在"
fi
echo ""

# 步驟 2：測試 SSH 連線（嘗試兩個用戶名）
echo -e "${GREEN}步驟 2/6: 測試 SSH 連線...${NC}"

SSH_USER=""
for USER in ubuntu ec2-user; do
    echo "嘗試用戶: $USER"
    if ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no -o ConnectTimeout=5 $USER@$AWS_IP "echo 'SSH 連線成功'" 2>/dev/null; then
        SSH_USER=$USER
        echo -e "${GREEN}✅ SSH 連線成功 (用戶: $SSH_USER)${NC}"
        break
    fi
done

if [ -z "$SSH_USER" ]; then
    echo -e "${RED}❌ SSH 連線失敗${NC}"
    echo ""
    echo "請檢查："
    echo "  1. 實例是否正在運行"
    echo "  2. 安全組是否允許 SSH (port 22)"
    echo "  3. 密鑰權限: ls -la $KEY_FILE"
    echo ""
    echo "手動測試："
    echo "  ssh -i $KEY_FILE ubuntu@$AWS_IP"
    echo "  ssh -i $KEY_FILE ec2-user@$AWS_IP"
    exit 1
fi
echo ""

# 步驟 3：上傳文件
echo -e "${GREEN}步驟 3/6: 上傳文件到 AWS...${NC}"
scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$PACKAGE_FILE" $SSH_USER@$AWS_IP:~/
echo "✅ 上傳完成"
echo ""

# 步驟 4：檢查當前部署
echo -e "${GREEN}步驟 4/6: 檢查當前部署...${NC}"
ssh -i "$KEY_FILE" $SSH_USER@$AWS_IP << 'ENDSSH'
if [ -d ~/v4.1 ]; then
    echo "✓ 找到現有 v4.1 部署"
    if [ -f ~/v4.1/.env ]; then
        echo "✓ 找到 .env 配置文件"
    fi
    if [ -f ~/v4.1/domains.txt ]; then
        echo "✓ 找到 domains.txt"
    fi
else
    echo "⚠️  未找到現有部署，將進行全新安裝"
fi
ENDSSH
echo ""

# 步驟 5：執行部署
echo -e "${GREEN}步驟 5/6: 執行部署...${NC}"
ssh -i "$KEY_FILE" $SSH_USER@$AWS_IP << 'ENDSSH'
set -e

echo "📦 停止當前服務..."
if [ -d ~/v4.1 ]; then
    cd ~/v4.1
    docker-compose down 2>/dev/null || true
    echo "✓ 服務已停止"
fi

echo "💾 備份配置..."
cd ~
if [ -d "v4.1" ]; then
    # 備份 .env
    if [ -f "v4.1/.env" ]; then
        cp v4.1/.env /tmp/v4.1.env.backup
        echo "✓ .env 已備份"
    fi
    
    # 備份 domains.txt
    if [ -f "v4.1/domains.txt" ]; then
        cp v4.1/domains.txt /tmp/v4.1.domains.backup
        echo "✓ domains.txt 已備份"
    fi
    
    # 移動舊版本
    BACKUP_DIR="v4.1-backup-$(date +%Y%m%d-%H%M%S)"
    mv v4.1 "$BACKUP_DIR"
    echo "✓ 舊版本已備份到: $BACKUP_DIR"
fi

echo "📂 解壓新版本..."
tar -xzf v4.1-update.tar.gz
cd v4.1

echo "⚙️  配置環境..."
if [ -f "/tmp/v4.1.env.backup" ]; then
    cp /tmp/v4.1.env.backup .env
    echo "✓ .env 已恢復"
else
    echo "✓ 創建新 .env 文件"
    cat > .env << 'EOF'
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5
POSTGRES_PASSWORD=globalping_secure_password
CHECK_INTERVAL_MINUTES=90
ABNORMAL_CHECK_HOUR=1
NORMAL_CHECK_HOUR=9
MAX_ITERATIONS=10
EOF
fi

if [ -f "/tmp/v4.1.domains.backup" ]; then
    cp /tmp/v4.1.domains.backup domains.txt
    echo "✓ domains.txt 已恢復"
fi

echo "🚀 啟動服務..."
docker-compose up -d --build

echo "⏳ 等待服務啟動..."
sleep 15

echo "📊 檢查服務狀態..."
docker-compose ps

echo ""
echo "✅ 部署完成！"
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 部署成功！${NC}"
else
    echo -e "${RED}❌ 部署失敗${NC}"
    exit 1
fi
echo ""

# 步驟 6：驗證部署
echo -e "${GREEN}步驟 6/6: 驗證部署...${NC}"
sleep 5

echo "測試 API..."
if curl -s -f http://$AWS_IP:8000/api/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API 正常${NC}"
    curl -s http://$AWS_IP:8000/api/stats | python3 -m json.tool | head -20
else
    echo -e "${YELLOW}⚠️  API 尚未就緒，請稍後再試${NC}"
fi
echo ""

# 完成
echo -e "${GREEN}========================================"
echo "🎉 V4.1 部署完成！"
echo "========================================${NC}"
echo ""
echo "📊 Dashboard: http://$AWS_IP:8000"
echo "📡 API Stats: http://$AWS_IP:8000/api/stats"
echo ""
echo "🔧 管理命令："
echo "  SSH 連線: ssh -i $KEY_FILE $SSH_USER@$AWS_IP"
echo "  查看日誌: ssh -i $KEY_FILE $SSH_USER@$AWS_IP 'cd v4.1 && docker-compose logs -f'"
echo "  重啟服務: ssh -i $KEY_FILE $SSH_USER@$AWS_IP 'cd v4.1 && docker-compose restart'"
echo ""
echo "✅ 更新內容："
echo "  • API_ERROR 自動等待 60 分鐘"
echo "  • 時區設置為 GMT+8 (Asia/Taipei)"
echo "  • 智能循環檢測系統"
echo ""

# 清理本地打包文件
rm -f "$PACKAGE_FILE"
echo "🧹 本地打包文件已清理"
echo ""
