#!/bin/bash

# 驗證 DNS 封鎖是否生效

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DNS_IP="${1:-205.251.197.44}"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 需要 root 權限${NC}"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 驗證 DNS 封鎖狀態${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. 檢查規則是否存在
echo -e "${CYAN}1. 檢查規則是否存在...${NC}"

# 檢查 anchor
ANCHOR_RULE=$(pfctl -a custom -sr 2>/dev/null | grep "$DNS_IP" || true)

# 檢查主規則集
MAIN_RULE=$(pfctl -sr 2>/dev/null | grep "$DNS_IP" || true)

if [ -n "$ANCHOR_RULE" ]; then
    echo -e "${GREEN}✅ 規則存在（anchor）${NC}"
    echo "規則：$ANCHOR_RULE"
    RULE_EXISTS=true
elif [ -n "$MAIN_RULE" ]; then
    echo -e "${GREEN}✅ 規則存在（主規則集）${NC}"
    echo "規則：$MAIN_RULE"
    RULE_EXISTS=true
else
    echo -e "${RED}❌ 規則不存在${NC}"
    echo ""
    echo "請先執行封鎖命令："
    echo "  echo 'block drop out quick proto udp from any to $DNS_IP port 53' | sudo pfctl -a custom -f -"
    RULE_EXISTS=false
fi

echo ""

# 2. 測試封鎖是否生效
if [ "$RULE_EXISTS" = true ]; then
    echo -e "${CYAN}2. 測試封鎖是否生效...${NC}"
    echo ""
    
    # 清除快取
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    
    echo "執行：dig @$DNS_IP www.clouddeployment168.site +time=2 +tries=1"
    echo ""
    
    RESULT=$(dig @$DNS_IP www.clouddeployment168.site +time=2 +tries=1 2>&1)
    
    if echo "$RESULT" | grep -qi "timeout\|connection refused\|no servers could be reached\|timed out"; then
        echo -e "${GREEN}✅ 封鎖生效：DNS 查詢失敗${NC}"
        echo ""
        echo "查詢結果："
        echo "$RESULT" | head -10
        echo ""
        echo -e "${GREEN}✅ 可以繼續進行故障切換測試${NC}"
    elif echo "$RESULT" | grep -qi "ANSWER SECTION"; then
        echo -e "${RED}❌ 封鎖未生效：DNS 查詢仍然成功${NC}"
        echo ""
        echo "查詢結果："
        echo "$RESULT" | grep -A 5 "ANSWER SECTION"
        echo ""
        echo -e "${YELLOW}⚠️  可能原因：${NC}"
        echo "  1. 規則語法問題"
        echo "  2. 系統設定覆蓋規則"
        echo "  3. 需要重啟 pfctl"
        echo ""
        echo "請檢查："
        echo "  sudo pfctl -sr | grep $DNS_IP"
        echo "  sudo pfctl -si"
    else
        echo -e "${YELLOW}⚠️  無法確定結果${NC}"
        echo ""
        echo "查詢結果："
        echo "$RESULT" | head -10
    fi
else
    echo -e "${YELLOW}⚠️  跳過測試（規則不存在）${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
