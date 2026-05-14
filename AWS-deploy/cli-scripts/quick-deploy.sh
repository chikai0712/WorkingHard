#!/bin/bash
# 快速部署腳本 - 互動式設定

set -e

# 顏色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS 域名設定 - 快速部署${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 互動式輸入
read -p "請輸入您的域名（例如：example.com）: " DOMAIN_NAME
read -p "請選擇 AWS 區域（預設：ap-northeast-1）: " AWS_REGION
AWS_REGION=${AWS_REGION:-ap-northeast-1}

read -p "請選擇 CloudFront 價格等級
  1) PriceClass_100 (美國、加拿大、歐洲 - 最便宜)
  2) PriceClass_200 (+ 亞洲、中東、非洲)
  3) PriceClass_All (全球 - 最快但最貴)
請選擇 [1-3] (預設：3): " PRICE_CHOICE

case $PRICE_CHOICE in
    1) CLOUDFRONT_PRICE_CLASS="PriceClass_100" ;;
    2) CLOUDFRONT_PRICE_CLASS="PriceClass_200" ;;
    *) CLOUDFRONT_PRICE_CLASS="PriceClass_All" ;;
esac

echo ""
echo -e "${YELLOW}確認設定：${NC}"
echo "  域名: $DOMAIN_NAME"
echo "  區域: $AWS_REGION"
echo "  價格等級: $CLOUDFRONT_PRICE_CLASS"
echo ""
read -p "確認開始部署？(y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "取消部署"
    exit 0
fi

# 更新 deploy.sh 中的變數
sed -i '' "s/^DOMAIN_NAME=.*/DOMAIN_NAME=\"$DOMAIN_NAME\"/" deploy.sh
sed -i '' "s/^AWS_REGION=.*/AWS_REGION=\"$AWS_REGION\"/" deploy.sh
sed -i '' "s/^CLOUDFRONT_PRICE_CLASS=.*/CLOUDFRONT_PRICE_CLASS=\"$CLOUDFRONT_PRICE_CLASS\"/" deploy.sh

# 執行部署
./deploy.sh
