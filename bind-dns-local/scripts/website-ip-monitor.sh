#!/bin/bash
# -------------------------------------------------------------------------------
# 網站 IP 監控腳本 v1.0 - 監控 DNS 解析 IP 和網頁顯示 IP
# 功能：
#   1. 即時監控 DNS 解析到的實際 IP
#   2. 抓取網頁內容中顯示的伺服器 IP
#   3. 對比兩者差異，判斷當前使用的伺服器
#   4. 支援自訂監控間隔和域名
# 
# 用法：
#   bash ./website-ip-monitor.sh [間隔秒數] [域名]
#   
# 範例：
#   bash ./website-ip-monitor.sh 2 www.clouddeployment168.site
#   bash ./website-ip-monitor.sh 5 example.com
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
LOG_FILE="/tmp/website_ip_monitor_$(date +%Y%m%d_%H%M%S).log"

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

# 查詢 DNS 解析的 IP
get_dns_ip() {
    local domain=$1
    local dns_ip=$(dig +short "$domain" A | grep -E '^[0-9.]+$' | head -1)
    echo "$dns_ip"
}

# 從網頁內容中提取顯示的 IP
get_webpage_ip() {
    local domain=$1
    local webpage_content=$(curl -s --max-time 5 "http://$domain/" 2>/dev/null)
    
    # 嘗試多種模式匹配網頁中的 IP
    local displayed_ip=""
    
    # 模式 1: IP: X.X.X.X
    displayed_ip=$(echo "$webpage_content" | grep -oE 'IP[: ]+[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | head -1)
    
    # 模式 2: 如果找不到，嘗試找任何 IP 格式
    if [ -z "$displayed_ip" ]; then
        displayed_ip=$(echo "$webpage_content" | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | head -1)
    fi
    
    echo "$displayed_ip"
}

# 判斷伺服器類型
identify_server() {
    local ip=$1
    
    case "$ip" in
        3.3.3.3)
            echo "AWS 主服務器"
            ;;
        2.2.2.2)
            echo "Google 備援服務器"
            ;;
        4.4.4.4)
            echo "Google 備援服務器"
            ;;
        *)
            echo "未知伺服器"
            ;;
    esac
}

# 主監控函數
monitor_website() {
    local round=1
    local last_dns_ip=""
    local last_webpage_ip=""
    local change_count=0
    
    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        # 查詢 DNS IP
        local dns_ip=$(get_dns_ip "$DOMAIN")
        
        # 查詢網頁顯示的 IP
        local webpage_ip=$(get_webpage_ip "$DOMAIN")
        
        # 檢測變化
        local dns_changed=false
        local webpage_changed=false
        
        if [ "$dns_ip" != "$last_dns_ip" ] && [ -n "$last_dns_ip" ]; then
            dns_changed=true
            change_count=$((change_count + 1))
        fi
        
        if [ "$webpage_ip" != "$last_webpage_ip" ] && [ -n "$last_webpage_ip" ]; then
            webpage_changed=true
        fi
        
        # 顯示標題
        echo -e "${CYAN}[$timestamp] 第 $round 輪監控${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # 顯示域名
        echo -e "${YELLOW}域名:${NC} $DOMAIN"
        echo ""
        
        # 顯示 DNS 解析 IP
        if [ -n "$dns_ip" ]; then
            if [ "$dns_changed" = true ]; then
                echo -e "${MAGENTA}🔄 DNS IP 已變更!${NC}"
                echo -e "  ${RED}舊 IP: $last_dns_ip${NC}"
                echo -e "  ${GREEN}新 IP: $dns_ip${NC}"
            else
                echo -e "${GREEN}✓${NC} DNS 解析 IP: ${GREEN}$dns_ip${NC}"
            fi
        else
            echo -e "${RED}✗${NC} DNS 解析失敗"
        fi
        
        echo ""
        
        # 顯示網頁顯示的 IP
        if [ -n "$webpage_ip" ]; then
            local server_type=$(identify_server "$webpage_ip")
            
            if [ "$webpage_changed" = true ]; then
                echo -e "${MAGENTA}🔄 網頁顯示 IP 已變更!${NC}"
                echo -e "  ${RED}舊 IP: $last_webpage_ip${NC}"
                echo -e "  ${GREEN}新 IP: $webpage_ip${NC}"
            else
                echo -e "${GREEN}✓${NC} 網頁顯示 IP: ${CYAN}$webpage_ip${NC}"
            fi
            
            echo -e "  ${BLUE}伺服器類型: $server_type${NC}"
        else
            echo -e "${RED}✗${NC} 無法取得網頁內容"
        fi
        
        echo ""
        
        # 對比分析
        if [ -n "$dns_ip" ] && [ -n "$webpage_ip" ]; then
            echo -e "${YELLOW}分析:${NC}"
            echo -e "  實際連接 IP: $dns_ip"
            echo -e "  網頁標示為: $webpage_ip ($(identify_server "$webpage_ip"))"
            
            if [ "$dns_ip" == "$webpage_ip" ]; then
                echo -e "  ${GREEN}✓ IP 一致${NC}"
            else
                echo -e "  ${YELLOW}⚠ IP 不一致 (網頁顯示的是標識用 IP)${NC}"
            fi
        fi
        
        echo ""
        
        # 統計資訊
        echo -e "${BLUE}統計:${NC}"
        echo -e "  監控輪數: $round"
        echo -e "  IP 變更次數: $change_count"
        
        # 寫入日誌
        {
            echo "[$timestamp] Round: $round | DNS IP: $dns_ip | Webpage IP: $webpage_ip | Server: $(identify_server "$webpage_ip")"
            if [ "$dns_changed" = true ]; then
                echo "[$timestamp] DNS IP CHANGED: $last_dns_ip -> $dns_ip"
            fi
            if [ "$webpage_changed" = true ]; then
                echo "[$timestamp] WEBPAGE IP CHANGED: $last_webpage_ip -> $webpage_ip"
            fi
        } >> "$LOG_FILE"
        
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        
        # 更新上一次的值
        last_dns_ip="$dns_ip"
        last_webpage_ip="$webpage_ip"
        
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
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}錯誤: 找不到 curl 命令${NC}"
        echo "請安裝 curl"
        exit 1
    fi
    
    clear
    echo -e "${GREEN}=== 網站 IP 監控 v1.0 ===${NC}\n"
    echo -e "監控域名: ${CYAN}${DOMAIN}${NC}"
    echo -e "監控間隔: ${CYAN}${INTERVAL} 秒${NC}"
    echo -e "日誌檔案: ${CYAN}$LOG_FILE${NC}"
    echo -e "按 ${YELLOW}Ctrl+C${NC} 停止監控\n"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 寫入日誌標頭
    {
        echo "=== 網站 IP 監控日誌 v1.0 ==="
        echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "監控域名: ${DOMAIN}"
        echo "監控間隔: ${INTERVAL} 秒"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    } > "$LOG_FILE"
    
    monitor_website
}

main "$@"

