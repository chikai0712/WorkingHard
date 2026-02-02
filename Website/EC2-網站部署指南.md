# EC2 網站部署完整指南

## 📋 概述

本指南將協助你在 AWS EC2 上部署網站，使用 Nginx 作為 Web 伺服器。

---

## 🎯 前置需求

### ✅ 已完成
- [x] 已連線到 AWS EC2 實例
- [x] 已設定 AWS CLI Access Key
- [x] 已設定 EC2 Key Pair

### 📦 需要準備
- 網站文件（HTML、CSS、JS 等）
- EC2 實例的公開 IP 或主機名
- EC2 Key Pair 檔案路徑（例如：`~/.ssh/my-ec2-key.pem`）

---

## 🚀 快速開始

### 方法 1：自動部署（推薦）

#### 步驟 1：在 EC2 上執行部署腳本

```bash
# 1. 連線到 EC2
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip

# 2. 下載部署腳本（在 EC2 上執行）
curl -O https://raw.githubusercontent.com/your-repo/deploy-to-ec2.sh
# 或從本機上傳腳本
```

**或直接複製腳本內容到 EC2：**

```bash
# 在 EC2 上執行
sudo bash << 'EOF'
# 貼上 deploy-to-ec2.sh 的內容
EOF
```

**或使用提供的腳本：**

```bash
# 從本機上傳腳本到 EC2
scp -i ~/.ssh/your-key.pem deploy-to-ec2.sh ec2-user@your-ec2-ip:~/

# 連線到 EC2
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip

# 執行腳本（需要 sudo）
sudo bash deploy-to-ec2.sh
```

#### 步驟 2：上傳網站文件

**使用提供的上傳腳本（在本機執行）：**

```bash
# 確保腳本有執行權限
chmod +x upload-to-ec2.sh

# 執行上傳
./upload-to-ec2.sh your-ec2-ip ~/.ssh/your-key.pem ./Website
```

**或手動上傳：**

```bash
# 上傳單一文件
scp -i ~/.ssh/your-key.pem index.html ec2-user@your-ec2-ip:/var/www/html/

# 上傳整個目錄
scp -i ~/.ssh/your-key.pem -r Website/* ec2-user@your-ec2-ip:/tmp/
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip "sudo cp -r /tmp/* /var/www/html/"
```

---

### 方法 2：手動部署

#### 步驟 1：安裝 Nginx

**Ubuntu/Debian：**
```bash
sudo apt-get update
sudo apt-get install -y nginx
```

**Amazon Linux/RHEL/CentOS：**
```bash
sudo yum install -y nginx
# 或
sudo dnf install -y nginx
```

#### 步驟 2：設定網站目錄

```bash
# 建立網站目錄
sudo mkdir -p /var/www/html

# 設定權限
sudo chown -R www-data:www-data /var/www/html  # Ubuntu/Debian
sudo chown -R nginx:nginx /var/www/html        # Amazon Linux/RHEL
sudo chmod -R 755 /var/www/html
```

#### 步驟 3：配置 Nginx

**Ubuntu/Debian：**
```bash
sudo nano /etc/nginx/sites-available/default
```

**Amazon Linux/RHEL：**
```bash
sudo nano /etc/nginx/conf.d/default.conf
```

**基本配置：**
```nginx
server {
    listen 80;
    server_name _;
    
    root /var/www/html;
    index index.html index.htm;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
```

**測試配置：**
```bash
sudo nginx -t
```

#### 步驟 4：啟動 Nginx

```bash
# 啟用服務
sudo systemctl enable nginx

# 啟動服務
sudo systemctl start nginx

# 檢查狀態
sudo systemctl status nginx
```

#### 步驟 5：設定防火牆

**UFW（Ubuntu）：**
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

**firewalld（RHEL/CentOS）：**
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### 步驟 6：上傳網站文件

```bash
# 從本機上傳
scp -i ~/.ssh/your-key.pem index.html ec2-user@your-ec2-ip:/var/www/html/
```

---

## 🔧 詳細步驟說明

### 1. 取得 EC2 資訊

```bash
# 取得公開 IP
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,State.Name]' \
  --output table

# 或從 EC2 Console 查看
```

### 2. 連線到 EC2

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip
```

### 3. 執行部署腳本

```bash
# 上傳腳本
scp -i ~/.ssh/your-key.pem deploy-to-ec2.sh ec2-user@your-ec2-ip:~/

# 連線到 EC2
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip

# 執行腳本
sudo bash deploy-to-ec2.sh
```

### 4. 上傳網站文件

**使用上傳腳本：**
```bash
# 在本機執行
./upload-to-ec2.sh your-ec2-ip ~/.ssh/your-key.pem ./Website
```

**手動上傳：**
```bash
# 上傳單一文件
scp -i ~/.ssh/your-key.pem index.html ec2-user@your-ec2-ip:/var/www/html/

# 上傳多個文件
scp -i ~/.ssh/your-key.pem *.html *.css *.js ec2-user@your-ec2-ip:/var/www/html/

# 上傳整個目錄（使用 rsync，推薦）
rsync -avz --progress \
  -e "ssh -i ~/.ssh/your-key.pem" \
  ./Website/ ec2-user@your-ec2-ip:/var/www/html/
```

### 5. 設定 AWS Security Group

**重要：** 確保 Security Group 開放 80 和 443 埠！

```bash
# 使用 AWS CLI
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

**或在 AWS Console：**
1. EC2 → Security Groups
2. 選擇你的 Security Group
3. Inbound rules → Edit inbound rules
4. 新增規則：
   - Type: HTTP, Port: 80, Source: 0.0.0.0/0
   - Type: HTTPS, Port: 443, Source: 0.0.0.0/0

---

## 🌐 測試網站

### 1. 檢查 Nginx 狀態

```bash
# 在 EC2 上執行
sudo systemctl status nginx
curl http://localhost
```

### 2. 從本機瀏覽器測試

開啟瀏覽器，訪問：
```
http://your-ec2-public-ip
```

### 3. 檢查日誌

```bash
# Nginx 存取日誌
sudo tail -f /var/log/nginx/access.log

# Nginx 錯誤日誌
sudo tail -f /var/log/nginx/error.log
```

---

## 🔒 設定 HTTPS（SSL/TLS）

### 使用 Let's Encrypt（免費）

```bash
# 安裝 Certbot
sudo apt-get install -y certbot python3-certbot-nginx  # Ubuntu/Debian
sudo yum install -y certbot python3-certbot-nginx      # Amazon Linux/RHEL

# 取得憑證（需要域名）
sudo certbot --nginx -d your-domain.com

# 自動續約
sudo certbot renew --dry-run
```

### 使用 AWS Certificate Manager（ACM）

1. 在 ACM 申請憑證
2. 使用 Application Load Balancer（ALB）或 CloudFront
3. 將憑證附加到負載平衡器

---

## 📝 常用命令

### Nginx 管理

```bash
# 啟動
sudo systemctl start nginx

# 停止
sudo systemctl stop nginx

# 重啟
sudo systemctl restart nginx

# 重新載入配置（不中斷服務）
sudo systemctl reload nginx

# 檢查狀態
sudo systemctl status nginx

# 測試配置
sudo nginx -t
```

### 文件管理

```bash
# 查看網站目錄
ls -la /var/www/html

# 設定權限
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# 備份網站
sudo cp -r /var/www/html /var/www/html-backup-$(date +%Y%m%d)
```

---

## 🐛 故障排除

### 問題 1：無法連線到網站

**檢查項目：**
1. Security Group 是否開放 80/443 埠？
2. Nginx 是否正在運行？
3. 防火牆是否阻擋？

```bash
# 檢查 Nginx
sudo systemctl status nginx

# 檢查埠口
sudo netstat -tlnp | grep :80

# 檢查 Security Group
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

### 問題 2：403 Forbidden

**可能原因：**
- 文件權限不正確
- Nginx 配置錯誤

```bash
# 檢查權限
ls -la /var/www/html

# 修正權限
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# 檢查 Nginx 配置
sudo nginx -t
```

### 問題 3：502 Bad Gateway

**可能原因：**
- Nginx 配置錯誤
- 後端服務未啟動

```bash
# 檢查 Nginx 錯誤日誌
sudo tail -f /var/log/nginx/error.log

# 檢查配置
sudo nginx -t
```

### 問題 4：上傳文件失敗

**檢查項目：**
1. Key Pair 路徑是否正確？
2. EC2 使用者名稱是否正確？
3. 是否有寫入權限？

```bash
# 測試 SSH 連線
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip "echo 'ok'"

# 檢查遠端目錄權限
ssh -i ~/.ssh/your-key.pem ec2-user@your-ec2-ip "ls -la /var/www/html"
```

---

## 📊 效能優化

### 1. 啟用 Gzip 壓縮

已在部署腳本中自動設定。

### 2. 設定快取

已在部署腳本中自動設定靜態資源快取。

### 3. 使用 CDN

考慮使用 CloudFront 加速網站。

### 4. 啟用 HTTP/2

```nginx
listen 443 ssl http2;
```

---

## 🔐 安全建議

1. **定期更新系統**
   ```bash
   sudo apt-get update && sudo apt-get upgrade  # Ubuntu/Debian
   sudo yum update                              # Amazon Linux/RHEL
   ```

2. **設定防火牆規則**
   - 只開放必要的埠
   - 限制來源 IP（如果可能）

3. **使用 HTTPS**
   - 設定 SSL/TLS 憑證
   - 強制 HTTPS 重定向

4. **定期備份**
   ```bash
   sudo tar -czf /backup/website-$(date +%Y%m%d).tar.gz /var/www/html
   ```

5. **監控日誌**
   ```bash
   sudo tail -f /var/log/nginx/access.log
   ```

---

## 📚 相關資源

- [Nginx 官方文件](https://nginx.org/en/docs/)
- [AWS EC2 文件](https://docs.aws.amazon.com/ec2/)
- [Let's Encrypt 文件](https://letsencrypt.org/docs/)

---

## ✅ 檢查清單

部署完成後，確認：

- [ ] Nginx 已安裝並運行
- [ ] 網站文件已上傳到 `/var/www/html`
- [ ] AWS Security Group 已開放 80/443 埠
- [ ] 可以從瀏覽器訪問網站
- [ ] 文件權限設定正確
- [ ] Nginx 配置正確
- [ ] 防火牆規則已設定
- [ ] （可選）HTTPS 已設定

---

## 🎉 完成！

你的網站現在應該已經在 EC2 上運行了！

如有問題，請參考故障排除章節或查看日誌。
