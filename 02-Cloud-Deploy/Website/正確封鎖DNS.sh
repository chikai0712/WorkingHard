#!/bin/bash

# 正確封鎖 DNS 的腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DNS_IP="${1:-205.251.197.44}"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 需要 root 權限${NC}"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚫 封鎖 DNS: $DNS_IP${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 確保 pfctl 已啟用
if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
    echo -e "${YELLOW}⚠️  啟用 pfctl...${NC}"
    pfctl -e 2>/dev/null || {
        echo -e "${RED}❌ 無法啟用 pfctl${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ pfctl 已啟用${NC}"
fi

# 方法 1：使用 anchor
echo -e "${CYAN}方法 1：使用 anchor...${NC}"
echo "block drop out quick proto udp from any to $DNS_IP port 53" | \
    pfctl -a custom -f - 2>/dev/null

sleep 1

# 驗證
if pfctl -a custom -sr 2>/dev/null | grep -q "$DNS_IP"; then
    echo -e "${GREEN}✅ 封鎖成功（使用 anchor）${NC}"
    echo ""
    echo "規則："
    pfctl -a custom -sr | grep "$DNS_IP"
    echo ""
    
    # 測試封鎖
    echo -e "${CYAN}測試封鎖...${NC}"
    if dig @$DNS_IP www.clouddeployment168.site +time=2 +tries=1 2>&1 | grep -qi "timeout\|connection refused\|no servers could be reached"; then
        echo -e "${GREEN}✅ 封鎖生效：DNS 查詢失敗${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  警告：DNS 查詢仍然成功${NC}"
        echo "嘗試方法 2..."
    fi
else
    echo -e "${YELLOW}⚠️  anchor 方法失敗${NC}"
fi

# 方法 2：使用主規則集
echo ""
echo -e "${CYAN}方法 2：使用主規則集...${NC}"
(sudo pfctl -sr 2>/dev/null; \
 echo "block drop out quick proto udp from any to $DNS_IP port 53") | \
    pfctl -f - 2>/dev/null

sleep 1

# 驗證
if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
    echo -e "${GREEN}✅ 封鎖成功（使用主規則集）${NC}"
    echo ""
    echo "規則："
    pfctl -sr | grep "$DNS_IP"
    echo ""
    
    # 測試封鎖
    echo -e "${CYAN}測試封鎖...${NC}"
    if dig @$DNS_IP www.clouddeployment168.site +time=2 +tries=1 2>&1 | grep -qi "timeout\|connection refused\|no servers could be reached"; then
        echo -e "${GREEN}✅ 封鎖生效：DNS 查詢失敗${NC}"
        exit 0
    else
        echo -e "${RED}❌ 封鎖未生效：DNS 查詢仍然成功${NC}"
        echo ""
        echo "可能原因："
        echo "  1. pfctl 規則語法問題"
        echo "  2. 系統設定覆蓋規則"
        echo "  3. 需要重啟 pfctl"
        exit 1
    fi
else
    echo -e "${RED}❌ 封鎖失敗${NC}"
    echo ""
    echo "請手動執行："
    echo "  sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to $DNS_IP port 53'"
    exit 1
fi
