#!/bin/bash

# 檢查 Globalping Checker 伺服器狀態

echo "🔍 檢查 Globalping Checker EC2 實例狀態..."

# 獲取實例資訊
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=Globalping-Checker-Server" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,InstanceType]' \
    --output text)

if [ -z "$INSTANCE_INFO" ]; then
    echo "❌ 找不到 Globalping-Checker-Server 實例"
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
    
    # 檢查定時任務
    echo "📅 檢查定時任務..."
    ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP 'crontab -l 2>/dev/null | grep globalping' || echo "  ⚠️  未設置定時任務"
    
    echo ""
    echo "📝 最近的日誌："
    ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP 'ls -lt /var/log/globalping-checker/*.log 2>/dev/null | head -3' || echo "  ⚠️  尚無日誌"
    
    echo ""
    echo "🔧 管理命令："
    echo "  SSH 連線: ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP"
    echo "  執行檢測: ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
    echo "  查看日誌: ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@$PUBLIC_IP 'tail -f /var/log/globalping-checker/check_*.log'"
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
