#!/bin/bash

# EC2 網站部署腳本
# 在 EC2 實例上執行此腳本以部署網站

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 EC2 網站部署助手${NC}"
echo ""

# 檢查是否為 root 或 sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  需要 root 權限，使用 sudo 執行...${NC}"
    exec sudo bash "$0" "$@"
fi

# 檢測作業系統
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
else
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
fi

echo -e "${BLUE}📋 檢測到作業系統：${OS}${NC}"
echo ""

# 步驟 1：安裝 Nginx
echo -e "${YELLOW}📦 步驟 1：安裝 Nginx${NC}"

if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✅ Nginx 已安裝${NC}"
    nginx -v
else
    echo "正在安裝 Nginx..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y nginx
            ;;
        amazon|amzn|rhel|centos|fedora)
            if command -v dnf &> /dev/null; then
                dnf install -y nginx
            else
                yum install -y nginx
            fi
            ;;
        *)
            echo -e "${RED}❌ 不支援的作業系統：${OS}${NC}"
            echo "請手動安裝 Nginx"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}✅ Nginx 安裝完成${NC}"
fi

# 步驟 2：設定網站目錄
echo ""
echo -e "${YELLOW}📁 步驟 2：設定網站目錄${NC}"

WEB_ROOT="/var/www/html"
BACKUP_DIR="/var/www/backup-$(date +%Y%m%d-%H%M%S)"

# 備份現有網站（如果存在）
if [ -d "$WEB_ROOT" ] && [ "$(ls -A $WEB_ROOT)" ]; then
    echo "備份現有網站到 $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    cp -r "$WEB_ROOT"/* "$BACKUP_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✅ 備份完成${NC}"
fi

# 建立網站目錄
mkdir -p "$WEB_ROOT"
chown -R www-data:www-data "$WEB_ROOT" 2>/dev/null || chown -R nginx:nginx "$WEB_ROOT" 2>/dev/null || true
chmod -R 755 "$WEB_ROOT"

echo -e "${GREEN}✅ 網站目錄已設定：${WEB_ROOT}${NC}"

# 步驟 3：配置 Nginx
echo ""
echo -e "${YELLOW}⚙️  步驟 3：配置 Nginx${NC}"

NGINX_CONF="/etc/nginx/sites-available/default"
if [ ! -d "/etc/nginx/sites-available" ]; then
    NGINX_CONF="/etc/nginx/conf.d/default.conf"
fi

# 建立基本配置
cat > "$NGINX_CONF" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    root /var/www/html;
    index index.html index.htm;
    
    # 啟用 gzip 壓縮
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # 安全標頭
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # 快取靜態資源
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 禁止存取隱藏檔案
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# 如果是 sites-available，建立 symbolic link
if [ -d "/etc/nginx/sites-available" ] && [ -d "/etc/nginx/sites-enabled" ]; then
    ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/default 2>/dev/null || true
fi

# 測試 Nginx 配置
echo "測試 Nginx 配置..."
if nginx -t; then
    echo -e "${GREEN}✅ Nginx 配置正確${NC}"
else
    echo -e "${RED}❌ Nginx 配置錯誤${NC}"
    exit 1
fi

# 步驟 4：設定防火牆
echo ""
echo -e "${YELLOW}🔥 步驟 4：設定防火牆${NC}"

# 檢查防火牆服務
if command -v ufw &> /dev/null; then
    echo "使用 UFW 防火牆..."
    ufw allow 'Nginx Full' 2>/dev/null || ufw allow 80/tcp
    ufw allow 443/tcp
    echo -e "${GREEN}✅ UFW 規則已設定${NC}"
elif command -v firewall-cmd &> /dev/null; then
    echo "使用 firewalld 防火牆..."
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    echo -e "${GREEN}✅ firewalld 規則已設定${NC}"
elif command -v iptables &> /dev/null; then
    echo "使用 iptables 防火牆..."
    iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
    iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
    echo -e "${YELLOW}⚠️  iptables 規則已設定（重開機後需重新設定）${NC}"
else
    echo -e "${YELLOW}⚠️  未檢測到防火牆工具，請在 AWS Security Group 中開放 80 和 443 埠${NC}"
fi

# 步驟 5：啟動 Nginx
echo ""
echo -e "${YELLOW}🚀 步驟 5：啟動 Nginx${NC}"

# 啟用並啟動服務
if command -v systemctl &> /dev/null; then
    systemctl enable nginx
    systemctl restart nginx
    systemctl status nginx --no-pager -l || true
elif command -v service &> /dev/null; then
    chkconfig nginx on 2>/dev/null || true
    service nginx restart
    service nginx status || true
fi

echo -e "${GREEN}✅ Nginx 已啟動${NC}"

# 步驟 6：顯示資訊
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${BLUE}📋 重要資訊：${NC}"
echo ""
echo "網站目錄：$WEB_ROOT"
echo "Nginx 配置：$NGINX_CONF"
if [ -d "$BACKUP_DIR" ]; then
    echo "備份位置：$BACKUP_DIR"
fi
echo ""

# 取得 EC2 實例的公開 IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "無法取得")
PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4 2>/dev/null || echo "無法取得")

echo -e "${BLUE}🌐 連線資訊：${NC}"
if [ "$PUBLIC_IP" != "無法取得" ]; then
    echo "公開 IP：http://$PUBLIC_IP"
fi
if [ "$PRIVATE_IP" != "無法取得" ]; then
    echo "私有 IP：http://$PRIVATE_IP"
fi
echo ""

echo -e "${YELLOW}📝 下一步：${NC}"
echo "1. 上傳網站文件到：$WEB_ROOT"
echo "2. 確保 AWS Security Group 開放 80 和 443 埠"
echo "3. 如果需要 HTTPS，請設定 SSL 憑證"
echo ""
echo -e "${BLUE}💡 提示：${NC}"
echo "使用以下命令上傳文件："
echo "  scp -i ~/.ssh/your-key.pem index.html ec2-user@$PUBLIC_IP:/var/www/html/"
echo "或使用提供的 upload-to-ec2.sh 腳本"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
