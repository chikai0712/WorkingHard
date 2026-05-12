#!/bin/bash
# -------------------------------------------------------------------------------
# DNS IP 監控腳本 v2.0 - 監控 DNS 解析 IP 變化並識別回應的 NS
# 功能：
#   1. 即時監控 DNS 解析到的實際 IP
#   2. 偵測 IP 變化並發出警告
#   3. 識別是哪組 NS (AWS/Google) 回應的
#   4. 記錄完整的 IP 變更歷史
# 
# 用法：
#   bash ./dns-ip-monitor.sh [間隔秒數] [域名]
#   
# 範例：
#   bash ./dns-ip-monitor.sh 2 www.clouddeployment168.site
#   bash ./dns-ip-monitor.sh 5 example.com
#
# 預設間隔：2 秒
# 預設域名：www.clouddeployment168.site
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
INTERVAL=2
DOMAIN="www.clouddeployment168.site"

for arg in "$@"; do
    case "$arg" in
        --help|-h)
            echo "用法: $0 [選項] [間隔秒數] [域名]"
            echo ""
            echo "選項:"
            echo "  --help     顯示此幫助訊息"
            echo ""
            echo "範例:"
            echo "  $0 2 www.example.com          # 每 2 秒監控一次"
            echo "  $0 5 example.com              # 每 5 秒監控一次"
            exit 0
            ;;
        *)
            if [[ "$arg" =~ ^[0-9]+$ ]]; then
                INTERVAL="$arg"
            elif [[ "$arg" != --* ]]; then
                DOMAIN="$arg"
            fi
            ;;
    esac
done

# 配置
LOG_FILE="/tmp/dns_ip_monitor_$(date +%Y%m%d_%H%M%S).log"

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

# 查詢特定 NS 並檢查回應
query_specific_ns() {
    local domain=$1
    local ns_ip=$2
    
    # 直接查詢指定的 NS
    local result=$(dig @"$ns_ip" "$domain" A +time=2 +tries=1 +short 2>&1 | grep -E '^[0-9.]+$' | head -1)
    echo "$result"
}

# 識別是哪組 NS 回應的
identify_responding_ns() {
    local domain=$1
    local resolved_ip=$2
    
    # 測試 AWS NS
    for ns_ip in "${AWS_NS[@]}"; do
        local test_ip=$(query_specific_ns "$domain" "$ns_ip")
        if [ "$test_ip" == "$resolved_ip" ]; then
            echo "AWS|$ns_ip"
            return 0
        fi
    done
    
    # 測試 Google NS
    for ns_ip in "${GOOGLE_NS[@]}"; do
        local test_ip=$(query_specific_ns "$domain" "$ns_ip")
        if [ "$test_ip" == "$resolved_ip" ]; then
            echo "Google|$ns_ip"
            return 0
        fi
    done
    
    echo "Unknown|"
}

# 查詢 DNS 解析的 IP（完整資訊）
get_dns_info() {
    local domain=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 執行 dig 查詢
    local dig_output=$(dig "$domain" A 2>&1)
    
    # 提取 IP
    local dns_ip=$(echo "$dig_output" | grep -A 1 "ANSWER SECTION" | grep -E "^${domain}" | awk '{print $NF}' | grep -E '^[0-9.]+$' | head -1)
    
    # 如果沒找到，嘗試用 +short
    if [ -z "$dns_ip" ]; then
        dns_ip=$(dig +short "$domain" A | grep -E '^[0-9.]+$' | head -1)
    fi
    
    # 提取回應的 DNS 伺服器（本機 DNS）
    local dns_server=$(echo "$dig_output" | grep "SERVER:" | awk '{print $3}' | cut -d'#' -f1)
    
    # 提取查詢時間
    local query_time=$(echo "$dig_output" | grep "Query time:" | awk '{print $4}')
    
    # 提取 TTL
    local ttl=$(echo "$dig_output" | grep -A 1 "ANSWER SECTION" | grep -E "^${domain}" | awk '{print $2}' | head -1)
    
    # 識別是哪組權威 NS 回應的
    local ns_info=""
    local ns_provider=""
    if [ -n "$dns_ip" ]; then
        ns_info=$(identify_responding_ns "$domain" "$dns_ip")
        ns_provider=$(echo "$ns_info" | cut -d'|' -f1)
        local ns_ip=$(echo "$ns_info" | cut -d'|' -f2)
    fi
    
    echo "$dns_ip|$dns_server|$query_time|$ttl|$ns_provider|$ns_ip"
}

# 判斷 IP 對應的伺服器
identify_server_by_ip() {
    local ip=$1
    
    # 根據實際 IP 判斷（你需要根據實際情況調整）
    case "$ip" in
        35.74.79.10)
            echo "AWS 主機 1"
            ;;
        54.*)
            echo "AWS 主機"
            ;;
        35.*)
            echo "AWS 主機"
            ;;
        34.*)
            echo "Google Cloud 主機"
            ;;
        *)
            echo "未知主機"
            ;;
    esac
}

# 主監控函數
monitor_dns_ip() {
    local round=1
    local last_ip=""
    local last_ns_provider=""
    local change_count=0
    local ip_history=()
    
    # NS 使用次數統計
    local aws_count=0
    local google_count=0
    local unknown_count=0
    
    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # 查詢 DNS 資訊
        local dns_info=$(get_dns_info "$DOMAIN")
        local current_ip=$(echo "$dns_info" | cut -d'|' -f1)
        local dns_server=$(echo "$dns_info" | cut -d'|' -f2)
        local query_time=$(echo "$dns_info" | cut -d'|' -f3)
        local ttl=$(echo "$dns_info" | cut -d'|' -f4)
        local ns_provider=$(echo "$dns_info" | cut -d'|' -f5)
        local ns_ip=$(echo "$dns_info" | cut -d'|' -f6)
        
        # 檢測 IP 變化
        local ip_changed=false
        local ns_changed=false
        
        if [ "$current_ip" != "$last_ip" ] && [ -n "$last_ip" ]; then
            ip_changed=true
            change_count=$((change_count + 1))
            ip_history+=("$timestamp: $last_ip ($last_ns_provider) -> $current_ip ($ns_provider)")
        fi
        
        if [ "$ns_provider" != "$last_ns_provider" ] && [ -n "$last_ns_provider" ]; then
            ns_changed=true
        fi
        
        # 統計 NS 使用次數
        if [ "$ns_provider" == "AWS" ]; then
            aws_count=$((aws_count + 1))
        elif [ "$ns_provider" == "Google" ]; then
            google_count=$((google_count + 1))
        else
            unknown_count=$((unknown_count + 1))
        fi
        
        # 顯示標題
        echo -e "${CYAN}[$timestamp] 第 $round 輪監控${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # 顯示域名
        echo -e "${YELLOW}監控域名:${NC} $DOMAIN"
        echo ""
        
        # 顯示 DNS 解析結果
        if [ -n "$current_ip" ]; then
            if [ "$ip_changed" = true ]; then
                echo -e "${MAGENTA}🔄 DNS IP 已變更！${NC}"
                echo -e "  ${RED}舊 IP: $last_ip${NC}"
                echo -e "  ${GREEN}新 IP: $current_ip${NC}"
                echo -e "  ${YELLOW}⚠️  偵測到 Failover 或 DNS 更新！${NC}"
            else
                echo -e "${GREEN}✓ DNS 解析 IP: ${GREEN}$current_ip${NC}"
            fi
            
            # 顯示伺服器資訊
            local server_type=$(identify_server_by_ip "$current_ip")
            echo -e "  ${BLUE}伺服器: $server_type${NC}"
            
        else
            echo -e "${RED}✗ DNS 解析失敗${NC}"
        fi
        
        echo ""
        
        # 顯示權威 NS 資訊（重點）
        echo -e "${YELLOW}權威 NS 資訊:${NC}"
        if [ -n "$ns_provider" ]; then
            if [ "$ns_provider" == "AWS" ]; then
                echo -e "  ${GREEN}✓ 回應來自: AWS Route53 NS${NC}"
                echo -e "  ${CYAN}NS IP: $ns_ip${NC}"
            elif [ "$ns_provider" == "Google" ]; then
                echo -e "  ${GREEN}✓ 回應來自: Google Cloud DNS NS${NC}"
                echo -e "  ${CYAN}NS IP: $ns_ip${NC}"
            else
                echo -e "  ${YELLOW}⚠ 無法識別權威 NS${NC}"
            fi
            
            if [ "$ns_changed" = true ]; then
                echo -e "  ${MAGENTA}🔄 NS 提供商已切換: $last_ns_provider -> $ns_provider${NC}"
            fi
        fi
        
        echo ""
        
        # 顯示 DNS 查詢詳細資訊
        echo -e "${YELLOW}DNS 查詢資訊:${NC}"
        if [ -n "$dns_server" ]; then
            echo -e "  本機 DNS: ${CYAN}$dns_server${NC}"
        fi
        if [ -n "$query_time" ]; then
            echo -e "  查詢時間: ${CYAN}${query_time} ms${NC}"
        fi
        if [ -n "$ttl" ]; then
            echo -e "  TTL: ${CYAN}${ttl} 秒${NC}"
        fi
        
        echo ""
        
        # 統計資訊
        echo -e "${BLUE}統計資訊:${NC}"
        echo -e "  監控輪數: $round"
        echo -e "  IP 變更次數: $change_count"
        echo -e "  當前 NS 提供商: ${GREEN}$ns_provider${NC}"
        
        echo ""
        
        # NS 使用次數統計
        echo -e "${MAGENTA}NS 使用統計 (累計):${NC}"
        local total_queries=$((aws_count + google_count + unknown_count))
        local aws_percentage=0
        local google_percentage=0
        
        if [ $total_queries -gt 0 ]; then
            aws_percentage=$(awk "BEGIN {printf \"%.1f\", ($aws_count/$total_queries)*100}")
            google_percentage=$(awk "BEGIN {printf \"%.1f\", ($google_count/$total_queries)*100}")
        fi
        
        echo -e "  ${GREEN}AWS Route53:${NC} $aws_count 次 (${aws_percentage}%)"
        echo -e "  ${GREEN}Google Cloud DNS:${NC} $google_count 次 (${google_percentage}%)"
        if [ $unknown_count -gt 0 ]; then
            echo -e "  ${YELLOW}未知:${NC} $unknown_count 次"
        fi
        echo -e "  ${CYAN}總查詢次數:${NC} $total_queries 次"
        
        if [ $change_count -gt 0 ]; then
            echo ""
            echo -e "${YELLOW}IP 變更歷史:${NC}"
            for history in "${ip_history[@]}"; do
                echo -e "  ${MAGENTA}→${NC} $history"
            done
        fi
        
        # 寫入日誌
        {
            echo "[$timestamp] Round: $round | DNS IP: $current_ip | NS Provider: $ns_provider | NS IP: $ns_ip | Local DNS: $dns_server | Query Time: ${query_time}ms | TTL: ${ttl}s"
            if [ "$ip_changed" = true ]; then
                echo "[$timestamp] ⚠️  IP CHANGED: $last_ip -> $current_ip"
            fi
            if [ "$ns_changed" = true ]; then
                echo "[$timestamp] ⚠️  NS PROVIDER CHANGED: $last_ns_provider -> $ns_provider"
            fi
        } >> "$LOG_FILE"
        
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        # 更新上一次的值
        last_ip="$current_ip"
        last_ns_provider="$ns_provider"
        
        round=$((round + 1))
        sleep "$INTERVAL"
    done
}

# 主程式
main() {
    # 檢查必要工具
    if ! command -v dig &> /dev/null; then
        echo -e "${RED}錯誤: 找不到 dig 命令${NC}"
        echo "請安裝 bind-tools"
        echo "  macOS: brew install bind"
        echo "  Ubuntu/Debian: sudo apt-get install dnsutils"
        echo "  CentOS/RHEL: sudo yum install bind-utils"
        exit 1
    fi
    
    clear
    echo -e "${GREEN}=== DNS IP 監控 v1.0 ===${NC}\n"
    echo -e "監控域名: ${CYAN}${DOMAIN}${NC}"
    echo -e "監控間隔: ${CYAN}${INTERVAL} 秒${NC}"
    echo -e "日誌檔案: ${CYAN}$LOG_FILE${NC}"
    echo -e "按 ${YELLOW}Ctrl+C${NC} 停止監控\n"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 寫入日誌標頭
    {
        echo "=== DNS IP 監控日誌 v1.0 ==="
        echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "監控域名: ${DOMAIN}"
        echo "監控間隔: ${INTERVAL} 秒"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    } > "$LOG_FILE"
    
    monitor_dns_ip
}

main "$@"

