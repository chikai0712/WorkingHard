#!/bin/bash

# 更新 Globalping Checker 的域名列表

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "📝 更新 Globalping Checker 域名列表..."

# 獲取 EC2 實例 IP
INSTANCE_ID=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=Globalping-Checker-Server" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
    echo "❌ 找不到運行中的 EC2 實例"
    exit 1
fi

PUBLIC_IP=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "📡 EC2 實例: $INSTANCE_ID"
echo "🌐 公開 IP: $PUBLIC_IP"
echo ""

# 選擇域名文件
echo "請選擇要上傳的域名文件："
echo "  1) test_2_domains.txt (測試用 2 個域名)"
echo "  2) test_10.txt (測試用 10 個域名)"
echo "  3) 自定義文件"
echo ""
read -p "選擇 (1-3): " CHOICE

case $CHOICE in
    1)
        DOMAINS_FILE="$PROJECT_DIR/GlobalpingChecker/test_2_domains.txt"
        ;;
    2)
        DOMAINS_FILE="$PROJECT_DIR/GlobalpingChecker/test_10.txt"
        ;;
    3)
        read -p "輸入域名文件路徑: " DOMAINS_FILE
        ;;
    *)
        echo "❌ 無效選擇"
        exit 1
        ;;
esac

if [ ! -f "$DOMAINS_FILE" ]; then
    echo "❌ 文件不存在: $DOMAINS_FILE"
    exit 1
fi

# 顯示域名數量
DOMAIN_COUNT=$(grep -v "^$\|^#" "$DOMAINS_FILE" | wc -l | tr -d ' ')
echo ""
echo "📊 域名數量: $DOMAIN_COUNT"
echo ""

# 上傳域名文件
echo "📤 上傳域名文件..."
scp -i ~/.ssh/globalping-checker-key.pem \
    "$DOMAINS_FILE" \
    ec2-user@$PUBLIC_IP:/tmp/domains.txt

# 移動文件
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP << 'EOF'
sudo mv /tmp/domains.txt /opt/globalping-checker/domains.txt
sudo chown $(whoami):$(whoami) /opt/globalping-checker/domains.txt
EOF

echo ""
echo "✅ 域名列表已更新！"
echo ""
echo "📋 更新內容："
echo "  ✓ 域名數量: $DOMAIN_COUNT"
echo "  ✓ 文件位置: /opt/globalping-checker/domains.txt"
echo ""
echo "🔧 執行檢測："
echo "  ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
echo ""
