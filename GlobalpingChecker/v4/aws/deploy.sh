#!/bin/bash

# GlobalpingChecker V4 - AWS 部署腳本
# 使用 CloudFormation 部署基礎設施

set -e

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
STACK_NAME="${STACK_NAME:-globalping-v4}"
REGION="${AWS_REGION:-ap-southeast-1}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.small}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GlobalpingChecker V4 - AWS 部署${NC}"
echo -e "${GREEN}========================================${NC}"

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ 請先安裝 AWS CLI${NC}"
    exit 1
fi

# 檢查 AWS 認證
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS 認證失敗，請執行 'aws configure'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI 已配置${NC}"

# 獲取參數
read -p "請輸入 SSH Key Pair 名稱: " KEY_PAIR_NAME
read -p "請輸入 Globalping API Token: " GLOBALPING_TOKEN
read -sp "請輸入 PostgreSQL 密碼 (至少8字元): " POSTGRES_PASSWORD
echo ""

if [ -z "$KEY_PAIR_NAME" ] || [ -z "$GLOBALPING_TOKEN" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}❌ 所有參數都是必填的${NC}"
    exit 1
fi

# 檢查 Key Pair 是否存在
if ! aws ec2 describe-key-pairs --key-names "$KEY_PAIR_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Key Pair '$KEY_PAIR_NAME' 不存在，正在創建...${NC}"
    aws ec2 create-key-pair --key-name "$KEY_PAIR_NAME" --region "$REGION" \
        --query 'KeyMaterial' --output text > "${KEY_PAIR_NAME}.pem"
    chmod 400 "${KEY_PAIR_NAME}.pem"
    echo -e "${GREEN}✅ Key Pair 已創建並保存到 ${KEY_PAIR_NAME}.pem${NC}"
fi

# 部署 CloudFormation Stack
echo -e "\n${GREEN}📦 開始部署 CloudFormation Stack...${NC}"

aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --parameter-overrides \
        EnvironmentName="$STACK_NAME" \
        InstanceType="$INSTANCE_TYPE" \
        KeyPairName="$KEY_PAIR_NAME" \
        GlobalpingToken="$GLOBALPING_TOKEN" \
        PostgresPassword="$POSTGRES_PASSWORD" \
    --capabilities CAPABILITY_IAM \
    --no-fail-on-empty-changeset

echo -e "${GREEN}✅ CloudFormation Stack 部署完成${NC}"

# 獲取輸出
echo -e "\n${GREEN}📋 部署信息：${NC}"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output table

# 獲取 Public IP
PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
    --output text)

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Public IP: ${YELLOW}$PUBLIC_IP${NC}"
echo -e "Web URL: ${YELLOW}http://$PUBLIC_IP:8000${NC}"
echo -e "SSH: ${YELLOW}ssh -i ${KEY_PAIR_NAME}.pem ec2-user@$PUBLIC_IP${NC}"
echo -e "\n${YELLOW}⚠️  請等待 EC2 實例初始化完成（約 2-3 分鐘）${NC}"
echo -e "${YELLOW}然後 SSH 登入並部署應用程式代碼${NC}"
