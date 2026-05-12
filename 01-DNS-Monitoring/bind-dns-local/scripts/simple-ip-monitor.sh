#!/bin/bash
# -------------------------------------------------------------------------------
# 簡單 IP 監控腳本 - 持續監控 DNS 解析 IP 變化
# 用法：
#   bash ./simple-ip-monitor.sh [域名] [間隔秒數]
#   
# 範例：
#   bash ./simple-ip-monitor.sh www.clouddeployment168.site 2
#   bash ./simple-ip-monitor.sh example.com 5
#
# 預設域名：www.clouddeployment168.site
# 預設間隔：2 秒
# 按 Ctrl+C 停止
# -------------------------------------------------------------------------------

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

DOMAIN="${1:-www.clouddeployment168.site}"
INTERVAL="${2:-2}"
last_ip=""
change_count=0

clear
echo -e "${GREEN}=== 簡單 IP 監控 ===${NC}"
echo -e "監控域名: ${CYAN}$DOMAIN${NC}"
echo -e "監控間隔: ${CYAN}$INTERVAL 秒${NC}"
echo -e "按 ${YELLOW}Ctrl+C${NC} 停止\n"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

while true; do
    current_ip=$(dig +short "$DOMAIN" A | grep -E '^[0-9.]+$' | head -1)
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ -z "$current_ip" ]; then
        echo -e "[$timestamp] ${RED}✗ 查詢失敗${NC}"
    elif [ "$current_ip" != "$last_ip" ] && [ -n "$last_ip" ]; then
        change_count=$((change_count + 1))
        echo -e "[$timestamp] ${MAGENTA}🔄 IP 變更:${NC} ${RED}$last_ip${NC} → ${GREEN}$current_ip${NC} ${YELLOW}(第 $change_count 次變更)${NC}"
    else
        echo -e "[$timestamp] ${GREEN}✓${NC} IP: ${CYAN}$current_ip${NC}"
    fi
    
    last_ip="$current_ip"
    sleep "$INTERVAL"
done

