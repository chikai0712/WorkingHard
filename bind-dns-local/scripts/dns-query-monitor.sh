#!/bin/bash
# -------------------------------------------------------------------------------
# DNS 查詢監控腳本 v1.0 - 測試 DNS 解析與故障切換
# 功能：
#   1. 持續監控 AWS 和 Google NS 的 DNS 查詢功能
#   2. 支援 dig 直接查詢模式（預設）
#   3. 支援 dig +trace 遞迴追蹤模式（--trace）
#   4. 即時顯示查詢狀態與統計
#   5. 記錄完整日誌供事後分析
# 
# 用法：
#   基本模式：bash ./dns-query-monitor.sh [間隔秒數] [測試域名]
#   追蹤模式：bash ./dns-query-monitor.sh --trace [間隔秒數] [測試域名]
#   
# 範例：
#   bash ./dns-query-monitor.sh 1 www.clouddeployment168.site
#   bash ./dns-query-monitor.sh --trace 5 www.clouddeployment168.site
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
MAGENTA='\033[0;35m'
NC='\033[0m'

# 解析參數
USE_TRACE=false
INTERVAL=1
TEST_DOMAIN="www.clouddeployment168.site"

for arg in "$@"; do
    case "$arg" in
        --trace)
            USE_TRACE=true
            ;;
        --help|-h)
            echo "用法: $0 [選項] [間隔秒數] [測試域名]"
            echo ""
            echo "選項:"
            echo "  --trace    使用 dig +trace 遞迴追蹤模式"
            echo "  --help     顯示此幫助訊息"
            echo ""
            echo "範例:"
            echo "  $0 1 www.example.com          # 每秒直接查詢"
            echo "  $0 --trace 5 www.example.com  # 每 5 秒追蹤查詢"
            exit 0
            ;;
        *)
            if [[ "$arg" =~ ^[0-9]+$ ]]; then
                INTERVAL="$arg"
            elif [[ "$arg" != --* ]]; then
                TEST_DOMAIN="$arg"
            fi
            ;;
    esac
done

# 配置
DNS_TIMEOUT=2
TRACE_TIMEOUT=10
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

# DNS 直接查詢單個 NS（預設模式）
query_dns_direct() {
    local ns_ip=$1
    local name=$2
    local domain=$3
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 使用 dig 直接查詢指定 NS，設定超時
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

# DNS 追蹤查詢（dig +trace 模式）
query_dns_trace() {
    local domain=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${MAGENTA}執行 dig +trace 遞迴追蹤...${NC}"
    
    local start_time=$(date +%s.%N 2>/dev/null || date +%s)
    local trace_output
    local trace_file=$(mktemp)
    
    # 執行 dig +trace，捕獲完整輸出
    set +e
    dig +trace +nodnssec "$domain" A > "$trace_file" 2>&1
    local dig_status=$?
    set -e
    
    local end_time=$(date +%s.%N 2>/dev/null || date +%s)
    local query_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
    local query_time_ms=$(echo "$query_time * 1000" | bc 2>/dev/null | cut -d'.' -f1)
    
    trace_output=$(cat "$trace_file")
    
    # 分析追蹤結果
    local final_ip=$(echo "$trace_output" | grep -E "^${domain}\." | grep -E "IN\s+A\s+" | awk '{print $NF}' | grep -E '^[0-9.]+$' | head -1)
    local ns_used=$(echo "$trace_output" | grep "Received" | tail -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    
    # 檢查是否有超時或錯誤
    local has_timeout=$(echo "$trace_output" | grep -c "timed out\|connection refused\|no servers" || true)
    
    if [ -n "$final_ip" ]; then
        if [ "$has_timeout" -gt 0 ]; then
            echo -e "${YELLOW}⚠${NC} 追蹤成功但有 ${has_timeout} 次超時 - ${query_time_ms}ms → $final_ip"
            echo -e "   ${CYAN}最終使用 NS: ${ns_used:-未知}${NC}"
        else
            echo -e "${GREEN}✓${NC} 追蹤成功 - ${query_time_ms}ms → $final_ip"
            echo -e "   ${CYAN}最終使用 NS: ${ns_used:-未知}${NC}"
        fi
        
        # 顯示追蹤路徑摘要
        echo -e "   ${BLUE}追蹤路徑:${NC}"
        echo "$trace_output" | grep -E "^\." | head -3 | sed 's/^/     /'
        echo "$trace_output" | grep -E "^${domain%.*}\." | head -2 | sed 's/^/     /'
        echo "$trace_output" | grep -E "^${domain}\." | grep "IN A" | sed 's/^/     /'
        
        echo "[$timestamp] TRACE_SUCCESS | ${query_time_ms}ms | $final_ip | NS: $ns_used | Timeouts: $has_timeout" >> "$LOG_FILE"
        echo "$trace_output" >> "$LOG_FILE"
        echo "---" >> "$LOG_FILE"
        
        rm -f "$trace_file"
        return 0
    else
        echo -e "${RED}✗${NC} 追蹤失敗 - ${query_time_ms}ms"
        echo -e "   ${RED}錯誤: 無法解析最終 IP${NC}"
        
        # 顯示錯誤訊息
        if [ "$has_timeout" -gt 0 ]; then
            echo -e "   ${YELLOW}偵測到 ${has_timeout} 次超時${NC}"
        fi
        
        echo "[$timestamp] TRACE_FAILED | ${query_time_ms}ms | Timeouts: $has_timeout" >> "$LOG_FILE"
        echo "$trace_output" >> "$LOG_FILE"
        echo "---" >> "$LOG_FILE"
        
        rm -f "$trace_file"
        return 1
    fi
}

# 主監控循環 - 直接查詢模式
monitor_direct() {
    local round=1
    
    # 總計統計變數
    local total_aws_success=0
    local total_aws_queries=0
    local total_google_success=0
    local total_google_queries=0
    
    # 各個 NS 的成功次數統計
    declare -A aws_ns_count
    declare -A google_ns_count
    for i in "${!AWS_NS[@]}"; do
        aws_ns_count["${AWS_NS[$i]}"]=0
    done
    for i in "${!GOOGLE_NS[@]}"; do
        google_ns_count["${GOOGLE_NS[$i]}"]=0
    done
    
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
            total_aws_queries=$((total_aws_queries + 1))
            if query_dns_direct "$ip" "$name" "$TEST_DOMAIN"; then
                aws_success=$((aws_success + 1))
                total_aws_success=$((total_aws_success + 1))
                aws_ns_count["$ip"]=$((aws_ns_count["$ip"] + 1))
            fi
        done
        
        echo ""
        
        # 查詢 Google NS
        echo -e "${YELLOW}Google Cloud DNS NS:${NC}"
        for i in "${!GOOGLE_NS[@]}"; do
            local ip="${GOOGLE_NS[$i]}"
            local name="Google-NS-$((i+1))"
            total_google_queries=$((total_google_queries + 1))
            if query_dns_direct "$ip" "$name" "$TEST_DOMAIN"; then
                google_success=$((google_success + 1))
                total_google_success=$((total_google_success + 1))
                google_ns_count["$ip"]=$((google_ns_count["$ip"] + 1))
            fi
        done
        
        echo ""
        
        # 顯示本輪統計
        echo -e "${BLUE}本輪統計:${NC}"
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
        
        echo ""
        
        # 顯示總計統計
        echo -e "${MAGENTA}總計統計 (累計):${NC}"
        local aws_success_rate=0
        local google_success_rate=0
        if [ $total_aws_queries -gt 0 ]; then
            aws_success_rate=$(awk "BEGIN {printf \"%.1f\", ($total_aws_success/$total_aws_queries)*100}")
        fi
        if [ $total_google_queries -gt 0 ]; then
            google_success_rate=$(awk "BEGIN {printf \"%.1f\", ($total_google_success/$total_google_queries)*100}")
        fi
        
        echo -e "  AWS NS 總計: ${GREEN}$total_aws_success${NC}/${total_aws_queries} 成功 (${aws_success_rate}%)"
        echo -e "  Google NS 總計: ${GREEN}$total_google_success${NC}/${total_google_queries} 成功 (${google_success_rate}%)"
        
        # 顯示各個 NS 的詳細統計
        echo ""
        echo -e "${CYAN}各 NS 成功次數:${NC}"
        echo -e "  ${YELLOW}AWS Route53:${NC}"
        for i in "${!AWS_NS[@]}"; do
            local ip="${AWS_NS[$i]}"
            local count=${aws_ns_count["$ip"]}
            echo -e "    NS-$((i+1)) ($ip): ${GREEN}$count${NC} 次"
        done
        
        echo -e "  ${YELLOW}Google Cloud DNS:${NC}"
        for i in "${!GOOGLE_NS[@]}"; do
            local ip="${GOOGLE_NS[$i]}"
            local count=${google_ns_count["$ip"]}
            echo -e "    NS-$((i+1)) ($ip): ${GREEN}$count${NC} 次"
        done
        
        # 寫入統計到日誌
        {
            echo "[$timestamp] SUMMARY | Round: $round | AWS: $aws_success/$aws_total | Google: $google_success/$google_total"
            echo "[$timestamp] TOTAL | AWS: $total_aws_success/$total_aws_queries (${aws_success_rate}%) | Google: $total_google_success/$total_google_queries (${google_success_rate}%)"
            echo ""
        } >> "$LOG_FILE"
        
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        round=$((round + 1))
        sleep "$INTERVAL"
    done
}

# 主監控循環 - 追蹤模式
monitor_trace() {
    local round=1
    
    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo -e "${CYAN}[$timestamp] 第 $round 輪追蹤監控${NC}\n"
        
        # 執行 dig +trace
        if query_dns_trace "$TEST_DOMAIN"; then
            echo -e "\n${GREEN}✓ 本輪追蹤成功${NC}"
        else
            echo -e "\n${RED}✗ 本輪追蹤失敗${NC}"
        fi
        
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        round=$((round + 1))
        sleep "$INTERVAL"
    done
}

# 主程式
main() {
    # 檢查 dig 是否可用
    if ! command -v dig &> /dev/null; then
        echo -e "${RED}錯誤: 找不到 dig 命令${NC}"
        echo "請安裝 bind-tools (Linux) 或 bind (macOS)"
        echo "  macOS: brew install bind"
        echo "  Ubuntu/Debian: sudo apt-get install dnsutils"
        echo "  CentOS/RHEL: sudo yum install bind-utils"
        exit 1
    fi
    
    clear
    echo -e "${GREEN}=== DNS 查詢監控 v1.0 ===${NC}\n"
    
    if [ "$USE_TRACE" = true ]; then
        echo -e "模式: ${MAGENTA}dig +trace 遞迴追蹤${NC}"
        echo -e "說明: 從根 DNS 開始追蹤，觀察完整解析路徑與故障切換"
    else
        echo -e "模式: ${CYAN}dig 直接查詢${NC}"
        echo -e "說明: 直接查詢各個 NS，測試可用性"
    fi
    
    echo ""
    echo -e "測試域名: ${CYAN}${TEST_DOMAIN}${NC}"
    echo -e "監控間隔: ${CYAN}${INTERVAL} 秒${NC}"
    
    if [ "$USE_TRACE" = true ]; then
        echo -e "追蹤超時: ${CYAN}${TRACE_TIMEOUT} 秒${NC}"
    else
        echo -e "DNS 超時: ${CYAN}${DNS_TIMEOUT} 秒${NC}"
    fi
    
    echo -e "日誌檔案: ${CYAN}$LOG_FILE${NC}"
    echo -e "按 ${YELLOW}Ctrl+C${NC} 停止監控\n"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 寫入日誌標頭
    {
        echo "=== DNS 查詢監控日誌 v1.0 ==="
        echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "模式: $([ "$USE_TRACE" = true ] && echo "dig +trace 追蹤" || echo "dig 直接查詢")"
        echo "測試域名: ${TEST_DOMAIN}"
        echo "監控間隔: ${INTERVAL} 秒"
        if [ "$USE_TRACE" = true ]; then
            echo "追蹤超時: ${TRACE_TIMEOUT} 秒"
        else
            echo "DNS 超時: ${DNS_TIMEOUT} 秒"
            echo "AWS NS: ${AWS_NS[*]}"
            echo "Google NS: ${GOOGLE_NS[*]}"
        fi
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    } > "$LOG_FILE"
    
    # 根據模式選擇監控函數
    if [ "$USE_TRACE" = true ]; then
        monitor_trace
    else
        monitor_direct
    fi
}

main "$@"
