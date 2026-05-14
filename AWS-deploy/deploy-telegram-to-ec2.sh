#!/bin/bash

# 部署 Telegram 通知到 EC2

set -e

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY
unset GIT_HTTP_PROXY GIT_HTTPS_PROXY

REGION="ap-northeast-1"
KEY_NAME="globalping-checker-key"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 部署 Telegram 通知到 EC2..."
echo ""

# 獲取實例資訊
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:Name,Values=Globalping-Checker-Server" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output text 2>/dev/null)

if [ "$INSTANCE_INFO" = "None" ] || [ -z "$INSTANCE_INFO" ]; then
    echo "❌ 找不到 Globalping-Checker-Server 實例"
    echo ""
    echo "請先部署實例："
    echo "  ./deploy-globalping-checker.sh"
    exit 1
fi

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

# 測試 SSH 連線
echo "🔍 測試 SSH 連線..."
if ! ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$PUBLIC_IP "echo 'SSH 連線成功'" 2>/dev/null; then
    echo "❌ SSH 連線失敗"
    echo ""
    echo "請檢查："
    echo "  1. 實例是否完全啟動（等待 1-2 分鐘）"
    echo "  2. 安全組是否允許 SSH"
    echo "  3. 密鑰權限: ls -la ~/.ssh/$KEY_NAME.pem"
    exit 1
fi

echo "✅ SSH 連線正常"
echo ""

# 檢查必要文件
echo "📋 檢查必要文件..."
REQUIRED_FILES=(
    "$PROJECT_DIR/GlobalpingChecker/telegram-config.env"
    "$PROJECT_DIR/GlobalpingChecker/telegram-notify.sh"
    "$PROJECT_DIR/GlobalpingChecker/id_globalping_multi_v3.3_Telegram.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 找不到文件: $file"
        exit 1
    fi
    echo "  ✓ $(basename $file)"
done

echo ""

# 上傳文件
echo "📤 上傳 Telegram 配置和腳本..."

scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    "$PROJECT_DIR/GlobalpingChecker/telegram-config.env" \
    ec2-user@$PUBLIC_IP:/tmp/

scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    "$PROJECT_DIR/GlobalpingChecker/telegram-notify.sh" \
    ec2-user@$PUBLIC_IP:/tmp/

scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no \
    "$PROJECT_DIR/GlobalpingChecker/id_globalping_multi_v3.3_Telegram.sh" \
    ec2-user@$PUBLIC_IP:/tmp/

echo "✅ 文件已上傳"
echo ""

# 在 EC2 上配置
echo "🔧 配置 EC2..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
# 移動文件
sudo mv /tmp/telegram-config.env /opt/globalping-checker/
sudo mv /tmp/telegram-notify.sh /opt/globalping-checker/
sudo mv /tmp/id_globalping_multi_v3.3_Telegram.sh /opt/globalping-checker/

# 設置權限
sudo chmod +x /opt/globalping-checker/*.sh
sudo chown ec2-user:ec2-user /opt/globalping-checker/*

echo "✓ 文件已配置"

# 檢查配置
if [ -f /opt/globalping-checker/telegram-config.env ]; then
    echo "✓ Telegram 配置已安裝"
fi

# 更新 run_check.sh 使用 Telegram 版本
if [ -f /opt/globalping-checker/run_check.sh ]; then
    sudo sed -i 's/id_globalping_multi_v3.1_Token.sh/id_globalping_multi_v3.3_Telegram.sh/g' /opt/globalping-checker/run_check.sh
    echo "✓ run_check.sh 已更新為 Telegram 版本"
fi
EOF

echo "✅ EC2 配置完成"
echo ""

# 測試通知
echo "🧪 測試 Telegram 通知..."
echo ""
read -p "是否要執行測試檢測? (y/N): " TEST_CONFIRM

if [[ "$TEST_CONFIRM" =~ ^[Yy]$ ]]; then
    echo ""
    echo "執行測試檢測..."
    ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/id_globalping_multi_v3.3_Telegram.sh /opt/globalping-checker/domains.txt | head -50'
    echo ""
    echo "請檢查 Telegram 是否收到通知"
fi

echo ""
echo "========================================"
echo "🎉 部署完成！"
echo "========================================"
echo ""
echo "📊 配置資訊："
echo "  實例 ID: $INSTANCE_ID"
echo "  公網 IP: $PUBLIC_IP"
echo "  Telegram 通知: 已啟用"
echo ""
echo "🔧 管理命令："
echo "  執行檢測: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
echo "  查看日誌: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'tail -f /var/log/globalping-checker/check_*.log'"
echo "  查看配置: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'cat /opt/globalping-checker/telegram-config.env'"
echo ""
echo "📅 定時任務："
echo "  每天凌晨 2 點自動執行檢測並發送 Telegram 通知"
echo ""
