# SSL 憑證自動更新與監控系統

自動管理 SSL 憑證的更新與監控系統，支援 Let's Encrypt 免費憑證，並在憑證剩餘 14 天內每天發送警報。

## 功能特色

- ✅ **自動檢查憑證到期時間**：定期檢查所有配置的憑證
- ✅ **自動更新憑證**：使用 Certbot 自動更新 Let's Encrypt 憑證
- ✅ **憑證保存**：更新後自動將憑證保存到指定資料夾
- ✅ **自動上傳**：支援將憑證自動上傳到多台遠端機器（SSH/SCP）
- ✅ **智能警報系統**：在憑證剩餘 14 天內，每天發送一次警報
- ✅ **多種警報方式**：支援 Email、Webhook、日誌等多種警報方式
- ✅ **靈活配置**：透過 JSON 配置檔案輕鬆管理多個憑證

## 安裝

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 安裝 Certbot（用於 Let's Encrypt 憑證）

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot

# macOS
brew install certbot

# 或使用 pip
pip install certbot
```

### 3. 配置檔案

複製範例配置檔案並修改：

```bash
cp config.example.json config.json
cp serverlist.example.json serverlist.json
```

編輯 `config.json` 並填入你的憑證資訊：

```json
{
  "alert_threshold_days": 14,
  "renew_threshold_days": 30,
  "certificates": [
    {
      "domain": "your-domain.com",
      "cert_path": "/etc/letsencrypt/live/your-domain.com/fullchain.pem",
      "key_path": "/etc/letsencrypt/live/your-domain.com/privkey.pem",
      "auto_renew": true
    }
  ],
  "renewer": {
    "certbot_path": "certbot",
    "webroot": "/var/www/html",
    "email": "your-email@example.com",
    "use_staging": false,
    "save_dir": "./certs"
  },
  "uploader": {
    "save_dir": "./certs",
    "upload_targets": [
      {
        "host": "server1.example.com",
        "port": 22,
        "username": "root",
        "password": "your-password",
        "remote_path": "/etc/ssl/certs",
        "remote_dir": "your-domain.com"
      }
    ]
  },
  "alert_methods": {
    "log": {
      "enabled": true
    },
    "email": {
      "enabled": true,
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "from": "your-email@gmail.com",
      "to": ["admin@example.com"]
    }
  }
}
```

## 使用方法

### 驗證配置和功能

在開始使用前，建議先驗證配置是否正確：

```bash
# 快速測試（僅檢查配置格式，不需要安裝依賴）
python quick_test.py config.json

# 完整驗證（需要安裝依賴套件）
python verify_cert.py config.json
```

詳細的驗證指南請參考 [VERIFICATION_GUIDE.md](VERIFICATION_GUIDE.md)

### 手動執行檢查

```bash
python cert_manager.py --config config.json
```

### 僅檢查不更新

```bash
python cert_manager.py --config config.json --check-only
```

### 設定定期執行（Cron）

建議每天執行一次檢查：

```bash
# 編輯 crontab
crontab -e

# 添加以下行（每天凌晨 2 點執行）
0 2 * * * cd /path/to/cert-manager && /usr/bin/python3 cert_manager.py --config config.json >> cert_manager.log 2>&1
```

或每 12 小時執行一次：

```bash
0 */12 * * * cd /path/to/cert-manager && /usr/bin/python3 cert_manager.py --config config.json >> cert_manager.log 2>&1
```

## 配置說明

### 憑證配置

- `domain`: 憑證的域名
- `cert_path`: 憑證檔案路徑（PEM 格式）
- `key_path`: 私鑰檔案路徑（可選）
- `auto_renew`: 是否自動更新（預設：true）

### 更新器配置

- `certbot_path`: Certbot 執行檔路徑（預設：`certbot`）
- `webroot`: Web 根目錄（用於 webroot 驗證方式）
- `email`: 用於 Let's Encrypt 註冊的 Email
- `use_staging`: 是否使用 Let's Encrypt 測試環境（預設：false）
- `save_dir`: 憑證保存目錄（更新後會將憑證複製到此目錄）

### 上傳器配置

配置憑證上傳到遠端機器。**推薦使用獨立的 serverlist 檔案**來管理多台伺服器：

#### 方式 1：使用獨立的 serverlist 檔案（推薦）

在 `config.json` 中：
```json
"uploader": {
  "save_dir": "./certs",
  "serverlist_path": "serverlist.json"
}
```

創建 `serverlist.json`：
```json
{
  "servers": [
    {
      "name": "Web Server 1",
      "host": "server1.example.com",
      "port": 22,
      "username": "root",
      "password": "your-password",
      "remote_path": "/etc/ssl/certs",
      "remote_dir": "your-domain.com",
      "enabled": true
    },
    {
      "name": "Web Server 2",
      "host": "server2.example.com",
      "port": 22,
      "username": "admin",
      "key_file": "~/.ssh/id_rsa",
      "remote_path": "/etc/ssl/certs",
      "remote_dir": "your-domain.com",
      "enabled": true
    },
    {
      "name": "Load Balancer",
      "host": "lb.example.com",
      "port": 22,
      "username": "root",
      "key_file": "~/.ssh/id_rsa",
      "remote_path": "/etc/ssl/certs",
      "remote_dir": "your-domain.com",
      "enabled": false
    }
  ]
}
```

#### 方式 2：在 config.json 中直接配置（向後兼容）

```json
"uploader": {
  "save_dir": "./certs",
  "upload_targets": [
    {
      "host": "server1.example.com",
      "port": 22,
      "username": "root",
      "password": "your-password",
      "remote_path": "/etc/ssl/certs",
      "remote_dir": "your-domain.com"
    }
  ]
}
```

**伺服器配置說明**：
- `name`: 伺服器名稱（可選，用於日誌顯示，便於識別）
- `host`: 遠端機器 IP 或域名（必填）
- `port`: SSH 連接埠（預設：22）
- `username`: SSH 使用者名稱（必填）
- `password`: SSH 密碼（與 `key_file` 二選一）
- `key_file`: SSH 私鑰檔案路徑（與 `password` 二選一，支援 `~` 和相對路徑）
- `remote_path`: 遠端憑證存放路徑（預設：`/etc/ssl/certs`）
- `remote_dir`: 遠端子目錄名稱（預設：使用域名）
- `enabled`: 是否啟用此伺服器（預設：true，設為 false 可暫時停用）

**認證方式**：
- 使用密碼：提供 `password` 欄位
- 使用 SSH 金鑰：提供 `key_file` 欄位（推薦，更安全）

**使用 serverlist 檔案的優點**：
- ✅ 伺服器列表與主配置分離，更易管理
- ✅ 可以輕鬆啟用/停用特定伺服器（使用 `enabled` 欄位）
- ✅ 可以為每台伺服器設定描述性名稱（`name` 欄位）
- ✅ 便於版本控制和協作

### 警報配置

#### 日誌警報
```json
"log": {
  "enabled": true
}
```

#### Email 警報
```json
"email": {
  "enabled": true,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "username": "your-email@gmail.com",
  "password": "your-app-password",
  "from": "your-email@gmail.com",
  "to": ["admin@example.com"]
}
```

**Gmail 設定說明**：
1. 啟用兩步驟驗證
2. 產生應用程式密碼：https://myaccount.google.com/apppasswords
3. 使用應用程式密碼作為 `password`

#### Webhook 警報（例如 Slack）
```json
"webhook": {
  "enabled": true,
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

## 工作流程

1. **檢查階段**：讀取所有配置的憑證，計算到期時間和剩餘天數
2. **更新階段**：如果憑證剩餘天數 ≤ 30 天（可配置），自動執行更新
3. **保存階段**：將更新後的憑證保存到指定資料夾（`save_dir`）
4. **上傳階段**：將憑證上傳到所有配置的遠端機器
5. **警報階段**：如果憑證剩餘天數 ≤ 14 天（可配置），每天發送一次警報

## 日誌

系統會將日誌寫入：
- 檔案：`cert_manager.log`
- 標準輸出：終端機

## 注意事項

1. **權限**：執行 Certbot 更新可能需要 root 權限
2. **Web Server**：使用 standalone 模式時，需要暫時停止 Web Server
3. **DNS 驗證**：如果需要使用 DNS 驗證，需要額外配置 DNS API
4. **備份**：建議定期備份憑證和私鑰
5. **SSH 連接**：確保可以透過 SSH 連接到所有目標機器
6. **憑證權限**：上傳後會自動設定適當的檔案權限（憑證 644，私鑰 600）
7. **安全建議**：建議使用 SSH 金鑰認證而非密碼，並將密碼存放在安全的配置管理系統中

## 故障排除

### 憑證讀取失敗
- 檢查憑證檔案路徑是否正確
- 確認檔案權限
- 確認憑證格式（PEM 或 DER）

### 更新失敗
- 檢查 Certbot 是否正確安裝
- 確認域名 DNS 設定正確
- 檢查 Let's Encrypt 配額（每週每個域名最多 50 次）

### 警報未發送
- 檢查警報配置是否正確
- 查看日誌檔案確認錯誤訊息
- 確認網路連線正常（Webhook）

### 憑證上傳失敗
- 檢查 SSH 連接是否正常（`ssh user@host`）
- 確認認證資訊正確（密碼或 SSH 金鑰）
- 檢查遠端目錄權限
- 查看日誌檔案確認詳細錯誤訊息

## 授權

MIT License

