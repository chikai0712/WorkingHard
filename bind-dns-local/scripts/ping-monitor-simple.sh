#!/bin/bash
# -------------------------------------------------------------------------------
# 簡化版 Ping 監控腳本 - 僅記錄到日誌
# 功能：持續 ping AWS 和 Google NS，結果寫入日誌
# 
# 用法：
#   bash ./ping-monitor-simple.sh [間隔秒數]
#   例如：bash ./ping-monitor-simple.sh 5
#
# 預設間隔：2 秒
# 按 Ctrl+C 停止
# -------------------------------------------------------------------------------

# 配置
INTERVAL="${1:-1}"
PING_TIMEOUT=2
LOG_FILE="/tmp/ping_monitor_$(date +%Y%m%d_%H%M%S).log"

# AWS Route53 NS IPs
AWS_NS=(
    "205.251.197.44"
    "205.251.199.48"
    "205.251.192.236"
    "205.251.195.65"
)

# Google Cloud DNS NS IPs
GOOGLE_NS=(
    "216.239.32.108"
    "216.239.34.108"
    "216.239.36.108"
    "216.239.38.108"
)

# 清理函數
cleanup() {
    echo ""
    echo "監控已停止"
    echo "完整日誌: $LOG_FILE"
    exit 0
}

trap cleanup INT TERM

# 寫入日誌標頭
{
    echo "=== DNS NS 連線監控日誌 ==="
    echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "監控間隔: ${INTERVAL} 秒"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
} > "$LOG_FILE"

echo "=== DNS NS 連線監控 ==="
echo "監控間隔: ${INTERVAL} 秒"
echo "Ping 超時: ${PING_TIMEOUT} 秒"
echo "日誌檔案: $LOG_FILE"
echo "按 Ctrl+C 停止監控"
echo ""

round=1

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] 第 $round 輪監控"
    
    aws_success=0
    google_success=0
    
    # Ping AWS NS
    for i in "${!AWS_NS[@]}"; do
        ip="${AWS_NS[$i]}"
        name="AWS-NS-$((i+1))"
        
        ping_output=$(ping -c 1 -W "$PING_TIMEOUT" "$ip" 2>&1)
        ping_status=$?
        
        if [ $ping_status -eq 0 ]; then
            latency=$(echo "$ping_output" | grep -oE "time=[0-9]+\.[0-9]+" | cut -d'=' -f2)
            
            if [ -z "$latency" ]; then
                latency=$(echo "$ping_output" | grep -oE "time=[0-9]+" | cut -d'=' -f2)
            fi
            
            if [ -z "$latency" ]; then
                latency="<1"
            fi
            
            echo "  ✓ $name ($ip) - ${latency}ms"
            echo "[$timestamp] SUCCESS | $name | $ip | ${latency}ms" >> "$LOG_FILE"
            aws_success=$((aws_success + 1))
        else
            echo "  ✗ $name ($ip) - 超時 (>${PING_TIMEOUT}s)"
            echo "[$timestamp] TIMEOUT | $name | $ip | >${PING_TIMEOUT}s" >> "$LOG_FILE"
        fi
    done
    
    # Ping Google NS
    for i in "${!GOOGLE_NS[@]}"; do
        ip="${GOOGLE_NS[$i]}"
        name="Google-NS-$((i+1))"
        
        ping_output=$(ping -c 1 -W "$PING_TIMEOUT" "$ip" 2>&1)
        ping_status=$?
        
        if [ $ping_status -eq 0 ]; then
            latency=$(echo "$ping_output" | grep -oE "time=[0-9]+\.[0-9]+" | cut -d'=' -f2)
            
            if [ -z "$latency" ]; then
                latency=$(echo "$ping_output" | grep -oE "time=[0-9]+" | cut -d'=' -f2)
            fi
            
            if [ -z "$latency" ]; then
                latency="<1"
            fi
            
            echo "  ✓ $name ($ip) - ${latency}ms"
            echo "[$timestamp] SUCCESS | $name | $ip | ${latency}ms" >> "$LOG_FILE"
            google_success=$((google_success + 1))
        else
            echo "  ✗ $name ($ip) - 超時 (>${PING_TIMEOUT}s)"
            echo "[$timestamp] TIMEOUT | $name | $ip | >${PING_TIMEOUT}s" >> "$LOG_FILE"
        fi
    done
    
    # 統計
    echo "  AWS: $aws_success/4 可達 | Google: $google_success/4 可達"
    echo "[$timestamp] SUMMARY | AWS: $aws_success/4 | Google: $google_success/4" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo ""
    
    round=$((round + 1))
    sleep "$INTERVAL"
done
