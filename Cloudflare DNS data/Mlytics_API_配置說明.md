# Mlytics API 配置說明

## 📋 概述

`mlytics_report.py` 腳本用於從 Mlytics 收集域名統計數據，並輸出與 Cloudflare 腳本相同格式的 CSV 文件。

**⚠️ 重要提示**：此腳本需要根據 Mlytics 實際 API 文檔進行調整才能正常運作。

---

## 🔧 配置步驟

### 1. 獲取 Mlytics API 認證資訊

#### 方式 A：API Key + Secret
1. 登入 Mlytics 控制台
2. 前往 API 設定頁面（通常位於「設定」→「API」）
3. 創建新的 API Key 和 Secret
4. 複製 API Key 和 Secret

#### 方式 B：Bearer Token
1. 使用 OAuth 2.0 或其他認證方式獲取 Bearer Token
2. 複製 Token

### 2. 更新腳本配置

打開 `mlytics_report.py`，更新以下配置：

```python
# Mlytics API 基礎 URL（請根據實際 API 文檔更新）
MLYTICS_API_BASE_URL = "https://api.mlytics.com/v1"  # ⚠️ 請更新為實際 URL

# Mlytics 帳戶認證資訊
MLYTICS_API_KEY = "your_api_key_here"  # ⚠️ 請替換為實際 API Key
MLYTICS_API_SECRET = "your_api_secret_here"  # ⚠️ 請替換為實際 API Secret
```

### 3. 調整 API 端點

根據 Mlytics API 文檔，您需要調整以下函數中的 API 端點：

#### 3.1 獲取域名列表 (`get_all_zones`)
```python
# 可能的端點（請根據實際 API 文檔選擇）：
url = f"{MLYTICS_API_BASE_URL}/domains"      # 選項 1
# url = f"{MLYTICS_API_BASE_URL}/zones"      # 選項 2
# url = f"{MLYTICS_API_BASE_URL}/projects/{project_id}/domains"  # 選項 3
```

#### 3.2 獲取域名詳情 (`get_zone_plan`)
```python
url = f"{MLYTICS_API_BASE_URL}/domains/{zone_id}"  # 請根據實際 API 文檔調整
```

#### 3.3 獲取 CDN 流量指標 (`get_zone_metric`)
```python
url = f"{MLYTICS_API_BASE_URL}/domains/{zone_id}/analytics"  # 請根據實際 API 文檔調整
```

#### 3.4 獲取 DNS 查詢數 (`get_dns_query_count`)
```python
url = f"{MLYTICS_API_BASE_URL}/domains/{zone_id}/dns/analytics"  # 請根據實際 API 文檔調整
```

---

## 📊 API 響應格式調整

### 1. 域名列表響應格式

Mlytics API 可能返回以下格式之一：

**格式 A**：
```json
{
  "data": [
    {"id": "123", "name": "example.com", "status": "active"},
    ...
  ],
  "total": 100,
  "has_more": true
}
```

**格式 B**：
```json
{
  "results": [
    {"domain_id": "123", "domain": "example.com"},
    ...
  ]
}
```

**格式 C**（陣列）：
```json
[
  {"id": "123", "domain": "example.com"},
  ...
]
```

請根據實際響應格式調整 `get_all_zones()` 函數中的解析邏輯。

### 2. 域名詳情響應格式

請確認以下欄位的實際路徑：
- 域名 ID：可能是 `id`, `domain_id`, `zone_id`
- 域名名稱：可能是 `name`, `domain`, `domain_name`
- 狀態：可能是 `status`, `state`
- 方案：可能是 `plan`, `tier`, `plan_type`, `features`

### 3. 統計數據響應格式

請確認以下欄位的實際名稱：
- 總流量：可能是 `bytes`, `total_bytes`, `traffic`
- 緩存流量：可能是 `cached_bytes`, `cache_bytes`, `cached_traffic`
- 總請求數：可能是 `requests`, `total_requests`, `hits`
- 緩存請求數：可能是 `cached_requests`, `cache_hits`
- DNS 查詢數：可能是 `query_count`, `queries`, `dns_queries`

---

## 🔐 認證方式調整

### 方式 1：Header 認證（API Key + Secret）

```python
def get_mlytics_headers(account):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": account["api_key"],
        "X-API-Secret": account["api_secret"]
    }
    return headers
```

### 方式 2：Basic Auth

```python
import base64

def get_mlytics_headers(account):
    credentials = f"{account['api_key']}:{account['api_secret']}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded}"
    }
    return headers
```

### 方式 3：Bearer Token

```python
def get_mlytics_headers(account):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {account['bearer_token']}"
    }
    return headers
```

---

## 🧪 測試步驟

1. **測試認證**：
   ```bash
   # 先測試是否能成功認證
   python3 mlytics_report.py
   ```

2. **檢查 API 響應**：
   - 查看錯誤訊息，確認 API 端點是否正確
   - 如果出現 401/403 錯誤，檢查認證方式
   - 如果出現 404 錯誤，檢查 API 端點路徑

3. **調整解析邏輯**：
   - 根據實際 API 響應格式調整解析邏輯
   - 可以添加 `print(json.dumps(data, indent=2))` 來查看實際響應

---

## 📝 輸出格式

腳本會產生與 Cloudflare 腳本相同格式的 CSV：

| 欄位 | 說明 |
|------|------|
| 帳戶 | Mlytics 帳戶 Email 或 ID |
| 域名 | 域名名稱 |
| 狀態 | 域名狀態（active/inactive） |
| 計劃 | 方案類型 |
| 總請求數 | CDN 請求總數 |
| 總流量(MB) | CDN 流量總和（MB） |
| 緩存流量(MB) | CDN 緩存流量總和（MB） |
| 緩存請求數 | CDN 緩存請求總數 |
| DNS查詢數 | DNS 查詢總數 |
| DNS查詢時間範圍 | DNS 查詢的時間範圍 |

---

## ⚠️ 注意事項

1. **API 文檔**：請務必參考 Mlytics 官方 API 文檔進行調整
2. **速率限制**：注意 API 速率限制，腳本已包含重試機制
3. **時間範圍**：確認 Mlytics API 支援的查詢時間範圍
4. **資料完整性**：Mlytics 主要提供 CDN 相關統計，可能與 Cloudflare 的 HTTP 統計範圍不同

---

## 🔗 參考資源

- Mlytics 官方文檔（請替換為實際文檔連結）
- [Mlytics API 文檔](https://docs.mlytics.com/api/)（範例連結）
- Cloudflare 腳本：`cloudflare_report_Global_Key_final (DNS).py`

---

## 📞 需要協助？

如果遇到問題，請檢查：
1. API 認證資訊是否正確
2. API 端點路徑是否正確
3. API 響應格式是否與預期一致
4. 網路連線是否正常
5. 查看錯誤訊息和日誌

