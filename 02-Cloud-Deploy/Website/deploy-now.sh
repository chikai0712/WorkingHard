#!/bin/bash

# 快速部署腳本 - 使用你的 EC2 IP
# 在本機執行此腳本

set -e

EC2_IP="44.202.226.49"
KEY_PATH="$HOME/.ssh/my-ec2-key.pem"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 開始部署網站到 EC2${NC}"
echo "EC2 IP: $EC2_IP"
echo ""

# 檢查 Key 檔案
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ 錯誤：找不到 Key 檔案：$KEY_PATH${NC}"
    exit 1
fi

# 設定 Key 權限
chmod 400 "$KEY_PATH" 2>/dev/null || true

# 檢測 EC2 使用者名稱
echo -e "${YELLOW}🔍 檢測 EC2 使用者名稱...${NC}"
EC2_USER=""

for USER in ec2-user ubuntu admin root; do
    echo "嘗試使用者：$USER"
    if ssh -i "$KEY_PATH" -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$USER@$EC2_IP" "echo 'ok'" &>/dev/null; then
        EC2_USER="$USER"
        echo -e "${GREEN}✅ 找到使用者：$EC2_USER${NC}"
        break
    fi
done

if [ -z "$EC2_USER" ]; then
    echo -e "${RED}❌ 無法連線到 EC2${NC}"
    echo "請確認："
    echo "  1. EC2 IP 是否正確：$EC2_IP"
    echo "  2. Security Group 是否開放 22 埠"
    echo "  3. Key Pair 是否正確：$KEY_PATH"
    exit 1
fi

# 步驟 1：上傳部署腳本
echo ""
echo -e "${YELLOW}📤 步驟 1：上傳部署腳本...${NC}"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
    "$SOURCE_DIR/deploy-to-ec2.sh" \
    "$EC2_USER@$EC2_IP:~/"

echo -e "${GREEN}✅ 部署腳本已上傳${NC}"

# 步驟 2：在 EC2 上執行部署腳本
echo ""
echo -e "${YELLOW}🔧 步驟 2：在 EC2 上執行部署腳本...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
    "sudo bash ~/deploy-to-ec2.sh"

echo -e "${GREEN}✅ Nginx 部署完成${NC}"

# 步驟 3：上傳網站文件
echo ""
echo -e "${YELLOW}📤 步驟 3：上傳網站文件...${NC}"

# 使用 rsync（如果可用）或 scp
if command -v rsync &> /dev/null; then
    echo "使用 rsync 上傳..."
    rsync -avz --progress \
        -e "ssh -i $KEY_PATH -o StrictHostKeyChecking=no" \
        --exclude='.git' \
        --exclude='.DS_Store' \
        --exclude='*.md' \
        --exclude='*.sh' \
        --exclude='terraform' \
        --exclude='node_modules' \
        "$SOURCE_DIR/" "$EC2_USER@$EC2_IP:/tmp/website-upload/"
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
        "sudo cp -r /tmp/website-upload/* /var/www/html/ && \
         sudo chown -R www-data:www-data /var/www/html 2>/dev/null || \
         sudo chown -R nginx:nginx /var/www/html && \
         sudo chmod -R 755 /var/www/html && \
         rm -rf /tmp/website-upload"
else
    echo "使用 scp 上傳..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
        "mkdir -p /tmp/website-upload"
    
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no -r \
        "$SOURCE_DIR"/* "$EC2_USER@$EC2_IP:/tmp/website-upload/" 2>/dev/null || {
        # 如果失敗，只上傳 HTML 文件
        echo "嘗試只上傳 HTML 文件..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
            "$SOURCE_DIR"/*.html "$EC2_USER@$EC2_IP:/tmp/website-upload/" 2>/dev/null || true
    }
    
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" \
        "sudo cp -r /tmp/website-upload/* /var/www/html/ && \
         sudo chown -R www-data:www-data /var/www/html 2>/dev/null || \
         sudo chown -R nginx:nginx /var/www/html && \
         sudo chmod -R 755 /var/www/html && \
         rm -rf /tmp/website-upload"
fi

echo -e "${GREEN}✅ 網站文件已上傳${NC}"

# 完成
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${BLUE}🌐 網站網址：${NC}"
echo "  http://$EC2_IP"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "1. 確保 AWS Security Group 已開放 80 埠"
echo "2. 在瀏覽器開啟 http://$EC2_IP 查看網站"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
