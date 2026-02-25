#!/bin/bash

# 檢查寶可夢遊戲伺服器狀態

echo "🔍 檢查 EC2 實例狀態..."

# 獲取實例資訊
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=Pokemon-Game-Server" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,InstanceType]' \
    --output text)

if [ -z "$INSTANCE_INFO" ]; then
    echo "❌ 找不到 Pokemon-Game-Server 實例"
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
    echo "🎮 遊戲網址: http://$PUBLIC_IP"
    echo ""
    echo "🔧 管理命令："
    echo "  更新遊戲: bash update-pokemon-game.sh"
    echo "  停止實例: aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-northeast-1"
    echo "  SSH 連線: ssh -i ~/.ssh/pokemon-game-key.pem ec2-user@$PUBLIC_IP"
elif [ "$STATE" == "stopped" ]; then
    echo "⏸️  實例已停止"
    echo ""
    echo "🔧 啟動命令："
    echo "  aws ec2 start-instances --instance-ids $INSTANCE_ID --region ap-northeast-1"
else
    echo "⚠️  實例狀態: $STATE"
fi

echo ""

