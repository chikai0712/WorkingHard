#!/bin/bash

# DNS 封包分析腳本
# 分析 Wireshark 捕獲的 DNS 封包，檢查故障切換行為

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DOMAIN="${1:-www.clouddeployment168.site}"
PCAP_FILE="${2:-}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 DNS 封包分析工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "分析域名：$DOMAIN"
echo ""

if [ -n "$PCAP_FILE" ] && [ -f "$PCAP_FILE" ]; then
    echo -e "${CYAN}從檔案分析：$PCAP_FILE${NC}"
    echo ""
    
    # 使用 tshark 分析（如果可用）
    if command -v tshark &> /dev/null; then
        echo -e "${CYAN}使用 tshark 分析...${NC}"
        tshark -r "$PCAP_FILE" -Y "dns.qry.name == \"$DOMAIN\"" -T fields \
            -e frame.number -e frame.time_relative -e ip.src -e ip.dst \
            -e dns.flags.response -e dns.qry.name -e dns.a 2>/dev/null | \
            while IFS=$'\t' read -r num time src dst is_response qname ip; do
                if [ "$is_response" = "0" ]; then
                    echo -e "${YELLOW}[$time] 查詢：$src -> $dst ($qname)${NC}"
                else
                    echo -e "${GREEN}[$time] 回應：$dst -> $src ($qname) IP: $ip${NC}"
                fi
            done
    else
        echo -e "${YELLOW}⚠️  tshark 未安裝，無法分析 pcap 檔案${NC}"
        echo "安裝方法：brew install wireshark"
    fi
else
    echo -e "${CYAN}即時捕獲 DNS 封包（10 秒）...${NC}"
    echo "請在另一個終端執行 DNS 查詢："
    echo "  nslookup $DOMAIN"
    echo ""
    
    # 使用 tcpdump 捕獲
    if command -v tcpdump &> /dev/null; then
        echo -e "${YELLOW}開始捕獲（10 秒）...${NC}"
        timeout 10 tcpdump -i any -n -s 0 'udp port 53' 2>/dev/null | \
            grep -i "$DOMAIN" || echo "未捕獲到相關封包"
    else
        echo -e "${RED}❌ tcpdump 未安裝${NC}"
        echo "安裝方法："
        echo "  macOS: 已內建（可能需要授權）"
        echo "  Linux: sudo apt-get install tcpdump"
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💡 分析提示：${NC}"
echo ""
echo "1. 查看查詢順序：系統是否按順序查詢 DNS 伺服器"
echo "2. 查看回應時間：如果第一個 DNS 失敗，多久後查詢第二個"
echo "3. 查看重傳：是否有 DNS 查詢重傳（表示第一個失敗）"
echo "4. 查看錯誤：是否有 ICMP Destination Unreachable（表示被封鎖）"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
