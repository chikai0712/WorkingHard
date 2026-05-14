#!/bin/bash
# 更新現有 EC2 的網站內容
# 將博弈網站部署到現有的兩台 EC2

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 現有 EC2 配置
EC2_IP_1="35.74.79.10"
EC2_IP_2="35.78.244.92"
KEY_PATH="$HOME/.ssh/dns-test-key.pem"
WEBSITE_FILE="/Users/ckchiu/Desktop/Project/websites/site2-gaming/aws.html"

echo -e "${GREEN}=== 更新現有 EC2 網站 ===${NC}\n"

# 檢查文件
if [ ! -f "$WEBSITE_FILE" ]; then
    echo -e "${RED}❌ 找不到網站文件: $WEBSITE_FILE${NC}"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ 找不到 SSH 密鑰: $KEY_PATH${NC}"
    exit 1
fi

chmod 400 "$KEY_PATH" 2>/dev/null || true

echo -e "${CYAN}配置：${NC}"
echo "  網站文件: $WEBSITE_FILE"
echo "  SSH 密鑰: $KEY_PATH"
echo "  目標服務器:"
echo "    1. $EC2_IP_1"
echo "    2. $EC2_IP_2"
echo ""

# 部署函數
deploy_to_server() {
    local ip=$1
    local num=$2
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}部署到服務器 $num: $ip${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 檢測用戶名
    echo -e "${YELLOW}檢測 EC2 用戶名...${NC}"
    local user=""
    for u in ec2-user ubuntu admin root; do
        if ssh -i "$KEY_PATH" -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$u@$ip" "echo ok" &>/dev/null; then
            user="$u"
            echo -e "${GREEN}✓ 用戶名: $user${NC}"
            break
        fi
    done
    
    if [ -z "$user" ]; then
        echo -e "${RED}✗ 無法連線${NC}"
        return 1
    fi
    
    # 備份
    echo -e "${YELLOW}備份現有網站...${NC}"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$user@$ip" \
        "sudo cp /var/www/html/index.html /var/www/html/index.html.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"
    
    # 上傳
    echo -e "${YELLOW}上傳網站文件...${NC}"
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$WEBSITE_FILE" "$user@$ip:/tmp/index.html"
    
    # 部署
    echo -e "${YELLOW}部署網站...${NC}"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$user@$ip" \
        "sudo mv /tmp/index.html /var/www/html/index.html && \
         sudo chmod 644 /var/www/html/index.html && \
         sudo systemctl restart httpd 2>/dev/null || sudo systemctl restart nginx 2>/dev/null || true"
    
    # 測試
    echo -e "${YELLOW}測試網站...${NC}"
    if curl -s --connect-timeout 3 "http://$ip" | grep -q "皇冠娛樂城"; then
        echo -e "${GREEN}✓ 部署成功！${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 部署完成，但無法驗證內容${NC}"
        return 0
    fi
}

# 確認
read -p "$(echo -e ${YELLOW}確定要部署博弈網站嗎？[y/N]: ${NC})" confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

echo ""

# 部署
success=0

if deploy_to_server "$EC2_IP_1" "1"; then
    ((success++))
fi

echo ""

if deploy_to_server "$EC2_IP_2" "2"; then
    ((success++))
fi

# 結果
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}成功: $success / 2 台服務器${NC}"
echo ""
echo -e "${CYAN}訪問網址：${NC}"
echo "  http://$EC2_IP_1"
echo "  http://$EC2_IP_2"
echo "  http://www.clouddeployment168.site"
echo ""

if [ $success -eq 2 ]; then
    echo -e "${GREEN}✓ 所有服務器部署成功！${NC}"
else
    echo -e "${YELLOW}⚠ 部分服務器部署失敗${NC}"
    echo ""
    echo -e "${YELLOW}可能原因：${NC}"
    echo "1. 網路連線問題"
    echo "2. SSH 密鑰不正確"
    echo "3. Security Group 未開放 22 埠"
fi
