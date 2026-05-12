# BIND DNS 容器使用指南

本指南說明如何在 macOS/Linux/Windows 環境下使用容器化的 BIND DNS 服務器。

---

## 📋 前置需求

### 必須安裝的軟件

1. **Docker Desktop** 或 **Docker Engine**
   - macOS: 下載 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - Linux: 安裝 Docker Engine
     ```bash
     # Ubuntu/Debian
     sudo apt-get update
     sudo apt-get install docker.io docker-compose
     ```
   - Windows: 下載 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

2. **Git**（可選，用於版本控制）

---

## 🚀 快速開始

### 1. 檢查 Docker 安裝

```bash
# 檢查 Docker 版本
docker --version

# 檢查 Docker Compose 版本
docker-compose --version

# 確認 Docker 服務運行中
docker info
```

### 2. 啟動 BIND DNS 服務

#### macOS/Linux:

```bash
# 賦予執行權限
chmod +x start.sh

# 啟動服務
./start.sh
```

#### Windows:

```cmd
# 雙擊執行或在命令行執行
start.bat
```

#### 或使用 Docker Compose 直接啟動:

```bash
docker-compose up -d
```

### 3. 驗證服務運行

```bash
# 檢查容器狀態
docker ps | grep bind9-dns

# 查看容器日誌
docker-compose logs -f bind9

# 測試 DNS 查詢（如果配置了 example.com zone）
dig @127.0.0.1 example.com
# 或
nslookup example.com 127.0.0.1
```

---

## 📁 目錄結構

```
Multi-NS/
├── docker-compose.yml          # Docker Compose 配置
├── start.sh                    # macOS/Linux 啟動腳本
├── start.bat                   # Windows 啟動腳本
├── bind/
│   ├── config/                 # BIND 配置文件
│   │   ├── named.conf          # 主配置文件
│   │   └── named.conf.local    # 本地 Zone 配置
│   ├── cache/                  # DNS 緩存目錄
│   ├── logs/                   # 日誌文件目錄
│   │   ├── named.log           # 主日誌
│   │   └── query.log           # 查詢日誌
│   └── zones/                  # Zone 文件目錄
│       └── db.example.com      # 範例 Zone 文件
└── BIND_DNS_使用指南.md        # 本文件
```

---

## ⚙️ 配置自定義 DNS Zone

### 步驟 1: 創建 Zone 文件

在 `bind/zones/` 目錄下創建您的 Zone 文件，例如 `db.mydomain.com`:

```bind
;
; BIND data file for mydomain.com
;

$TTL    3600
$ORIGIN mydomain.com.

@       IN      SOA     ns1.mydomain.com. admin.mydomain.com. (
                        2025011701      ; Serial
                        3600            ; Refresh
                        1800            ; Retry
                        604800          ; Expire
                        86400           ; Minimum TTL
                        )

        ; Name Servers
        IN      NS      ns1.mydomain.com.
        IN      NS      ns2.mydomain.com.

        ; A Records
        IN      A       192.0.2.100
www     IN      A       192.0.2.100
ns1     IN      A       192.0.2.100
ns2     IN      A       192.0.2.100

        ; MX Records
        IN      MX      10 mail.mydomain.com.

        ; CNAME Records
mail    IN      CNAME   www.mydomain.com.

        ; TXT Records
        IN      TXT     "v=spf1 mx a ~all"
```

### 步驟 2: 配置 named.conf.local

編輯 `bind/config/named.conf.local`，添加您的 Zone 配置:

```bind
zone "mydomain.com" {
    type master;
    file "/var/lib/bind/zones/db.mydomain.com";
    allow-update { none; };
    notify no;
};
```

### 步驟 3: 重載配置

```bash
# 重啟容器以載入新配置
docker-compose restart bind9

# 或進入容器重載配置（如果 rndc 已配置）
docker exec -it bind9-dns rndc reload
```

### 步驟 4: 驗證配置

```bash
# 測試 DNS 查詢
dig @127.0.0.1 mydomain.com
dig @127.0.0.1 www.mydomain.com

# 檢查 Zone 文件語法
docker exec -it bind9-dns named-checkzone mydomain.com /var/lib/bind/zones/db.mydomain.com
```

---

## 🔍 常用操作

### 查看日誌

```bash
# 查看實時日誌
docker-compose logs -f bind9

# 查看最近 100 行日誌
docker-compose logs --tail=100 bind9

# 查看查詢日誌
tail -f bind/logs/query.log

# 查看錯誤日誌
tail -f bind/logs/named.log
```

### 檢查配置語法

```bash
# 檢查主配置文件
docker exec -it bind9-dns named-checkconf /etc/bind/named.conf

# 檢查特定 Zone
docker exec -it bind9-dns named-checkzone example.com /var/lib/bind/zones/db.example.com
```

### 重啟服務

```bash
# 重啟容器
docker-compose restart bind9

# 停止服務
docker-compose down

# 停止並刪除數據（注意：會刪除緩存和日誌）
docker-compose down -v
```

### 進入容器

```bash
# 進入容器 shell
docker exec -it bind9-dns bash

# 在容器內執行命令
docker exec -it bind9-dns named-checkconf
```

---

## 🌐 作為 Name Server 使用

### 配置您的域名使用此 BIND DNS

1. **確保容器可從外部訪問**
   - 如果服務器有公網 IP，確保防火牆開放 53/UDP 和 53/TCP 端口
   - 如果使用內網，確保 DNS 查詢可以到達此服務器

2. **在域名註冊商設定 Name Server**
   - 例如：設定 `ns1.yourdomain.com` 指向運行 BIND 的服務器 IP
   - 設定 `ns2.yourdomain.com` 指向另一個服務器 IP（推薦）

3. **配置 Zone 文件中的 NS 記錄**
   ```bind
   @       IN      NS      ns1.yourdomain.com.
   @       IN      NS      ns2.yourdomain.com.
   
   ns1     IN      A       <您的服務器IP>
   ns2     IN      A       <另一個服務器IP>
   ```

4. **等待 DNS 傳播**
   - 通常需要 24-48 小時
   - 可以使用 [dnschecker.org](https://dnschecker.org/) 檢查傳播狀態

---

## 🔒 安全建議

1. **限制查詢來源**
   - 編輯 `named.conf` 中的 `allow-query` 和 `allow-recursion`
   - 避免對外開放遞迴查詢

2. **使用防火牆**
   - 只允許必要的 IP 訪問 53 端口

3. **定期更新**
   - 定期更新 Docker 映像: `docker-compose pull`

4. **備份配置**
   - 定期備份 `bind/config` 和 `bind/zones` 目錄

---

## 🐛 故障排除

### 容器無法啟動

```bash
# 查看錯誤日誌
docker-compose logs bind9

# 檢查配置文件語法
docker run --rm -v $(pwd)/bind/config:/etc/bind ubuntu/bind9:latest named-checkconf
```

### DNS 查詢失敗

1. 檢查容器是否運行: `docker ps | grep bind9-dns`
2. 檢查端口是否被占用: `netstat -an | grep 53` (Linux/Mac) 或 `netstat -an | findstr 53` (Windows)
3. 檢查防火牆設置
4. 查看日誌: `docker-compose logs bind9`

### Zone 文件錯誤

```bash
# 檢查 Zone 文件語法
docker exec -it bind9-dns named-checkzone example.com /var/lib/bind/zones/db.example.com

# 常見錯誤：
# - Serial 號未更新
# - 缺少 SOA 記錄
# - 語法錯誤
```

---

## 📚 參考資源

- [BIND 9 官方文檔](https://bind9.readthedocs.io/)
- [DNS Zone 文件格式](https://en.wikipedia.org/wiki/Zone_file)
- [Docker Compose 文檔](https://docs.docker.com/compose/)

---

## 📝 注意事項

1. **端口衝突**: 如果系統已經運行 DNS 服務（如 systemd-resolved），可能需要先停止或配置端口轉發
2. **權限問題**: Linux 系統可能需要調整文件權限
3. **資源使用**: BIND 容器會使用一定的系統資源，請確保有足夠的內存和 CPU

---

**最後更新**: 2025-01-17  
**版本**: v1.0

