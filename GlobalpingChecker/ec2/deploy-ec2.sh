#!/bin/bash

# ============================================
# Globalping Checker - EC2 部署腳本
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

STACK_NAME="GlobalpingCheckerEC2"
REGION="${AWS_REGION:-ap-northeast-1}"

echo -e "${BLUE}========================================"
echo "Globalping Checker - EC2 部署"
echo "========================================${NC}"
echo ""

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}錯誤: 未安裝 AWS CLI${NC}"
    exit 1
fi

# 檢查 AWS 憑證
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}錯誤: AWS 憑證未配置${NC}"
    exit 1
fi

echo -e "${GREEN}✓ AWS CLI 已配置${NC}"
echo ""

# 列出可用的 Key Pairs
echo -e "${BLUE}可用的 SSH Key Pairs:${NC}"
aws ec2 describe-key-pairs --region "$REGION" --query 'KeyPairs[*].KeyName' --output table

echo ""
read -p "輸入 SSH Key Pair 名稱: " KEY_NAME

if [ -z "$KEY_NAME" ]; then
    echo -e "${RED}錯誤: 必須指定 Key Pair${NC}"
    exit 1
fi

# 其他參數
read -p "輸入實例類型 (預設: t3.micro): " INSTANCE_TYPE
INSTANCE_TYPE=${INSTANCE_TYPE:-t3.micro}

read -p "輸入 SSH 訪問來源 IP (預設: 0.0.0.0/0): " SSH_LOCATION
SSH_LOCATION=${SSH_LOCATION:-0.0.0.0/0}

read -p "輸入 Globalping API Token (可選): " GLOBALPING_TOKEN

read -p "輸入 S3 Bucket 名稱 (可選): " S3_BUCKET

echo ""
echo -e "${BLUE}部署參數:${NC}"
echo "  Stack 名稱: $STACK_NAME"
echo "  AWS 區域: $REGION"
echo "  實例類型: $INSTANCE_TYPE"
echo "  SSH Key: $KEY_NAME"
echo "  SSH 來源: $SSH_LOCATION"
echo "  API Token: ${GLOBALPING_TOKEN:+已設置}"
echo "  S3 Bucket: ${S3_BUCKET:-未設置}"
echo ""

read -p "確認部署? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "取消部署"
    exit 0
fi

echo ""
echo -e "${YELLOW}開始部署 CloudFormation Stack...${NC}"

# 準備參數
PARAMS="ParameterKey=InstanceType,ParameterValue=$INSTANCE_TYPE"
PARAMS="$PARAMS ParameterKey=KeyName,ParameterValue=$KEY_NAME"
PARAMS="$PARAMS ParameterKey=SSHLocation,ParameterValue=$SSH_LOCATION"

if [ -n "$GLOBALPING_TOKEN" ]; then
    PARAMS="$PARAMS ParameterKey=GlobalpingToken,ParameterValue=$GLOBALPING_TOKEN"
fi

if [ -n "$S3_BUCKET" ]; then
    PARAMS="$PARAMS ParameterKey=S3BucketName,ParameterValue=$S3_BUCKET"
fi

# 部署 Stack
aws cloudformation deploy \
    --template-file cloudformation-ec2.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides $PARAMS \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION"

echo -e "${GREEN}✓ CloudFormation Stack 已部署${NC}"
echo ""

# 獲取輸出
echo -e "${YELLOW}獲取部署信息...${NC}"

INSTANCE_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" \
    --output text)

PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='PublicIP'].OutputValue" \
    --output text)

echo -e "${GREEN}✓ EC2 實例已創建${NC}"
echo ""

# 等待實例啟動
echo -e "${YELLOW}等待 EC2 實例啟動...${NC}"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
echo -e "${GREEN}✓ EC2 實例已啟動${NC}"
echo ""

# 等待 SSH 可用
echo -e "${YELLOW}等待 SSH 服務啟動 (約 30 秒)...${NC}"
sleep 30

echo -e "${GREEN}✓ 部署完成！${NC}"
echo ""

echo -e "${BLUE}========================================"
echo "部署信息"
echo "========================================${NC}"
echo "Stack 名稱: $STACK_NAME"
echo "AWS 區域: $REGION"
echo "實例 ID: $INSTANCE_ID"
echo "公網 IP: $PUBLIC_IP"
echo ""

echo -e "${BLUE}========================================"
echo "下一步操作"
echo "========================================${NC}"
echo ""
echo "1. SSH 連線到 EC2:"
echo -e "   ${YELLOW}ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP}${NC}"
echo ""
echo "2. 上傳安裝腳本和項目文件:"
echo -e "   ${YELLOW}scp -i ${KEY_NAME}.pem -r ../GlobalpingChecker ec2-user@${PUBLIC_IP}:~/${NC}"
echo ""
echo "3. 在 EC2 上執行安裝:"
echo -e "   ${YELLOW}cd ~/GlobalpingChecker/ec2${NC}"
echo -e "   ${YELLOW}chmod +x setup.sh${NC}"
echo -e "   ${YELLOW}./setup.sh${NC}"
echo ""
echo "4. 編輯配置文件:"
echo -e "   ${YELLOW}nano /opt/globalping-checker/config.env${NC}"
echo ""
echo "5. 上傳域名列表:"
echo -e "   ${YELLOW}nano /opt/globalping-checker/domains.txt${NC}"
echo ""
echo "6. 執行測試:"
echo -e "   ${YELLOW}/opt/globalping-checker/run_check.sh${NC}"
echo ""

# 創建快速連線腳本
cat > connect.sh << EOF
#!/bin/bash
ssh -i ${KEY_NAME}.pem ec2-user@${PUBLIC_IP}
EOF
chmod +x connect.sh

echo -e "${GREEN}✓ 已創建快速連線腳本: ./connect.sh${NC}"
echo ""

echo -e "${GREEN}部署成功！ 🎉${NC}"
