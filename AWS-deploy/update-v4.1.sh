#!/bin/bash

# 更新 V4.1 到 AWS EC2 (東京實例)
# 基於 AWS-deploy 的部署方式

set -e

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

REGION="ap-northeast-1"
KEY_NAME="globalping-checker-key"
INSTANCE_NAME="Globalping-V4.1-Tokyo"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V41_DIR="$PROJECT_DIR/v4.1"

echo "🔄 更新 V4.1 到 AWS EC2..."
echo ""

# 獲取實例資訊
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output text 2>/dev/null)

if [ "$INSTANCE_INFO" = "None" ] || [ -z "$INSTANCE_INFO" ]; then
    echo "❌ 找不到 $INSTANCE_NAME 實例"
    echo ""
    echo "請確認："
    echo "  1. 實例名稱是否正確"
    echo "  2. 實例是否在 $REGION 區域"
    echo "  3. 或手動指定 IP: export AWS_IP=54.238.247.106"
    
    # 如果有手動指定 IP
    if [ -n "$AWS_IP" ]; then
        PUBLIC_IP=$AWS_IP
        echo ""
        echo "✅ 使用手動指定的 IP: $PUBLIC_IP"
    else
        exit 1
    fi
else
    INSTANCE_ID=$(echo $INSTANCE_INFO | awk '{print $1}')
    STATE=$(echo $INSTANCE_INFO | awk '{print $2}')
    PUBLIC_IP=$(echo $INSTANCE_INFO | awk '{print $3}')
    
    echo "📊 實例資訊："
    echo "  ID: $INSTANCE_ID"
    echo "  狀態: $STATE"
    echo "  IP: $PUBLIC_IP"
    echo ""
    
    # 如果實例停止，先啟動
    if [ "$STATE" = "stopped" ]; then
        echo "⏳ 啟動實例..."
        aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID
        aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID
        
        PUBLIC_IP=$(aws ec2 describe-instances \
            --region $REGION \
            --instance-ids $INSTANCE_ID \
            --query 'Reservations[0].Instances[0].PublicIpAddress' \
            --output text)
        
        echo "✅ 實例已啟動: $PUBLIC_IP"
        echo "⏳ 等待 SSH 就緒..."
        sleep 30
    fi
fi

# 測試 SSH 連線
echo "🔍 測試 SSH 連線..."
if ! ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$PUBLIC_IP "echo 'SSH 連線成功'" 2>/dev/null; then
    echo "❌ SSH 連線失敗"
    echo ""
    echo "請檢查："
    echo "  1. 實例是否完全啟動（等待 1-2 分鐘）"
    echo "  2. 安全組是否允許 SSH (port 22)"
    echo "  3. 密鑰權限: chmod 400 ~/.ssh/$KEY_NAME.pem"
    echo "  4. 手動測試: ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
    exit 1
fi

echo "✅ SSH 連線正常"
echo ""

# 打包 V4.1
echo "📦 打包 V4.1 代碼..."
cd "$PROJECT_DIR"
tar -czf v4.1-update.tar.gz \
    --exclude='v4.1/__pycache__' \
    --exclude='v4.1/app/__pycache__' \
    --exclude='v4.1/.env' \
    v4.1/

echo "✅ 打包完成"
echo ""

# 上傳到 AWS
echo "📤 上傳到 AWS..."
scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    v4.1-update.tar.gz \
    ubuntu@$PUBLIC_IP:~/

echo "✅ 上傳完成"
echo ""

# 在 AWS 上執行更新
echo "🔄 在 AWS 上執行更新..."
ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP << 'ENDSSH'
set -e

echo "📦 停止當前服務..."
cd ~/v4.1 2>/dev/null || true
docker-compose down 2>/dev/null || true

echo "💾 備份當前版本..."
cd ~
if [ -d "v4.1" ]; then
    # 備份 .env 文件
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
    mv v4.1 v4.1-backup-$(date +%Y%m%d-%H%M%S)
    echo "✓ 舊版本已備份"
fi

echo "📂 解壓新版本..."
tar -xzf v4.1-update.tar.gz

echo "⚙️  恢復配置..."
cd v4.1

# 恢復 .env
if [ -f "/tmp/v4.1.env.backup" ]; then
    cp /tmp/v4.1.env.backup .env
    echo "✓ .env 已恢復"
else
    # 創建新的 .env
    cat > .env << 'EOF'
# Globalping API Token
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5

# PostgreSQL 密碼
POSTGRES_PASSWORD=globalping_secure_password

# 檢測間隔（分鐘）
CHECK_INTERVAL_MINUTES=90

# 異常區檢測時間（小時，24小時制，GMT+8）
ABNORMAL_CHECK_HOUR=1

# 正常區檢測時間（小時，24小時制，GMT+8）
NORMAL_CHECK_HOUR=9

# 最大迭代次數（異常區）
MAX_ITERATIONS=10
EOF
    echo "✓ 新 .env 已創建"
fi

# 恢復 domains.txt
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
echo "✅ 更新完成！"
ENDSSH

echo ""
echo "🎉 V4.1 更新完成！"
echo ""
echo "📋 更新內容："
echo "  ✅ API_ERROR 自動等待 60 分鐘"
echo "  ✅ 時區設置為 GMT+8 (Asia/Taipei)"
echo "  ✅ 智能循環檢測系統"
echo "  ✅ 配置文件已保留"
echo "  ✅ 域名列表已保留"
echo ""
echo "🔧 驗證部署："
echo "  1. 測試 API: curl http://$PUBLIC_IP:8000/api/stats"
echo "  2. 訪問 Dashboard: http://$PUBLIC_IP:8000"
echo "  3. 查看日誌: ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP 'cd v4.1 && docker-compose logs -f'"
echo ""
echo "📊 管理命令："
echo "  SSH 連線: ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo "  查看狀態: cd v4.1 && docker-compose ps"
echo "  重啟服務: cd v4.1 && docker-compose restart"
echo "  查看日誌: cd v4.1 && docker-compose logs -f --tail=50"
echo ""

# 清理本地打包文件
rm -f v4.1-update.tar.gz
echo "🧹 本地打包文件已清理"
echo ""
