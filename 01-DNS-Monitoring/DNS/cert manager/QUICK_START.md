# 快速開始指南

## 憑證自動更新與上傳功能

本系統支援：
1. ✅ 自動更新 Let's Encrypt 憑證
2. ✅ 將憑證保存到本地資料夾
3. ✅ 自動上傳憑證到多台遠端機器

## 配置步驟

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置檔案範例

編輯 `config.json`：

```json
{
  "alert_threshold_days": 14,
  "renew_threshold_days": 30,
  "certificates": [
    {
      "domain": "example.com",
      "cert_path": "/etc/letsencrypt/live/example.com/fullchain.pem",
      "key_path": "/etc/letsencrypt/live/example.com/privkey.pem",
      "auto_renew": true
    }
  ],
  "renewer": {
    "certbot_path": "certbot",
    "webroot": "/var/www/html",
    "email": "admin@example.com",
    "use_staging": false,
    "save_dir": "./certs"
  },
  "uploader": {
    "save_dir": "./certs",
    "upload_targets": [
      {
        "host": "192.168.1.100",
        "port": 22,
        "username": "root",
        "password": "your-password",
        "remote_path": "/etc/ssl/certs",
        "remote_dir": "example.com"
      },
      {
        "host": "192.168.1.101",
        "port": 22,
        "username": "admin",
        "key_file": "~/.ssh/id_rsa",
        "remote_path": "/etc/ssl/certs",
        "remote_dir": "example.com"
      }
    ]
  },
  "alert_methods": {
    "log": {
      "enabled": true
    }
  }
}
```

### 3. 配置說明

#### 憑證配置
- `domain`: 你的域名
- `cert_path`: Let's Encrypt 憑證路徑
- `key_path`: 私鑰路徑
- `auto_renew`: 是否自動更新

#### 更新器配置
- `save_dir`: 憑證保存目錄（更新後會複製到這裡）
  - 例如：`"./certs"` 或 `"/var/ssl/certs"`

#### 上傳器配置
- `save_dir`: 必須與 renewer 的 save_dir 相同
- `serverlist_path`: 伺服器列表檔案路徑（推薦使用獨立檔案管理）

**方式 1：使用獨立的 serverlist 檔案（推薦）**

在 `config.json` 中：
```json
{
  "uploader": {
    "save_dir": "./certs",
    "serverlist_path": "serverlist.json"
  }
}
```

然後創建 `serverlist.json`：
```json
{
  "servers": [
    {
      "name": "Web Server 1",
      "host": "192.168.1.100",
      "port": 22,
      "username": "root",
      "password": "your-password",
      "remote_path": "/etc/ssl/certs",
      "remote_dir": "example.com",
      "enabled": true
    },
    {
      "name": "Web Server 2",
      "host": "192.168.1.101",
      "port": 22,
      "username": "admin",
      "key_file": "~/.ssh/id_rsa",
      "remote_path": "/etc/ssl/certs",
      "remote_dir": "example.com",
      "enabled": true
    }
  ]
}
```

**方式 2：在 config.json 中直接配置（向後兼容）**

```json
{
  "uploader": {
    "save_dir": "./certs",
    "upload_targets": [
      {
        "host": "192.168.1.100",
        "port": 22,
        "username": "root",
        "password": "your-password",
        "remote_path": "/etc/ssl/certs",
        "remote_dir": "example.com"
      }
    ]
  }
}
```

**伺服器配置欄位說明：**
- `name`: 伺服器名稱（可選，用於日誌顯示）
- `host`: 遠端機器 IP 或域名
- `port`: SSH 埠（預設 22）
- `username`: SSH 使用者名稱
- `password`: SSH 密碼（或使用 `key_file`）
- `key_file`: SSH 私鑰路徑（推薦，支援 ~ 和相對路徑）
- `remote_path`: 遠端存放路徑
- `remote_dir`: 遠端子目錄名稱
- `enabled`: 是否啟用此伺服器（預設 true）

### 4. 測試配置

```bash
# 測試憑證檢查
python3 cert_manager.py --config config.json --check-only

# 執行完整流程（檢查、更新、上傳）
python3 cert_manager.py --config config.json
```

## 工作流程

1. **檢查憑證**：讀取憑證並計算到期時間
2. **判斷是否需要更新**：如果剩餘 ≤ 30 天，執行更新
3. **更新憑證**：使用 Certbot 更新 Let's Encrypt 憑證
4. **保存憑證**：將新憑證複製到 `save_dir` 目錄
5. **上傳憑證**：將憑證上傳到所有配置的遠端機器
6. **發送警報**：如果剩餘 ≤ 14 天，發送警報

## 憑證檔案結構

更新後，憑證會保存在以下結構：

```
save_dir/
└── example.com/
    ├── fullchain.pem  (完整憑證鏈)
    ├── privkey.pem    (私鑰)
    ├── chain.pem      (中間憑證)
    └── cert.pem       (憑證)
```

這些檔案會自動上傳到遠端機器的 `remote_path/remote_dir/` 目錄。

## SSH 認證方式

### 方式 1：使用密碼（不推薦）

```json
{
  "host": "192.168.1.100",
  "username": "root",
  "password": "your-password"
}
```

### 方式 2：使用 SSH 金鑰（推薦）

```json
{
  "host": "192.168.1.100",
  "username": "root",
  "key_file": "~/.ssh/id_rsa"
}
```

**設定 SSH 金鑰**：
```bash
# 產生 SSH 金鑰（如果還沒有）
ssh-keygen -t rsa -b 4096

# 複製公鑰到遠端機器
ssh-copy-id user@host
```

## 設定定期執行

### 使用 Cron（Linux/macOS）

```bash
# 編輯 crontab
crontab -e

# 每天凌晨 2 點執行
0 2 * * * cd /path/to/cert-manager && python3 cert_manager.py --config config.json >> logs/cert_manager.log 2>&1
```

### 使用 systemd timer（Linux）

建立 `/etc/systemd/system/cert-manager.service`：
```ini
[Unit]
Description=SSL Certificate Manager
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/path/to/cert-manager
ExecStart=/usr/bin/python3 cert_manager.py --config config.json
```

建立 `/etc/systemd/system/cert-manager.timer`：
```ini
[Unit]
Description=Run SSL Certificate Manager daily
Requires=cert-manager.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

啟用：
```bash
sudo systemctl enable cert-manager.timer
sudo systemctl start cert-manager.timer
```

## 故障排除

### 憑證更新失敗
- 檢查 Certbot 是否正確安裝
- 確認域名 DNS 設定正確
- 檢查 Let's Encrypt 配額

### 上傳失敗
- 測試 SSH 連接：`ssh user@host`
- 檢查認證資訊（密碼或金鑰）
- 確認遠端目錄權限
- 查看日誌檔案

### 權限問題
- 執行 Certbot 可能需要 root 權限
- 確保有寫入 `save_dir` 的權限
- 確保 SSH 金鑰有正確的權限（600）

## 安全建議

1. **使用 SSH 金鑰而非密碼**
2. **保護配置檔案**：`chmod 600 config.json`
3. **使用環境變數**：將敏感資訊放在環境變數中
4. **定期備份**：備份憑證和私鑰
5. **監控日誌**：定期檢查日誌檔案

## 範例：多域名配置

```json
{
  "certificates": [
    {
      "domain": "example.com",
      "cert_path": "/etc/letsencrypt/live/example.com/fullchain.pem",
      "key_path": "/etc/letsencrypt/live/example.com/privkey.pem",
      "auto_renew": true
    },
    {
      "domain": "www.example.com",
      "cert_path": "/etc/letsencrypt/live/www.example.com/fullchain.pem",
      "key_path": "/etc/letsencrypt/live/www.example.com/privkey.pem",
      "auto_renew": true
    }
  ],
  "uploader": {
    "upload_targets": [
      {
        "host": "web1.example.com",
        "username": "root",
        "key_file": "~/.ssh/id_rsa",
        "remote_path": "/etc/ssl/certs"
      },
      {
        "host": "web2.example.com",
        "username": "root",
        "key_file": "~/.ssh/id_rsa",
        "remote_path": "/etc/ssl/certs"
      }
    ]
  }
}
```

每個域名的憑證會自動上傳到所有配置的機器。

