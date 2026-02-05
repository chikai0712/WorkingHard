#!/bin/bash
# -------------------------------------------------------------------------------
# DNS 查詢監控腳本 - 測試 DNS 解析（UDP 53 埠）
# 功能：持續測試 AWS 和 Google NS 的 DNS 查詢功能
# 
# 用法：
#   bash ./dns-query-monitor.sh [間隔秒數] [測試域名]
#   例如：bash ./dns-query-monitor.sh 1 www.clouddeployment168.site
#
# 預設間隔：1 秒
# 預設測試域名：www.clouddeployment168.site
# 按 Ctrl+C 停止
# -------------------------------------------------------------------------------

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
INTERVAL="${1:-1}"
TEST_DOMAIN="${2:-www.clouddeployment168.site}"
DNS_TIMEOUT=2
LOG_FILE="/tmp/dns_query_monitor_$(date +%Y%m%d_%H%M%S).log"

# AWS Route53 NS IPs
AWS_NS=(
    "205.251.197.44"   # ns-1324.awsdns-37.org
    "205.251.199.48"   # ns-1840.awsdns-38.co.uk
    "205.251.192.236"  # ns-236.awsdns-29.com
    "205.251.195.65"   # ns-833.awsdns-40.net
)

# Google Cloud DNS NS IPs
GOOGLE_NS=(
    "216.239.32.108"   # ns-cloud-c1.googledomains.com
    "216.239.34.108"   # ns-cloud-c2.googledomains.com
    "216.239.36.108"   # ns-cloud-c3.googledomains.com
    "216.239.38.108"   # ns-cloud-c4.googledomains.com
)

# 清理函數
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止監控...${NC}"
    echo ""
    echo -e "${GREEN}監控已停止${NC}"
    echo -e "完整日誌: ${CYAN}$LOG_FILE${NC}"
    exit 0
}

trap cleanup INT TERM

# DNS 查詢單個 NS
query_dns() {
    local ns_ip=$1
    local name=$2
    local domain=$3
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 使用 dig 查詢，設定超時
    local dig_output
    local start_time=$(date +%s.%N 2>/dev/null || date +%s)
    
    dig_output=$(dig @"$ns_ip" "$domain" A +time="$DNS_TIMEOUT" +tries=1 +short 2>&1)
    local dig_status=$?
    
    local end_time=$(date +%s.%N 2>/dev/null || date +%s)
    local query_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
    local query_time_ms=$(echo "$query_time * 1000" | bc 2>/dev/null | cut -d'.' -f1)
    
    if [ $dig_status -eq 0 ] && [ -n "$dig_output" ] && ! echo "$dig_output" | grep -q "connection timed out\|no servers could be reached"; then
        # 查詢成功，提取 IP
        local resolved_ip=$(echo "$dig_output" | grep -E '^[0-9.]+$' | head -1)
        
        if [ -n "$resolved_ip" ]; then
            echo -e "${GREEN}✓${NC} $name ($ns_ip) - ${query_time_ms}ms → $resolved_ip"
            echo "[$timestamp] SUCCESS | $name | $ns_ip | ${query_time_ms}ms | $resolved_ip" >> "$LOG_FILE"
            return 0
        else
            echo -e "${YELLOW}?${NC} $name ($ns_ip) - 回應異常"
            echo "[$timestamp] INVALID | $name | $ns_ip | - | $dig_output" >> "$LOG_FILE"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $name ($ns_ip) - 超時/失敗 (>${DNS_TIMEOUT}s)"
        echo "[$timestamp] TIMEOUT | $name | $ns_ip | >${DNS_TIMEOUT}s | -" >> "$LOG_FILE"
        return 1
    fi
}

# 主監控循環
main() {
    clear
    echo -e "${GREEN}=== DNS 查詢監控（UDP 53 埠）===${NC}\n"
    echo -e "測試域名: ${CYAN}${TEST_DOMAIN}${NC}"
    echo -e "監控間隔: ${CYAN}${INTERVAL} 秒${NC}"
    echo -e "DNS 超時: ${CYAN}${DNS_TIMEOUT} 秒${NC}"
    echo -e "日誌檔案: ${CYAN}$LOG_FILE${NC}"
    echo -e "按 ${YELLOW}Ctrl+C${NC} 停止監控\n"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 寫入日誌標頭
    {
        echo "=== DNS 查詢監控日誌 ==="
        echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "測試域名: ${TEST_DOMAIN}"
        echo "監控間隔: ${INTERVAL} 秒"
        echo "DNS 超時: ${DNS_TIMEOUT} 秒"
        echo "AWS NS: ${AWS_NS[*]}"
        echo "Google NS: ${GOOGLE_NS[*]}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    } > "$LOG_FILE"
    
    local round=1
    
    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo -e "${CYAN}[$timestamp] 第 $round 輪監控${NC}"
        
        # 統計
        local aws_success=0
        local aws_total=${#AWS_NS[@]}
        local google_success=0
        local google_total=${#GOOGLE_NS[@]}
        
        # 查詢 AWS NS
        echo -e "${YELLOW}AWS Route53 NS:${NC}"
        for i in "${!AWS_NS[@]}"; do
            local ip="${AWS_NS[$i]}"
            local name="AWS-NS-$((i+1))"
            if query_dns "$ip" "$name" "$TEST_DOMAIN"; then
                aws_success=$((aws_success + 1))
            fi
        done
        
        echo ""
        
        # 查詢 Google NS
        echo -e "${YELLOW}Google Cloud DNS NS:${NC}"
        for i in "${!GOOGLE_NS[@]}"; do
            local ip="${GOOGLE_NS[$i]}"
            local name="Google-NS-$((i+1))"
            if query_dns "$ip" "$name" "$TEST_DOMAIN"; then
                google_success=$((google_success + 1))
            fi
        done
        
        echo ""
        
        # 顯示統計
        echo -e "${BLUE}統計:${NC}"
        if [ $aws_success -eq $aws_total ]; then
            echo -e "  AWS NS: ${GREEN}$aws_success${NC}/${aws_total} 可查詢"
        elif [ $aws_success -eq 0 ]; then
            echo -e "  AWS NS: ${RED}$aws_success${NC}/${aws_total} 可查詢 ${RED}(全部失敗)${NC}"
        else
            echo -e "  AWS NS: ${YELLOW}$aws_success${NC}/${aws_total} 可查詢"
        fi
        
        if [ $google_success -eq $google_total ]; then
            echo -e "  Google NS: ${GREEN}$google_success${NC}/${google_total} 可查詢"
        elif [ $google_success -eq 0 ]; then
            echo -e "  Google NS: ${RED}$google_success${NC}/${google_total} 可查詢 ${RED}(全部失敗)${NC}"
        else
            echo -e "  Google NS: ${YELLOW}$google_success${NC}/${google_total} 可查詢"
        fi
        
        # 寫入統計到日誌
        {
            echo "[$timestamp] SUMMARY | AWS: $aws_success/$aws_total | Google: $google_success/$google_total"
            echo ""
        } >> "$LOG_FILE"
        
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        round=$((round + 1))
        sleep "$INTERVAL"
    done
}

main "$@"
