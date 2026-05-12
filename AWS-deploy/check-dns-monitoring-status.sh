#!/bin/bash

# 檢查 DNS 監控系統伺服器狀態

echo "🔍 檢查 DNS 監控系統 EC2 實例狀態..."

# 獲取實例資訊
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=DNS-Monitoring-Server" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,InstanceType]' \
    --output text)

if [ -z "$INSTANCE_INFO" ]; then
    echo "❌ 找不到 DNS-Monitoring-Server 實例"
    exit 1
fi

INSTANCE_ID=$(echo $INSTANCE_INFO | awk '{print $1}')
STATE=$(echo $INSTANCE_INFO | awk '{print $2}')
PUBLIC_IP=$(echo $INSTANCE_INFO | awk '{print $3}')
INSTANCE_TYPE=$(echo $INSTANCE_INFO | awk '{print $4}')

echo ""
echo "📊 實例資訊："
echo "  ID: $INSTANCE_ID"
echo "  狀態: $STATE"
echo "  類型: $INSTANCE_TYPE"
echo "  IP: $PUBLIC_IP"
echo ""

if [ "$STATE" == "running" ]; then
    echo "✅ 實例正在運行"
    echo ""
    
    # 檢查服務狀態
    echo "🔧 檢查服務狀態..."
    ssh -i ~/.ssh/dns-monitoring-key.pem ec2-user@$PUBLIC_IP << 'EOF'
# 檢查 PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo "  ✅ PostgreSQL: 運行中"
else
    echo "  ❌ PostgreSQL: 未運行"
fi

# 檢查 Redis
if systemctl is-active --quiet redis; then
    echo "  ✅ Redis: 運行中"
else
    echo "  ❌ Redis: 未運行"
fi

# 檢查 API 服務
if pgrep -f "uvicorn" > /dev/null; then
    echo "  ✅ API 服務: 運行中"
else
    echo "  ❌ API 服務: 未運行"
fi
EOF
    
    echo ""
    echo "🌐 API 端點："
    echo "  http://$PUBLIC_IP:8000/docs"
    echo ""
    echo "🔧 管理命令："
    echo "  SSH 連線: ssh -i ~/.ssh/dns-monitoring-key.pem ec2-user@$PUBLIC_IP"
    echo "  查看日誌: ssh -i ~/.ssh/dns-monitoring-key.pem ec2-user@$PUBLIC_IP 'tail -f ~/domain-monitoring-system/logs/*.log'"
    echo "  重啟服務: ssh -i ~/.ssh/dns-monitoring-key.pem ec2-user@$PUBLIC_IP 'cd ~/domain-monitoring-system && ./start.sh'"
    echo "  停止實例: aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-northeast-1"
elif [ "$STATE" == "stopped" ]; then
    echo "⏸️  實例已停止"
    echo ""
    echo "🔧 啟動命令："
    echo "  aws ec2 start-instances --instance-ids $INSTANCE_ID --region ap-northeast-1"
else
    echo "⚠️  實例狀態: $STATE"
fi

echo ""
