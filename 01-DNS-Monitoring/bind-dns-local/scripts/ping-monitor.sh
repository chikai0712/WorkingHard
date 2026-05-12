#!/bin/bash
# -------------------------------------------------------------------------------
# 持續 Ping 監控腳本 - AWS 和 Google NS
# 功能：持續 ping AWS Route53 和 Google Cloud DNS 的 NS 伺服器
# 
# 用法：
#   bash ./ping-monitor.sh [間隔秒數]
#   例如：bash ./ping-monitor.sh 5
#
# 預設間隔：2 秒
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
INTERVAL="${1:-1}"  # ping 間隔（秒），預設 1 秒
PING_TIMEOUT=2      # ping 超時時間（秒），預設 2 秒
LOG_FILE="/tmp/ping_monitor_$(date +%Y%m%d_%H%M%S).log"

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

# Ping 單個 IP
ping_ip() {
    local ip=$1
    local name=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 執行 ping 並捕獲完整輸出
    local ping_output
    ping_output=$(ping -c 1 -W "$PING_TIMEOUT" "$ip" 2>&1)
    local ping_status=$?
    
    if [ $ping_status -eq 0 ]; then
        # 從輸出中提取延遲時間
        # macOS ping 格式: "64 bytes from 8.8.8.8: icmp_seq=0 ttl=117 time=12.345 ms"
        local latency=$(echo "$ping_output" | grep -oE "time=[0-9]+\.[0-9]+" | cut -d'=' -f2)
        
        if [ -z "$latency" ]; then
            # 備用方法：提取整數部分
            latency=$(echo "$ping_output" | grep -oE "time=[0-9]+" | cut -d'=' -f2)
        fi
        
        if [ -z "$latency" ]; then
            latency="<1"
        fi
        
        echo -e "${GREEN}✓${NC} $name ($ip) - ${latency}ms"
        echo "[$timestamp] SUCCESS | $name | $ip | ${latency}ms" >> "$LOG_FILE"
        return 0
    else
        echo -e "${RED}✗${NC} $name ($ip) - 超時 (>${PING_TIMEOUT}s)"
        echo "[$timestamp] TIMEOUT | $name | $ip | >${PING_TIMEOUT}s" >> "$LOG_FILE"
        return 1
    fi
}

# 主監控循環
main() {
    clear
    echo -e "${GREEN}=== DNS NS 連線監控 ===${NC}\n"
    echo -e "監控間隔: ${CYAN}${INTERVAL} 秒${NC}"
    echo -e "Ping 超時: ${CYAN}${PING_TIMEOUT} 秒${NC}"
    echo -e "日誌檔案: ${CYAN}$LOG_FILE${NC}"
    echo -e "按 ${YELLOW}Ctrl+C${NC} 停止監控\n"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 寫入日誌標頭
    {
        echo "=== DNS NS 連線監控日誌 ==="
        echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "監控間隔: ${INTERVAL} 秒"
        echo "Ping 超時: ${PING_TIMEOUT} 秒"
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
        
        # Ping AWS NS
        echo -e "${YELLOW}AWS Route53 NS:${NC}"
        for i in "${!AWS_NS[@]}"; do
            local ip="${AWS_NS[$i]}"
            local name="AWS-NS-$((i+1))"
            if ping_ip "$ip" "$name"; then
                aws_success=$((aws_success + 1))
            fi
        done
        
        echo ""
        
        # Ping Google NS
        echo -e "${YELLOW}Google Cloud DNS NS:${NC}"
        for i in "${!GOOGLE_NS[@]}"; do
            local ip="${GOOGLE_NS[$i]}"
            local name="Google-NS-$((i+1))"
            if ping_ip "$ip" "$name"; then
                google_success=$((google_success + 1))
            fi
        done
        
        echo ""
        
        # 顯示統計
        echo -e "${BLUE}統計:${NC}"
        echo -e "  AWS NS: ${GREEN}$aws_success${NC}/${aws_total} 可達"
        echo -e "  Google NS: ${GREEN}$google_success${NC}/${google_total} 可達"
        
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
