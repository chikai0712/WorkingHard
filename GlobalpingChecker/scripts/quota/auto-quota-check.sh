#!/bin/bash

# 智能額度監控和自動檢測腳本
# 每 10 分鐘檢查一次額度，當額度 >= 400 時執行檢測

set -e

# 配置
API_TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"
QUOTA_THRESHOLD=300  # 額度 >= 300 才執行
CHECK_INTERVAL=600  # 10 分鐘（秒）
DOMAINS_FILE="${1:-domains.txt}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/auto-check.log"

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 檢查額度
check_quota() {
    local response=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
        "https://api.globalping.io/v1/limits")
    
    if [ $? -ne 0 ]; then
        log "❌ API 請求失敗"
        return 1
    fi
    
    local remaining=$(echo "$response" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    print(data["rateLimit"]["measurements"]["create"]["remaining"])
except:
    print("0")
')
    
    echo "$remaining"
}

# 執行檢測
run_check() {
    log "🚀 開始執行域名檢測..."
    
    if [ ! -f "$DOMAINS_FILE" ]; then
        log "❌ 找不到域名文件: $DOMAINS_FILE"
        return 1
    fi
    
    # 執行檢測腳本
    if [ -f "$SCRIPT_DIR/id_globalping_multi_v3.3_Telegram.sh" ]; then
        bash "$SCRIPT_DIR/id_globalping_multi_v3.3_Telegram.sh" "$DOMAINS_FILE" >> "$LOG_FILE" 2>&1
        log "✅ 檢測完成"
    else
        log "❌ 找不到檢測腳本"
        return 1
    fi
}

# 主循環
main() {
    log "========================================"
    log "🤖 智能額度監控啟動"
    log "========================================"
    log "配置："
    log "  API Token: ${API_TOKEN:0:20}..."
    log "  額度閾值: $QUOTA_THRESHOLD"
    log "  檢查間隔: $CHECK_INTERVAL 秒 ($(($CHECK_INTERVAL / 60)) 分鐘)"
    log "  域名文件: $DOMAINS_FILE"
    log "========================================"
    log ""
    
    while true; do
        log "🔍 檢查 API 額度..."
        
        REMAINING=$(check_quota)
        
        if [ -z "$REMAINING" ] || [ "$REMAINING" = "0" ]; then
            log "⚠️  無法獲取額度資訊，等待下次檢查"
        else
            log "📊 當前剩餘額度: $REMAINING / 500"
            
            if [ "$REMAINING" -ge "$QUOTA_THRESHOLD" ]; then
                log "✅ 額度充足 ($REMAINING >= $QUOTA_THRESHOLD)，開始檢測"
                
                if run_check; then
                    log "🎉 檢測成功完成"
                    
                    # 檢測完成後再次檢查額度
                    REMAINING_AFTER=$(check_quota)
                    log "📊 檢測後剩餘額度: $REMAINING_AFTER / 500"
                    
                    # 如果額度仍然充足，繼續等待下次檢查
                    # 如果額度不足，也等待下次檢查
                else
                    log "❌ 檢測執行失敗"
                fi
            else
                log "⏳ 額度不足 ($REMAINING < $QUOTA_THRESHOLD)，等待額度恢復"
                
                # 計算還需要多久額度會恢復
                NEEDED=$((QUOTA_THRESHOLD - REMAINING))
                log "   還需要 $NEEDED 次額度"
            fi
        fi
        
        log "⏰ 等待 $(($CHECK_INTERVAL / 60)) 分鐘後再次檢查..."
        log ""
        
        sleep $CHECK_INTERVAL
    done
}

# 捕獲中斷信號
trap 'log "🛑 收到中斷信號，停止監控"; exit 0' INT TERM

# 啟動
main
