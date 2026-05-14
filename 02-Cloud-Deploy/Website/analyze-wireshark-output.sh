#!/bin/bash

# Wireshark 輸出分析腳本
# 分析 DNS 封包，識別故障切換行為

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DOMAIN="${1:-www.clouddeployment168.site}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 Wireshark DNS 封包分析工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "分析域名：$DOMAIN"
echo ""
echo -e "${YELLOW}請貼上 Wireshark 的封包輸出（Ctrl+D 結束輸入）...${NC}"
echo ""

# 讀取輸入
INPUT=$(cat)

if [ -z "$INPUT" ]; then
    echo -e "${RED}❌ 沒有輸入${NC}"
    exit 1
fi

echo -e "${CYAN}分析中...${NC}"
echo ""

# 提取相關的 DNS 封包
DNS_QUERIES=$(echo "$INPUT" | grep -i "query.*$DOMAIN" | grep -v "response")
DNS_RESPONSES=$(echo "$INPUT" | grep -i "response.*$DOMAIN")
ICMP_ERRORS=$(echo "$INPUT" | grep -i "icmp.*unreachable")
RETRANSMISSIONS=$(echo "$INPUT" | grep -i "retransmission")

# 分析查詢
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 DNS 查詢分析${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -n "$DNS_QUERIES" ]; then
    echo -e "${GREEN}找到 $(echo "$DNS_QUERIES" | wc -l | tr -d ' ') 個 DNS 查詢${NC}"
    echo ""
    
    # 提取時間和 DNS 伺服器
    echo "$DNS_QUERIES" | while IFS= read -r line; do
        # 提取時間（第一個數字）
        time=$(echo "$line" | awk '{print $2}')
        # 提取來源 IP
        src=$(echo "$line" | awk '{print $3}')
        # 提取目標 IP（DNS 伺服器）
        dst=$(echo "$line" | awk '{print $4}')
        
        echo -e "${CYAN}[$time] 查詢：$src → $dst${NC}"
    done
else
    echo -e "${RED}❌ 沒有找到 DNS 查詢${NC}"
fi

echo ""

# 分析回應
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 DNS 回應分析${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -n "$DNS_RESPONSES" ]; then
    echo -e "${GREEN}找到 $(echo "$DNS_RESPONSES" | wc -l | tr -d ' ') 個 DNS 回應${NC}"
    echo ""
    
    # 統計成功和失敗
    SUCCESS=$(echo "$DNS_RESPONSES" | grep -i "A $DOMAIN" | wc -l | tr -d ' ')
    FAILED=$(echo "$DNS_RESPONSES" | grep -iE "No such name|NXDOMAIN|SERVFAIL" | wc -l | tr -d ' ')
    
    echo -e "${GREEN}✅ 成功回應：$SUCCESS${NC}"
    if [ "$FAILED" -gt 0 ]; then
        echo -e "${RED}❌ 失敗回應：$FAILED${NC}"
    fi
    echo ""
    
    # 提取 IP 位址
    echo "$DNS_RESPONSES" | grep -i "A $DOMAIN" | while IFS= read -r line; do
        time=$(echo "$line" | awk '{print $2}')
        src=$(echo "$line" | awk '{print $3}')
        dst=$(echo "$line" | awk '{print $4}')
        ip=$(echo "$line" | grep -oE 'A [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1 | awk '{print $2}')
        
        if [ -n "$ip" ]; then
            echo -e "${GREEN}[$time] 回應：$src → $dst (IP: $ip)${NC}"
        fi
    done
else
    echo -e "${RED}❌ 沒有找到 DNS 回應${NC}"
fi

echo ""

# 分析 ICMP 錯誤
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 ICMP 錯誤分析${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -n "$ICMP_ERRORS" ]; then
    echo -e "${RED}⚠️  找到 $(echo "$ICMP_ERRORS" | wc -l | tr -d ' ') 個 ICMP 錯誤${NC}"
    echo ""
    echo "$ICMP_ERRORS" | head -5
    echo ""
    echo -e "${YELLOW}💡 這表示 DNS 被封鎖或不可達${NC}"
else
    echo -e "${GREEN}✅ 沒有 ICMP 錯誤${NC}"
    echo -e "${YELLOW}💡 這表示 DNS 沒有被封鎖，或封鎖未生效${NC}"
fi

echo ""

# 分析重傳
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 重傳分析${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -n "$RETRANSMISSIONS" ]; then
    echo -e "${YELLOW}⚠️  找到 $(echo "$RETRANSMISSIONS" | wc -l | tr -d ' ') 個重傳${NC}"
    echo ""
    echo "$RETRANSMISSIONS" | head -5
    echo ""
    echo -e "${YELLOW}💡 這表示查詢超時，系統正在重試${NC}"
else
    echo -e "${GREEN}✅ 沒有重傳${NC}"
    echo -e "${YELLOW}💡 這表示所有查詢都有回應，沒有超時${NC}"
fi

echo ""

# 總結
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 分析總結${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 檢查是否有故障切換跡象
HAS_FAILOVER=false

if [ -n "$ICMP_ERRORS" ]; then
    echo -e "${GREEN}✅ 發現 ICMP 錯誤 → 可能有故障切換${NC}"
    HAS_FAILOVER=true
fi

if [ -n "$RETRANSMISSIONS" ]; then
    echo -e "${GREEN}✅ 發現重傳 → 可能有故障切換${NC}"
    HAS_FAILOVER=true
fi

if [ "$HAS_FAILOVER" = false ]; then
    echo -e "${YELLOW}⚠️  沒有發現故障切換跡象${NC}"
    echo ""
    echo "可能原因："
    echo "  1. DNS 沒有被封鎖"
    echo "  2. 系統使用並行查詢（同時查詢多個 DNS）"
    echo "  3. DNS 快取導致沒有查詢"
    echo ""
    echo "建議："
    echo "  1. 確認封鎖規則是否生效：sudo pfctl -sr | grep <DNS_IP>"
    echo "  2. 清除 DNS 快取：sudo dscacheutil -flushcache"
    echo "  3. 只配置一個 DNS 進行測試"
fi

echo ""
