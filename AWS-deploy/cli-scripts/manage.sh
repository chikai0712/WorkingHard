#!/bin/bash
# AWS 資源管理工具

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_menu() {
    echo ""
    echo "=========================================="
    echo "AWS 域名管理工具"
    echo "=========================================="
    echo "1) 查看所有 CloudFront Distributions"
    echo "2) 查看 Route53 Hosted Zones"
    echo "3) 查看 ACM 憑證"
    echo "4) 上傳網站內容到 S3"
    echo "5) 清除 CloudFront 快取"
    echo "6) 查看 DNS 記錄"
    echo "7) 測試網站連線"
    echo "8) 查看資源成本估算"
    echo "0) 退出"
    echo "=========================================="
    read -p "請選擇操作 [0-8]: " choice
    echo ""
}

list_distributions() {
    log_info "CloudFront Distributions:"
    aws cloudfront list-distributions \
        --query 'DistributionList.Items[*].[Id,DomainName,Aliases.Items[0],Status]' \
        --output table
}

list_hosted_zones() {
    log_info "Route53 Hosted Zones:"
    aws route53 list-hosted-zones \
        --query 'HostedZones[*].[Id,Name,ResourceRecordSetCount]' \
        --output table
}

list_certificates() {
    log_info "ACM 憑證 (us-east-1):"
    aws acm list-certificates \
        --region us-east-1 \
        --query 'CertificateSummaryList[*].[DomainName,Status,CertificateArn]' \
        --output table
}

upload_to_s3() {
    read -p "請輸入 S3 Bucket 名稱: " bucket
    read -p "請輸入本地資料夾路徑: " folder
    
    if [ ! -d "$folder" ]; then
        log_error "資料夾不存在: $folder"
        return
    fi
    
    log_info "上傳 $folder 到 s3://$bucket/"
    aws s3 sync "$folder" "s3://$bucket/" --delete
    log_info "✅ 上傳完成"
}

invalidate_cache() {
    read -p "請輸入 CloudFront Distribution ID: " dist_id
    read -p "請輸入要清除的路徑（預設 /*）: " paths
    paths=${paths:-/*}
    
    log_info "清除快取: $paths"
    aws cloudfront create-invalidation \
        --distribution-id "$dist_id" \
        --paths "$paths"
    log_info "✅ 快取清除請求已提交"
}

show_dns_records() {
    read -p "請輸入 Hosted Zone ID: " zone_id
    
    log_info "DNS 記錄:"
    aws route53 list-resource-record-sets \
        --hosted-zone-id "$zone_id" \
        --query 'ResourceRecordSets[*].[Name,Type,TTL,ResourceRecords[0].Value]' \
        --output table
}

test_website() {
    read -p "請輸入域名: " domain
    
    log_info "測試 DNS 解析..."
    dig +short "$domain"
    
    log_info "測試 HTTPS 連線..."
    curl -I "https://$domain" 2>&1 | head -n 10
}

estimate_cost() {
    log_info "AWS 資源成本估算（每月）:"
    echo ""
    echo "Route53 Hosted Zone: ~$0.50/月"
    echo "ACM 憑證: 免費"
    echo "CloudFront:"
    echo "  - 前 10TB: $0.085/GB"
    echo "  - HTTPS 請求: $0.01/10,000 請求"
    echo "S3 儲存: $0.023/GB/月"
    echo ""
    echo "範例（小型網站）:"
    echo "  - 流量 100GB/月: ~$9"
    echo "  - 儲存 1GB: ~$0.50"
    echo "  - 總計: ~$10/月"
}

main() {
    while true; do
        show_menu
        
        case $choice in
            1) list_distributions ;;
            2) list_hosted_zones ;;
            3) list_certificates ;;
            4) upload_to_s3 ;;
            5) invalidate_cache ;;
            6) show_dns_records ;;
            7) test_website ;;
            8) estimate_cost ;;
            0) log_info "再見！"; exit 0 ;;
            *) log_error "無效選項" ;;
        esac
        
        echo ""
        read -p "按 Enter 繼續..."
    done
}

main
