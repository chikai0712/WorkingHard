# Google Cloud DNS 管理工具

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 設定

### 取得服務帳號金鑰

**詳細步驟請參考：[取得服務金鑰指南.md](取得服務金鑰指南.md)**

快速步驟：
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 啟用 Cloud DNS API
3. 建立服務帳號並授予「Cloud DNS Admin」角色
4. 建立並下載 JSON 格式的金鑰檔案
5. 將金鑰檔案放在專案目錄中

### 設定參數

修改 `example.py` 中的參數：
   - `PROJECT_ID`: 你的 GCP 專案 ID
   - `SERVICE_ACCOUNT_KEY`: 服務帳號金鑰檔案的路徑
   - `ZONE_NAME`: 要管理的 Managed Zone 名稱

## 執行方式

### 方式 1: 使用範例腳本

```bash
python example.py
```

### 方式 2: 在 Python 程式中匯入使用

```python
from dns_manager import DnsManager, RecordSet

# 初始化
manager = DnsManager.from_service_account_file(
    project_id="your-project-id",
    key_path="path/to/key.json"
)

# 使用各種功能
zone = manager.ensure_managed_zone({...})
records = manager.list_rrsets("zone-name")
# ... 等等
```

## 功能說明

- `ensure_managed_zone()`: 確保 Managed Zone 存在，不存在則建立
- `list_rrsets()`: 列出指定 zone 的所有 DNS 記錄
- `plan_changes()`: 比較現有記錄與目標記錄，產生變更計劃
- `apply_changes()`: 套用變更並等待完成

