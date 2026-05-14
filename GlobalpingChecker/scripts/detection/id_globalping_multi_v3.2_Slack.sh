#!/bin/bash

# ============================================
# 域名檢測腳本 v3.2 - 支持 Slack 通知
# 特點：
# - 支持 Globalping API Token（更高配額）
# - 自動重試失敗域名
# - Slack 通知集成
# - 完整的狀態分類和報告
# ============================================

# Globalping API Token
GLOBALPING_TOKEN="${GLOBALPING_TOKEN:-gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5}"

# 禁用代理（避免 403 錯誤）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY

DOMAINS_FILE="$1"
TIMESTAMP=$(date +%m%d_%H%M)
LOG_FILE="$HOME/globalping_${TIMESTAMP}.log"
TEMP_FAILED=$(mktemp)
TEMP_DONE=$(mktemp)
TEMP_PARTIAL=$(mktemp)

# 載入 Slack 通知函數（如果存在）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/slack-notify.sh" ]; then
    source "$SCRIPT_DIR/slack-notify.sh"
    load_slack_config "$SCRIPT_DIR/slack-config.env" 2>/dev/null || true
    SLACK_AVAILABLE=true
else
    SLACK_AVAILABLE=false
fi

# 配置
DELAY=8
API_ERROR_DELAY=30
BATCH_SIZE=30
BATCH_DELAY=60
MAX_RETRY_ROUNDS=2

# 統計
TOTAL=0
PROCESSED=0
CLEAN=0
TIMEOUT=0
WARNING=0
PARTIAL=0
BLOCKED=0
API_ERROR=0

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 檢查域名是否已處理
is_done() {
    grep -Fxq "$1" "$TEMP_DONE" 2>/dev/null
}

# 標記域名為已處理
mark_done() {
    echo "$1" >> "$TEMP_DONE"
}

# 檢查域名函數
check_domain() {
    local domain="$1"
    local retry=0
    
    while [ $retry -lt 3 ]; do
        JSON='{"type":"http","target":"'"$domain"'","limit":3,"locations":[{"country":"ID"}]}'
        POST_RES=$(curl -s -w "\n%{http_code}" -X POST https://api.globalping.io/v1/measurements \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $GLOBALPING_TOKEN" \
            -d "$JSON")
        
        HTTP_CODE=$(echo "$POST_RES" | tail -n1)
        RESPONSE_BODY=$(echo "$POST_RES" | sed '$d')
        
        MEASURE_ID=$(echo "$RESPONSE_BODY" | grep -Eo '"id"\s*:\s*"[^"]+"' | head -1 | cut -d'"' -f4)
        
        if [ -n "$MEASURE_ID" ]; then
            sleep 8
            GET_RES=$(curl -s -H "Authorization: Bearer $GLOBALPING_TOKEN" \
                "https://api.globalping.io/v1/measurements/$MEASURE_ID")
            
            PARSED_DATA=$(echo "$GET_RES" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    for r in data.get("results", []):
        probe = r.get("probe", {})
        net = probe.get("network", "未知 ISP")
        asn = probe.get("asn", "")
        city = probe.get("city", "")
        node_ip = probe.get("resolvers", [""])[0] if probe.get("resolvers") else ""
        
        ip = r.get("result", {}).get("resolvedAddress", "")
        code = r.get("result", {}).get("statusCode", 0)
        
        print(f"{net}|{asn}|{city}|{node_ip}|{ip}|{code}")
except Exception as e:
    print(f"ERROR|PARSE_ERROR|{str(e)}", file=sys.stderr)
    pass
')
            
            if [ -n "$PARSED_DATA" ]; then
                echo "$PARSED_DATA"
                return 0
            fi
        fi
        
        retry=$((retry + 1))
        [ $retry -lt 3 ] && sleep $((3 * 2 ** retry))
    done
    
    return 1
}

# 處理單個域名
process() {
    local domain="$1"
    
    if is_done "$domain"; then
        return
    fi
    
    PROCESSED=$((PROCESSED + 1))
    echo -ne "\r${BLUE}進度: [$PROCESSED/$TOTAL]${NC} "
    echo -e "\n🔍 檢測域名 [$PROCESSED/$TOTAL]: $domain ..." | tee -a "$LOG_FILE"
    
    RESULT=$(check_domain "$domain")
    
    if [ $? -ne 0 ]; then
        echo "  -> ${RED}[API_ERROR] ❌ API 請求失敗${NC}" | tee -a "$LOG_FILE"
        echo "$domain" >> "$TEMP_FAILED"
        API_ERROR=$((API_ERROR + 1))
        
        # Slack 通知
        if [ "$SLACK_AVAILABLE" = true ]; then
            send_slack_domain_result "$domain" "API_ERROR" "API 請求失敗"
        fi
        
        echo "------------------------------------------------" | tee -a "$LOG_FILE"
        sleep $API_ERROR_DELAY
        return
    fi
    
    # 解析結果
    local clean_cnt=0
    local timeout_cnt=0
    local warning_cnt=0
    local blocked_cnt=0
    local details=""
    
    while IFS='|' read -r isp asn city node_ip ip code; do
        if [ "$ip" = "36.86.63.185" ] || [[ "$ip" == "10."* ]]; then
            status="BLOCKED"
            color=$RED
            msg="[BLOCKED] 🚨 DNS 污染"
            blocked_cnt=$((blocked_cnt + 1))
        elif [ -z "$ip" ] || [ "$code" = "0" ]; then
            status="TIMEOUT"
            color=$YELLOW
            msg="[TIMEOUT] ⚠️  阻斷/無回應"
            timeout_cnt=$((timeout_cnt + 1))
        elif [[ "$code" == 2* ]] || [[ "$code" == 3* ]] || [ "$code" = "403" ]; then
            status="CLEAN"
            color=$GREEN
            msg="[CLEAN] ✅ 正常連通 (HTTP $code)"
            clean_cnt=$((clean_cnt + 1))
        else
            status="WARNING"
            color=$YELLOW
            msg="[WARNING] ⚠️  異常狀態 (HTTP $code)"
            warning_cnt=$((warning_cnt + 1))
        fi
        
        local node_info="${isp:0:24}"
        [ -n "$asn" ] && node_info="$node_info (AS$asn)"
        [ -n "$city" ] && node_info="$node_info [$city]"
        
        printf "  📍 %-40s\n" "$node_info"
        printf "     🎯 目標IP: %-15s | ${color}%s${NC}\n" "${ip:-無解析}" "$msg" | tee -a "$LOG_FILE"
        
        details="${details}${node_info}: ${ip:-無解析} - ${status}\n"
    done <<< "$RESULT"
    
    # 判斷整體狀態
    if [ $clean_cnt -eq 3 ]; then
        overall="CLEAN"
        CLEAN=$((CLEAN + 1))
    elif [ $timeout_cnt -eq 3 ]; then
        overall="TIMEOUT"
        TIMEOUT=$((TIMEOUT + 1))
    elif [ $warning_cnt -eq 3 ]; then
        overall="WARNING"
        WARNING=$((WARNING + 1))
    elif [ $blocked_cnt -eq 3 ]; then
        overall="BLOCKED"
        BLOCKED=$((BLOCKED + 1))
    else
        overall="PARTIAL"
        PARTIAL=$((PARTIAL + 1))
        echo "$domain" >> "$TEMP_PARTIAL"
    fi
    
    mark_done "$domain"
    echo "  -> 整體狀態: $overall" | tee -a "$LOG_FILE"
    echo "------------------------------------------------" | tee -a "$LOG_FILE"
    
    # Slack 通知（根據配置）
    if [ "$SLACK_AVAILABLE" = true ]; then
        send_slack_domain_result "$domain" "$overall" "$details"
    fi
}

# 主程序
main() {
    if [ -z "$DOMAINS_FILE" ] || [ ! -f "$DOMAINS_FILE" ]; then
        echo "用法: $0 <域名文件>"
        exit 1
    fi
    
    TOTAL=$(grep -v "^$\|^域名" "$DOMAINS_FILE" | grep "\." | wc -l | tr -d ' ')
    
    echo "========================================"
    echo "域名檢測腳本 v3.2 - Slack 通知版"
    echo "========================================"
    echo "域名文件: $DOMAINS_FILE"
    echo "總域名數: $TOTAL"
    echo "Slack 通知: $([ "$SLACK_AVAILABLE" = true ] && echo "啟用" || echo "未配置")"
    echo "========================================"
    echo ""
    
    {
        echo "=== 域名檢測開始 ==="
        echo "時間: $(date)"
        echo "總域名數: $TOTAL"
        echo "------------------------------------------------"
    } | tee "$LOG_FILE"
    
    # Slack 開始通知
    if [ "$SLACK_AVAILABLE" = true ]; then
        send_slack_start "$TOTAL"
    fi
    
    # 第一輪檢測
    echo -e "${GREEN}=== 第一輪檢測 ===${NC}"
    
    local batch=0
    while IFS= read -r domain || [ -n "$domain" ]; do
        domain=$(echo "$domain" | tr -d '\r\n[:space:]')
        [ -z "$domain" ] && continue
        [ "$domain" = "域名" ] && continue
        [[ "$domain" != *.* ]] && continue
        
        batch=$((batch + 1))
        process "$domain"
        
        if [ $batch -ge $BATCH_SIZE ] && [ $PROCESSED -lt $TOTAL ]; then
            echo -e "\n⏸️  已完成 $batch 個域名，休息 ${BATCH_DELAY} 秒...\n" | tee -a "$LOG_FILE"
            sleep $BATCH_DELAY
            batch=0
        else
            sleep $DELAY
        fi
    done < "$DOMAINS_FILE"
    
    # 清理
    rm -f "$TEMP_FAILED" "$TEMP_DONE" "$TEMP_PARTIAL"
    
    # 生成摘要
    echo -e "\n"
    echo "========================================"
    echo "檢測完成"
    echo "========================================"
    echo "✅ 正常連通 (CLEAN):   $CLEAN"
    echo "🚨 DNS 污染 (BLOCKED): $BLOCKED"
    echo "⚠️  完全超時 (TIMEOUT): $TIMEOUT"
    echo "⚠️  服務異常 (WARNING): $WARNING"
    echo "🔄 部分異常 (PARTIAL): $PARTIAL"
    echo "❌ 檢測失敗 (API_ERROR): $API_ERROR"
    echo "========================================"
    echo "詳細日誌: $LOG_FILE"
    echo "========================================"
    
    # Slack 摘要通知
    if [ "$SLACK_AVAILABLE" = true ]; then
        send_slack_summary "$TOTAL" "$CLEAN" "$BLOCKED" "$TIMEOUT" "$WARNING" "$PARTIAL" "$API_ERROR"
        send_slack_complete
    fi
}

main
