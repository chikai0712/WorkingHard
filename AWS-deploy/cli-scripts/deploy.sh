#!/bin/bash
# AWS CLI 自動化部署腳本
# 用途：使用 AWS CLI 設定 Route53、ACM 憑證和 CloudFront

set -e  # 遇到錯誤立即停止

# ============================================
# 配置變數（請修改這些值）
# ============================================
DOMAIN_NAME="example.com"           # 您的域名
AWS_REGION="ap-northeast-1"         # 主要區域
BUCKET_NAME="${DOMAIN_NAME}-website"
CLOUDFRONT_PRICE_CLASS="PriceClass_All"  # PriceClass_100, PriceClass_200, PriceClass_All

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# 輔助函數
# ============================================
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

wait_for_input() {
    echo -e "${YELLOW}按 Enter 繼續...${NC}"
    read
}

# ============================================
# 步驟 1: 建立 Route53 Hosted Zone
# ============================================
create_hosted_zone() {
    log_info "步驟 1: 建立 Route53 Hosted Zone..."
    
    # 檢查是否已存在
    ZONE_ID=$(aws route53 list-hosted-zones-by-name \
        --dns-name "${DOMAIN_NAME}" \
        --query "HostedZones[?Name=='${DOMAIN_NAME}.'].Id" \
        --output text 2>/dev/null | cut -d'/' -f3)
    
    if [ -n "$ZONE_ID" ]; then
        log_warn "Hosted Zone 已存在: $ZONE_ID"
    else
        CALLER_REFERENCE=$(date +%s)
        ZONE_ID=$(aws route53 create-hosted-zone \
            --name "${DOMAIN_NAME}" \
            --caller-reference "${CALLER_REFERENCE}" \
            --hosted-zone-config Comment="Created by CLI script" \
            --query 'HostedZone.Id' \
            --output text | cut -d'/' -f3)
        
        log_info "✅ Hosted Zone 建立成功: $ZONE_ID"
    fi
    
    # 顯示 Name Servers
    log_info "Name Servers（請設定到您的域名註冊商）:"
    aws route53 get-hosted-zone \
        --id "$ZONE_ID" \
        --query 'DelegationSet.NameServers' \
        --output table
    
    echo "$ZONE_ID" > /tmp/zone_id.txt
}

# ============================================
# 步驟 2: 申請 ACM 憑證
# ============================================
request_certificate() {
    log_info "步驟 2: 申請 ACM 憑證（us-east-1 區域）..."
    
    # 檢查是否已存在
    CERT_ARN=$(aws acm list-certificates \
        --region us-east-1 \
        --query "CertificateSummaryList[?DomainName=='${DOMAIN_NAME}'].CertificateArn" \
        --output text 2>/dev/null)
    
    if [ -n "$CERT_ARN" ]; then
        log_warn "憑證已存在: $CERT_ARN"
    else
        CERT_ARN=$(aws acm request-certificate \
            --region us-east-1 \
            --domain-name "${DOMAIN_NAME}" \
            --subject-alternative-names "*.${DOMAIN_NAME}" \
            --validation-method DNS \
            --query 'CertificateArn' \
            --output text)
        
        log_info "✅ 憑證申請成功: $CERT_ARN"
    fi
    
    echo "$CERT_ARN" > /tmp/cert_arn.txt
    
    # 等待憑證資訊可用
    log_info "等待憑證驗證資訊..."
    sleep 5
}

# ============================================
# 步驟 3: 建立 DNS 驗證記錄
# ============================================
create_validation_records() {
    log_info "步驟 3: 建立 ACM DNS 驗證記錄..."
    
    ZONE_ID=$(cat /tmp/zone_id.txt)
    CERT_ARN=$(cat /tmp/cert_arn.txt)
    
    # 取得驗證記錄
    VALIDATION_RECORDS=$(aws acm describe-certificate \
        --region us-east-1 \
        --certificate-arn "$CERT_ARN" \
        --query 'Certificate.DomainValidationOptions[*].ResourceRecord' \
        --output json)
    
    # 建立變更批次檔案
    cat > /tmp/validation-records.json <<EOF
{
  "Changes": [
EOF
    
    # 解析並建立每個驗證記錄
    echo "$VALIDATION_RECORDS" | jq -c '.[]' | while read -r record; do
        NAME=$(echo "$record" | jq -r '.Name')
        TYPE=$(echo "$record" | jq -r '.Type')
        VALUE=$(echo "$record" | jq -r '.Value')
        
        cat >> /tmp/validation-records.json <<EOF
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$NAME",
        "Type": "$TYPE",
        "TTL": 60,
        "ResourceRecords": [{"Value": "$VALUE"}]
      }
    },
EOF
    done
    
    # 移除最後一個逗號並關閉 JSON
    sed -i '' '$ s/,$//' /tmp/validation-records.json
    cat >> /tmp/validation-records.json <<EOF
  ]
}
EOF
    
    # 套用變更
    aws route53 change-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --change-batch file:///tmp/validation-records.json \
        --output table
    
    log_info "✅ DNS 驗證記錄建立成功"
    
    # 等待憑證驗證
    log_info "等待憑證驗證完成（這可能需要幾分鐘）..."
    aws acm wait certificate-validated \
        --region us-east-1 \
        --certificate-arn "$CERT_ARN"
    
    log_info "✅ 憑證驗證完成"
}

# ============================================
# 步驟 4: 建立 S3 Bucket
# ============================================
create_s3_bucket() {
    log_info "步驟 4: 建立 S3 Bucket..."
    
    # 檢查 bucket 是否存在
    if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
        log_warn "S3 Bucket 已存在: ${BUCKET_NAME}"
    else
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3api create-bucket \
                --bucket "${BUCKET_NAME}" \
                --region "${AWS_REGION}"
        else
            aws s3api create-bucket \
                --bucket "${BUCKET_NAME}" \
                --region "${AWS_REGION}" \
                --create-bucket-configuration LocationConstraint="${AWS_REGION}"
        fi
        
        log_info "✅ S3 Bucket 建立成功: ${BUCKET_NAME}"
    fi
    
    # 封鎖公開存取
    aws s3api put-public-access-block \
        --bucket "${BUCKET_NAME}" \
        --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    # 設定網站配置
    aws s3api put-bucket-website \
        --bucket "${BUCKET_NAME}" \
        --website-configuration '{
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "error.html"}
        }'
    
    log_info "✅ S3 Bucket 配置完成"
}

# ============================================
# 步驟 5: 建立 CloudFront Distribution
# ============================================
create_cloudfront_distribution() {
    log_info "步驟 5: 建立 CloudFront Distribution..."
    
    CERT_ARN=$(cat /tmp/cert_arn.txt)
    S3_DOMAIN="${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com"
    
    # 建立 Origin Access Control
    OAC_ID=$(aws cloudfront create-origin-access-control \
        --origin-access-control-config \
            "Name=${DOMAIN_NAME}-oac,\
            Description=OAC for ${DOMAIN_NAME},\
            SigningProtocol=sigv4,\
            SigningBehavior=always,\
            OriginAccessControlOriginType=s3" \
        --query 'OriginAccessControl.Id' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$OAC_ID" ]; then
        log_warn "OAC 可能已存在，繼續..."
        OAC_ID=$(aws cloudfront list-origin-access-controls \
            --query "OriginAccessControlList.Items[?Name=='${DOMAIN_NAME}-oac'].Id" \
            --output text)
    fi
    
    log_info "OAC ID: $OAC_ID"
    
    # 建立 CloudFront 配置檔案
    cat > /tmp/cloudfront-config.json <<EOF
{
  "CallerReference": "$(date +%s)",
  "Aliases": {
    "Quantity": 2,
    "Items": ["${DOMAIN_NAME}", "www.${DOMAIN_NAME}"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${DOMAIN_NAME}",
        "DomainName": "${S3_DOMAIN}",
        "OriginAccessControlId": "${OAC_ID}",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${DOMAIN_NAME}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 3,
      "Items": ["GET", "HEAD", "OPTIONS"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "MinTTL": 0,
    "DefaultTTL": 3600,
    "MaxTTL": 86400,
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    }
  },
  "Comment": "Distribution for ${DOMAIN_NAME}",
  "Enabled": true,
  "PriceClass": "${CLOUDFRONT_PRICE_CLASS}",
  "ViewerCertificate": {
    "ACMCertificateArn": "${CERT_ARN}",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/error.html",
        "ResponseCode": "404",
        "ErrorCachingMinTTL": 300
      },
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/error.html",
        "ResponseCode": "403",
        "ErrorCachingMinTTL": 300
      }
    ]
  }
}
EOF
    
    # 建立 Distribution
    DIST_OUTPUT=$(aws cloudfront create-distribution \
        --distribution-config file:///tmp/cloudfront-config.json \
        --output json)
    
    DIST_ID=$(echo "$DIST_OUTPUT" | jq -r '.Distribution.Id')
    DIST_DOMAIN=$(echo "$DIST_OUTPUT" | jq -r '.Distribution.DomainName')
    DIST_ARN=$(echo "$DIST_OUTPUT" | jq -r '.Distribution.ARN')
    
    log_info "✅ CloudFront Distribution 建立成功"
    log_info "Distribution ID: $DIST_ID"
    log_info "Domain Name: $DIST_DOMAIN"
    
    echo "$DIST_ID" > /tmp/dist_id.txt
    echo "$DIST_DOMAIN" > /tmp/dist_domain.txt
    echo "$DIST_ARN" > /tmp/dist_arn.txt
}

# ============================================
# 步驟 6: 更新 S3 Bucket Policy
# ============================================
update_s3_policy() {
    log_info "步驟 6: 更新 S3 Bucket Policy..."
    
    DIST_ARN=$(cat /tmp/dist_arn.txt)
    
    cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "${DIST_ARN}"
        }
      }
    }
  ]
}
EOF
    
    aws s3api put-bucket-policy \
        --bucket "${BUCKET_NAME}" \
        --policy file:///tmp/bucket-policy.json
    
    log_info "✅ S3 Bucket Policy 更新完成"
}

# ============================================
# 步驟 7: 建立 Route53 記錄
# ============================================
create_route53_records() {
    log_info "步驟 7: 建立 Route53 DNS 記錄..."
    
    ZONE_ID=$(cat /tmp/zone_id.txt)
    DIST_DOMAIN=$(cat /tmp/dist_domain.txt)
    
    # CloudFront 的 Hosted Zone ID（固定值）
    CF_ZONE_ID="Z2FDTNDATAQYW2"
    
    cat > /tmp/dns-records.json <<EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "${DOMAIN_NAME}",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "${CF_ZONE_ID}",
          "DNSName": "${DIST_DOMAIN}",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "${DOMAIN_NAME}",
        "Type": "AAAA",
        "AliasTarget": {
          "HostedZoneId": "${CF_ZONE_ID}",
          "DNSName": "${DIST_DOMAIN}",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "www.${DOMAIN_NAME}",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "${CF_ZONE_ID}",
          "DNSName": "${DIST_DOMAIN}",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "www.${DOMAIN_NAME}",
        "Type": "AAAA",
        "AliasTarget": {
          "HostedZoneId": "${CF_ZONE_ID}",
          "DNSName": "${DIST_DOMAIN}",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}
EOF
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --change-batch file:///tmp/dns-records.json \
        --output table
    
    log_info "✅ Route53 DNS 記錄建立完成"
}

# ============================================
# 步驟 8: 上傳測試頁面
# ============================================
upload_test_page() {
    log_info "步驟 8: 上傳測試頁面..."
    
    # 建立簡單的測試頁面
    cat > /tmp/index.html <<EOF
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${DOMAIN_NAME}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            text-align: center;
        }
        h1 { font-size: 3em; margin-bottom: 0.5em; }
        p { font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 網站部署成功！</h1>
        <p>您的域名 <strong>${DOMAIN_NAME}</strong> 已成功配置</p>
        <p>CloudFront + Route53 + ACM</p>
    </div>
</body>
</html>
EOF
    
    cat > /tmp/error.html <<EOF
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>錯誤 - ${DOMAIN_NAME}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }
        .container {
            text-align: center;
        }
        h1 { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>404 - 頁面不存在</h1>
        <p>抱歉，您訪問的頁面不存在</p>
    </div>
</body>
</html>
EOF
    
    # 上傳到 S3
    aws s3 cp /tmp/index.html "s3://${BUCKET_NAME}/index.html" --content-type "text/html"
    aws s3 cp /tmp/error.html "s3://${BUCKET_NAME}/error.html" --content-type "text/html"
    
    log_info "✅ 測試頁面上傳完成"
}

# ============================================
# 主程式
# ============================================
main() {
    log_info "=========================================="
    log_info "AWS CloudFront + Route53 + ACM 自動部署"
    log_info "=========================================="
    log_info "域名: ${DOMAIN_NAME}"
    log_info "區域: ${AWS_REGION}"
    log_info "=========================================="
    echo ""
    
    # 檢查 AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI 未安裝，請先安裝 AWS CLI"
        exit 1
    fi
    
    # 檢查 jq
    if ! command -v jq &> /dev/null; then
        log_error "jq 未安裝，請先安裝 jq (brew install jq)"
        exit 1
    fi
    
    # 檢查 AWS 認證
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS 認證失敗，請先配置 AWS CLI (aws configure)"
        exit 1
    fi
    
    log_info "AWS 認證成功"
    aws sts get-caller-identity --output table
    echo ""
    
    # 執行部署步驟
    create_hosted_zone
    echo ""
    
    request_certificate
    echo ""
    
    create_validation_records
    echo ""
    
    create_s3_bucket
    echo ""
    
    create_cloudfront_distribution
    echo ""
    
    update_s3_policy
    echo ""
    
    create_route53_records
    echo ""
    
    upload_test_page
    echo ""
    
    # 顯示完成資訊
    log_info "=========================================="
    log_info "✅ 部署完成！"
    log_info "=========================================="
    echo ""
    log_info "重要資訊："
    echo ""
    echo "1. Route53 Hosted Zone ID: $(cat /tmp/zone_id.txt)"
    echo "2. ACM 憑證 ARN: $(cat /tmp/cert_arn.txt)"
    echo "3. CloudFront Distribution ID: $(cat /tmp/dist_id.txt)"
    echo "4. S3 Bucket: ${BUCKET_NAME}"
    echo ""
    log_info "Name Servers（請到域名註冊商設定）："
    aws route53 get-hosted-zone --id "$(cat /tmp/zone_id.txt)" \
        --query 'DelegationSet.NameServers' --output table
    echo ""
    log_info "網站 URL："
    echo "  https://${DOMAIN_NAME}"
    echo "  https://www.${DOMAIN_NAME}"
    echo ""
    log_info "上傳網站內容："
    echo "  aws s3 sync ./your-website s3://${BUCKET_NAME}/"
    echo ""
    log_info "清除 CloudFront 快取："
    echo "  aws cloudfront create-invalidation --distribution-id $(cat /tmp/dist_id.txt) --paths '/*'"
    echo ""
    log_info "=========================================="
    
    # 清理臨時檔案
    # rm -f /tmp/zone_id.txt /tmp/cert_arn.txt /tmp/dist_id.txt /tmp/dist_domain.txt /tmp/dist_arn.txt
    # rm -f /tmp/validation-records.json /tmp/cloudfront-config.json /tmp/bucket-policy.json /tmp/dns-records.json
    # rm -f /tmp/index.html /tmp/error.html
}

# 執行主程式
main
