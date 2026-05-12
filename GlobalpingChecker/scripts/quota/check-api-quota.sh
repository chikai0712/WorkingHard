#!/bin/bash

# Globalping API 額度檢查工具

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

# 你的 API Token
API_TOKEN="${GLOBALPING_TOKEN:-uh5vlg4ttg3v5gwby5zgtqrciimahql5}"

echo "🔍 Globalping API 額度檢查"
echo "========================================"
echo ""

# 檢查 API Token
if [ -z "$API_TOKEN" ]; then
    echo "❌ 未設置 API Token"
    echo ""
    echo "請設置環境變數："
    echo "  export GLOBALPING_TOKEN='your_token_here'"
    exit 1
fi

echo "📊 API Token: ${API_TOKEN:0:20}..."
echo ""

# 獲取額度資訊
echo "⏳ 查詢額度..."
RESPONSE=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
    "https://api.globalping.io/v1/limits")

if [ $? -ne 0 ]; then
    echo "❌ API 請求失敗"
    exit 1
fi

# 解析並顯示額度資訊
echo "$RESPONSE" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    
    print("✅ API 額度資訊")
    print("=" * 50)
    print()
    
    # 測量限制
    if "measurements" in data:
        m = data["measurements"]
        print("📈 測量 (Measurements):")
        print(f"   每分鐘限制: {m.get(\"rateLimit\", {}).get(\"limit\", \"N/A\")}")
        print(f"   已使用: {m.get(\"rateLimit\", {}).get(\"remaining\", \"N/A\")}")
        reset_time = m.get("rateLimit", {}).get("reset", 0)
        if reset_time:
            from datetime import datetime
            reset_dt = datetime.fromtimestamp(reset_time)
            print(f"   重置時間: {reset_dt.strftime(\"%Y-%m-%d %H:%M:%S\")}")
        print()
    
    # 信用額度
    if "credits" in data:
        c = data["credits"]
        print("💰 信用額度 (Credits):")
        print(f"   剩餘額度: {c.get(\"remaining\", \"N/A\")}")
        print()
    
    # 原始數據
    print("📋 原始數據:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"❌ 解析失敗: {e}")
    print()
    print("原始回應:")
    print(sys.stdin.read())
'

echo ""
echo "========================================"
echo "✅ 檢查完成"
echo "========================================"
echo ""

# 提供建議
echo "💡 使用建議："
echo ""
echo "1. 免費用戶限制："
echo "   - 每分鐘 100 次測量"
echo "   - 每月 10,000 次測量"
echo ""
echo "2. 優化建議："
echo "   - 增加檢測間隔（目前 8 秒）"
echo "   - 減少批次大小（目前 30 個）"
echo "   - 使用 API Token 獲得更高額度"
echo ""
echo "3. 監控額度："
echo "   - 定期執行此腳本檢查額度"
echo "   - 在檢測腳本中添加額度檢查"
echo ""
