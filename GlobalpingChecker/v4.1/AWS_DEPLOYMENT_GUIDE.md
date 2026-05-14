# GlobalpingChecker V4.1 - AWS 部署指南

## 📋 前置要求

- AWS 帳戶
- EC2 實例（推薦 t3.medium 或更高）
- Ubuntu 20.04 LTS 或 Amazon Linux 2
- SSH 密鑰對

## 🚀 快速部署步驟

### 1. 啟動 EC2 實例

```bash
# 推薦配置
- 實例類型: t3.medium
- 存儲: 30GB EBS
- 安全組: 開放 8000 端口（HTTP）
- 操作系統: Ubuntu 20.04 LTS
```

### 2. SSH 連接到實例

```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

### 3. 安裝依賴

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Python 和必要工具
sudo apt install -y python3.9 python3-pip python3-venv git

# 安裝 Docker（可選，用於 PostgreSQL）
sudo apt install -y docker.io
sudo usermod -aG docker ubuntu
```

### 4. 克隆項目

```bash
cd /opt
sudo git clone https://github.com/your-repo/GlobalpingChecker.git
cd GlobalpingChecker/v4.1
sudo chown -R ubuntu:ubuntu /opt/GlobalpingChecker
```

### 5. 配置環境

```bash
# 複製 .env 文件
cp .env.example .env

# 編輯 .env 文件
nano .env
```

**必須配置的環境變數：**

```bash
# 數據庫（使用 SQLite 或 PostgreSQL）
DATABASE_URL=sqlite:///./data/globalping_results.db

# Globalping API Token
GLOBALPING_TOKEN=uh5vlg4ttg3v5gwby5zgtqrciimahql5

# 檢測配置
CHECK_INTERVAL_MINUTES=90
ABNORMAL_CHECK_HOUR=1
NORMAL_CHECK_HOUR=9
MAX_ITERATIONS=10

# 服務器配置
HOST=0.0.0.0
PORT=8000
```

### 6. 創建虛擬環境並安裝依賴

```bash
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. 初始化數據庫

```bash
python generate_mock_data.py  # 先生成模擬數據進行測試
```

### 8. 啟動應用

```bash
# 方式 1：直接運行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 方式 2：使用 systemd 服務（推薦用於生產環境）
sudo nano /etc/systemd/system/globalping.service
```

**systemd 服務文件內容：**

```ini
[Unit]
Description=GlobalpingChecker V4.1
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/GlobalpingChecker/v4.1
Environment="PATH=/opt/GlobalpingChecker/v4.1/venv/bin"
ExecStart=/opt/GlobalpingChecker/v4.1/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**啟動服務：**

```bash
sudo systemctl daemon-reload
sudo systemctl enable globalping
sudo systemctl start globalping
sudo systemctl status globalping
```

### 9. 配置 Nginx 反向代理（可選但推薦）

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/globalping
```

**Nginx 配置：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**啟用配置：**

```bash
sudo ln -s /etc/nginx/sites-available/globalping /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. 配置 SSL（使用 Let's Encrypt）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 訪問監控頁面

部署完成後，訪問：

```
http://your-instance-ip:8000
或
https://your-domain.com
```

## 🔧 故障排除

### 檢查應用日誌

```bash
# 如果使用 systemd
sudo journalctl -u globalping -f

# 如果直接運行
# 查看終端輸出
```

### 檢查端口

```bash
sudo netstat -tlnp | grep 8000
```

### 檢查 API 連接

```bash
curl -X GET https://api.globalping.io/v1/limits \
  -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5"
```

## 📈 性能優化

### 1. 使用 PostgreSQL（推薦用於生產環境）

```bash
# 安裝 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 創建數據庫
sudo -u postgres createdb globalping_db
sudo -u postgres createuser globalping
sudo -u postgres psql -c "ALTER USER globalping WITH PASSWORD 'your_password';"

# 更新 .env
DATABASE_URL=postgresql://globalping:your_password@localhost/globalping_db
```

### 2. 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn

# 啟動
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. 配置自動備份

```bash
# 創建備份腳本
sudo nano /usr/local/bin/backup-globalping.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backups/globalping"
mkdir -p $BACKUP_DIR
cp /opt/GlobalpingChecker/v4.1/data/globalping_results.db $BACKUP_DIR/globalping_results_$(date +%Y%m%d_%H%M%S).db
# 保留最近 7 天的備份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

```bash
# 添加到 crontab
sudo crontab -e
# 添加: 0 2 * * * /usr/local/bin/backup-globalping.sh
```

## 🔐 安全建議

1. **使用 VPC 和安全組** - 限制只允許必要的端口
2. **啟用 SSL/TLS** - 使用 Let's Encrypt
3. **定期更新** - 保持系統和依賴最新
4. **監控日誌** - 使用 CloudWatch 或其他日誌服務
5. **備份數據** - 定期備份數據庫
6. **限制 API Token** - 不要在代碼中硬編碼 Token

## 📞 支持

如有問題，檢查：
- 應用日誌
- Nginx 日誌：`/var/log/nginx/error.log`
- 系統日誌：`sudo journalctl -xe`

---

**部署完成後，應用會自動開始檢測並填充監控頁面！**
