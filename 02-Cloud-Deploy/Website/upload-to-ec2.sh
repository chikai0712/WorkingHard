#!/bin/bash

# 上傳網站文件到 EC2 的腳本
# 在本機執行此腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📤 上傳網站文件到 EC2${NC}"
echo ""

# 檢查參數
if [ "$#" -lt 2 ]; then
    echo "用法：$0 <EC2-IP或主機名> <Key-Pair路徑> [網站文件目錄]"
    echo ""
    echo "範例："
    echo "  $0 1.2.3.4 ~/.ssh/my-ec2-key.pem"
    echo "  $0 ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com ~/.ssh/my-ec2-key.pem ./Website"
    echo ""
    exit 1
fi

EC2_HOST="$1"
KEY_PATH="$2"
SOURCE_DIR="${3:-.}"

# 檢查 Key 檔案
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ 錯誤：找不到 Key 檔案：$KEY_PATH${NC}"
    exit 1
fi

# 檢查 Key 檔案權限
PERM=$(stat -f "%A" "$KEY_PATH" 2>/dev/null || stat -c "%a" "$KEY_PATH" 2>/dev/null)
if [ "$PERM" != "400" ] && [ "$PERM" != "600" ]; then
    echo -e "${YELLOW}⚠️  修正 Key 檔案權限...${NC}"
    chmod 400 "$KEY_PATH"
    echo -e "${GREEN}✅ 權限已設定${NC}"
fi

# 檢查來源目錄
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ 錯誤：找不到目錄：$SOURCE_DIR${NC}"
    exit 1
fi

# 檢測 EC2 使用者名稱
echo -e "${YELLOW}🔍 檢測 EC2 使用者名稱...${NC}"

# 嘗試常見的使用者名稱
for USER in ec2-user ubuntu admin root; do
    if ssh -i "$KEY_PATH" -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$USER@$EC2_HOST" "echo 'ok'" &>/dev/null; then
        EC2_USER="$USER"
        echo -e "${GREEN}✅ 找到使用者：$EC2_USER${NC}"
        break
    fi
done

if [ -z "$EC2_USER" ]; then
    echo -e "${YELLOW}⚠️  無法自動檢測使用者名稱${NC}"
    read -p "請輸入 EC2 使用者名稱（例如：ec2-user, ubuntu）：" EC2_USER
    if [ -z "$EC2_USER" ]; then
        echo -e "${RED}❌ 錯誤：使用者名稱不能為空${NC}"
        exit 1
    fi
fi

# 檢查遠端目錄是否存在
echo -e "${YELLOW}📁 檢查遠端目錄...${NC}"
if ! ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "test -d /var/www/html" 2>/dev/null; then
    echo -e "${RED}❌ 錯誤：遠端目錄 /var/www/html 不存在${NC}"
    echo "請先在 EC2 上執行 deploy-to-ec2.sh 腳本"
    exit 1
fi

# 列出要上傳的文件
echo ""
echo -e "${BLUE}📋 要上傳的文件：${NC}"
find "$SOURCE_DIR" -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.json" -o -name "*.png" -o -name "*.jpg" -o -name "*.svg" -o -name "*.ico" \) ! -path "*/.*" | head -20
FILE_COUNT=$(find "$SOURCE_DIR" -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.json" -o -name "*.png" -o -name "*.jpg" -o -name "*.svg" -o -name "*.ico" \) ! -path "*/.*" | wc -l | tr -d ' ')
echo "共 $FILE_COUNT 個文件"
echo ""

read -p "確認上傳？(y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 上傳文件
echo ""
echo -e "${YELLOW}📤 正在上傳文件...${NC}"

# 使用 rsync（如果可用）或 scp
if command -v rsync &> /dev/null; then
    echo "使用 rsync 上傳（較快且支援增量同步）..."
    rsync -avz --progress \
        -e "ssh -i $KEY_PATH -o StrictHostKeyChecking=no" \
        --exclude='.git' \
        --exclude='.DS_Store' \
        --exclude='*.md' \
        --exclude='*.sh' \
        --exclude='terraform' \
        --exclude='node_modules' \
        "$SOURCE_DIR/" "$EC2_USER@$EC2_HOST:/var/www/html/"
else
    echo "使用 scp 上傳..."
    # 建立臨時目錄
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "mkdir -p /tmp/website-upload"
    
    # 上傳文件
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no -r \
        "$SOURCE_DIR"/* "$EC2_USER@$EC2_HOST:/tmp/website-upload/" 2>/dev/null || {
        # 如果失敗，嘗試只上傳 HTML 文件
        echo "嘗試只上傳 HTML 文件..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
            "$SOURCE_DIR"/*.html "$EC2_USER@$EC2_HOST:/tmp/website-upload/" 2>/dev/null || true
    }
    
    # 移動到目標目錄
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" \
        "sudo cp -r /tmp/website-upload/* /var/www/html/ && sudo chown -R www-data:www-data /var/www/html 2>/dev/null || sudo chown -R nginx:nginx /var/www/html && rm -rf /tmp/website-upload"
fi

# 設定權限
echo ""
echo -e "${YELLOW}🔐 設定文件權限...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" \
    "sudo chown -R www-data:www-data /var/www/html 2>/dev/null || sudo chown -R nginx:nginx /var/www/html && sudo chmod -R 755 /var/www/html"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 上傳完成！${NC}"
echo ""
echo -e "${BLUE}🌐 網站網址：${NC}"
echo "  http://$EC2_HOST"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "1. 確保 AWS Security Group 已開放 80 埠"
echo "2. 在瀏覽器開啟 http://$EC2_HOST 查看網站"
echo "3. 如果需要 HTTPS，請設定 SSL 憑證"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
