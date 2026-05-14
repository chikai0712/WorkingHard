#!/bin/bash

# =====================================================
# 印尼 ISP DNS 查詢工具
# 使用印尼前10大ISP的DNS伺服器檢測域名解析
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

# 印尼 ISP DNS 伺服器列表
declare -A INDONESIA_DNS=(
    # Telkomsel (最大行動網路)
    ["Telkomsel-1"]="202.3.208.5"
    ["Telkomsel-2"]="202.3.208.6"
    
    # Indosat Ooredoo (第二大)
    ["Indosat-1"]="202.155.0.10"
    ["Indosat-2"]="202.155.0.15"
    
    # XL Axiata (第三大)
    ["XL-Axiata-1"]="202.152.0.2"
    ["XL-Axiata-2"]="202.152.2.2"
    
    # Biznet (企業/高端)
    ["Biznet-1"]="202.169.224.68"
    ["Biznet-2"]="202.169.224.69"
    
    # First Media (雅加達主要)
    ["First-Media-1"]="203.130.193.74"
    ["First-Media-2"]="203.130.206.250"
    
    # Telkom Indonesia (IndiHome 固網)
    ["Telkom-1"]="202.134.0.155"
    ["Telkom-2"]="202.134.1.10"
    
    # CBN (Cyber)
    ["CBN-1"]="202.158.3.6"
    ["CBN-2"]="202.158.3.7"
    
    # MyRepublic
    ["MyRepublic-1"]="103.10.66.66"
    ["MyRepublic-2"]="103.10.67.67"
)

# 統計變數
TOTAL_CHECKS=0
SUCCESS_COUNT=0
FAILED_COUNT=0
TIMEOUT_COUNT=0

# 結果儲存
declare -A RESULTS
declare -A IP_ADDRESSES

# =====================================================
# 函數：顯示標題
# =====================================================
show_header() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║         印尼 ISP DNS 查詢工具                             ║"
    echo "║         Indonesia Top 10 ISP DNS Checker                 ║"
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
# 函數：查詢單個 DNS
# =====================================================
query_dns() {
    local isp_name=$1
    local dns_server=$2
    local domain=$3
    local timeout=3
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # 執行 DNS 查詢
    local result=$(dig +short +time=$timeout +tries=1 @${dns_server} ${domain} A 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        # 過濾掉非 IP 的結果（如 CNAME）
        local ip=$(echo "$result" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
        
        if [ -n "$ip" ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            RESULTS["$isp_name"]="✓"
            IP_ADDRESSES["$isp_name"]="$ip"
            echo -e "${GREEN}✓${NC} ${isp_name:0:20} | ${dns_server:0:15} | ${CYAN}${ip}${NC}"
            return 0
        else
            # 可能是 CNAME，顯示原始結果
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            RESULTS["$isp_name"]="✓"
            IP_ADDRESSES["$isp_name"]="$result"
            echo -e "${GREEN}✓${NC} ${isp_name:0:20} | ${dns_server:0:15} | ${YELLOW}${result:0:30}${NC}"
            return 0
        fi
    elif [[ "$result" == *"connection timed out"* ]] || [[ "$result" == *"no servers could be reached"* ]]; then
        TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
        RESULTS["$isp_name"]="⏱"
        echo -e "${YELLOW}⏱${NC} ${isp_name:0:20} | ${dns_server:0:15} | ${YELLOW}Timeout${NC}"
        return 1
    else
        FAILED_COUNT=$((FAILED_COUNT + 1))
        RESULTS["$isp_name"]="✗"
        echo -e "${RED}✗${NC} ${isp_name:0:20} | ${dns_server:0:15} | ${RED}Failed${NC}"
        return 2
    fi
}

# =====================================================
# 函數：檢查所有 DNS
# =====================================================
check_all_dns() {
    local domain=$1
    
    echo -e "\n${BLUE}檢測域名：${MAGENTA}${domain}${NC}"
    echo -e "${BLUE}使用印尼前10大ISP的DNS伺服器${NC}\n"
    echo -e "${CYAN}狀態 | ISP 名稱           | DNS 伺服器      | 解析結果${NC}"
    echo -e "${CYAN}-----|---------------------|-----------------|------------------${NC}"
    
    # 按 ISP 分組顯示
    local current_isp=""
    
    for isp_name in $(echo "${!INDONESIA_DNS[@]}" | tr ' ' '\n' | sort); do
        local dns_server="${INDONESIA_DNS[$isp_name]}"
        
        # 提取 ISP 主名稱（去掉 -1, -2 後綴）
        local main_isp=$(echo "$isp_name" | sed 's/-[0-9]$//')
        
        # 如果是新的 ISP，顯示分隔
        if [ "$current_isp" != "$main_isp" ]; then
            if [ -n "$current_isp" ]; then
                echo ""
            fi
            current_isp="$main_isp"
        fi
        
        query_dns "$isp_name" "$dns_server" "$domain"
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
    
    # 判斷狀態
    echo ""
    if [ $SUCCESS_COUNT -eq $TOTAL_CHECKS ]; then
        echo -e "${GREEN}✓ 所有印尼ISP都能正常解析此域名${NC}"
    elif [ $SUCCESS_COUNT -ge $((TOTAL_CHECKS * 80 / 100)) ]; then
        echo -e "${YELLOW}⚠ 大部分印尼ISP能解析，但有部分失敗${NC}"
    elif [ $SUCCESS_COUNT -ge $((TOTAL_CHECKS * 50 / 100)) ]; then
        echo -e "${YELLOW}⚠ 約半數印尼ISP能解析此域名${NC}"
    else
        echo -e "${RED}✗ 大部分印尼ISP無法解析此域名${NC}"
        echo -e "${RED}  可能原因：域名被封鎖或DNS污染${NC}"
    fi
    
    # 檢查 IP 一致性
    echo ""
    check_ip_consistency
}

# =====================================================
# 函數：檢查 IP 一致性
# =====================================================
check_ip_consistency() {
    local unique_ips=$(printf '%s\n' "${IP_ADDRESSES[@]}" | sort -u | wc -l)
    
    if [ $unique_ips -eq 1 ]; then
        local the_ip=$(printf '%s\n' "${IP_ADDRESSES[@]}" | head -1)
        echo -e "${GREEN}✓ 所有ISP解析結果一致${NC}"
        echo -e "  IP: ${CYAN}${the_ip}${NC}"
    elif [ $unique_ips -le 3 ]; then
        echo -e "${YELLOW}⚠ 發現 ${unique_ips} 個不同的解析結果${NC}"
        echo -e "\n解析結果分佈："
        printf '%s\n' "${IP_ADDRESSES[@]}" | sort | uniq -c | while read count ip; do
            echo -e "  ${CYAN}${ip}${NC} - ${count} 個ISP"
        done
    else
        echo -e "${RED}✗ 發現多個不同的解析結果 (${unique_ips}個)${NC}"
        echo -e "${RED}  可能存在DNS劫持或污染${NC}"
        echo -e "\n解析結果分佈："
        printf '%s\n' "${IP_ADDRESSES[@]}" | sort | uniq -c | while read count ip; do
            echo -e "  ${CYAN}${ip}${NC} - ${count} 個ISP"
        done
    fi
}

# =====================================================
# 函數：生成報告
# =====================================================
generate_report() {
    local domain=$1
    local report_file="indonesia_dns_report_${domain}_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "印尼 ISP DNS 查詢報告"
        echo "====================="
        echo ""
        echo "域名: ${domain}"
        echo "檢測時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "檢測結果："
        echo "----------"
        
        for isp_name in $(echo "${!RESULTS[@]}" | tr ' ' '\n' | sort); do
            local status="${RESULTS[$isp_name]}"
            local dns_server="${INDONESIA_DNS[$isp_name]}"
            local ip="${IP_ADDRESSES[$isp_name]:-N/A}"
            
            printf "%-20s | %-15s | %s | %s\n" "$isp_name" "$dns_server" "$status" "$ip"
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
    
    local batch_report="indonesia_dns_batch_report_$(date +%Y%m%d_%H%M%S).csv"
    echo "Domain,Total,Success,Failed,Timeout,Success_Rate" > "$batch_report"
    
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
        
        echo -e "${MAGENTA}檢測: ${domain}${NC}"
        
        for isp_name in "${!INDONESIA_DNS[@]}"; do
            local dns_server="${INDONESIA_DNS[$isp_name]}"
            query_dns "$isp_name" "$dns_server" "$domain" > /dev/null 2>&1
        done
        
        local success_rate=0
        if [ $TOTAL_CHECKS -gt 0 ]; then
            success_rate=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS_COUNT/$TOTAL_CHECKS)*100}")
        fi
        
        echo "${domain},${TOTAL_CHECKS},${SUCCESS_COUNT},${FAILED_COUNT},${TIMEOUT_COUNT},${success_rate}%" >> "$batch_report"
        echo -e "  成功率: ${GREEN}${success_rate}%${NC}\n"
        
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

