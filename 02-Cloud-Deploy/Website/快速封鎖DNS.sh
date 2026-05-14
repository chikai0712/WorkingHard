#!/bin/bash

# 快速封鎖 DNS 腳本（使用絕對路徑）

DNS_IP="${1:-205.251.197.44}"

if [ "$EUID" -ne 0 ]; then 
    echo "❌ 需要 root 權限"
    echo "請使用 sudo 執行"
    exit 1
fi

echo "🚫 封鎖 DNS: $DNS_IP"

# 確保 pfctl 已啟用
if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
    echo "⚠️  啟用 pfctl..."
    pfctl -e 2>/dev/null
fi

# 封鎖 DNS
echo "block drop out quick proto udp from any to $DNS_IP port 53" | \
    pfctl -a custom -f - 2>/dev/null

# 驗證
sleep 1
if pfctl -a custom -sr 2>/dev/null | grep -q "$DNS_IP"; then
    echo "✅ 封鎖成功"
    echo ""
    echo "規則："
    pfctl -a custom -sr | grep "$DNS_IP"
    echo ""
    echo "測試封鎖："
    dig @$DNS_IP www.clouddeployment168.site +time=2 +tries=1 2>&1 | head -5
else
    echo "⚠️  anchor 方法失敗，嘗試備用方法..."
    
    # 備用方法
    (pfctl -sr 2>/dev/null; \
     echo "block drop out quick proto udp from any to $DNS_IP port 53") | \
        pfctl -f - 2>/dev/null
    
    sleep 1
    if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
        echo "✅ 封鎖成功（使用主規則集）"
        pfctl -sr | grep "$DNS_IP"
    else
        echo "❌ 封鎖失敗"
        exit 1
    fi
fi
