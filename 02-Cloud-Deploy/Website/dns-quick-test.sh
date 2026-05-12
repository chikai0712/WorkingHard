#!/bin/bash

# DNS 快速測試腳本（不需要 root 權限）
# 用於快速驗證 DNS 伺服器是否正常

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
DOMAIN="${1:-www.clouddeployment168.site}"
AWS_DNS="205.251.197.44"
GOOGLE_DNS="216.239.32.108"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 DNS 快速測試${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "測試域名：$DOMAIN"
echo ""

# 函數：測試 DNS
test_dns() {
    local dns_server=$1
    local description=$2
    
    echo -e "${CYAN}測試 $description ($dns_server)...${NC}"
    
    if command -v dig &> /dev/null; then
        local result=$(dig @$dns_server $DOMAIN A +short +time=3 +tries=2 2>&1)
        local ip=$(echo "$result" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
        
        if [ -n "$ip" ]; then
            echo -e "${GREEN}✅ 成功：$ip${NC}"
            echo ""
            return 0
        else
            echo -e "${RED}❌ 失敗：無法解析${NC}"
            echo ""
            return 1
        fi
    else
        # 使用 nslookup
        local result=$(nslookup -timeout=3 $DOMAIN $dns_server 2>&1)
        local ip=$(echo "$result" | grep -A 1 "Name:" | grep "Address:" | tail -1 | awk '{print $2}')
        
        if [ -n "$ip" ]; then
            echo -e "${GREEN}✅ 成功：$ip${NC}"
            echo "$result" | grep -A 3 "Name:"
            echo ""
            return 0
        else
            echo -e "${RED}❌ 失敗：無法解析${NC}"
            echo ""
            return 1
        fi
    fi
}

# 執行測試
echo -e "${BLUE}1. 測試 AWS DNS${NC}"
test_dns "$AWS_DNS" "AWS DNS"
AWS_RESULT=$?

echo -e "${BLUE}2. 測試 Google DNS${NC}"
test_dns "$GOOGLE_DNS" "Google DNS"
GOOGLE_RESULT=$?

# 總結
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 測試結果${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $AWS_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ AWS DNS ($AWS_DNS)：正常${NC}"
else
    echo -e "${RED}❌ AWS DNS ($AWS_DNS)：異常${NC}"
fi

if [ $GOOGLE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Google DNS ($GOOGLE_DNS)：正常${NC}"
else
    echo -e "${RED}❌ Google DNS ($GOOGLE_DNS)：異常${NC}"
fi

echo ""

if [ $AWS_RESULT -eq 0 ] && [ $GOOGLE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 兩個 DNS 伺服器都正常運作${NC}"
    echo ""
    echo -e "${YELLOW}💡 下一步：${NC}"
    echo "執行完整故障切換測試："
    echo "  sudo ./dns-failover-test.sh $DOMAIN"
else
    echo -e "${RED}❌ 部分 DNS 伺服器異常，請檢查網路連線或 DNS 設定${NC}"
fi

echo ""
