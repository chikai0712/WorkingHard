#!/bin/bash

# ============================================
# 域名檢測腳本 v2.0 - 改進版
# 功能：
# - 完整的狀態分類（CLEAN/BLOCKED/TIMEOUT/WARNING/PARTIAL/API_ERROR）
# - 頻率控制和重試機制
# - 進度顯示
# - 摘要報告
# - CSV 導出
# - 失敗域名自動記錄
# ============================================

# ============================================
# 配置參數
# ============================================
DELAY_BETWEEN_DOMAINS=4         # 每個域名之間的延遲（秒）
DELAY_AFTER_API_ERROR=15        # API 錯誤後的延遲（秒）
BATCH_SIZE=50                   # 批次大小
BATCH_DELAY=30                  # 批次間延遲（秒）
MAX_RETRIES=3                   # 最大重試次數
RETRY_BACKOFF_BASE=3            # 重試退避基數（秒）
API_WAIT_TIME=8                 # 等待 API 結果的時間（秒）

# 污染 IP 列表
BLOCKED_IPS=("36.86.63.185" "10." "127.0.0.1" "0.0.0.0")

# ============================================
# 文件路徑
# ============================================
DOMAINS_FILE="$1"
TIMESTAMP=$(date +%m%d_%H%M)
LOG_FILE="$HOME/globalping_multi_${TIMESTAMP}.log"
CSV_FILE="$HOME/globalping_multi_${TIMESTAMP}.csv"
FAILED_FILE="$HOME/globalping_failed_${TIMESTAMP}.txt"
SUMMARY_FILE="$HOME/globalping_summary_${TIMESTAMP}.txt"

# ============================================
# 統計變量
# ============================================
TOTAL_DOMAINS=0
PROCESSED_DOMAINS=0
CLEAN_COUNT=0
BLOCKED_COUNT=0
TIMEOUT_COUNT=0
WARNING_COUNT=0
PARTIAL_COUNT=0
API_ERROR_COUNT=0

# 用於存儲需要關注的域名
declare -a BLOCKED_DOMAINS
declare -a TIMEOUT_DOMAINS
declare -a PARTIAL_DOMAINS
declare -a WARNING_DOMAINS
declare -a API_ERROR_DOMAINS

# ============================================
# 顏色定義
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# 函數：檢查 IP 是否為污染 IP
# ============================================
is_blocked_ip() {
    local ip="$1"
    for blocked in "${BLOCKED_IPS[@]}"; do
        if [[ "$ip" == "$blocked"* ]]; then
            return 0  # 是污染 IP
        fi
    done
    return 1  # 不是污染 IP
}

# ============================================
# 函數：分類單個節點的狀態
# ============================================
classify_node_status() {
    local ip="$1"
    local code="$2"
    
    # 檢查是否為污染 IP
    if is_blocked_ip "$ip"; then
        echo "BLOCKED"
        return
    fi
    
    # 檢查是否為超時/無解析
    if [[ -z "$ip" || -z "$code" || "$code" == "0" || "$code" == "null" || "$code" == "None" ]]; then
        echo "TIMEOUT"
        return
    fi
    
    # 檢查 HTTP 狀態碼
    if [[ "$code" == 2* || "$code" == 3* || "$code" == "403" ]]; then
        echo "CLEAN"
        return
    fi
    
    # 其他狀態碼視為異常
    echo "WARNING"
}

# ============================================
# 函數：綜合判斷域名整體狀態
# ============================================
classify_domain_status() {
    local status1="$1"
    local status2="$2"
    local status3="$3"
    
    # 統計各狀態數量
    local blocked_count=0
    local timeout_count=0
    local clean_count=0
    local warning_count=0
    
    for status in "$status1" "$status2" "$status3"; do
        case "$status" in
            BLOCKED) ((blocked_count++)) ;;
            TIMEOUT) ((timeout_count++)) ;;
            CLEAN) ((clean_count++)) ;;
            WARNING) ((warning_count++)) ;;
        esac
    done
    
    # 判斷整體狀態
    if [[ $blocked_count -eq 3 ]]; then
        echo "BLOCKED"
    elif [[ $timeout_count -eq 3 ]]; then
        echo "TIMEOUT"
    elif [[ $clean_count -eq 3 ]]; then
        echo "CLEAN"
    elif [[ $warning_count -eq 3 ]]; then
        echo "WARNING"
    else
        echo "PARTIAL"
    fi
}

# ============================================
# 函數：格式化狀態輸出
# ============================================
format_status_output() {
    local status="$1"
    local code="$2"
    
    case "$status" in
        BLOCKED)
            echo "[BLOCKED] 🚨 DNS 污染"
            ;;
        TIMEOUT)
            echo "[TIMEOUT] ⚠️  阻斷/無回應"
            ;;
        CLEAN)
            echo "[CLEAN] ✅ 正常連通 (HTTP $code)"
            ;;
        WARNING)
            echo "[WARNING] ⚠️  異常狀態 (HTTP $code)"
            ;;
        *)
            echo "[UNKNOWN] ❓ 未知狀態"
            ;;
    esac
}

# ============================================
# 函數：檢測單個域名（帶重試）
# ============================================
check_domain_with_retry() {
    local domain="$1"
    local retry_count=0
    local success=false
    
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        # 發起 API 請求
        JSON_PAYLOAD='{"type":"http","target":"'"$domain"'","limit":3,"locations":[{"country":"ID"}]}'
        POST_RES=$(curl -s -w "\n%{http_code}" -X POST https://api.globalping.io/v1/measurements \
            -H "Content-Type: application/json" -d "$JSON_PAYLOAD")
        
        # 分離響應體和狀態碼
        HTTP_CODE=$(echo "$POST_RES" | tail -n1)
        RESPONSE_BODY=$(echo "$POST_RES" | sed '$d')
        
        MEASURE_ID=$(echo "$RESPONSE_BODY" | grep -Eo '"id"\s*:\s*"[^"]+"' | head -1 | cut -d'"' -f4)
        
        if [[ -n "$MEASURE_ID" ]]; then
            success=true
            break
        fi
        
        # API 請求失敗，準備重試
        ((retry_count++))
        
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            local backoff_time=$((RETRY_BACKOFF_BASE * (2 ** (retry_count - 1))))
            echo "  ⚠️  API 請求失敗 (嘗試 $retry_count/$MAX_RETRIES)，等待 ${backoff_time} 秒後重試..." | tee -a "$LOG_FILE"
            sleep $backoff_time
        fi
    done
    
    if [[ "$success" == false ]]; then
        echo "API_ERROR"
        return 1
    fi
    
    # 等待結果
    sleep $API_WAIT_TIME
    
    # 獲取結果
    GET_RES=$(curl -s "https://api.globalping.io/v1/measurements/$MEASURE_ID")
    
    # 解析結果
    PARSED_DATA=$(echo "$GET_RES" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    for r in data.get("results", []):
        net = r.get("probe", {}).get("network", "未知 ISP")
        ip = r.get("result", {}).get("resolvedAddress", "")
        code = r.get("result", {}).get("statusCode", 0)
        print(f"{net}|{ip}|{code}")
except Exception as e:
    print(f"ERROR|PARSE_ERROR|{str(e)}", file=sys.stderr)
    pass
')
    
    if [[ -z "$PARSED_DATA" ]]; then
        echo "NO_RESPONSE"
        return 1
    fi
    
    echo "$PARSED_DATA"
    return 0
}

# ============================================
# 函數：初始化 CSV 文件
# ============================================
init_csv() {
    echo "域名,整體狀態,節點1_ISP,節點1_IP,節點1_狀態碼,節點1_狀態,節點2_ISP,節點2_IP,節點2_狀態碼,節點2_狀態,節點3_ISP,節點3_IP,節點3_狀態碼,節點3_狀態,備註" > "$CSV_FILE"
}

# ============================================
# 函數：寫入 CSV 記錄
# ============================================
write_csv_record() {
    local domain="$1"
    local overall_status="$2"
    shift 2
    local nodes=("$@")
    
    echo -n "$domain,$overall_status" >> "$CSV_FILE"
    
    for node in "${nodes[@]}"; do
        echo -n ",$node" >> "$CSV_FILE"
    done
    
    echo "" >> "$CSV_FILE"
}

# ============================================
# 函數：顯示進度
# ============================================
show_progress() {
    local current="$1"
    local total="$2"
    local percentage=$((current * 100 / total))
    
    echo -ne "\r${BLUE}進度: [$current/$total] ($percentage%)${NC}"
}

# ============================================
# 函數：生成摘要報告
# ============================================
generate_summary() {
    {
        echo "========================================"
        echo "域名檢測摘要報告"
        echo "========================================"
        echo "檢測時間: $(date)"
        echo "總域名數: $TOTAL_DOMAINS"
        echo "已處理: $PROCESSED_DOMAINS"
        echo ""
        echo "========================================"
        echo "狀態統計"
        echo "========================================"
        echo "✅ 正常連通 (CLEAN):     $CLEAN_COUNT ($(( CLEAN_COUNT * 100 / PROCESSED_DOMAINS ))%)"
        echo "🚨 DNS 污染 (BLOCKED):   $BLOCKED_COUNT ($(( BLOCKED_COUNT * 100 / PROCESSED_DOMAINS ))%)"
        echo "⚠️  完全超時 (TIMEOUT):   $TIMEOUT_COUNT ($(( TIMEOUT_COUNT * 100 / PROCESSED_DOMAINS ))%)"
        echo "⚠️  服務異常 (WARNING):   $WARNING_COUNT ($(( WARNING_COUNT * 100 / PROCESSED_DOMAINS ))%)"
        echo "🔄 部分異常 (PARTIAL):   $PARTIAL_COUNT ($(( PARTIAL_COUNT * 100 / PROCESSED_DOMAINS ))%)"
        echo "❌ 檢測失敗 (API_ERROR): $API_ERROR_COUNT ($(( API_ERROR_COUNT * 100 / PROCESSED_DOMAINS ))%)"
        echo ""
        
        if [[ $BLOCKED_COUNT -gt 0 ]]; then
            echo "========================================"
            echo "🚨 DNS 污染域名 ($BLOCKED_COUNT 個)"
            echo "========================================"
            for domain in "${BLOCKED_DOMAINS[@]}"; do
                echo "  - $domain"
            done
            echo ""
        fi
        
        if [[ $TIMEOUT_COUNT -gt 0 ]]; then
            echo "========================================"
            echo "⚠️  完全超時域名 ($TIMEOUT_COUNT 個)"
            echo "========================================"
            for domain in "${TIMEOUT_DOMAINS[@]}"; do
                echo "  - $domain"
            done
            echo ""
        fi
        
        if [[ $PARTIAL_COUNT -gt 0 ]]; then
            echo "========================================"
            echo "🔄 部分異常域名 ($PARTIAL_COUNT 個)"
            echo "========================================"
            for domain in "${PARTIAL_DOMAINS[@]}"; do
                echo "  - $domain"
            done
            echo ""
        fi
        
        if [[ $WARNING_COUNT -gt 0 ]]; then
            echo "========================================"
            echo "⚠️  服務異常域名 ($WARNING_COUNT 個)"
            echo "========================================"
            for domain in "${WARNING_DOMAINS[@]}"; do
                echo "  - $domain"
            done
            echo ""
        fi
        
        if [[ $API_ERROR_COUNT -gt 0 ]]; then
            echo "========================================"
            echo "❌ 檢測失敗域名 ($API_ERROR_COUNT 個)"
            echo "========================================"
            echo "這些域名因 API 限制未能完成檢測"
            echo "已保存到: $FAILED_FILE"
            for domain in "${API_ERROR_DOMAINS[@]}"; do
                echo "  - $domain"
            done
            echo ""
        fi
        
        echo "========================================"
        echo "文件輸出"
        echo "========================================"
        echo "詳細日誌: $LOG_FILE"
        echo "CSV 報告: $CSV_FILE"
        echo "失敗清單: $FAILED_FILE"
        echo "摘要報告: $SUMMARY_FILE"
        echo "========================================"
    } | tee "$SUMMARY_FILE"
}

# ============================================
# 主程序
# ============================================
main() {
    # 檢查參數
    if [[ -z "$DOMAINS_FILE" ]]; then
        echo "用法: $0 <域名文件>"
        echo "範例: $0 ~/domains.txt"
        exit 1
    fi
    
    if [[ ! -f "$DOMAINS_FILE" ]]; then
        echo "錯誤: 域名文件不存在: $DOMAINS_FILE"
        exit 1
    fi
    
    # 計算總域名數
    TOTAL_DOMAINS=$(grep -v "^$\|^域名" "$DOMAINS_FILE" | grep "\." | wc -l | tr -d ' ')
    
    # 初始化
    init_csv
    
    echo "========================================"
    echo "域名檢測腳本 v2.0"
    echo "========================================"
    echo "域名文件: $DOMAINS_FILE"
    echo "總域名數: $TOTAL_DOMAINS"
    echo "批次大小: $BATCH_SIZE"
    echo "延遲設置: ${DELAY_BETWEEN_DOMAINS}秒/域名"
    echo "========================================"
    echo ""
    
    {
        echo "=== 啟動印尼多節點交叉比對檢測 (Globalping v2.0) ==="
        echo "測試時間: $(date)"
        echo "總域名數: $TOTAL_DOMAINS"
        echo "------------------------------------------------"
    } | tee "$LOG_FILE"
    
    local batch_count=0
    
    # 逐行讀取域名
    while IFS= read -r domain || [[ -n "$domain" ]]; do
        domain=$(echo "$domain" | tr -d '\r\n[:space:]')
        [[ -z "$domain" || "$domain" == "域名" || "$domain" != *.* ]] && continue
        
        ((PROCESSED_DOMAINS++))
        ((batch_count++))
        
        # 顯示進度
        show_progress "$PROCESSED_DOMAINS" "$TOTAL_DOMAINS"
        
        echo -e "\n🔍 檢測域名 [$PROCESSED_DOMAINS/$TOTAL_DOMAINS]: $domain ..." | tee -a "$LOG_FILE"
        
        # 檢測域名（帶重試）
        RESULT=$(check_domain_with_retry "$domain")
        CHECK_STATUS=$?
        
        if [[ $CHECK_STATUS -ne 0 ]]; then
            # API 錯誤
            if [[ "$RESULT" == "API_ERROR" ]]; then
                echo "  -> ${RED}[API_ERROR] ❌ API 請求失敗，已達最大重試次數${NC}" | tee -a "$LOG_FILE"
                ((API_ERROR_COUNT++))
                API_ERROR_DOMAINS+=("$domain")
                echo "$domain" >> "$FAILED_FILE"
                write_csv_record "$domain" "API_ERROR" "" "" "" "" "" "" "" "" "" "" "" "" "API請求失敗"
                
                # API 錯誤後延遲更長時間
                sleep $DELAY_AFTER_API_ERROR
            else
                echo "  -> ${YELLOW}[NO_RESPONSE] ⚠️  探針無回應${NC}" | tee -a "$LOG_FILE"
                ((API_ERROR_COUNT++))
                API_ERROR_DOMAINS+=("$domain")
                echo "$domain" >> "$FAILED_FILE"
                write_csv_record "$domain" "NO_RESPONSE" "" "" "" "" "" "" "" "" "" "" "" "" "探針無回應"
            fi
            
            echo "------------------------------------------------" | tee -a "$LOG_FILE"
            continue
        fi
        
        # 解析結果
        declare -a node_data
        declare -a node_statuses
        local line_count=0
        
        while IFS='|' read -r NET IP CODE; do
            ((line_count++))
            
            # 分類節點狀態
            NODE_STATUS=$(classify_node_status "$IP" "$CODE")
            node_statuses+=("$NODE_STATUS")
            
            # 格式化輸出
            STATUS_TEXT=$(format_status_output "$NODE_STATUS" "$CODE")
            
            # 根據狀態設置顏色
            case "$NODE_STATUS" in
                BLOCKED) COLOR=$RED ;;
                TIMEOUT) COLOR=$YELLOW ;;
                CLEAN) COLOR=$GREEN ;;
                WARNING) COLOR=$YELLOW ;;
                *) COLOR=$NC ;;
            esac
            
            printf "  📍 %-26s | IP: %-15s | ${COLOR}%s${NC}\n" "${NET:0:24}" "${IP:-無解析}" "$STATUS_TEXT" | tee -a "$LOG_FILE"
            
            # 保存節點數據用於 CSV
            node_data+=("${NET:0:24}" "${IP:-無解析}" "${CODE:-0}" "$NODE_STATUS")
        done <<< "$RESULT"
        
        # 綜合判斷域名狀態
        if [[ ${#node_statuses[@]} -ge 3 ]]; then
            OVERALL_STATUS=$(classify_domain_status "${node_statuses[0]}" "${node_statuses[1]}" "${node_statuses[2]}")
        else
            OVERALL_STATUS="PARTIAL"
        fi
        
        # 更新統計
        case "$OVERALL_STATUS" in
            CLEAN)
                ((CLEAN_COUNT++))
                ;;
            BLOCKED)
                ((BLOCKED_COUNT++))
                BLOCKED_DOMAINS+=("$domain")
                ;;
            TIMEOUT)
                ((TIMEOUT_COUNT++))
                TIMEOUT_DOMAINS+=("$domain")
                ;;
            WARNING)
                ((WARNING_COUNT++))
                WARNING_DOMAINS+=("$domain")
                ;;
            PARTIAL)
                ((PARTIAL_COUNT++))
                PARTIAL_DOMAINS+=("$domain")
                ;;
        esac
        
        # 寫入 CSV
        write_csv_record "$domain" "$OVERALL_STATUS" "${node_data[@]}"
        
        echo "  -> 整體狀態: $OVERALL_STATUS" | tee -a "$LOG_FILE"
        echo "------------------------------------------------" | tee -a "$LOG_FILE"
        
        # 批次控制
        if [[ $batch_count -ge $BATCH_SIZE && $PROCESSED_DOMAINS -lt $TOTAL_DOMAINS ]]; then
            echo "" | tee -a "$LOG_FILE"
            echo "⏸️  已完成 $batch_count 個域名，休息 ${BATCH_DELAY} 秒避免頻率限制..." | tee -a "$LOG_FILE"
            echo "" | tee -a "$LOG_FILE"
            sleep $BATCH_DELAY
            batch_count=0
        else
            # 正常延遲
            sleep $DELAY_BETWEEN_DOMAINS
        fi
        
    done < "$DOMAINS_FILE"
    
    echo -e "\n"
    echo "=== 檢測完成！===" | tee -a "$LOG_FILE"
    echo ""
    
    # 生成摘要報告
    generate_summary
}

# 執行主程序
main
