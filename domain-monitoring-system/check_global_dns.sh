#!/bin/bash

# =====================================================
# 全球 DNS 解析檢測工具
# 使用全球主要公共 DNS 伺服器檢測域名解析
# =====================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 全球主要 DNS 伺服器列表
declare -A GLOBAL_DNS=(
    # Google Public DNS (美國)
    ["Google-Primary"]="8.8.8.8"
    ["Google-Secondary"]="8.8.4.4"
    
    # Cloudflare DNS (美國)
    ["Cloudflare-Primary"]="1.1.1.1"
    ["Cloudflare-Secondary"]="1.0.0.1"
    
    # Quad9 (瑞士)
    ["Quad9-Primary"]="9.9.9.9"
    ["Quad9-Secondary"]="149.112.112.112"
    
    # OpenDNS (美國)
    ["OpenDNS-Primary"]="208.67.222.222"
    ["OpenDNS-Secondary"]="208.67.220.220"
    
    # AdGuard DNS (塞浦路斯)
    ["AdGuard-Primary"]="94.140.14.14"
    ["AdGuard-Secondary"]="94.140.15.15"
    
    # DNS.Watch (德國)
    ["DNS.Watch-Primary"]="84.200.69.80"
    ["DNS.Watch-Secondary"]="84.200.70.40"
    
    # Comodo Secure DNS (美國)
    ["Comodo-Primary"]="8.26.56.26"
    ["Comodo-Secondary"]="8.20.247.20"
    
    # Level3 (美國)
    ["Level3-Primary"]="209.244.0.3"
    ["Level3-Secondary"]="209.244.0.4"
    
    # Verisign (美國)
    ["Verisign-Primary"]="64.6.64.6"
    ["Verisign-Secondary"]="64.6.65.6"
    
    # Alternate DNS (美國)
    ["Alternate-Primary"]="76.76.19.19"
    ["Alternate-Secondary"]="76.223.122.150"
)

# 統計變數
TOTAL_CHECKS=0
SUCCESS_COUNT=0
FAILED_COUNT=0
TIMEOUT_COUNT=0

# 結果儲存
declare -A RESULTS
declare -A IP_ADDRESSES
declare -A RESPONSE_TIMES

# =====================================================
# 函數：顯示標題
# =====================================================
show_header() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║         全球 DNS 解析檢測工具                             ║"
    echo "║         Global DNS Resolution Checker                    ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# =====================================================
# 函數：檢查依賴
# =====================================================
check_dependencies() {
    if ! command -v dig &> /dev/null; then
        echo -e "${RED}✗ 找不到 dig 命令${NC}"
        echo -e "${YELLOW}請安裝 dnsutils:${NC}"
        echo -e "  macOS: brew install bind"
        echo -e "  Ubuntu: sudo apt-get install dnsutils"
        exit 1
    fi
}

# =====================================================
# 函數：查詢單個 DNS（帶響應時間）
# =====================================================
query_dns() {
    local dns_name=$1
    local dns_server=$2
    local domain=$3
    local timeout=5
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # 記錄開始時間
    local start_time=$(date +%s%3N)
    
    # 執行 DNS 查詢
    local result=$(dig +short +time=$timeout +tries=1 @${dns_server} ${domain} A 2>&1)
    local exit_code=$?
    
    # 計算響應時間
    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        # 過濾掉非 IP 的結果（如 CNAME）
        local ip=$(echo "$result" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
        
        if [ -n "$ip" ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            RESULTS["$dns_name"]="✓"
            IP_ADDRESSES["$dns_name"]="$ip"
            RESPONSE_TIMES["$dns_name"]="${response_time}ms"
            
            # 根據響應時間顯示不同顏色
            local time_color=$GREEN
            if [ $response_time -gt 1000 ]; then
                time_color=$RED
            elif [ $response_time -gt 500 ]; then
                time_color=$YELLOW
            fi
            
            printf "${GREEN}✓${NC} %-25s | %-17s | ${CYAN}%-15s${NC} | ${time_color}%6s${NC}\n" \
                "${dns_name}" "${dns_server}" "${ip}" "${response_time}ms"
            return 0
        else
            # 可能是 CNAME，顯示原始結果
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            RESULTS["$dns_name"]="✓"
            IP_ADDRESSES["$dns_name"]="$result"
            RESPONSE_TIMES["$dns_name"]="${response_time}ms"
            printf "${GREEN}✓${NC} %-25s | %-17s | ${YELLOW}%-15s${NC} | ${response_time}ms\n" \
                "${dns_name}" "${dns_server}" "${result:0:15}"
            return 0
        fi
    elif [[ "$result" == *"connection timed out"* ]] || [[ "$result" == *"no servers could be reached"* ]]; then
        TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
        RESULTS["$dns_name"]="⏱"
        RESPONSE_TIMES["$dns_name"]="timeout"
        printf "${YELLOW}⏱${NC} %-25s | %-17s | ${YELLOW}%-15s${NC} | ${YELLOW}%6s${NC}\n" \
            "${dns_name}" "${dns_server}" "Timeout" "N/A"
        return 1
    else
        FAILED_COUNT=$((FAILED_COUNT + 1))
        RESULTS["$dns_name"]="✗"
        RESPONSE_TIMES["$dns_name"]="failed"
        printf "${RED}✗${NC} %-25s | %-17s | ${RED}%-15s${NC} | ${RED}%6s${NC}\n" \
            "${dns_name}" "${dns_server}" "Failed" "N/A"
        return 2
    fi
}

# =====================================================
# 函數：檢查所有 DNS
# =====================================================
check_all_dns() {
    local domain=$1
    
    echo -e "\n${BLUE}檢測域名：${MAGENTA}${domain}${NC}"
    echo -e "${BLUE}使用全球主要公共 DNS 伺服器${NC}\n"
    echo -e "${CYAN}狀態 | DNS 提供商              | DNS 伺服器        | 解析結果        | 響應時間${NC}"
    echo -e "${CYAN}-----|-------------------------|-------------------|-----------------|----------${NC}"
    
    # 按 DNS 提供商分組顯示
    local current_provider=""
    
    for dns_name in $(echo "${!GLOBAL_DNS[@]}" | tr ' ' '\n' | sort); do
        local dns_server="${GLOBAL_DNS[$dns_name]}"
        
        # 提取提供商名稱（去掉 -Primary, -Secondary 後綴）
        local provider=$(echo "$dns_name" | sed 's/-Primary$//' | sed 's/-Secondary$//')
        
        # 如果是新的提供商，顯示分隔
        if [ "$current_provider" != "$provider" ]; then
            if [ -n "$current_provider" ]; then
                echo ""
            fi
            current_provider="$provider"
        fi
        
        query_dns "$dns_name" "$dns_server" "$domain"
    done
}

# =====================================================
# 函數：顯示統計
# =====================================================
show_statistics() {
    local domain=$1
    
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}統計結果${NC}\n"
    
    local success_rate=0
    if [ $TOTAL_CHECKS -gt 0 ]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS_COUNT/$TOTAL_CHECKS)*100}")
    fi
    
    echo -e "域名：${MAGENTA}${domain}${NC}"
    echo -e "總檢測數：${CYAN}${TOTAL_CHECKS}${NC}"
    echo -e "成功：${GREEN}${SUCCESS_COUNT}${NC} | 失敗：${RED}${FAILED_COUNT}${NC} | 超時：${YELLOW}${TIMEOUT_COUNT}${NC}"
    echo -e "成功率：${GREEN}${success_rate}%${NC}"
    
    # 計算平均響應時間
    calculate_avg_response_time
    
    # 判斷狀態
    echo ""
    if [ $SUCCESS_COUNT -eq $TOTAL_CHECKS ]; then
        echo -e "${GREEN}✓ 所有全球 DNS 都能正常解析此域名${NC}"
    elif [ $SUCCESS_COUNT -ge $((TOTAL_CHECKS * 80 / 100)) ]; then
        echo -e "${YELLOW}⚠ 大部分全球 DNS 能解析，但有部分失敗${NC}"
    elif [ $SUCCESS_COUNT -ge $((TOTAL_CHECKS * 50 / 100)) ]; then
        echo -e "${YELLOW}⚠ 約半數全球 DNS 能解析此域名${NC}"
    else
        echo -e "${RED}✗ 大部分全球 DNS 無法解析此域名${NC}"
        echo -e "${RED}  可能原因：域名不存在或DNS配置錯誤${NC}"
    fi
    
    # 檢查 IP 一致性
    echo ""
    check_ip_consistency
}

# =====================================================
# 函數：計算平均響應時間
# =====================================================
calculate_avg_response_time() {
    local total_time=0
    local count=0
    
    for dns_name in "${!RESPONSE_TIMES[@]}"; do
        local time="${RESPONSE_TIMES[$dns_name]}"
        if [[ "$time" =~ ^[0-9]+ms$ ]]; then
            local time_value=$(echo "$time" | sed 's/ms$//')
            total_time=$((total_time + time_value))
            count=$((count + 1))
        fi
    done
    
    if [ $count -gt 0 ]; then
        local avg_time=$((total_time / count))
        echo -e "平均響應時間：${CYAN}${avg_time}ms${NC}"
        
        # 找出最快和最慢的
        local min_time=999999
        local max_time=0
        local fastest_dns=""
        local slowest_dns=""
        
        for dns_name in "${!RESPONSE_TIMES[@]}"; do
            local time="${RESPONSE_TIMES[$dns_name]}"
            if [[ "$time" =~ ^[0-9]+ms$ ]]; then
                local time_value=$(echo "$time" | sed 's/ms$//')
                if [ $time_value -lt $min_time ]; then
                    min_time=$time_value
                    fastest_dns="$dns_name"
                fi
                if [ $time_value -gt $max_time ]; then
                    max_time=$time_value
                    slowest_dns="$dns_name"
                fi
            fi
        done
        
        if [ -n "$fastest_dns" ]; then
            echo -e "最快：${GREEN}${fastest_dns}${NC} (${min_time}ms)"
            echo -e "最慢：${YELLOW}${slowest_dns}${NC} (${max_time}ms)"
        fi
    fi
}

# =====================================================
# 函數：檢查 IP 一致性
# =====================================================
check_ip_consistency() {
    local unique_ips=$(printf '%s\n' "${IP_ADDRESSES[@]}" | sort -u | wc -l)
    
    if [ $unique_ips -eq 1 ]; then
        local the_ip=$(printf '%s\n' "${IP_ADDRESSES[@]}" | head -1)
        echo -e "${GREEN}✓ 所有 DNS 解析結果一致${NC}"
        echo -e "  IP: ${CYAN}${the_ip}${NC}"
    elif [ $unique_ips -le 3 ]; then
        echo -e "${YELLOW}⚠ 發現 ${unique_ips} 個不同的解析結果${NC}"
        echo -e "${YELLOW}  這可能是正常的（CDN、負載均衡、GeoDNS）${NC}"
        echo -e "\n解析結果分佈："
        printf '%s\n' "${IP_ADDRESSES[@]}" | sort | uniq -c | while read count ip; do
            echo -e "  ${CYAN}${ip}${NC} - ${count} 個 DNS"
        done
    else
        echo -e "${RED}✗ 發現多個不同的解析結果 (${unique_ips}個)${NC}"
        echo -e "${RED}  可能存在 DNS 污染或配置問題${NC}"
        echo -e "\n解析結果分佈："
        printf '%s\n' "${IP_ADDRESSES[@]}" | sort | uniq -c | while read count ip; do
            echo -e "  ${CYAN}${ip}${NC} - ${count} 個 DNS"
        done
    fi
}

# =====================================================
# 函數：生成報告
# =====================================================
generate_report() {
    local domain=$1
    local report_file="global_dns_report_${domain}_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "全球 DNS 解析檢測報告"
        echo "====================="
        echo ""
        echo "域名: ${domain}"
        echo "檢測時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "檢測結果："
        echo "----------"
        
        for dns_name in $(echo "${!RESULTS[@]}" | tr ' ' '\n' | sort); do
            local status="${RESULTS[$dns_name]}"
            local dns_server="${GLOBAL_DNS[$dns_name]}"
            local ip="${IP_ADDRESSES[$dns_name]:-N/A}"
            local time="${RESPONSE_TIMES[$dns_name]:-N/A}"
            
            printf "%-25s | %-17s | %s | %-15s | %s\n" "$dns_name" "$dns_server" "$status" "$ip" "$time"
        done
        
        echo ""
        echo "統計："
        echo "------"
        echo "總檢測數: ${TOTAL_CHECKS}"
        echo "成功: ${SUCCESS_COUNT}"
        echo "失敗: ${FAILED_COUNT}"
        echo "超時: ${TIMEOUT_COUNT}"
        
        if [ $TOTAL_CHECKS -gt 0 ]; then
            local success_rate=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS_COUNT/$TOTAL_CHECKS)*100}")
            echo "成功率: ${success_rate}%"
        fi
        
    } > "$report_file"
    
    echo -e "\n${GREEN}✓ 報告已保存：${report_file}${NC}"
}

# =====================================================
# 函數：批量檢測
# =====================================================
batch_check() {
    local domain_file=$1
    
    if [ ! -f "$domain_file" ]; then
        echo -e "${RED}✗ 找不到文件：${domain_file}${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}批量檢測模式${NC}"
    echo -e "讀取域名列表：${domain_file}\n"
    
    local batch_report="global_dns_batch_report_$(date +%Y%m%d_%H%M%S).csv"
    echo "Domain,Total,Success,Failed,Timeout,Success_Rate,Avg_Response_Time" > "$batch_report"
    
    while IFS= read -r domain; do
        # 跳過空行和註釋
        [[ -z "$domain" || "$domain" =~ ^# ]] && continue
        
        # 重置統計
        TOTAL_CHECKS=0
        SUCCESS_COUNT=0
        FAILED_COUNT=0
        TIMEOUT_COUNT=0
        RESULTS=()
        IP_ADDRESSES=()
        RESPONSE_TIMES=()
        
        echo -e "${MAGENTA}檢測: ${domain}${NC}"
        
        for dns_name in "${!GLOBAL_DNS[@]}"; do
            local dns_server="${GLOBAL_DNS[$dns_name]}"
            query_dns "$dns_name" "$dns_server" "$domain" > /dev/null 2>&1
        done
        
        local success_rate=0
        if [ $TOTAL_CHECKS -gt 0 ]; then
            success_rate=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS_COUNT/$TOTAL_CHECKS)*100}")
        fi
        
        # 計算平均響應時間
        local total_time=0
        local count=0
        for dns_name in "${!RESPONSE_TIMES[@]}"; do
            local time="${RESPONSE_TIMES[$dns_name]}"
            if [[ "$time" =~ ^[0-9]+ms$ ]]; then
                local time_value=$(echo "$time" | sed 's/ms$//')
                total_time=$((total_time + time_value))
                count=$((count + 1))
            fi
        done
        
        local avg_time="N/A"
        if [ $count -gt 0 ]; then
            avg_time="$((total_time / count))ms"
        fi
        
        echo "${domain},${TOTAL_CHECKS},${SUCCESS_COUNT},${FAILED_COUNT},${TIMEOUT_COUNT},${success_rate}%,${avg_time}" >> "$batch_report"
        echo -e "  成功率: ${GREEN}${success_rate}%${NC} | 平均響應: ${CYAN}${avg_time}${NC}\n"
        
    done < "$domain_file"
    
    echo -e "${GREEN}✓ 批量報告已保存：${batch_report}${NC}"
}

# =====================================================
# 主程序
# =====================================================
main() {
    show_header
    check_dependencies
    
    # 解析參數
    if [ $# -eq 0 ]; then
        echo -e "${YELLOW}使用方法：${NC}"
        echo -e "  單個域名: $0 <domain>"
        echo -e "  批量檢測: $0 -f <domain_list.txt>"
        echo ""
        echo -e "${YELLOW}範例：${NC}"
        echo -e "  $0 google.com"
        echo -e "  $0 -f domains.txt"
        exit 1
    fi
    
    if [ "$1" == "-f" ]; then
        if [ -z "$2" ]; then
            echo -e "${RED}✗ 請提供域名列表文件${NC}"
            exit 1
        fi
        batch_check "$2"
    else
        local domain=$1
        check_all_dns "$domain"
        show_statistics "$domain"
        generate_report "$domain"
    fi
    
    echo ""
}

# 執行主程序
main "$@"

