#!/bin/bash

# DNS 故障切換測試 - 快速開始（3 步驟）

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DOMAIN="${1:-www.clouddeployment168.site}"
DNS_IP="${2:-205.251.197.44}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 DNS 故障切換測試 - 快速開始${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "測試域名：$DOMAIN"
echo "封鎖 DNS：$DNS_IP"
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 需要 root 權限${NC}"
    echo "請使用 sudo 執行"
    exit 1
fi

echo -e "${YELLOW}⚠️  請先開啟 Wireshark：${NC}"
echo "  1. 選擇網路介面（Wi-Fi 或 en0）"
echo "  2. 過濾器輸入：dns || icmp"
echo "  3. 點擊「開始捕獲」"
echo ""
read -p "按 Enter 繼續（確認 Wireshark 已開啟）..."

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}步驟 1：封鎖 DNS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 確保 pfctl 已啟用
if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
    echo -e "${YELLOW}啟用 pfctl...${NC}"
    pfctl -e 2>/dev/null
fi

# 封鎖 DNS
echo -e "${CYAN}封鎖 DNS: $DNS_IP${NC}"
echo "block drop out quick proto udp from any to $DNS_IP port 53" | \
    pfctl -a custom -f - 2>/dev/null

sleep 1

# 驗證
if pfctl -a custom -sr 2>/dev/null | grep -q "$DNS_IP"; then
    echo -e "${GREEN}✅ 封鎖成功${NC}"
    pfctl -a custom -sr | grep "$DNS_IP"
else
    echo -e "${YELLOW}⚠️  anchor 方法失敗，嘗試備用方法...${NC}"
    (pfctl -sr 2>/dev/null; \
     echo "block drop out quick proto udp from any to $DNS_IP port 53") | \
        pfctl -f - 2>/dev/null
    
    if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
        echo -e "${GREEN}✅ 封鎖成功（備用方法）${NC}"
    else
        echo -e "${RED}❌ 封鎖失敗${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${CYAN}測試封鎖...${NC}"
if dig @$DNS_IP $DOMAIN +time=2 +tries=1 2>&1 | grep -qi "timeout\|connection refused\|no servers could be reached"; then
    echo -e "${GREEN}✅ 封鎖生效${NC}"
else
    echo -e "${YELLOW}⚠️  警告：查詢仍然成功，可能快取影響${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}步驟 2：清除 DNS 快取${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${CYAN}清除 DNS 快取...${NC}"
dscacheutil -flushcache 2>/dev/null || true
killall -HUP mDNSResponder 2>/dev/null || true
echo -e "${GREEN}✅ DNS 快取已清除${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}步驟 3：執行查詢（觀察故障切換）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}💡 現在在 Wireshark 中觀察封包${NC}"
echo ""
echo -e "${CYAN}執行查詢（不指定 DNS，讓系統自動選擇）...${NC}"
echo ""

nslookup $DOMAIN

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 在 Wireshark 中應該看到：${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. DNS Query → $DNS_IP"
echo "2. ICMP Destination Unreachable ← $DNS_IP（表示被封鎖）"
echo "3. DNS Query → 其他 DNS 伺服器（切換）"
echo "4. DNS Response ← 成功回應"
echo ""

echo -e "${YELLOW}💡 觀察時間間隔：${NC}"
echo "  - 第一次查詢到 ICMP 錯誤：< 10ms"
echo "  - ICMP 錯誤到切換：1-5 秒"
echo "  - 切換到成功回應：< 100ms"
echo ""

read -p "按 Enter 解除封鎖..."

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔓 解除封鎖${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

pfctl -a custom -F all 2>/dev/null || true
(pfctl -sr 2>/dev/null | grep -v "$DNS_IP") | pfctl -f - 2>/dev/null || true

sleep 1

if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
    echo -e "${YELLOW}⚠️  仍有規則存在${NC}"
else
    echo -e "${GREEN}✅ 已解除封鎖${NC}"
fi

echo ""
echo -e "${GREEN}✅ 測試完成！${NC}"
echo ""
echo -e "${YELLOW}💡 下一步：${NC}"
echo "  1. 在 Wireshark 中分析封包"
echo "  2. 查看是否有故障切換行為"
echo "  3. 記錄切換時間"
echo ""
