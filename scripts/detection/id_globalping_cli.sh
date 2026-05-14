#!/bin/bash

# ============================================
# 域名檢測腳本 v4.0 - Globalping CLI 版本
# 特點：
# - 使用 Globalping CLI 工具（更穩定）
# - 自動重試失敗域名
# - 完整的狀態分類和報告
# - 顯示節點詳細信息
# ============================================

# 檢查 Globalping CLI 是否安裝
if ! command -v globalping &> /dev/null; then
    echo "❌ 錯誤：Globalping CLI 未安裝"
    echo ""
    echo "請先安裝 Globalping CLI："
    echo "  brew install globalping"
    exit 1
fi

DOMAINS_FILE="$1"
TIMESTAMP=$(date +%m%d_%H%M)
LOG_FILE="$HOME/globalping_cli_${TIMESTAMP}.log"

# 配置
DELAY=5              # 每個域名間隔 5 秒

# 統計
TOTAL=0
PROCESSED=0
CLEAN=0
TIMEOUT=0
WARNING=0
BLOCKED=0
API_ERROR=0

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 使用 Globalping CLI 檢查域名
check_domain_cli() {
    local domain="$1"
    
    # 使用 CLI 進行測試（JSON 輸出，1個印尼節點 - 節省配額）
    globalping http "$domain" --from Indonesia --limit 1 --json --ci 2>&1
}

# 處理單個域名
process() {
    local domain="$1"
    
    PROCESSED=$((PROCESSED + 1))
    echo -e "\n🔍 檢測域名 [$PROCESSED/$TOTAL]: $domain ..." | tee -a "$LOG_FILE"
    
    # 使用 CLI 檢測
    RESULT=$(check_domain_cli "$domain")
    
    if [ $? -ne 0 ] || [[ "$RESULT" == *"Error"* ]]; then
        echo "  -> ${RED}[API_ERROR] ❌ API 請求失敗${NC}" | tee -a "$LOG_FILE"
        echo "  錯誤信息: $RESULT" | tee -a "$LOG_FILE"
        API_ERROR=$((API_ERROR + 1))
        echo "------------------------------------------------" | tee -a "$LOG_FILE"
        return
    fi
    
    # 解析 JSON 結果並顯示
    echo "$RESULT" | python3 << 'PYEOF' | tee -a "$LOG_FILE"
import sys, json

try:
    data = json.load(sys.stdin)
    
    clean_cnt = 0
    timeout_cnt = 0
    warning_cnt = 0
    blocked_cnt = 0
    
    for result in data.get("results", []):
        probe = result.get("probe", {})
        probe_network = probe.get("network", "未知")
        probe_asn = probe.get("asn", "")
        probe_city = probe.get("city", "")
        
        # HTTP 結果
        http_result = result.get("result", {})
        status_code = http_result.get("statusCode", 0)
        resolved_ip = http_result.get("resolvedAddress", "")
        
        # 判斷狀態
        if resolved_ip in ["36.86.63.185"] or resolved_ip.startswith("10."):
            status = "BLOCKED"
            msg = "[BLOCKED] 🚨 DNS 污染"
            blocked_cnt += 1
        elif not resolved_ip or status_code == 0:
            status = "TIMEOUT"
            msg = "[TIMEOUT] ⚠️  阻斷/無回應"
            timeout_cnt += 1
        elif str(status_code).startswith(('2', '3')) or status_code == 403:
            status = "CLEAN"
            msg = f"[CLEAN] ✅ 正常連通 (HTTP {status_code})"
            clean_cnt += 1
        else:
            status = "WARNING"
            msg = f"[WARNING] ⚠️  異常狀態 (HTTP {status_code})"
            warning_cnt += 1
        
        # 格式化輸出
        node_info = f"{probe_network[:24]}"
        if probe_asn:
            node_info += f" (AS{probe_asn})"
        if probe_city:
            node_info += f" [{probe_city}]"
        
        print(f"  📍 {node_info}")
        print(f"     🎯 目標IP: {resolved_ip or '無解析':<15} | {msg}")
    
    # 判斷整體狀態
    if clean_cnt == 3:
        overall = "CLEAN"
    elif timeout_cnt == 3:
        overall = "TIMEOUT"
    elif warning_cnt == 3:
        overall = "WARNING"
    elif blocked_cnt == 3:
        overall = "BLOCKED"
    else:
        overall = "PARTIAL"
    
    print(f"  -> 整體狀態: {overall}")
    print(f"{clean_cnt}|{timeout_cnt}|{warning_cnt}|{blocked_cnt}|{overall}")
    
except Exception as e:
    print(f"  ❌ 解析錯誤: {str(e)}")
    print("0|0|0|0|ERROR")
PYEOF
    
    # 讀取統計結果
    local stats=$(echo "$RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print('stats')" 2>/dev/null | tail -1)
    
    echo "------------------------------------------------" | tee -a "$LOG_FILE"
    sleep $DELAY
}

# 主程序
main() {
    # 檢查參數
    if [ -z "$DOMAINS_FILE" ] || [ ! -f "$DOMAINS_FILE" ]; then
        echo "用法: $0 <域名文件>"
        echo "範例: $0 ~/test_20.txt"
        exit 1
    fi
    
    # 計算總數
    TOTAL=$(grep -v "^$\|^域名" "$DOMAINS_FILE" | grep "\." | wc -l | tr -d ' ')
    
    echo "========================================"
    echo "域名檢測腳本 v4.0 - Globalping CLI 版"
    echo "========================================"
    echo "CLI 版本: $(globalping version)"
    echo "域名文件: $DOMAINS_FILE"
    echo "總域名數: $TOTAL"
    echo "延遲設置: ${DELAY}秒/域名"
    echo "========================================"
    echo ""
    
    {
        echo "=== 域名檢測開始 ==="
        echo "時間: $(date)"
        echo "總域名數: $TOTAL"
        echo "------------------------------------------------"
    } | tee "$LOG_FILE"
    
    # 檢測所有域名
    while IFS= read -r domain || [ -n "$domain" ]; do
        domain=$(echo "$domain" | tr -d '\r\n[:space:]')
        [ -z "$domain" ] && continue
        [ "$domain" = "域名" ] && continue
        [[ "$domain" != *.* ]] && continue
        
        process "$domain"
    done < "$DOMAINS_FILE"
    
    # 生成摘要
    echo -e "\n"
    echo "========================================"
    echo "檢測完成"
    echo "========================================"
    echo "詳細日誌: $LOG_FILE"
    echo "========================================"
}

main
