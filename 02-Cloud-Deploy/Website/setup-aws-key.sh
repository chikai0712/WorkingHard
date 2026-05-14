#!/bin/bash

# AWS 金鑰連線設定腳本
# 協助你快速設定 AWS Key Pair 並測試連線

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 AWS 金鑰連線設定助手${NC}"
echo ""

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ 錯誤：未安裝 AWS CLI${NC}"
    echo "請先安裝："
    echo "  macOS: brew install awscli"
    echo "  Linux: 參考 https://aws.amazon.com/cli/"
    exit 1
fi

# 檢查 AWS 憑證
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ 錯誤：AWS 憑證未設定${NC}"
    echo "請執行：aws configure"
    exit 1
fi

# 步驟 1：建立或選擇 Key Pair
echo -e "${YELLOW}📋 步驟 1：Key Pair 設定${NC}"
echo ""

# 列出現有的 Key Pairs
echo "現有的 Key Pairs："
aws ec2 describe-key-pairs --query 'KeyPairs[*].KeyName' --output table
echo ""

read -p "要建立新的 Key Pair 嗎？(y/n): " create_new

if [ "$create_new" == "y" ] || [ "$create_new" == "Y" ]; then
    read -p "輸入 Key Pair 名稱（例如：my-ec2-key）: " KEY_NAME
    
    if [ -z "$KEY_NAME" ]; then
        echo -e "${RED}❌ 錯誤：Key Pair 名稱不能為空${NC}"
        exit 1
    fi
    
    # 檢查是否已存在
    if aws ec2 describe-key-pairs --key-names "$KEY_NAME" &> /dev/null; then
        echo -e "${YELLOW}⚠️  Key Pair '$KEY_NAME' 已存在${NC}"
        read -p "要使用現有的 Key Pair 嗎？(y/n): " use_existing
        if [ "$use_existing" != "y" ] && [ "$use_existing" != "Y" ]; then
            exit 0
        fi
    else
        # 建立新的 Key Pair
        echo -e "${GREEN}🔨 建立新的 Key Pair...${NC}"
        mkdir -p ~/.ssh
        
        aws ec2 create-key-pair \
          --key-name "$KEY_NAME" \
          --query 'KeyMaterial' \
          --output text > ~/.ssh/${KEY_NAME}.pem
        
        # 設定權限
        chmod 400 ~/.ssh/${KEY_NAME}.pem
        
        echo -e "${GREEN}✅ Key Pair 已建立：~/.ssh/${KEY_NAME}.pem${NC}"
    fi
else
    read -p "輸入要使用的 Key Pair 名稱: " KEY_NAME
    
    if [ ! -f ~/.ssh/${KEY_NAME}.pem ]; then
        echo -e "${RED}❌ 錯誤：找不到 key 檔案 ~/.ssh/${KEY_NAME}.pem${NC}"
        echo "請確認："
        echo "  1. Key Pair 名稱正確"
        echo "  2. Key 檔案已下載到 ~/.ssh/"
        exit 1
    fi
fi

# 確認 key 檔案權限
if [ -f ~/.ssh/${KEY_NAME}.pem ]; then
    PERM=$(stat -f "%A" ~/.ssh/${KEY_NAME}.pem 2>/dev/null || stat -c "%a" ~/.ssh/${KEY_NAME}.pem 2>/dev/null)
    if [ "$PERM" != "400" ] && [ "$PERM" != "600" ]; then
        echo -e "${YELLOW}⚠️  修正 key 檔案權限...${NC}"
        chmod 400 ~/.ssh/${KEY_NAME}.pem
        echo -e "${GREEN}✅ 權限已設定為 400${NC}"
    fi
fi

echo ""

# 步驟 2：列出 EC2 實例
echo -e "${YELLOW}📋 步驟 2：選擇 EC2 實例${NC}"
echo ""

INSTANCES=$(aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,State.Name,KeyName]' \
  --output text)

if [ -z "$INSTANCES" ]; then
    echo -e "${RED}❌ 沒有找到運行中的 EC2 實例${NC}"
    echo ""
    echo "請先："
    echo "  1. 在 AWS Console 啟動一個 EC2 實例"
    echo "  2. 確保選擇了 Key Pair: $KEY_NAME"
    exit 1
fi

echo "可用的 EC2 實例："
echo ""
printf "%-20s %-30s %-18s %-12s %-20s\n" "Instance ID" "Name" "Public IP" "State" "Key Name"
echo "--------------------------------------------------------------------------------"
echo "$INSTANCES" | while read -r line; do
    if [ -n "$line" ]; then
        printf "%-20s %-30s %-18s %-12s %-20s\n" $line
    fi
done
echo ""

read -p "輸入要連線的 Instance ID（或按 Enter 跳過）: " INSTANCE_ID

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${YELLOW}⏭️  跳過連線測試${NC}"
    echo ""
    echo -e "${GREEN}✅ 設定完成！${NC}"
    echo ""
    echo "Key Pair 資訊："
    echo "  名稱: $KEY_NAME"
    echo "  檔案: ~/.ssh/${KEY_NAME}.pem"
    echo ""
    echo "連線範例："
    echo "  ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@<EC2-IP>"
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

PUBLIC_IP=$(echo $INSTANCE_INFO | jq -r '.PublicIpAddress // "N/A"')
STATE=$(echo $INSTANCE_INFO | jq -r '.State.Name')
INSTANCE_KEY=$(echo $INSTANCE_INFO | jq -r '.KeyName // "N/A"')
IMAGE_ID=$(echo $INSTANCE_INFO | jq -r '.ImageId')

# 檢查實例狀態
if [ "$STATE" != "running" ]; then
    echo -e "${RED}❌ 錯誤：實例狀態為 $STATE，無法連線${NC}"
    exit 1
fi

# 檢查 Key Pair 是否匹配
if [ "$INSTANCE_KEY" != "$KEY_NAME" ]; then
    echo -e "${YELLOW}⚠️  警告：實例使用的 Key Pair ($INSTANCE_KEY) 與你選擇的不同 ($KEY_NAME)${NC}"
    read -p "要繼續嗎？(y/n): " continue_anyway
    if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
        exit 0
    fi
fi

# 判斷用戶名
if echo $IMAGE_ID | grep -q "ubuntu"; then
    USERNAME="ubuntu"
elif echo $IMAGE_ID | grep -q "debian"; then
    USERNAME="admin"
else
    USERNAME="ec2-user"
fi

echo ""
echo -e "${GREEN}📋 實例資訊：${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  公網 IP: $PUBLIC_IP"
echo "  狀態: $STATE"
echo "  Key Pair: $INSTANCE_KEY"
echo "  用戶名: $USERNAME"
echo ""

if [ "$PUBLIC_IP" == "N/A" ]; then
    echo -e "${RED}❌ 錯誤：實例沒有公網 IP${NC}"
    echo "請使用 AWS Systems Manager Session Manager："
    echo "  aws ssm start-session --target $INSTANCE_ID"
    exit 1
fi

# 步驟 3：測試連線
echo -e "${YELLOW}📋 步驟 3：測試連線${NC}"
echo ""

read -p "要現在測試連線嗎？(y/n): " test_connection

if [ "$test_connection" == "y" ] || [ "$test_connection" == "Y" ]; then
    echo -e "${GREEN}🔐 嘗試連線...${NC}"
    echo ""
    echo "連線命令："
    echo "  ssh -i ~/.ssh/${KEY_NAME}.pem $USERNAME@$PUBLIC_IP"
    echo ""
    echo "如果這是第一次連線，會詢問是否繼續，輸入 'yes'"
    echo ""
    
    # 實際連線
    ssh -i ~/.ssh/${KEY_NAME}.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no $USERNAME@$PUBLIC_IP "echo '✅ 連線成功！'; hostname; whoami" 2>&1 || {
        echo ""
        echo -e "${RED}❌ 連線失敗${NC}"
        echo ""
        echo "可能的原因："
        echo "  1. Security Group 未開放 port 22"
        echo "  2. Key Pair 不匹配"
        echo "  3. 實例正在啟動中，請稍候再試"
        echo ""
        echo "手動測試："
        echo "  ssh -i ~/.ssh/${KEY_NAME}.pem $USERNAME@$PUBLIC_IP"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✅ 連線測試成功！${NC}"
    echo ""
    read -p "要現在開啟 SSH 連線嗎？(y/n): " open_ssh
    
    if [ "$open_ssh" == "y" ] || [ "$open_ssh" == "Y" ]; then
        echo -e "${GREEN}🚀 開啟 SSH 連線...${NC}"
        ssh -i ~/.ssh/${KEY_NAME}.pem $USERNAME@$PUBLIC_IP
    fi
else
    echo ""
    echo -e "${GREEN}✅ 設定完成！${NC}"
    echo ""
    echo "手動連線命令："
    echo "  ssh -i ~/.ssh/${KEY_NAME}.pem $USERNAME@$PUBLIC_IP"
fi

echo ""
echo -e "${BLUE}💡 提示：${NC}"
echo "  要簡化連線，可以設定 ~/.ssh/config："
echo ""
echo "  Host ec2-$(echo $INSTANCE_ID | cut -c1-8)"
echo "      HostName $PUBLIC_IP"
echo "      User $USERNAME"
echo "      IdentityFile ~/.ssh/${KEY_NAME}.pem"
echo ""
echo "  然後使用：ssh ec2-$(echo $INSTANCE_ID | cut -c1-8)"
