#!/bin/bash

# 更新 Globalping Checker 代碼到現有 EC2 實例

set -e

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

REGION="ap-northeast-1"
KEY_NAME="globalping-checker-key"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔄 更新 Globalping Checker 代碼..."
echo ""

# 獲取實例資訊
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:Name,Values=Globalping-Checker-Server" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output text)

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

# 備份現有配置
echo "💾 備份現有配置..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
if [ -f /opt/globalping-checker/config.env ]; then
    cp /opt/globalping-checker/config.env /tmp/config.env.backup
    echo "✓ 配置已備份"
fi

if [ -f /opt/globalping-checker/domains.txt ]; then
    cp /opt/globalping-checker/domains.txt /tmp/domains.txt.backup
    echo "✓ 域名列表已備份"
fi
EOF

echo ""

# 上傳最新代碼
echo "📤 上傳最新代碼..."
scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -r \
    "$PROJECT_DIR/GlobalpingChecker" \
    ec2-user@$PUBLIC_IP:~/

echo "✅ 代碼已上傳"
echo ""

# 更新系統
echo "🔄 更新系統..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
cd ~/GlobalpingChecker/ec2

# 複製腳本到工作目錄
sudo cp ~/GlobalpingChecker/*.sh /opt/globalping-checker/ 2>/dev/null || true
sudo chmod +x /opt/globalping-checker/*.sh

# 恢復配置
if [ -f /tmp/config.env.backup ]; then
    sudo cp /tmp/config.env.backup /opt/globalping-checker/config.env
    echo "✓ 配置已恢復"
fi

if [ -f /tmp/domains.txt.backup ]; then
    sudo cp /tmp/domains.txt.backup /opt/globalping-checker/domains.txt
    echo "✓ 域名列表已恢復"
fi

echo "✓ 系統更新完成"
EOF

echo ""
echo "🎉 更新完成！"
echo ""
echo "📋 更新內容："
echo "  ✓ 檢測腳本已更新"
echo "  ✓ 配置文件已保留"
echo "  ✓ 域名列表已保留"
echo ""
echo "🔧 下一步："
echo "  1. 測試執行: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
echo "  2. 查看日誌: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'tail -f /var/log/globalping-checker/check_*.log'"
echo "  3. 檢查狀態: ./check-globalping-status.sh"
echo ""
