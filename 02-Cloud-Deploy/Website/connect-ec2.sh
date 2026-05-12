#!/bin/bash

# AWS EC2 快速連線腳本
# 使用方式：
#   ./connect-ec2.sh                    # 列出所有實例
#   ./connect-ec2.sh <instance-id>       # 連線到指定實例
#   ./connect-ec2.sh <instance-id> ssh  # 強制使用 SSH

set -e

INSTANCE_ID=$1
MODE=$2

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 AWS CLI 是否安裝
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ 錯誤：未安裝 AWS CLI${NC}"
    echo "請執行：brew install awscli"
    exit 1
fi

# 如果沒有提供實例 ID，列出所有實例
if [ -z "$INSTANCE_ID" ]; then
    echo -e "${GREEN}📋 可用的 EC2 實例：${NC}"
    echo ""
    aws ec2 describe-instances \
      --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,State.Name]' \
      --output table
    echo ""
    echo "使用方式："
    echo "  ./connect-ec2.sh <instance-id>        # 自動選擇最佳連線方式"
    echo "  ./connect-ec2.sh <instance-id> ssh    # 強制使用 SSH"
    exit 0
fi

# 取得實例資訊
echo -e "${YELLOW}🔍 查詢實例資訊...${NC}"
INSTANCE_INFO=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0]' \
  --output json 2>/dev/null)

if [ -z "$INSTANCE_INFO" ] || [ "$INSTANCE_INFO" == "null" ]; then
    echo -e "${RED}❌ 錯誤：找不到實例 $INSTANCE_ID${NC}"
    exit 1
fi

# 解析實例資訊
INSTANCE_NAME=$(echo $INSTANCE_INFO | jq -r '.Tags[]? | select(.Key=="Name") | .Value // "N/A"')
PUBLIC_IP=$(echo $INSTANCE_INFO | jq -r '.PublicIpAddress // "N/A"')
PRIVATE_IP=$(echo $INSTANCE_INFO | jq -r '.PrivateIpAddress')
STATE=$(echo $INSTANCE_INFO | jq -r '.State.Name')
KEY_NAME=$(echo $INSTANCE_INFO | jq -r '.KeyName // "N/A"')
IMAGE_ID=$(echo $INSTANCE_INFO | jq -r '.ImageId')

# 判斷 AMI 類型以決定預設用戶名
if echo $IMAGE_ID | grep -q "ubuntu"; then
    DEFAULT_USER="ubuntu"
elif echo $IMAGE_ID | grep -q "debian"; then
    DEFAULT_USER="admin"
else
    DEFAULT_USER="ec2-user"
fi

echo ""
echo -e "${GREEN}📋 實例資訊：${NC}"
echo "  名稱: $INSTANCE_NAME"
echo "  狀態: $STATE"
echo "  公網 IP: $PUBLIC_IP"
echo "  私網 IP: $PRIVATE_IP"
echo "  Key Pair: $KEY_NAME"
echo "  預設用戶: $DEFAULT_USER"
echo ""

# 檢查實例狀態
if [ "$STATE" != "running" ]; then
    echo -e "${RED}❌ 錯誤：實例狀態為 $STATE，無法連線${NC}"
    exit 1
fi

# 決定連線方式
if [ "$MODE" == "ssh" ] || [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" == "N/A" ]; then
    # 使用 SSH
    if [ "$KEY_NAME" == "N/A" ] || [ ! -f ~/.ssh/${KEY_NAME}.pem ]; then
        echo -e "${RED}❌ 錯誤：找不到 SSH key${NC}"
        echo "  預期位置：~/.ssh/${KEY_NAME}.pem"
        echo ""
        echo "請確認："
        echo "  1. Key Pair 名稱：$KEY_NAME"
        echo "  2. Key 檔案是否存在：~/.ssh/${KEY_NAME}.pem"
        echo "  3. Key 檔案權限：chmod 400 ~/.ssh/${KEY_NAME}.pem"
        exit 1
    fi

    echo -e "${GREEN}🔐 使用 SSH 連線...${NC}"
    echo ""
    ssh -i ~/.ssh/${KEY_NAME}.pem $DEFAULT_USER@$PUBLIC_IP

else
    # 嘗試使用 SSM Session Manager
    echo -e "${YELLOW}🔄 嘗試使用 SSM Session Manager...${NC}"
    
    if aws ssm start-session --target $INSTANCE_ID 2>/dev/null; then
        echo -e "${GREEN}✅ 使用 SSM Session Manager 連線成功${NC}"
    else
        echo -e "${YELLOW}⚠️  SSM Session Manager 不可用，改用 SSH...${NC}"
        
        if [ "$PUBLIC_IP" == "N/A" ]; then
            echo -e "${RED}❌ 錯誤：實例沒有公網 IP，且 SSM 不可用${NC}"
            echo "請確認："
            echo "  1. 實例已安裝 SSM Agent"
            echo "  2. 實例有正確的 IAM Role 權限"
            exit 1
        fi

        if [ "$KEY_NAME" == "N/A" ] || [ ! -f ~/.ssh/${KEY_NAME}.pem ]; then
            echo -e "${RED}❌ 錯誤：找不到 SSH key${NC}"
            exit 1
        fi

        echo -e "${GREEN}🔐 使用 SSH 連線...${NC}"
        echo ""
        ssh -i ~/.ssh/${KEY_NAME}.pem $DEFAULT_USER@$PUBLIC_IP
    fi
fi
