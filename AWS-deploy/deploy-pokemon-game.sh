#!/bin/bash

# 寶可夢遊戲完整部署腳本
# 用途：創建 EC2 實例並部署遊戲

set -e

# 禁用代理（避免 AWS CLI 連線問題）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

REGION="ap-northeast-1"
KEY_NAME="pokemon-game-key"
SECURITY_GROUP_NAME="pokemon-game-sg"

echo "🚀 開始部署寶可夢遊戲到 AWS EC2..."

# 檢查是否已有實例
EXISTING_INSTANCE=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:Name,Values=Pokemon-Game-Server" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$EXISTING_INSTANCE" != "None" ] && [ -n "$EXISTING_INSTANCE" ]; then
    echo "⚠️  已存在實例: $EXISTING_INSTANCE"
    echo "請使用 update-pokemon-game.sh 更新遊戲"
    exit 1
fi

# 創建密鑰對
if [ ! -f ~/.ssh/$KEY_NAME.pem ]; then
    echo "🔑 創建 SSH 密鑰..."
    aws ec2 create-key-pair \
        --region $REGION \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/$KEY_NAME.pem
    chmod 400 ~/.ssh/$KEY_NAME.pem
fi

# 創建安全組
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

if [ "$SECURITY_GROUP_ID" == "None" ] || [ -z "$SECURITY_GROUP_ID" ]; then
    echo "🔒 創建安全組..."
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --region $REGION \
        --group-name $SECURITY_GROUP_NAME \
        --description "Security group for Pokemon game server" \
        --query 'GroupId' \
        --output text)
    
    # 允許 HTTP
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0
    
    # 允許 SSH
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0
fi

# 創建 EC2 實例
echo "🖥️  創建 EC2 實例..."
INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id ami-0d52744d6551d851e \
    --instance-type t3.micro \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Pokemon-Game-Server}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "⏳ 等待實例啟動..."
aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID

PUBLIC_IP=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ 實例已啟動: $PUBLIC_IP"
echo "⏳ 等待 SSH 就緒..."
sleep 30

# 安裝 Nginx
echo "📦 安裝 Nginx..."
ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no ec2-user@$PUBLIC_IP << 'EOF'
sudo yum update -y
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
EOF

# 上傳遊戲文件
echo "📤 上傳遊戲文件..."
scp -i ~/.ssh/$KEY_NAME.pem Ollie/pokemon_game.html ec2-user@$PUBLIC_IP:/tmp/index.html

ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
sudo mv /tmp/index.html /usr/share/nginx/html/index.html
sudo chown nginx:nginx /usr/share/nginx/html/index.html
sudo chmod 644 /usr/share/nginx/html/index.html
EOF

echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 實例資訊："
echo "  ID: $INSTANCE_ID"
echo "  IP: $PUBLIC_IP"
echo "  區域: $REGION"
echo ""
echo "🎮 遊戲網址: http://$PUBLIC_IP"
echo ""
echo "🔧 管理命令："
echo "  更新遊戲: bash update-pokemon-game.sh"
echo "  查看狀態: bash check-game-status.sh"
echo "  停止實例: aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""

