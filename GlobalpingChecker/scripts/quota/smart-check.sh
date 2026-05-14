#!/bin/bash

# 單次智能檢測腳本
# 檢查額度，如果 >= 400 則執行檢測，否則跳過

set -e

# 配置
API_TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"
QUOTA_THRESHOLD=300  # 額度 >= 300 才執行
DOMAINS_FILE="${1:-domains.txt}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

echo "🔍 智能檢測 - 檢查額度..."
echo ""

# 檢查額度
RESPONSE=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
    "https://api.globalping.io/v1/limits")

if [ $? -ne 0 ]; then
    echo "❌ API 請求失敗"
    exit 1
fi

REMAINING=$(echo "$RESPONSE" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    print(data["rateLimit"]["measurements"]["create"]["remaining"])
except:
    print("0")
')

echo "📊 當前剩餘額度: $REMAINING / 500"
echo "🎯 執行閾值: $QUOTA_THRESHOLD"
echo ""

if [ "$REMAINING" -ge "$QUOTA_THRESHOLD" ]; then
    echo "✅ 額度充足 ($REMAINING >= $QUOTA_THRESHOLD)"
    echo "🚀 開始執行域名檢測..."
    echo ""
    
    if [ ! -f "$DOMAINS_FILE" ]; then
        echo "❌ 找不到域名文件: $DOMAINS_FILE"
        exit 1
    fi
    
    # 執行檢測
    if [ -f "$SCRIPT_DIR/id_globalping_multi_v3.3_Telegram.sh" ]; then
        bash "$SCRIPT_DIR/id_globalping_multi_v3.3_Telegram.sh" "$DOMAINS_FILE"
        
        echo ""
        echo "✅ 檢測完成"
        
        # 檢測後再次查看額度
        REMAINING_AFTER=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
            "https://api.globalping.io/v1/limits" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    print(data["rateLimit"]["measurements"]["create"]["remaining"])
except:
    print("0")
')
        
        echo "📊 檢測後剩餘額度: $REMAINING_AFTER / 500"
    else
        echo "❌ 找不到檢測腳本: id_globalping_multi_v3.3_Telegram.sh"
        exit 1
    fi
else
    echo "⏳ 額度不足 ($REMAINING < $QUOTA_THRESHOLD)"
    echo "❌ 跳過本次檢測"
    echo ""
    echo "💡 建議："
    echo "   - 等待額度恢復（每分鐘重置）"
    echo "   - 或降低閾值（當前: $QUOTA_THRESHOLD）"
    exit 0
fi
