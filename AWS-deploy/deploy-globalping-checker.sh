#!/bin/bash

# Globalping Checker 自動部署腳本
# 用途：部署 Globalping 域名檢測系統到 AWS EC2

set -e

# 禁用代理（避免 AWS CLI 連線問題）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

REGION="ap-northeast-1"
KEY_NAME="globalping-checker-key"
SECURITY_GROUP_NAME="globalping-checker-sg"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 開始部署 Globalping Checker 到 AWS EC2..."

# 檢查是否已有實例
EXISTING_INSTANCE=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:Name,Values=Globalping-Checker-Server" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress]' \
    --output text)

if [ "$EXISTING_INSTANCE" != "None" ] && [ -n "$EXISTING_INSTANCE" ]; then
    INSTANCE_ID=$(echo $EXISTING_INSTANCE | awk '{print $1}')
    INSTANCE_STATE=$(echo $EXISTING_INSTANCE | awk '{print $2}')
    PUBLIC_IP=$(echo $EXISTING_INSTANCE | awk '{print $3}')
    
    echo "✅ 找到現有實例: $INSTANCE_ID"
    echo "   狀態: $INSTANCE_STATE"
    echo "   IP: $PUBLIC_IP"
    echo ""
    echo "請選擇操作："
    echo "  1) 更新現有實例（推薦）"
    echo "  2) 刪除並重新部署"
    echo "  3) 取消"
    echo ""
    read -p "選擇 (1-3): " CHOICE
    
    case $CHOICE in
        1)
            echo ""
            echo "🔄 更新現有實例..."
            
            # 如果實例停止，先啟動
            if [ "$INSTANCE_STATE" = "stopped" ]; then
                echo "⏳ 啟動實例..."
                aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID
                aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID
                
                PUBLIC_IP=$(aws ec2 describe-instances \
                    --region $REGION \
                    --instance-ids $INSTANCE_ID \
                    --query 'Reservations[0].Instances[0].PublicIpAddress' \
                    --output text)
                
                echo "✅ 實例已啟動: $PUBLIC_IP"
                sleep 30
            fi
            
            # 跳到更新流程
            UPDATE_MODE=true
            ;;
        2)
            echo ""
            echo "🗑️  終止舊實例..."
            aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID
            aws ec2 wait instance-terminated --region $REGION --instance-ids $INSTANCE_ID
            echo "✅ 舊實例已終止"
            UPDATE_MODE=false
            ;;
        3)
            echo "取消操作"
            exit 0
            ;;
        *)
            echo "❌ 無效選擇"
            exit 1
            ;;
    esac
fi

# 如果是更新模式，跳過創建新實例
if [ "$UPDATE_MODE" = "true" ]; then
    echo ""
    echo "📤 上傳最新代碼..."
    
    # 上傳項目文件
    scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -r \
        "$PROJECT_DIR/GlobalpingChecker" \
        ec2-user@$PUBLIC_IP:~/
    
    # 更新安裝
    echo "🔄 更新系統..."
    ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
cd ~/GlobalpingChecker/ec2
chmod +x setup.sh
./setup.sh <<< "n"  # 不重新設置 cron
EOF
    
    echo ""
    echo "🎉 更新完成！"
    echo ""
    echo "📊 實例資訊："
    echo "  ID: $INSTANCE_ID"
    echo "  IP: $PUBLIC_IP"
    echo ""
    echo "🔧 管理命令："
    echo "  執行檢測: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
    echo "  查看日誌: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'tail -f /var/log/globalping-checker/check_*.log'"
    echo ""
    exit 0
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
    echo "✅ SSH 密鑰已創建並設置權限"
else
    echo "✅ SSH 密鑰已存在，檢查權限..."
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
        --description "Security group for Globalping Checker" \
        --query 'GroupId' \
        --output text)
    
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
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Globalping-Checker-Server},{Key=Project,Value=GlobalpingChecker}]' \
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
echo "⏳ 等待 SSH 就緒（約 60 秒）..."
sleep 60

# 測試 SSH 連線
echo "🔍 測試 SSH 連線..."
MAX_RETRIES=5
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$PUBLIC_IP "echo 'SSH 連線成功'" 2>/dev/null; then
        echo "✅ SSH 連線測試成功"
        break
    else
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRIES ]; then
            echo "⏳ SSH 尚未就緒，等待 10 秒後重試 ($RETRY/$MAX_RETRIES)..."
            sleep 10
        else
            echo "❌ SSH 連線失敗，請檢查："
            echo "  1. 安全組是否允許 SSH (port 22)"
            echo "  2. 密鑰權限: ls -la ~/.ssh/$KEY_NAME.pem"
            echo "  3. 手動測試: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
            exit 1
        fi
    fi
done

# 上傳項目文件
echo "📤 上傳項目文件..."
scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no -r \
    "$PROJECT_DIR/GlobalpingChecker" \
    ec2-user@$PUBLIC_IP:~/

# 執行安裝
echo "📦 執行安裝腳本..."
ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
cd ~/GlobalpingChecker/ec2
chmod +x setup.sh
./setup.sh <<< "y"
EOF

# 上傳測試域名
echo "📝 上傳測試域名..."
scp -i ~/.ssh/$KEY_NAME.pem \
    "$PROJECT_DIR/GlobalpingChecker/test_2_domains.txt" \
    ec2-user@$PUBLIC_IP:/tmp/domains.txt

ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP << 'EOF'
sudo mv /tmp/domains.txt /opt/globalping-checker/domains.txt
sudo chown $(whoami):$(whoami) /opt/globalping-checker/domains.txt
EOF

echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 實例資訊："
echo "  ID: $INSTANCE_ID"
echo "  IP: $PUBLIC_IP"
echo "  區域: $REGION"
echo ""
echo "🔧 管理命令："
echo "  SSH 連線: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo "  執行檢測: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
echo "  查看日誌: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'tail -f /var/log/globalping-checker/check_*.log'"
echo "  查看狀態: bash AWS-deploy/check-globalping-status.sh"
echo "  更新配置: bash AWS-deploy/update-globalping-config.sh"
echo ""
echo "💡 下一步："
echo "  1. 編輯配置: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'sudo nano /opt/globalping-checker/config.env'"
echo "  2. 上傳域名: bash AWS-deploy/update-globalping-domains.sh"
echo "  3. 執行測試: ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP '/opt/globalping-checker/run_check.sh'"
echo ""
