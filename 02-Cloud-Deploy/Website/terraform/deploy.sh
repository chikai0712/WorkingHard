#!/bin/bash

# AWS 網站部署腳本
# 使用方式：./deploy.sh

set -e

echo "🚀 開始部署網站到 AWS..."

# 檢查 Terraform 是否安裝
if ! command -v terraform &> /dev/null; then
    echo "❌ 錯誤：未安裝 Terraform"
    echo "請執行：brew install terraform"
    exit 1
fi

# 檢查 AWS CLI 是否安裝
if ! command -v aws &> /dev/null; then
    echo "❌ 錯誤：未安裝 AWS CLI"
    echo "請執行：brew install awscli"
    exit 1
fi

# 檢查 terraform.tfvars 是否存在
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ 錯誤：找不到 terraform.tfvars"
    echo "請先複製 terraform.tfvars.example 並填入你的設定"
    exit 1
fi

# 進入 terraform 目錄
cd "$(dirname "$0")"

# 初始化 Terraform（如果尚未初始化）
if [ ! -d ".terraform" ]; then
    echo "📦 初始化 Terraform..."
    terraform init
fi

# 預覽變更
echo "🔍 預覽變更..."
terraform plan

# 確認部署
read -p "是否要繼續部署？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ 部署已取消"
    exit 0
fi

# 部署基礎設施
echo "🏗️  部署基礎設施..."
terraform apply -auto-approve

# 取得 S3 Bucket 名稱
BUCKET_NAME=$(terraform output -raw s3_bucket_name)
DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)

echo "📤 上傳網站檔案到 S3..."
# 從專案根目錄上傳（假設腳本在 terraform 目錄）
cd ..
aws s3 sync Website s3://$BUCKET_NAME \
  --exclude "*.md" \
  --exclude ".git/*" \
  --exclude "terraform/*" \
  --exclude "*.sh" \
  --delete

echo "🔄 清除 CloudFront 快取..."
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*" \
  --output json > /dev/null

echo ""
echo "✅ 部署完成！"
echo ""
echo "📋 重要資訊："
terraform output

echo ""
echo "⚠️  如果域名不在 Route 53，請設定 DNS："
terraform output dns_instructions

echo ""
echo "🌐 網站網址：https://$(terraform output -raw domain_name 2>/dev/null || grep 'domain_name' terraform.tfvars | cut -d'"' -f2)"
echo ""
echo "💡 提示："
echo "   - 如果使用自訂域名，請先完成 ACM 證書驗證"
echo "   - DNS 傳播可能需要 5-30 分鐘"
echo "   - 使用 'terraform output' 查看所有輸出"
