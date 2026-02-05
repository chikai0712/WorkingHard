#!/bin/bash
# -------------------------------------------------------------------------------
# DNS Failover 快速測試腳本
# 簡化版測試，快速驗證 DNS failover 功能
# -------------------------------------------------------------------------------

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILOVER_SCRIPT="$SCRIPT_DIR/dns-failover-test.sh"

echo -e "${GREEN}=== DNS Failover 快速測試 ===${NC}\n"

# 檢查權限
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}❌ 需要 sudo 權限${NC}"
    echo -e "請使用: ${CYAN}sudo bash $0${NC}"
    exit 1
fi

# 檢查主腳本是否存在
if [ ! -f "$FAILOVER_SCRIPT" ]; then
    echo -e "${RED}❌ 找不到主測試腳本: $FAILOVER_SCRIPT${NC}"
    exit 1
fi

# 提示輸入參數
echo -e "${CYAN}請輸入測試參數（或按 Enter 使用預設值）:${NC}\n"

read -p "域名 [www.clouddeployment168.site]: " DOMAIN
DOMAIN="${DOMAIN:-www.clouddeployment168.site}"

read -p "AWS EC2 IP [3.3.3.3]: " AWS_IP
AWS_IP="${AWS_IP:-3.3.3.3}"

read -p "Google EC2 IP [2.2.2.2]: " GCP_IP
GCP_IP="${GCP_IP:-2.2.2.2}"

echo ""
echo -e "${YELLOW}測試配置:${NC}"
echo -e "  域名: ${CYAN}$DOMAIN${NC}"
echo -e "  AWS EC2 IP: ${CYAN}$AWS_IP${NC}"
echo -e "  Google EC2 IP: ${CYAN}$GCP_IP${NC}"
echo ""

read -p "確認開始測試？(y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}開始執行測試...${NC}\n"

# 執行主測試腳本
bash "$FAILOVER_SCRIPT" "$DOMAIN" "$AWS_IP" "$GCP_IP"
