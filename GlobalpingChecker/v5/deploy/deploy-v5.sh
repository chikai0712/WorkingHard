#!/bin/bash
# GlobalpingChecker V5 - 部署腳本
# 用法：bash deploy/deploy-v5.sh

set -euo pipefail

EC2_HOST="54.238.247.106"
EC2_USER="ec2-user"
KEY="$HOME/.ssh/globalping-checker-key.pem"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
TARBALL="/tmp/v5-deploy-$(date +%Y%m%d-%H%M%S).tar.gz"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=15"

echo "╔══════════════════════════════════════════════╗"
echo "║   GlobalpingChecker V5 → AWS 部署            ║"
echo "║   目標: $EC2_USER@$EC2_HOST                ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. 驗證 SSH 金鑰
if [ ! -f "$KEY" ]; then
    echo "❌ 找不到 SSH 金鑰: $KEY"
    exit 1
fi
echo "✅ SSH 密鑰: $KEY"

# 2. 測試 SSH 連線
echo "🔍 測試 SSH 連線..."
if ! ssh $SSH_OPTS "$EC2_USER@$EC2_HOST" 'echo ok' > /dev/null 2>&1; then
    echo "❌ SSH 連線失敗"
    exit 1
fi
echo "✅ SSH 連線成功"

# 3. 打包
echo "📦 打包 V5 代碼..."
cd "$PROJECT_DIR/.."
tar -czf "$TARBALL" \
    --no-xattrs \
    --exclude='v5/__pycache__' \
    --exclude='v5/app/__pycache__' \
    --exclude='v5/.env' \
    --exclude='v5/data' \
    --exclude='v5/*.tar.gz' \
    v5/
echo "✅ 打包完成: $TARBALL"

# 4. 上傳
echo "📤 上傳到 EC2..."
scp $SSH_OPTS "$TARBALL" "$EC2_USER@$EC2_HOST:/tmp/"
scp $SSH_OPTS "$PROJECT_DIR/.env" "$EC2_USER@$EC2_HOST:/tmp/v5_env_upload"
echo "✅ 上傳完成"

# 5. 遠端部署
echo "🚀 在 EC2 上執行部署..."
ssh $SSH_OPTS "$EC2_USER@$EC2_HOST" bash <<'ENDSSH'
set -e
TARBALL=$(ls /tmp/v5-deploy-*.tar.gz | tail -1)
echo "── EC2 部署開始 ──"

# 停止現有容器
echo "⏹  停止現有服務..."
cd ~/v5 2>/dev/null && docker compose down --remove-orphans 2>/dev/null || true
cd ~/v41 2>/dev/null && docker compose down --remove-orphans 2>/dev/null || true
docker rm -f globalping_v5_web globalping_v5_postgres globalping_v41_web globalping_v41_postgres 2>/dev/null || true
docker network rm globalping_v5_network globalping_v41_network 2>/dev/null || true
# 強制釋放 port 8000
fuser -k 8000/tcp 2>/dev/null || true
sleep 2

# 備份
if [ -d ~/v5 ]; then
    echo "💾 備份配置..."
    [ -f ~/v5/.env ]         && cp ~/v5/.env /tmp/v5_env.bak
    [ -f ~/v5/domains.txt ]  && cp ~/v5/domains.txt /tmp/v5_domains.bak
    rm -rf ~/v5.bak && mv ~/v5 ~/v5.bak
fi

# 解壓
echo "📂 解壓新版本..."
mkdir -p ~/v5
tar -xzf "$TARBALL" -C ~ --no-same-owner

# 恢復配置
echo "⚙️  恢復配置..."
[ -f /tmp/v5_env_upload ]  && cp /tmp/v5_env_upload ~/v5/.env     && echo "   ✓ .env 已從本機上傳"
[ -f /tmp/v5_env.bak ] && [ ! -f ~/v5/.env ] && cp /tmp/v5_env.bak ~/v5/.env && echo "   ✓ .env 已從備份恢復"
[ -f /tmp/v5_domains.bak ] && cp /tmp/v5_domains.bak ~/v5/domains.txt && echo "   ✓ domains.txt 已恢復"

# AWS 環境：port 改為 8000:8000
sed -i 's/- "8001:8000"/- "8000:8000"/' ~/v5/docker-compose.yml
echo "   ✓ Port 已設定為 8000:8000"

# 啟動
echo "🚀 啟動服務..."
cd ~/v5
docker-compose up -d --build --remove-orphans
echo "   ✓ Docker 服務已啟動"

echo ""
docker-compose ps
ENDSSH

# 6. 驗證
echo ""
echo "🔍 驗證部署（等待 10 秒）..."
sleep 10
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$EC2_HOST:8000/api/stats" || echo "000")

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║              部署結果摘要                     ║"
echo "╠══════════════════════════════════════════════╣"
if [ "$HTTP_CODE" = "200" ]; then
    echo "║  ✅ API 響應正常 (HTTP 200)                  ║"
else
    echo "║  ❌ API 無響應 (HTTP $HTTP_CODE)             ║"
fi
echo "╠══════════════════════════════════════════════╣"
echo "║  Dashboard : http://$EC2_HOST:8000           ║"
echo "║  API Stats : http://$EC2_HOST:8000/api/stats  ║"
echo "║  API Quota : http://$EC2_HOST:8000/api/quota  ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  SSH: ssh -i ~/.ssh/globalping-checker-key.pem ║"
echo "║       $EC2_USER@$EC2_HOST                ║"
echo "╚══════════════════════════════════════════════╝"
