#!/bin/bash

# 原始版本 v1.1
DOMAINS_FILE="$1"
LOG_FILE="$HOME/globalping_v1_$(date +%m%d_%H%M).log"

echo "=== 啟動印尼多節點交叉比對檢測 (Globalping v1.1) ===" | tee "$LOG_FILE"
echo "測試時間: $(date)" | tee -a "$LOG_FILE"
echo "------------------------------------------------" | tee -a "$LOG_FILE"

while IFS= read -r domain || [ -n "$domain" ]; do
    domain=$(echo "$domain" | tr -d '\r\n[:space:]')
    [[ -z "$domain" || "$domain" == "域名" || "$domain" != *.* ]] && continue
    
    echo "🔍 檢測域名: $domain ..." | tee -a "$LOG_FILE"

    # [升級點 1] 要求 3 個印尼節點進行並發測試
    JSON_PAYLOAD='{"type":"http","target":"'"$domain"'","limit":3,"locations":[{"country":"ID"}]}'
    
    POST_RES=$(curl -s -X POST https://api.globalping.io/v1/measurements \
        -H "Content-Type: application/json" -d "$JSON_PAYLOAD")
    
    MEASURE_ID=$(echo "$POST_RES" | grep -Eo '"id"\s*:\s*"[^"]+"' | head -1 | cut -d'"' -f4)
    
    if [ -z "$MEASURE_ID" ]; then
        echo "  -> [ERROR] API 建立失敗，可能觸發頻率限制，請稍後再試。" | tee -a "$LOG_FILE"
        echo "------------------------------------------------" | tee -a "$LOG_FILE"
        sleep 2
        continue
    fi

    # [升級點 2] 3 台設備需要較多時間回傳，給予 8 秒緩衝
    sleep 8

    GET_RES=$(curl -s "https://api.globalping.io/v1/measurements/$MEASURE_ID")
    
    # [升級點 3] 呼叫 Mac 內建 Python 進行防錯位 JSON 陣列解析
    PARSED_DATA=$(echo "$GET_RES" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    for r in data.get("results", []):
        net = r.get("probe", {}).get("network", "未知 ISP")
        ip = r.get("result", {}).get("resolvedAddress", "")
        code = r.get("result", {}).get("statusCode", 0)
        print(f"{net}|{ip}|{code}")
except Exception:
    pass
')

    if [ -z "$PARSED_DATA" ]; then
        echo "  -> ⚠️ 探針無回應 (可能 API 尚未測量完畢)" | tee -a "$LOG_FILE"
    else
        # 逐行讀取這 3 台探針的回報結果
        echo "$PARSED_DATA" | while IFS='|' read -r NET IP CODE; do
            
            # 狀態判讀
            if [[ "$IP" == "36.86.63.185" || "$IP" == "10."* ]]; then
                STATUS="[BLOCKED] 🚨 DNS 污染"
            elif [[ -z "$CODE" || "$CODE" == "0" || "$CODE" == "null" || "$CODE" == "None" ]]; then
                STATUS="[TIMEOUT] ⚠️ 阻斷/無回應"
            elif [[ "$CODE" == 2* || "$CODE" == 3* || "$CODE" == 403 ]]; then
                STATUS="[CLEAN] ✅ 正常連通 (HTTP $CODE)"
            else
                STATUS="[WARNING] 異常狀態 (HTTP $CODE)"
            fi
            
            # 專業的排版輸出 (對齊 ISP 名稱、IP 與結論)
            printf "  📍 %-26s | IP: %-15s | %s\n" "${NET:0:24}" "${IP:-無解析}" "$STATUS" | tee -a "$LOG_FILE"
        done
    fi

    echo "------------------------------------------------" | tee -a "$LOG_FILE"
    
    # 稍微延遲避免被 Globalping 系統當成惡意 DDoS
    sleep 2
done < "$DOMAINS_FILE"

echo "=== 檢測完成！詳細報告請查看: $LOG_FILE ==="
