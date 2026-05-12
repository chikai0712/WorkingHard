#!/bin/bash

# DNS 監控系統自動部署腳本
# 用途：部署 DNS 監控系統到 AWS EC2

set -e

# 禁用代理（避免 AWS CLI 連線問題）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

REGION="ap-northeast-1"
KEY_NAME="dns-monitoring-key"
SECURITY_GROUP_NAME="dns-monitoring-sg"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 開始部署 DNS 監控系統到 AWS EC2..."

# 檢查是否已有實例
EXISTING_INSTANCE=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:Name,Values=DNS-Monitoring-Server" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$EXISTING_INSTANCE" != "None" ] && [ -n "$EXISTING_INSTANCE" ]; then
    echo "⚠️  已存在實例: $EXISTING_INSTANCE"
    read -p "是否要刪除舊實例並重新部署? (y/N): " CONFIRM
    if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "🗑️  終止舊實例..."
        aws ec2 terminate-instances --region $REGION --instance-ids $EXISTING_INSTANCE
        aws ec2 wait instance-terminated --region $REGION --instance-ids $EXISTING_INSTANCE
    else
        echo "取消部署"
        exit 1
    fi
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
        --description "Security group for DNS Monitoring System" \
        --query 'GroupId' \
        --output text)
    
    # 允許 HTTP (API)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0
    
    # 允許 SSH
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0
fi

# 創建 EC2 實例 (使用較大的實例類型)
echo "🖥️  創建 EC2 實例..."
INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id ami-0d52744d6551d851e \
    --instance-type t3.small \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=30,VolumeType=gp3}' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=DNS-Monitoring-Server},{Key=Project,Value=DNSMonitoring}]' \
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

# 上傳項目文件
echo "📤 上傳項目文件..."
scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -r \
    "$PROJECT_DIR/domain-monitoring-system" \
    ec2-user@$PUBLIC_IP:~/

# 安裝系統
echo "📦 安裝系統依賴..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
# 更新系統
sudo yum update -y

# 安裝 Python 3.9+
sudo yum install -y python3 python3-pip git

# 安裝 PostgreSQL
sudo yum install -y postgresql postgresql-server postgresql-devel

# 初始化資料庫
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 安裝 Redis
sudo yum install -y redis
sudo systemctl start redis
sudo systemctl enable redis

# 進入項目目錄
cd ~/domain-monitoring-system

# 安裝 Python 依賴
pip3 install -r requirements.txt

# 複製環境變數範例
cp env.example .env

echo "✅ 系統依賴安裝完成"
EOF

echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 實例資訊："
echo "  ID: $INSTANCE_ID"
echo "  IP: $PUBLIC_IP"
echo "  區域: $REGION"
echo ""
echo "⚠️  重要：需要手動配置"
echo ""
echo "1. SSH 連線到伺服器："
echo "   ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "2. 配置資料庫："
echo "   cd ~/domain-monitoring-system"
echo "   sudo -u postgres psql"
echo "   CREATE DATABASE dns_monitoring;"
echo "   CREATE USER dns_user WITH PASSWORD 'your_password';"
echo "   GRANT ALL PRIVILEGES ON DATABASE dns_monitoring TO dns_user;"
echo "   \\q"
echo ""
echo "3. 編輯環境變數："
echo "   nano ~/domain-monitoring-system/.env"
echo ""
echo "4. 初始化資料庫："
echo "   cd ~/domain-monitoring-system"
echo "   ./init_db.sh"
echo ""
echo "5. 啟動服務："
echo "   ./start.sh"
echo ""
echo "6. 訪問 API："
echo "   http://$PUBLIC_IP:8000/docs"
echo ""
echo "🔧 管理命令："
echo "  查看狀態: bash AWS-deploy/check-dns-monitoring-status.sh"
echo "  停止實例: aws ec2 stop-instances --instance-ids $INSTANCE_ID --region ap-northeast-1"
echo ""
