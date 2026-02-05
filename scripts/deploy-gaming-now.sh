#!/bin/bash

# 快速部署博弈網站到兩台 AWS EC2
# 參考 Website/deploy-now.sh 的邏輯

set -e

# EC2 配置
EC2_IP_1="35.74.79.10"
EC2_IP_2="35.78.244.92"
KEY_PATH="$HOME/.ssh/dns-test-key.pem"
WEBSITE_FILE="/Users/ckchiu/Desktop/Project/websites/site2-gaming/aws.html"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🚀 開始部署博弈網站到 AWS EC2${NC}"
echo ""

# 檢查網站文件
if [ ! -f "$WEBSITE_FILE" ]; then
    echo -e "${RED}❌ 錯誤：找不到網站文件${NC}"
    echo "路徑：$WEBSITE_FILE"
    exit 1
fi

# 檢查 Key 檔案
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ 錯誤：找不到 Key 檔案：$KEY_PATH${NC}"
    exit 1
fi

# 設定 Key 權限
chmod 400 "$KEY_PATH" 2>/dev/null || true

echo -e "${CYAN}配置資訊：${NC}"
echo "  SSH 密鑰：$KEY_PATH"
echo "  網站文件：$WEBSITE_FILE"
echo "  目標服務器："
echo "    1. $EC2_IP_1"
echo "    2. $EC2_IP_2"
echo ""

# 部署函數
deploy_to_server() {
    local EC2_IP=$1
    local SERVER_NUM=$2
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}部署到服務器 $SERVER_NUM: $EC2_IP${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 檢測 EC2 使用者名稱
    echo -e "${YELLOW}🔍 檢測 EC2 使用者名稱...${NC}"
    EC2_USER=""
    
    for USER in ec2-user ubuntu admin root; do
        if ssh -i "$KEY_PATH" -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes "$USER@$EC2_IP" "echo 'ok'" &>/dev/null; then
            EC2_USER="$USER"
            echo -e "${GREEN}✅ 找到使用者：$EC2_USER${NC}"
            break
        fi
    done
    
    if [ -z "$EC2_USER" ]; then
        echo -e "${RED}❌ 無法連線到 $EC2_IP${NC}"
        return 1
    fi
    
    # 備份現有網站
    echo -e "${YELLOW}📦 備份現有網站...${NC}"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
        "sudo cp /var/www/html/index.html /var/www/html/index.html.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"
    
    # 上傳網站文件
    echo -e "${YELLOW}📤 上傳網站文件...${NC}"
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        "$WEBSITE_FILE" "$EC2_USER@$EC2_IP:/tmp/index.html"
    
    # 移動到網站目錄並設置權限
    echo -e "${YELLOW}🔧 設置文件權限...${NC}"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
        "sudo mv /tmp/index.html /var/www/html/index.html && \
         sudo chown www-data:www-data /var/www/html/index.html 2>/dev/null || \
         sudo chown nginx:nginx /var/www/html/index.html 2>/dev/null || true && \
         sudo chmod 644 /var/www/html/index.html"
    
    # 重啟 Web 服務
    echo -e "${YELLOW}🔄 重啟 Web 服務...${NC}"
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
        "sudo systemctl restart httpd 2>/dev/null || sudo systemctl restart nginx 2>/dev/null || true"
    
    # 測試訪問
    echo -e "${YELLOW}🧪 測試網站訪問...${NC}"
    if curl -s --connect-timeout 3 "http://$EC2_IP" | grep -q "皇冠娛樂城"; then
        echo -e "${GREEN}✅ 部署成功！網站可正常訪問${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  部署完成，但無法驗證網站內容${NC}"
        return 0
    fi
}

# 確認部署
read -p "$(echo -e ${YELLOW}確定要部署嗎？[y/N]: ${NC})" confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消部署${NC}"
    exit 0
fi

echo ""

# 部署到兩台服務器
success_count=0

if deploy_to_server "$EC2_IP_1" "1"; then
    ((success_count++))
fi

echo ""

if deploy_to_server "$EC2_IP_2" "2"; then
    ((success_count++))
fi

# 顯示結果
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  部署完成！${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}部署統計：${NC}"
echo -e "  成功：${GREEN}$success_count${NC} / 2 台服務器"
echo ""
echo -e "${CYAN}訪問網址：${NC}"
echo -e "  http://$EC2_IP_1"
echo -e "  http://$EC2_IP_2"
echo -e "  http://www.clouddeployment168.site (透過 DNS)"
echo ""

if [ $success_count -eq 2 ]; then
    echo -e "${GREEN}✓ 所有服務器部署成功！${NC}"
    echo ""
    echo -e "${YELLOW}💡 提示：${NC}"
    echo "1. 確保 AWS Security Group 已開放 80 埠"
    echo "2. 在瀏覽器開啟上述網址查看博弈網站"
    echo "3. 備份文件保存在 /var/www/html/index.html.backup.*"
elif [ $success_count -gt 0 ]; then
    echo -e "${YELLOW}⚠ 部分服務器部署成功${NC}"
else
    echo -e "${RED}✗ 所有服務器部署失敗${NC}"
    echo ""
    echo -e "${YELLOW}可能的原因：${NC}"
    echo "1. 網路連線問題（請確認已切換到行動網路）"
    echo "2. SSH 密鑰不正確"
    echo "3. AWS Security Group 未開放 22 埠"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
