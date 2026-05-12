#!/bin/bash

# ============================================
# 域名檢測腳本 v3.1 - Token 版本
# 特點：
# - 支持 Globalping API Token（更高配額）
# - 一次性完成，自動重試失敗域名
# - 優化延遲配置，避免 API 頻率限制
# - 自動禁用代理
# - 完整的狀態分類和報告
# ============================================

# Globalping API Token
GLOBALPING_TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"

# 禁用代理（避免 403 錯誤）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY
unset socks_proxy SOCKS_PROXY socks5_proxy SOCKS5_PROXY

DOMAINS_FILE="$1"
TIMESTAMP=$(date +%m%d_%H%M)
LOG_FILE="$HOME/globalping_${TIMESTAMP}.log"
TEMP_FAILED=$(mktemp)
TEMP_DONE=$(mktemp)
TEMP_PARTIAL=$(mktemp)  # 新增：記錄 PARTIAL 域名

# 配置（增加延遲避免頻率限制）
DELAY=8              # 每個域名間隔 8 秒（增加）
API_ERROR_DELAY=30   # API 錯誤後延遲 30 秒（增加）
BATCH_SIZE=30        # 每批 30 個（減少）
BATCH_DELAY=60       # 批次間休息 60 秒（增加）
MAX_RETRY_ROUNDS=2   # 最多重試 2 輪

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

# 檢查域名函數（基於測試版）
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
        
        # 格式: 網絡名稱|ASN|城市|節點IP|目標IP|狀態碼
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
    
    # 避免重複處理
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
        echo "------------------------------------------------" | tee -a "$LOG_FILE"
        sleep $API_ERROR_DELAY
        return
    fi
    
    # 解析結果
    local clean_cnt=0
    local timeout_cnt=0
    local warning_cnt=0
    local blocked_cnt=0
    
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
        
        # 格式化節點信息
        local node_info="${isp:0:24}"
        if [ -n "$asn" ]; then
            node_info="$node_info (AS$asn)"
        fi
        if [ -n "$city" ]; then
            node_info="$node_info [$city]"
        fi
        
        # 顯示結果（包含節點 IP 和目標 IP）
        printf "  📍 %-40s\n" "$node_info"
        printf "  📍 %-40s\n" "$node_info" >> "$LOG_FILE"
        printf "     🔌 節點IP: %-15s | 🎯 目標IP: %-15s | ${color}%s${NC}\n" "${node_ip:-N/A}" "${ip:-無解析}" "$msg"
        printf "     🔌 節點IP: %-15s | 🎯 目標IP: %-15s | %s\n" "${node_ip:-N/A}" "${ip:-無解析}" "$msg" >> "$LOG_FILE"
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
        # 記錄 PARTIAL 域名，稍後重新檢測
        echo "$domain" >> "$TEMP_PARTIAL"
    fi
    
    mark_done "$domain"
    echo "  -> 整體狀態: $overall" | tee -a "$LOG_FILE"
    echo "------------------------------------------------" | tee -a "$LOG_FILE"
}

# 主程序
main() {
    # 檢查參數
    if [ -z "$DOMAINS_FILE" ] || [ ! -f "$DOMAINS_FILE" ]; then
        echo "用法: $0 <域名文件>"
        echo "範例: $0 ~/domains.txt"
        exit 1
    fi
    
    # 計算總數
    TOTAL=$(grep -v "^$\|^域名" "$DOMAINS_FILE" | grep "\." | wc -l | tr -d ' ')
    
    echo "========================================"
    echo "域名檢測腳本 v3.1 - Token 版本"
    echo "========================================"
    echo "域名文件: $DOMAINS_FILE"
    echo "總域名數: $TOTAL"
    echo "延遲設置: ${DELAY}秒/域名"
    echo "自動重試: 啟用（最多 $MAX_RETRY_ROUNDS 輪）"
    echo "使用 Token: ${GLOBALPING_TOKEN:0:10}..."
    echo "========================================"
    echo ""
    
    {
        echo "=== 域名檢測開始 ==="
        echo "時間: $(date)"
        echo "總域名數: $TOTAL"
        echo "------------------------------------------------"
    } | tee "$LOG_FILE"
    
    # 第一輪：檢測所有域名
    echo -e "${GREEN}=== 第一輪檢測 ===${NC}"
    
    local batch=0
    while IFS= read -r domain || [ -n "$domain" ]; do
        domain=$(echo "$domain" | tr -d '\r\n[:space:]')
        [ -z "$domain" ] && continue
        [ "$domain" = "域名" ] && continue
        [[ "$domain" != *.* ]] && continue
        
        batch=$((batch + 1))
        process "$domain"
        
        # 批次控制
        if [ $batch -ge $BATCH_SIZE ] && [ $PROCESSED -lt $TOTAL ]; then
            echo -e "\n⏸️  已完成 $batch 個域名，休息 ${BATCH_DELAY} 秒避免頻率限制...\n" | tee -a "$LOG_FILE"
            sleep $BATCH_DELAY
            batch=0
        else
            sleep $DELAY
        fi
    done < "$DOMAINS_FILE"
    
    # 自動重試失敗的域名
    local round=1
    while [ $round -le $MAX_RETRY_ROUNDS ]; do
        # 檢查是否有失敗域名
        if [ ! -s "$TEMP_FAILED" ]; then
            break
        fi
        
        # 讀取失敗域名
        local failed_count=$(wc -l < "$TEMP_FAILED" | tr -d ' ')
        if [ "$failed_count" -eq 0 ]; then
            break
        fi
        
        echo -e "\n${YELLOW}========================================"
        echo "自動重試失敗域名 - 第 $round 輪"
        echo "========================================${NC}"
        echo "失敗域名數: $failed_count"
        echo "休息 60 秒後開始重試..."
        echo ""
        
        sleep 60
        
        # 保存失敗列表
        local failed_list=$(cat "$TEMP_FAILED")
        
        # 清空失敗列表
        > "$TEMP_FAILED"
        
        # 重置計數
        PROCESSED=0
        TOTAL=$failed_count
        batch=0
        
        # 重試每個失敗域名
        while IFS= read -r domain; do
            [ -z "$domain" ] && continue
            
            batch=$((batch + 1))
            process "$domain"
            
            if [ $batch -ge $BATCH_SIZE ] && [ $PROCESSED -lt $TOTAL ]; then
                echo -e "\n⏸️  休息 ${BATCH_DELAY} 秒...\n" | tee -a "$LOG_FILE"
                sleep $BATCH_DELAY
                batch=0
            else
                sleep $DELAY
            fi
        done <<< "$failed_list"
        
        round=$((round + 1))
    done
    
    # 二次檢測 PARTIAL 域名
    if [ -s "$TEMP_PARTIAL" ]; then
        local partial_count=$(wc -l < "$TEMP_PARTIAL" | tr -d ' ')
        
        echo -e "\n${BLUE}========================================"
        echo "二次檢測 PARTIAL 域名"
        echo "========================================${NC}"
        echo "PARTIAL 域名數: $partial_count"
        echo "這些域名在部分 ISP 無法訪問，將重新檢測"
        echo "休息 60 秒後開始..."
        echo ""
        
        sleep 60
        
        # 保存 PARTIAL 列表
        local partial_list=$(cat "$TEMP_PARTIAL")
        
        # 清空 PARTIAL 列表
        > "$TEMP_PARTIAL"
        
        # 重置計數
        PROCESSED=0
        TOTAL=$partial_count
        batch=0
        
        echo -e "${BLUE}=== 開始二次檢測 PARTIAL 域名 ===${NC}"
        
        # 重新檢測每個 PARTIAL 域名
        while IFS= read -r domain; do
            [ -z "$domain" ] && continue
            
            # 從已處理列表中移除，允許重新檢測
            grep -v "^${domain}$" "$TEMP_DONE" > "${TEMP_DONE}.tmp" 2>/dev/null
            mv "${TEMP_DONE}.tmp" "$TEMP_DONE" 2>/dev/null
            
            batch=$((batch + 1))
            
            echo -e "\n${BLUE}🔄 重新檢測 PARTIAL 域名 [$PROCESSED/$TOTAL]: $domain${NC}" | tee -a "$LOG_FILE"
            process "$domain"
            
            if [ $batch -ge $BATCH_SIZE ] && [ $PROCESSED -lt $TOTAL ]; then
                echo -e "\n⏸️  休息 ${BATCH_DELAY} 秒...\n" | tee -a "$LOG_FILE"
                sleep $BATCH_DELAY
                batch=0
            else
                sleep $DELAY
            fi
        done <<< "$partial_list"
        
        echo -e "\n${GREEN}✅ PARTIAL 域名二次檢測完成${NC}" | tee -a "$LOG_FILE"
    fi
    
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
    
    # 同時寫入日誌文件
    {
        echo ""
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
    } >> "$LOG_FILE"
    
    if [ $API_ERROR -gt 0 ]; then
        echo ""
        echo "⚠️  仍有 $API_ERROR 個域名檢測失敗"
        echo "建議：增加延遲時間或稍後重試"
    fi
}

main
