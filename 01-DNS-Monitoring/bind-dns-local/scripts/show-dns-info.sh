#!/bin/bash
# DNS 對外服務測試腳本

# 顏色定義
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== DNS 對外服務資訊 ===${NC}\n"

# 取得本機 IP
echo -e "${CYAN}你的 IP 地址：${NC}"
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "  " $2}'
echo ""

# 顯示 DNS 埠號
echo -e "${CYAN}DNS 服務埠號：${NC}"
echo "  本機存取: 53"
echo "  區域網路存取: 5353"
echo ""

# 取得主要 IP（通常是 Wi-Fi 或乙太網路）
PRIMARY_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -n "$PRIMARY_IP" ]; then
    echo -e "${CYAN}其他人可以這樣查詢你的 DNS：${NC}"
    echo "  dig @$PRIMARY_IP -p 5353 example.com"
    echo "  dig @$PRIMARY_IP -p 5353 www.clouddeployment168.site"
    echo ""
    
    echo -e "${YELLOW}測試連線：${NC}"
    if dig @"$PRIMARY_IP" -p 5353 example.com +short +time=2 &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} DNS 服務正常運行"
    else
        echo -e "  ${YELLOW}⚠${NC} 無法連線，請檢查："
        echo "    1. Docker 容器是否運行: docker ps | grep bind-dns-local"
        echo "    2. 防火牆設定"
    fi
else
    echo -e "${YELLOW}⚠ 無法取得 IP 地址${NC}"
fi

echo ""
echo -e "${CYAN}檢查 Docker 容器狀態：${NC}"
if docker ps | grep -q bind-dns-local; then
    echo -e "  ${GREEN}✓${NC} BIND 容器正在運行"
else
    echo -e "  ${YELLOW}✗${NC} BIND 容器未運行"
    echo "  啟動容器: cd bind-dns-local && ./scripts/start.sh"
fi
