#!/bin/bash

# 寶可夢遊戲更新腳本
# 用途：將本地的 pokemon_game.html 更新到 AWS EC2

set -e

echo "🎮 開始更新寶可夢遊戲..."

# 獲取 EC2 實例 IP
INSTANCE_ID=$(aws ec2 describe-instances \
    --region ap-northeast-1 \
    --filters "Name=tag:Name,Values=Pokemon-Game-Server" "Name=instance-state-name,Values=running" \
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

# 上傳遊戲文件
echo "📤 上傳遊戲文件..."
scp -i ~/.ssh/pokemon-game-key.pem \
    Ollie/pokemon_game.html \
    ec2-user@$PUBLIC_IP:/tmp/index.html

# 移動文件到 Nginx 目錄
echo "🔄 更新網站文件..."
ssh -i ~/.ssh/pokemon-game-key.pem ec2-user@$PUBLIC_IP << 'EOF'
sudo mv /tmp/index.html /usr/share/nginx/html/index.html
sudo chown nginx:nginx /usr/share/nginx/html/index.html
sudo chmod 644 /usr/share/nginx/html/index.html
sudo systemctl reload nginx
EOF

echo ""
echo "✅ 更新完成！"
echo ""
echo "🎮 遊戲網址: http://$PUBLIC_IP"
echo ""
echo "📋 更新內容："
echo "  ✓ pokemon_game.html → index.html"
echo ""
echo "立即訪問遊戲查看更新！🎮"

