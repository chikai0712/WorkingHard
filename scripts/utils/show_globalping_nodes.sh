#!/bin/bash

# 查詢 Globalping 節點信息工具
# 用途：顯示測試節點的 IP 和詳細信息

echo "========================================"
echo "Globalping 節點信息查詢"
echo "========================================"
echo ""

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

# 測試域名
TEST_DOMAIN="${1:-google.com}"

echo "測試域名: $TEST_DOMAIN"
echo "請求 3 個印尼節點..."
echo ""

# 發起測試請求
JSON='{"type":"http","target":"'"$TEST_DOMAIN"'","limit":3,"locations":[{"country":"ID"}]}'
POST_RES=$(curl -s -w "\n%{http_code}" -X POST https://api.globalping.io/v1/measurements \
    -H "Content-Type: application/json" -d "$JSON")

HTTP_CODE=$(echo "$POST_RES" | tail -n1)
RESPONSE_BODY=$(echo "$POST_RES" | sed '$d')

MEASURE_ID=$(echo "$RESPONSE_BODY" | grep -Eo '"id"\s*:\s*"[^"]+"' | head -1 | cut -d'"' -f4)

if [ -z "$MEASURE_ID" ]; then
    echo "❌ API 請求失敗"
    echo "HTTP 狀態碼: $HTTP_CODE"
    echo "響應: $RESPONSE_BODY"
    exit 1
fi

echo "✅ 測量 ID: $MEASURE_ID"
echo "等待結果（8 秒）..."
sleep 8

# 獲取結果
GET_RES=$(curl -s "https://api.globalping.io/v1/measurements/$MEASURE_ID")

# 解析並顯示詳細信息
echo "$GET_RES" | python3 << 'EOF'
import sys, json

try:
    data = json.load(sys.stdin)
    
    print("\n" + "="*80)
    print("測試節點詳細信息")
    print("="*80)
    
    for idx, result in enumerate(data.get("results", []), 1):
        probe = result.get("probe", {})
        
        print(f"\n【節點 {idx}】")
        print("-" * 80)
        
        # 節點基本信息
        print(f"📍 網絡名稱: {probe.get('network', '未知')}")
        print(f"🌐 ASN: AS{probe.get('asn', '未知')}")
        print(f"🏢 組織: {probe.get('asn_org', '未知')}")
        
        # 節點 IP 地址
        print(f"🔌 節點 IP: {probe.get('resolvers', ['未知'])[0] if probe.get('resolvers') else '未知'}")
        
        # 地理位置
        print(f"📌 城市: {probe.get('city', '未知')}")
        print(f"🗺️  國家: {probe.get('country', '未知')}")
        print(f"🌍 洲: {probe.get('continent', '未知')}")
        print(f"📍 經緯度: {probe.get('latitude', 'N/A')}, {probe.get('longitude', 'N/A')}")
        
        # 測試結果
        test_result = result.get("result", {})
        resolved_ip = test_result.get("resolvedAddress", "無法解析")
        status_code = test_result.get("statusCode", 0)
        
        print(f"\n🎯 測試結果:")
        print(f"   目標域名解析 IP: {resolved_ip}")
        print(f"   HTTP 狀態碼: {status_code}")
        
        # 節點標籤
        tags = probe.get("tags", [])
        if tags:
            print(f"🏷️  標籤: {', '.join(tags)}")
    
    print("\n" + "="*80)
    print("✅ 查詢完成")
    print("="*80)
    
except Exception as e:
    print(f"❌ 解析錯誤: {str(e)}")
    print("\n原始響應:")
    print(sys.stdin.read())
EOF

echo ""
echo "💡 說明："
echo "  - 節點 IP：Globalping 測試節點的 IP 地址"
echo "  - ASN：自治系統號碼，標識網絡運營商"
echo "  - 目標域名解析 IP：你要測試的域名解析到的 IP"
