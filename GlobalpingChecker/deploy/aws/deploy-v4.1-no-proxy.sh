#!/bin/bash

# V4.1 部署腳本 - 禁用代理版本（使用 AWS-deploy 方式）

# 禁用所有代理（設置為空字符串）
export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""
export no_proxy="*"
export NO_PROXY="*"
export socks_proxy=""
export SOCKS_PROXY=""
export socks5_proxy=""
export SOCKS5_PROXY=""

AWS_IP="54.238.247.106"
KEY_FILE="$HOME/.ssh/globalping-checker-key.pem"
PACKAGE_FILE="/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1-update.tar.gz"

echo "🚀 V4.1 部署到 AWS"
echo "目標: ubuntu@$AWS_IP"
echo ""
echo "⚠️  注意：此腳本會自動禁用代理"
echo ""

# 步驟 1：測試 SSH 連線
echo "🔍 測試 SSH 連線..."
if ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$AWS_IP "echo 'SSH 連線成功'" 2>/dev/null; then
    echo "✅ SSH 連線正常"
else
    echo "❌ SSH 連線失敗"
    echo ""
    echo "請在終端手動執行以下命令："
    echo ""
    echo "# 1. 禁用代理"
    echo "unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY"
    echo "unset all_proxy ALL_PROXY no_proxy NO_PROXY"
    echo ""
    echo "# 2. 測試連線"
    echo "ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@54.238.247.106"
    echo ""
    exit 1
fi

echo ""

# 步驟 2：上傳文件
echo "📤 上傳 V4.1 到 AWS..."
scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$PACKAGE_FILE" ubuntu@$AWS_IP:~/

if [ $? -eq 0 ]; then
    echo "✅ 上傳成功"
else
    echo "❌ 上傳失敗"
    exit 1
fi

echo ""

# 步驟 3：執行部署
echo "🔄 在 AWS 上執行部署..."
ssh -i "$KEY_FILE" ubuntu@$AWS_IP << 'ENDSSH'
set -e

echo "📦 停止當前服務..."
cd ~/v4.1 2>/dev/null || true
docker-compose down 2>/dev/null || true

echo "💾 備份配置..."
cd ~
if [ -d "v4.1" ]; then
    if [ -f "v4.1/.env" ]; then
        cp v4.1/.env /tmp/v4.1.env.backup
        echo "✓ .env 已備份"
    fi
    
    if [ -f "v4.1/domains.txt" ]; then
        cp v4.1/domains.txt /tmp/v4.1.domains.backup
        echo "✓ domains.txt 已備份"
    fi
    
    mv v4.1 v4.1-backup-$(date +%Y%m%d-%H%M%S)
    echo "✓ 舊版本已備份"
fi

echo "📂 解壓新版本..."
tar -xzf v4.1-update.tar.gz
cd v4.1

echo "⚙️  配置環境..."
if [ -f "/tmp/v4.1.env.backup" ]; then
    cp /tmp/v4.1.env.backup .env
    echo "✓ .env 已恢復"
else
    cat > .env << 'EOF'
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5
POSTGRES_PASSWORD=globalping_secure_password
CHECK_INTERVAL_MINUTES=90
ABNORMAL_CHECK_HOUR=1
NORMAL_CHECK_HOUR=9
MAX_ITERATIONS=10
EOF
    echo "✓ 新 .env 已創建"
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

echo ""
echo "🎉 V4.1 部署完成！"
echo ""
echo "📋 更新內容："
echo "  ✅ API_ERROR 自動等待 60 分鐘"
echo "  ✅ 時區設置為 GMT+8 (Asia/Taipei)"
echo "  ✅ 智能循環檢測系統"
echo ""
echo "🔍 驗證部署："
echo "  curl http://$AWS_IP:8000/api/stats"
echo ""
echo "📊 Dashboard："
echo "  http://$AWS_IP:8000"
echo ""
echo "🔧 管理命令："
echo "  ssh -i ~/.ssh/globalping-checker-key.pem ubuntu@$AWS_IP"
echo "  cd v4.1 && docker-compose logs -f"
echo ""

# 清理
rm -f "$PACKAGE_FILE"
echo "🧹 本地打包文件已清理"
