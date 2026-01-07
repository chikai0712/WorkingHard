# 憑證功能驗證指南

本指南說明如何驗證 SSL 憑證管理器的各項功能。

## 快速驗證

### 方法 1: 快速測試（不依賴外部套件）

適合快速檢查配置檔案格式：

```bash
# 基本測試（僅檢查配置格式）
python quick_test.py

# 指定配置檔案
python quick_test.py config.json

# 包含憑證檔案檢查
python quick_test.py config.json /path/to/cert.pem
```

### 方法 2: 完整驗證（需要安裝依賴）

需要先安裝依賴套件：

```bash
pip install -r requirements.txt
```

然後執行完整驗證：

```bash
# 基本驗證（使用 config.json）
python verify_cert.py

# 指定配置檔案
python verify_cert.py config.json

# 包含憑證讀取測試
python verify_cert.py config.json /path/to/cert.pem

# 創建測試憑證並驗證
python verify_cert.py config.json --create-test-cert
```

## 驗證項目

驗證腳本會檢查以下項目：

### 1. 憑證讀取與解析
- ✅ 驗證能否正確讀取 PEM 格式憑證
- ✅ 驗證能否正確解析到期時間
- ✅ 驗證剩餘天數計算是否正確

**測試方法：**
```bash
# 使用現有憑證
python verify_cert.py config.json /etc/letsencrypt/live/example.com/fullchain.pem

# 或創建測試憑證
python verify_cert.py config.json --create-test-cert
```

### 2. 配置檔案載入
- ✅ 驗證 JSON 格式是否正確
- ✅ 驗證必要欄位是否存在
- ✅ 驗證 CertificateManager 能否正確初始化

**測試方法：**
```bash
python verify_cert.py config.json
```

### 3. 伺服器列表載入
- ✅ 驗證 serverlist.json 是否存在
- ✅ 驗證伺服器配置格式是否正確
- ✅ 驗證 CertificateUploader 能否正確初始化

**檢查項目：**
- `serverlist_path` 是否正確設定
- 伺服器列表檔案是否存在
- 每個伺服器的必要欄位是否完整

### 4. 憑證檢查功能
- ✅ 驗證所有配置的憑證能否正確讀取
- ✅ 驗證到期時間計算是否正確
- ✅ 驗證更新/警報判斷邏輯是否正確

**測試方法：**
```bash
python verify_cert.py config.json
```

### 5. 更新器配置
- ✅ 驗證 Certbot 路徑是否正確
- ✅ 驗證 Certbot 是否已安裝
- ✅ 驗證 CertificateRenewer 能否正確初始化

**檢查項目：**
- `certbot_path` 是否指向正確的可執行檔
- `email` 是否設定
- `save_dir` 是否存在或可創建

### 6. 警報系統配置
- ✅ 驗證警報方式配置是否正確
- ✅ 驗證 AlertManager 能否正確初始化

**檢查項目：**
- 至少一種警報方式已啟用
- Email 警報需要完整的 SMTP 設定
- Webhook 警報需要有效的 URL

## 手動驗證步驟

### 步驟 1: 驗證憑證讀取

```python
from cert_manager import CertificateInfo

# 測試憑證讀取
cert_info = CertificateInfo(
    domain="example.com",
    cert_path="/path/to/cert.pem",
    auto_renew=True
)

print(f"到期日期: {cert_info.expiry_date}")
print(f"剩餘天數: {cert_info.days_remaining}")
```

### 步驟 2: 驗證配置載入

```python
from cert_manager import CertificateManager

# 載入配置
manager = CertificateManager("config.json")

print(f"憑證數量: {len(manager.certificates)}")
print(f"警報閾值: {manager.alert_threshold} 天")
print(f"更新閾值: {manager.renew_threshold} 天")
```

### 步驟 3: 驗證伺服器列表

```python
import json

# 讀取伺服器列表
with open("serverlist.json", 'r') as f:
    serverlist = json.load(f)

print(f"伺服器數量: {len(serverlist['servers'])}")
for server in serverlist['servers']:
    print(f"  - {server.get('name', 'Unnamed')}: {server['host']}")
```

### 步驟 4: 執行完整檢查

```bash
# 僅檢查，不更新
python cert_manager.py --config config.json --check-only

# 完整執行（檢查 + 更新）
python cert_manager.py --config config.json
```

## 創建測試憑證

如果需要測試憑證讀取功能，可以創建一個自簽名憑證：

```bash
# 使用 openssl 創建測試憑證（有效期 365 天）
openssl req -x509 -newkey rsa:2048 \
  -keyout /tmp/test.key \
  -out /tmp/test.pem \
  -days 365 \
  -nodes \
  -subj '/CN=test.example.com/O=Test/C=TW'

# 使用驗證腳本測試
python verify_cert.py config.json /tmp/test.pem
```

或使用驗證腳本自動創建：

```bash
python verify_cert.py config.json --create-test-cert
```

## 常見問題排查

### 問題 1: 憑證讀取失敗

**錯誤訊息：** `無法讀取憑證`

**解決方法：**
1. 檢查憑證檔案路徑是否正確
2. 確認檔案權限（需要讀取權限）
3. 確認憑證格式（PEM 或 DER）
4. 使用 `openssl x509 -in cert.pem -text -noout` 驗證憑證格式

### 問題 2: 配置檔案載入失敗

**錯誤訊息：** `JSON 格式錯誤`

**解決方法：**
1. 使用 JSON 驗證工具檢查格式：`python -m json.tool config.json`
2. 檢查是否有遺漏的逗號或括號
3. 確認所有字串都有引號

### 問題 3: 伺服器列表載入失敗

**錯誤訊息：** `伺服器列表檔案不存在`

**解決方法：**
1. 確認 `serverlist_path` 路徑是否正確
2. 檢查路徑是相對路徑還是絕對路徑
3. 確認檔案是否存在：`ls -l serverlist.json`

### 問題 4: Certbot 未找到

**錯誤訊息：** `Certbot 可執行檔不存在`

**解決方法：**
1. 安裝 Certbot：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install certbot
   
   # macOS
   brew install certbot
   ```
2. 確認路徑：`which certbot`
3. 在配置中指定完整路徑：`/usr/bin/certbot`

### 問題 5: 憑證檢查時找不到憑證

**錯誤訊息：** `無法讀取憑證: example.com`

**解決方法：**
1. 檢查 `config.json` 中的 `cert_path` 是否正確
2. 確認憑證檔案存在：`ls -l /path/to/cert.pem`
3. 檢查檔案權限

## 測試環境建議

### 開發環境測試

1. **使用測試憑證：**
   ```bash
   # 創建短期測試憑證（30 天）
   openssl req -x509 -newkey rsa:2048 \
     -keyout test.key -out test.pem \
     -days 30 -nodes \
     -subj '/CN=test.example.com'
   ```

2. **使用 Let's Encrypt 測試環境：**
   在 `config.json` 中設定：
   ```json
   {
     "renewer": {
       "use_staging": true
     }
   }
   ```

3. **測試警報功能：**
   創建一個即將到期的測試憑證（剩餘 10 天），驗證警報是否正常觸發。

### 生產環境驗證

1. **先使用 `--check-only` 模式：**
   ```bash
   python cert_manager.py --config config.json --check-only
   ```

2. **檢查日誌輸出：**
   ```bash
   tail -f cert_manager.log
   ```

3. **驗證憑證上傳（可選）：**
   在 `serverlist.json` 中先設定一台測試伺服器，驗證上傳功能。

## 驗證檢查清單

在部署到生產環境前，請確認：

- [ ] 所有配置檔案格式正確
- [ ] 所有憑證檔案路徑正確且可讀取
- [ ] Certbot 已安裝且可執行
- [ ] 伺服器列表配置正確
- [ ] SSH 連接測試成功（如果使用上傳功能）
- [ ] 警報系統配置正確（至少一種方式啟用）
- [ ] 日誌檔案可正常寫入
- [ ] 使用 `--check-only` 模式測試通過
- [ ] 驗證腳本所有測試通過

## 進階測試

### 測試憑證更新流程

```bash
# 1. 創建一個即將到期的測試憑證
# 2. 配置自動更新
# 3. 執行更新
python cert_manager.py --config config.json

# 4. 驗證憑證是否已更新
python verify_cert.py config.json /path/to/updated/cert.pem
```

### 測試憑證上傳

```python
from cert_manager import CertificateUploader
import json

# 載入配置
with open('config.json', 'r') as f:
    config = json.load(f)

uploader = CertificateUploader(config['uploader'])

# 測試上傳（使用測試憑證）
uploader.upload_certificate(
    domain="test.example.com",
    cert_path="/tmp/test.pem",
    key_path="/tmp/test.key"
)
```

### 測試警報發送

```python
from cert_manager import AlertManager, CertificateInfo
import json

# 載入配置
with open('config.json', 'r') as f:
    config = json.load(f)

# 創建測試憑證資訊（剩餘 10 天）
cert_info = CertificateInfo(
    domain="test.example.com",
    cert_path="/tmp/test.pem",
    days_remaining=10
)

# 發送警報
alert_manager = AlertManager(config)
alert_manager.send_alert(cert_info, "測試警報訊息")
```

## 相關檔案

- `verify_cert.py` - 自動驗證腳本
- `test_cert_manager.py` - 單元測試腳本
- `cert_manager.py` - 主程式
- `config.example.json` - 配置範例
- `serverlist.example.json` - 伺服器列表範例

## 取得幫助

如果遇到問題：

1. 查看日誌檔案：`cert_manager.log`
2. 執行驗證腳本：`python verify_cert.py config.json`
3. 檢查配置檔案格式：`python -m json.tool config.json`
4. 查看 README.md 了解詳細配置說明

