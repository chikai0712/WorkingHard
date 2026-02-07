#!/bin/bash
# ==============================================================================
# 遞回 DNS 解析行為監控工具 (Split-Brain / 多活負載平衡測試)
# 流程：先查 8.8.8.8 → 隔 GAP_MINUTES 分鐘 → 再查 1.1.1.1，各跑 DURATION_MINUTES
# 可覆寫：TARGET_DNS_1 TARGET_DNS_2 DURATION_MINUTES GAP_MINUTES INTERVAL
# ==============================================================================

# 配置區域
DOMAIN="${1:-www.clouddeployment168.site}"
TARGET_DNS_1="${TARGET_DNS_1:-8.8.8.8}"
TARGET_DNS_2="${TARGET_DNS_2:-1.1.1.1}"
DURATION_MINUTES="${DURATION_MINUTES:-5}"
GAP_MINUTES="${GAP_MINUTES:-1}"   # 第一段結束後隔幾分鐘再查第二段
INTERVAL="${INTERVAL:-1}"        # 每次查詢間隔秒數 (建議 >= 1)

# 預期測試 IP（AWS / Google 權威各設不同 A 記錄時）
IP_AWS="${IP_AWS:-3.3.3.3}"
IP_GOOGLE="${IP_GOOGLE:-2.2.2.2}"

# 日誌：時間戳檔名（勿用會將 " 改為智慧引號的編輯器儲存，以免語法錯誤）
LOG=/tmp/recursive-dns-monitor_$(date '+%Y%m%d_%H%M%S').log

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 單段計數器（每段開始前重置）
count_aws=0
count_google=0
count_other=0
total_queries=0
IP_OTHER=""
EMPTY_LABEL="(空)"

# 輸出單段總結（傳入遞回 DNS 名稱與編號）
show_phase_summary() {
    local dns=$1
    local phase_name=$2
    echo ""
    echo -e "${CYAN}---------- $phase_name (Target: $dns) ----------${NC}"
    echo "查詢次數: $total_queries"
    if [ "$total_queries" -gt 0 ]; then
        pct_aws=$(echo "scale=2; $count_aws * 100 / $total_queries" 2>/dev/null | bc) || pct_aws="0"
        pct_google=$(echo "scale=2; $count_google * 100 / $total_queries" 2>/dev/null | bc) || pct_google="0"
        pct_other=$(echo "scale=2; $count_other * 100 / $total_queries" 2>/dev/null | bc) || pct_other="0"
        echo -e "${GREEN}AWS ($IP_AWS):     $count_aws 次  (${pct_aws}%)${NC}"
        echo -e "${BLUE}Google ($IP_GOOGLE): $count_google 次  (${pct_google}%)${NC}"
        [ "$count_other" -gt 0 ] && echo -e "${RED}其他 (${IP_OTHER:-空/未知}): $count_other 次  (${pct_other}%)${NC}"
    fi
}

# 中斷時只印出目前階段結果並結束（用變數避免 trap 內引號問題）
PHASE_LABEL_CURRENT='目前階段'
trap 'echo ""; echo -e "${YELLOW}已中斷${NC}"; show_phase_summary "$CURRENT_DNS" "$PHASE_LABEL_CURRENT"; exit 0' INT TERM

# 執行單段查詢（傳入：遞回 DNS、階段名稱）
run_phase() {
    local dns=$1
    local phase_name=$2
    CURRENT_DNS=$dns
    count_aws=0
    count_google=0
    count_other=0
    total_queries=0
    IP_OTHER=""

    local start_time end_time
    start_time=$(date +%s)
    end_time=$((start_time + DURATION_MINUTES * 60))

    echo ""
    echo -e "${YELLOW}>>>> 階段: $phase_name (Target: $dns)，$DURATION_MINUTES 分鐘，間隔 ${INTERVAL}s <<<<${NC}"
    echo -e "時間\t\t遞回DNS\t\t解析結果\t來源判定"
    echo "------------------------------------------------------------------"

    while [ $(date +%s) -lt $end_time ]; do
        current_time_str=$(date "+%H:%M:%S")
        result=$(dig @"$dns" "$DOMAIN" +short 2>/dev/null | head -n 1)
        total_queries=$((total_queries + 1))
        if [ "$result" = "$IP_AWS" ]; then
            echo -e "$current_time_str\t$dns\t$result\t\t${GREEN}[AWS]${NC}"
            count_aws=$((count_aws + 1))
        elif [ "$result" = "$IP_GOOGLE" ]; then
            echo -e "$current_time_str\t$dns\t$result\t\t${BLUE}[Google]${NC}"
            count_google=$((count_google + 1))
        else
            echo -e "$current_time_str\t$dns\t${result:-$EMPTY_LABEL}\t\t${RED}[其他]${NC}"
            count_other=$((count_other + 1))
            IP_OTHER="$result"
        fi
        sleep "$INTERVAL"
    done

    show_phase_summary "$dns" "$phase_name"
}

# 主流程（subshell 管線到 tee，即時輸出到終端與日誌，避免 exec 引號解析問題）
(
echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   遞回 DNS 解析監控（兩段：8.8.8.8 間隔 ${GAP_MINUTES} 分鐘 1.1.1.1）${NC}"
echo -e "${CYAN}======================================================${NC}"
echo "日誌寫入: $LOG"
echo "監控域名: $DOMAIN"
echo "每段時長: $DURATION_MINUTES 分鐘，間隔: ${INTERVAL}s"
echo "段間隔: ${GAP_MINUTES} 分鐘"
echo "AWS 預期 IP:   $IP_AWS"
echo "Google 預期 IP: $IP_GOOGLE"

PHASE1_NAME="第一段 8.8.8.8"
PHASE2_NAME="第二段 1.1.1.1"
run_phase "$TARGET_DNS_1" "$PHASE1_NAME"

WAIT_MSG="等待 ${GAP_MINUTES} 分鐘後開始第二段..."
echo -e "\n${CYAN}${WAIT_MSG}${NC}"
sleep $((GAP_MINUTES * 60))

run_phase "$TARGET_DNS_2" "$PHASE2_NAME"

echo -e "\n${CYAN}======================================================${NC}"
echo -e "${CYAN}   兩段皆完成${NC}"
echo -e "${CYAN}======================================================${NC}"
) 2>&1 | tee $LOG
