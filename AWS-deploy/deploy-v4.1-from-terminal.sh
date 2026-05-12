#!/bin/bash
# ============================================================
# GlobalpingChecker V4.1 — 部署腳本（從系統終端執行）
# 用途：繞過 Cursor IDE 的代理沙箱，直接 SSH 部署到 AWS
#
# 使用方式：
#   在 Terminal.app 或 iTerm2（非 Cursor）中執行：
#   chmod +x ~/Desktop/Project/AWS-deploy/deploy-v4.1-from-terminal.sh
#   ~/Desktop/Project/AWS-deploy/deploy-v4.1-from-terminal.sh
# ============================================================

set -e

# ── 1. 清除所有代理環境變量 ──────────────────────────────────
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
unset ALL_PROXY all_proxy NO_PROXY no_proxy
unset SOCKS_PROXY SOCKS5_PROXY socks_proxy socks5_proxy
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

# ── 2. 設定變量 ───────────────────────────────────────────────
KEY="/Users/ckchiu/.ssh/globalping-checker-key.pem"
EC2_IP="54.238.247.106"
EC2_USER="ec2-user"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=15"
SCP_OPTS="-i $KEY -o StrictHostKeyChecking=no"

PROJECT_DIR="$HOME/Desktop/Project/GlobalpingChecker"
V41_DIR="$PROJECT_DIR/v4.1"
TARBALL="/tmp/v4.1-deploy-$(date +%Y%m%d-%H%M%S).tar.gz"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   GlobalpingChecker V4.1 → AWS 部署          ║"
echo "║   目標: $EC2_USER@$EC2_IP           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 3. 確認密鑰存在並設定正確權限 ────────────────────────────
if [ ! -f "$KEY" ]; then
    echo "❌ 找不到 SSH 密鑰: $KEY"
    exit 1
fi
chmod 400 "$KEY"
echo "✅ SSH 密鑰: $KEY"

# ── 4. 測試 SSH 連線 ──────────────────────────────────────────
echo ""
echo "🔍 測試 SSH 連線..."
if ssh $SSH_OPTS $EC2_USER@$EC2_IP 'echo "✅ SSH 連線成功"' ; then
    echo "   主機: $EC2_USER@$EC2_IP"
else
    echo ""
    echo "❌ SSH 連線失敗。請確認："
    echo "   1. EC2 實例正在運行"
    echo "   2. 安全組允許 port 22"
    echo "   3. 你的網路未封鎖 port 22"
    echo "   手動測試: ssh $SSH_OPTS $EC2_USER@$EC2_IP"
    exit 1
fi

# ── 5. 打包本地 V4.1（排除快取和 .env）────────────────────────
echo ""
echo "📦 打包 V4.1 代碼..."
cd "$PROJECT_DIR"
tar -czf "$TARBALL" \
    --no-xattrs \
    --exclude='v4.1/__pycache__' \
    --exclude='v4.1/app/__pycache__' \
    --exclude='v4.1/.env' \
    --exclude='v4.1/data' \
    --exclude='v4.1/*.tar.gz' \
    --exclude='v4.1/*.gz' \
    v4.1/
echo "✅ 打包完成: $TARBALL"

# ── 6. 上傳到 EC2 ────────────────────────────────────────────
echo ""
echo "📤 上傳到 EC2..."
scp $SCP_OPTS "$TARBALL" $EC2_USER@$EC2_IP:~/v4.1-update.tar.gz
echo "✅ 上傳完成"

# ── 7. 在 EC2 上執行部署 ─────────────────────────────────────
echo ""
echo "🚀 在 EC2 上執行部署..."

ssh $SSH_OPTS $EC2_USER@$EC2_IP << 'REMOTE'
set -e
echo ""
echo "── EC2 部署開始 ──"

# 停止現有服務
echo "⏹  停止現有服務..."
# 強制移除所有可能衝突的容器
docker rm -f globalping_v41_web globalping_v41_postgres 2>/dev/null || true
# 同時清理舊目錄的 compose
if [ -d ~/v4.1 ]; then
    cd ~/v4.1
    docker-compose down --remove-orphans 2>/dev/null || true
    cd ~
elif [ -d ~/globalping-v4.1 ]; then
    cd ~/globalping-v4.1
    docker-compose down --remove-orphans 2>/dev/null || true
    cd ~
fi
# 確保容器完全移除
docker rm -f globalping_v41_web globalping_v41_postgres 2>/dev/null || true

# 備份 .env 和 domains.txt
echo "💾 備份配置文件..."
if [ -d ~/v4.1 ]; then
    [ -f ~/v4.1/.env ]         && cp ~/v4.1/.env         /tmp/v4.1.env.backup         && echo "   ✓ .env 已備份"
    [ -f ~/v4.1/domains.txt ]  && cp ~/v4.1/domains.txt  /tmp/v4.1.domains.backup     && echo "   ✓ domains.txt 已備份"
    mv ~/v4.1 ~/v4.1-backup-$(date +%Y%m%d-%H%M%S) && echo "   ✓ 舊版本已備份"
fi

# 解壓新版本
echo "📂 解壓新版本..."
tar -xzf ~/v4.1-update.tar.gz -C ~/
echo "   ✓ 解壓完成"

# 恢復配置
echo "⚙️  恢復配置..."
cd ~/v4.1
if [ -f /tmp/v4.1.env.backup ]; then
    cp /tmp/v4.1.env.backup .env
    echo "   ✓ .env 已恢復"
elif [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "   ⚠️  使用 .env.example，請手動設定 GLOBALPING_TOKEN"
fi

if [ -f /tmp/v4.1.domains.backup ]; then
    cp /tmp/v4.1.domains.backup domains.txt
    echo "   ✓ domains.txt 已恢復"
fi

# 啟動服務
echo "🚀 啟動服務..."
if [ -f docker-compose.yml ]; then
    docker-compose up -d --build --remove-orphans
    echo "   ✓ Docker 服務已啟動"
    sleep 15
    echo ""
    echo "📊 服務狀態:"
    docker-compose ps
else
    # 非 Docker 模式
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt -q
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/globalping.log 2>&1 &
    echo "   ✓ 應用已在後台啟動 (PID: $!)"
fi

echo ""
echo "✅ EC2 部署完成！"
REMOTE

# ── 8. 清理本地暫存文件 ───────────────────────────────────────
rm -f "$TARBALL"

# ── 9. 驗證部署 ───────────────────────────────────────────────
echo ""
echo "🔍 驗證部署（等待 10 秒服務啟動）..."
sleep 10
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://$EC2_IP:8000/api/stats" 2>/dev/null || echo "000")

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║              部署結果摘要                     ║"
echo "╠══════════════════════════════════════════════╣"
if [ "$HTTP_STATUS" = "200" ]; then
echo "║  ✅ API 響應正常 (HTTP $HTTP_STATUS)              ║"
else
echo "║  ⚠️  API 狀態: HTTP $HTTP_STATUS (服務可能還在啟動)  ║"
fi
echo "╠══════════════════════════════════════════════╣"
echo "║  Dashboard : http://$EC2_IP:8000          ║"
echo "║  API Stats : http://$EC2_IP:8000/api/stats ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  SSH 進入實例:                                ║"
printf "║  ssh -i ~/.ssh/globalping-checker-key.pem  ║\n"
printf "║       $EC2_USER@$EC2_IP                    ║\n"
echo "╠══════════════════════════════════════════════╣"
echo "║  查看日誌 (在 EC2 上):                        ║"
echo "║  cd ~/v4.1 && docker-compose logs -f         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
