# EC2 網站部署指南 - DNS Failover 測試

本指南說明如何在 AWS 上部署兩台 EC2，分別顯示不同的內容，用於 DNS failover 測試。

## 架構概述

- **EC2-1 (AWS)**: 顯示 "我是 AWS 3.3.3.3"（假設 IP 為 3.3.3.3）
- **EC2-2 (Google)**: 顯示 "我是 Google 2.2.2.2"（假設 IP 為 2.2.2.2）
- **域名**: 同時配置 AWS Route53 和 Google Cloud DNS 作為 NS

## 步驟 1：部署 EC2-1 (AWS)

### 1.1 啟動 EC2 實例

```bash
# 使用 AWS CLI 啟動實例（或透過 AWS Console）
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --key-name your-key-name \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=DNS-Test-AWS}]'
```

### 1.2 配置安全群組

允許以下流量：
- **HTTP (80)**: 0.0.0.0/0
- **HTTPS (443)**: 0.0.0.0/0
- **SSH (22)**: 你的 IP

### 1.3 安裝 Web 伺服器

```bash
# SSH 連線到 EC2
ssh -i your-key.pem ec2-user@<EC2-IP>

# 安裝 Nginx
sudo yum update -y
sudo yum install -y nginx

# 建立網站內容
sudo tee /usr/share/nginx/html/index.html > /dev/null <<EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DNS Failover Test - AWS</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        h1 { font-size: 3em; margin: 20px 0; }
        .ip { font-size: 2em; font-weight: bold; }
    </style>
</head>
<body>
    <h1>我是 AWS</h1>
    <div class="ip">3.3.3.3</div>
    <p>這是 AWS EC2 實例</p>
    <p>時間: <span id="time"></span></p>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
EOF

# 啟動 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 1.4 取得 EC2 公網 IP

```bash
# 查詢實例的公網 IP
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=DNS-Test-AWS" \
    --query 'Reservations[*].Instances[*].PublicIpAddress' \
    --output text
```

假設取得 IP 為 `3.3.3.3`（實際請替換為你的 EC2 IP）

## 步驟 2：部署 EC2-2 (Google)

### 2.1 啟動 EC2 實例

```bash
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --key-name your-key-name \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=DNS-Test-Google}]'
```

### 2.2 配置安全群組

與 EC2-1 相同配置

### 2.3 安裝 Web 伺服器

```bash
# SSH 連線到 EC2
ssh -i your-key.pem ec2-user@<EC2-IP>

# 安裝 Nginx
sudo yum update -y
sudo yum install -y nginx

# 建立網站內容
sudo tee /usr/share/nginx/html/index.html > /dev/null <<EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DNS Failover Test - Google</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        h1 { font-size: 3em; margin: 20px 0; }
        .ip { font-size: 2em; font-weight: bold; }
    </style>
</head>
<body>
    <h1>我是 Google</h1>
    <div class="ip">2.2.2.2</div>
    <p>這是 Google Cloud DNS 對應的 EC2 實例</p>
    <p>時間: <span id="time"></span></p>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
EOF

# 啟動 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2.4 取得 EC2 公網 IP

```bash
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=DNS-Test-Google" \
    --query 'Reservations[*].Instances[*].PublicIpAddress' \
    --output text
```

假設取得 IP 為 `2.2.2.2`（實際請替換為你的 EC2 IP）

## 步驟 3：配置 DNS

### 3.1 AWS Route53 配置

1. 登入 AWS Console → Route53
2. 建立或選擇 Hosted Zone
3. 建立 A 記錄：
   - **名稱**: `www`（或你的子域名）
   - **類型**: A
   - **值**: `3.3.3.3`（AWS EC2 IP）
   - **TTL**: 60

### 3.2 Google Cloud DNS 配置

1. 登入 Google Cloud Console → Cloud DNS
2. 建立或選擇 Zone
3. 建立 A 記錄：
   - **DNS 名稱**: `www.yourdomain.com`
   - **資源記錄類型**: A
   - **IPv4 地址**: `2.2.2.2`（Google EC2 IP）
   - **TTL**: 60

### 3.3 域名 NS 配置

在域名註冊商處，設定 NS 記錄同時指向：
- AWS Route53 的 NS 伺服器（例如：`ns-xxx.awsdns-xx.com`）
- Google Cloud DNS 的 NS 伺服器（例如：`ns-cloud-x.googledomains.com`）

**重要**: 確保兩個 NS 都配置，這樣才能測試 failover

## 步驟 4：驗證配置

### 4.1 測試 DNS 解析

```bash
# 查詢 NS 記錄
dig NS www.yourdomain.com

# 查詢 A 記錄（可能返回 AWS 或 Google 的 IP）
dig A www.yourdomain.com

# 使用 +trace 觀察解析過程
dig +trace www.yourdomain.com
```

### 4.2 測試網站連線

```bash
# 測試 AWS EC2
curl http://3.3.3.3
# 應顯示 "我是 AWS 3.3.3.3"

# 測試 Google EC2
curl http://2.2.2.2
# 應顯示 "我是 Google 2.2.2.2"
```

## 步驟 5：執行 Failover 測試

### 5.1 在本機執行測試腳本

```bash
cd bind-dns-local/scripts
sudo bash ./dns-failover-test.sh www.yourdomain.com 3.3.3.3 2.2.2.2
```

### 5.2 測試流程

腳本會執行以下測試：
1. **基準測試**: 無阻擋，確認域名可正常解析
2. **阻擋 AWS NS**: 只放行 Google NS，應解析到 Google EC2
3. **阻擋 Google NS**: 只放行 AWS NS，應解析到 AWS EC2
4. **全黑測試**: 阻擋所有 DNS，應無法解析
5. **切換測試**: 多次切換 NS，觀察系統反應時間

## 故障排除

### 問題 1: DNS 解析失敗

- 檢查安全群組是否允許 HTTP/HTTPS 流量
- 確認 EC2 實例正在運行
- 檢查 Nginx 服務狀態：`sudo systemctl status nginx`

### 問題 2: 防火牆規則未生效

- 確認使用 `sudo` 執行腳本
- 檢查 pfctl 狀態：`sudo pfctl -si`
- 查看 Debug 日誌：`/tmp/dns_failover_debug.log`

### 問題 3: 無法切換到備用 NS

- 確認兩個 NS 都已正確配置
- 檢查 DNS TTL 設定（建議設為 60 秒）
- 清除本地 DNS 快取：`dscacheutil -flushcache`

## 清理資源

測試完成後，記得刪除 EC2 實例以節省費用：

```bash
# 查詢實例 ID
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=DNS-Test-*" \
    --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
    --output table

# 終止實例
aws ec2 terminate-instances --instance-ids i-xxxxxxxxx
```

## 注意事項

1. **費用**: EC2 實例會產生費用，測試完成後請及時刪除
2. **IP 地址**: 上述 IP（3.3.3.3、2.2.2.2）為範例，請替換為實際的 EC2 IP
3. **安全**: 測試環境建議使用限制性安全群組，只允許必要的流量
4. **HTTPS**: 如需測試 HTTPS，請配置 SSL 憑證（可使用 Let's Encrypt）
