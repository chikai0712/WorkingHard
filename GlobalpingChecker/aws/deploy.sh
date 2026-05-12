#!/bin/bash

# ============================================
# Globalping Checker - AWS 部署腳本
# ============================================

set -e

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

STACK_NAME="GlobalpingChecker"
REGION="${AWS_REGION:-ap-northeast-1}"  # 預設東京區域

echo -e "${BLUE}========================================"
echo "Globalping Checker - AWS 部署"
echo "========================================${NC}"
echo ""

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}錯誤: 未安裝 AWS CLI${NC}"
    echo "請先安裝: https://aws.amazon.com/cli/"
    exit 1
fi

# 檢查 AWS 憑證
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}錯誤: AWS 憑證未配置${NC}"
    echo "請執行: aws configure"
    exit 1
fi

echo -e "${GREEN}✓ AWS CLI 已配置${NC}"
echo ""

# 詢問參數
read -p "輸入 Globalping API Token (可選，直接按 Enter 跳過): " GLOBALPING_TOKEN
read -p "輸入通知 Email 地址 (可選，直接按 Enter 跳過): " NOTIFICATION_EMAIL
read -p "輸入執行排程 (預設: cron(0 2 * * ? *)，每天凌晨 2 點 UTC): " SCHEDULE_EXPRESSION
SCHEDULE_EXPRESSION=${SCHEDULE_EXPRESSION:-"cron(0 2 * * ? *)"}

echo ""
echo -e "${BLUE}部署參數:${NC}"
echo "  Stack 名稱: $STACK_NAME"
echo "  AWS 區域: $REGION"
echo "  API Token: ${GLOBALPING_TOKEN:+已設置}"
echo "  通知 Email: ${NOTIFICATION_EMAIL:-未設置}"
echo "  執行排程: $SCHEDULE_EXPRESSION"
echo ""

read -p "確認部署? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "取消部署"
    exit 0
fi

echo ""
echo -e "${YELLOW}步驟 1/5: 打包 Lambda 函數...${NC}"

# 創建臨時目錄
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# 複製 Lambda 代碼
cp lambda_function.py "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"

# 安裝依賴
cd "$TEMP_DIR"
pip3 install -r requirements.txt -t . --quiet

# 打包
zip -r lambda_package.zip . -q

echo -e "${GREEN}✓ Lambda 函數已打包${NC}"
echo ""

echo -e "${YELLOW}步驟 2/5: 創建 S3 Bucket 存放部署包...${NC}"

# 創建部署 Bucket
DEPLOY_BUCKET="globalping-deploy-$(aws sts get-caller-identity --query Account --output text)"
if ! aws s3 ls "s3://$DEPLOY_BUCKET" 2>/dev/null; then
    aws s3 mb "s3://$DEPLOY_BUCKET" --region "$REGION"
    echo -e "${GREEN}✓ 創建 Bucket: $DEPLOY_BUCKET${NC}"
else
    echo -e "${GREEN}✓ Bucket 已存在: $DEPLOY_BUCKET${NC}"
fi

# 上傳 Lambda 包
aws s3 cp lambda_package.zip "s3://$DEPLOY_BUCKET/lambda_package.zip"
echo -e "${GREEN}✓ Lambda 包已上傳${NC}"
echo ""

echo -e "${YELLOW}步驟 3/5: 部署 CloudFormation Stack...${NC}"

# 準備參數
PARAMS="ParameterKey=ScheduleExpression,ParameterValue=\"$SCHEDULE_EXPRESSION\""

if [ -n "$GLOBALPING_TOKEN" ]; then
    PARAMS="$PARAMS ParameterKey=GlobalpingToken,ParameterValue=\"$GLOBALPING_TOKEN\""
fi

if [ -n "$NOTIFICATION_EMAIL" ]; then
    PARAMS="$PARAMS ParameterKey=NotificationEmail,ParameterValue=\"$NOTIFICATION_EMAIL\""
fi

# 部署 Stack
cd "$(dirname "$0")"
aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides $PARAMS \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION"

echo -e "${GREEN}✓ CloudFormation Stack 已部署${NC}"
echo ""

echo -e "${YELLOW}步驟 4/5: 更新 Lambda 函數代碼...${NC}"

# 獲取 Lambda 函數名稱
FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionArn'].OutputValue" \
    --output text | awk -F: '{print $NF}')

# 更新 Lambda 代碼
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$DEPLOY_BUCKET" \
    --s3-key lambda_package.zip \
    --region "$REGION" \
    --no-cli-pager > /dev/null

echo -e "${GREEN}✓ Lambda 函數代碼已更新${NC}"
echo ""

echo -e "${YELLOW}步驟 5/5: 獲取部署信息...${NC}"

# 獲取輸出
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
    --output text)

echo -e "${GREEN}✓ 部署完成！${NC}"
echo ""

echo -e "${BLUE}========================================"
echo "部署信息"
echo "========================================${NC}"
echo "Stack 名稱: $STACK_NAME"
echo "AWS 區域: $REGION"
echo "S3 Bucket: $BUCKET_NAME"
echo "Lambda 函數: $FUNCTION_NAME"
echo ""

echo -e "${BLUE}========================================"
echo "下一步操作"
echo "========================================${NC}"
echo ""
echo "1. 上傳域名列表到 S3:"
echo -e "   ${YELLOW}aws s3 cp test_2_domains.txt s3://$BUCKET_NAME/domains.txt${NC}"
echo ""
echo "2. 手動觸發測試:"
echo -e "   ${YELLOW}aws lambda invoke --function-name $FUNCTION_NAME --region $REGION output.json${NC}"
echo ""
echo "3. 查看執行日誌:"
echo -e "   ${YELLOW}aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION${NC}"
echo ""
echo "4. 查看檢測結果:"
echo -e "   ${YELLOW}aws s3 ls s3://$BUCKET_NAME/results/ --recursive${NC}"
echo ""
echo "5. 下載最新結果:"
echo -e "   ${YELLOW}aws s3 cp s3://$BUCKET_NAME/results/ . --recursive${NC}"
echo ""

if [ -n "$NOTIFICATION_EMAIL" ]; then
    echo -e "${YELLOW}⚠️  請檢查 Email 並確認 SNS 訂閱${NC}"
    echo ""
fi

echo -e "${GREEN}部署成功！ 🎉${NC}"
