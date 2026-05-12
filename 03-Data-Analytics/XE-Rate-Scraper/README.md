# XE.com 匯率抓取工具

抓取 [XE.com Activity](https://app.xe.com/activity) 的所有匯率數據。

## 功能特點

### 方式 1: API 方式（推薦 ⭐⭐⭐⭐⭐）
- ✅ **使用免費匯率 API**（無需登入、2FA）
- ✅ 支援多種 API 提供者（ExchangeRate-API, Open Exchange Rates, Fixer）
- ✅ 快速、穩定、可靠
- ✅ 支援 160+ 種貨幣
- ✅ 完全免費（有限制）

### 方式 2: 網頁爬蟲方式
- ✅ 支援 Selenium（處理 JavaScript 渲染的頁面）
- ✅ 支援 requests + BeautifulSoup（輕量級方案）
- ✅ **自動登入功能**（支援多種登入方式）
- ✅ **Cookies 方式**（可處理 2FA）
- ✅ 自動檢測和提取匯率數據

### 通用功能
- ✅ 支援多種輸出格式（JSON、CSV、Excel）
- ✅ 無頭模式執行（可選）

## 安裝

### 1. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 2. 安裝 Chrome 瀏覽器

Selenium 需要 Chrome 瀏覽器。如果未安裝，請先安裝 Chrome。

## 使用方法

### 🎯 推薦方式 1: 公開頁面爬蟲（最簡單 ⭐⭐⭐⭐⭐）

**無需登入、無需 2FA、無需 API Key、完全免費**：

```bash
# 爬取台幣匯率（今天或最新可用）
python3 xe_table_scraper.py

# 爬取指定日期的匯率
python3 xe_table_scraper.py --date 2025-12-28

# 以美元為基準
python3 xe_table_scraper.py --base USD

# 🆕 爬取30天平均匯率（推薦！）
python3 xe_table_scraper.py --days 30

# 只輸出 JSON
python3 xe_table_scraper.py --format json
```

**優點**：
- ✅ 無需任何配置
- ✅ 支援歷史匯率查詢
- ✅ 包含 189+ 種貨幣（包括加密貨幣）
- ✅ 完全免費

**詳細說明**：請參考 [公開頁面爬蟲說明.md](公開頁面爬蟲說明.md)

---

### 🎯 推薦方式 2: 使用 API 方式

**無需登入、無需 2FA、完全免費**：

```bash
# 使用 ExchangeRate-API.com（無需註冊，無需 API Key）
python3 xe_api_scraper.py

# 以台幣為基準
python3 xe_api_scraper.py --base TWD

# 只輸出 JSON
python3 xe_api_scraper.py --format json
```

**詳細說明**：請參考 [API使用說明.md](API使用說明.md)

---

### 網頁爬蟲方式

#### 基本使用

```bash
python xe_scraper.py
```

### 選項說明

```bash
# 不使用 Selenium（僅使用 requests）
python xe_scraper.py --no-selenium

# 顯示瀏覽器視窗（除錯用）
python xe_scraper.py --no-headless

# 指定輸出格式
python xe_scraper.py --format json
python xe_scraper.py --format csv
python xe_scraper.py --format excel
python xe_scraper.py --format all  # 預設：所有格式

# 指定輸出檔案名稱
python xe_scraper.py --output my_rates

# 登入選項（詳見下方「登入功能」）
python xe_scraper.py --email your-email@example.com --password your-password
```

### 登入功能

**⚠️ 重要**：`https://app.xe.com/activity` 需要登入才能訪問。

#### 方法 1: 使用 Cookies（推薦，最可靠）

如果自動登入失敗（例如網站有反爬蟲機制），可以使用手動登入後保存的 cookies：

```bash
# 1. 手動登入並保存 cookies
python3 manual_login_helper.py

# 2. 使用保存的 cookies 執行抓取
python3 xe_scraper.py --use-cookies
```

**優點**：
- ✅ 繞過自動化檢測
- ✅ 可以處理驗證碼
- ✅ 更穩定可靠

#### 方法 2: 自動登入（已改進）

已改進登入邏輯，添加更真實的用戶行為模擬：

```bash
# 使用環境變數
export XE_EMAIL=your-email@example.com
export XE_PASSWORD=your-password
python xe_scraper.py

# 或使用 .env 檔案
cp .env.example .env
# 編輯 .env 填入帳號資訊
python xe_scraper.py

# 或使用命令列參數
python xe_scraper.py --email your-email@example.com --password your-password
```

**改進內容**：
- ✅ 模擬人類輸入（逐字輸入，隨機延遲）
- ✅ 增強反檢測機制
- ✅ 自動檢測驗證碼（非 headless 模式下可手動處理）

**詳細說明請參考**：[登入使用說明.md](登入使用說明.md)

## 輸出檔案

- `xe_rates_YYYYMMDD_HHMMSS.json` - JSON 格式
- `xe_rates_YYYYMMDD_HHMMSS.csv` - CSV 格式
- `xe_rates_YYYYMMDD_HHMMSS.xlsx` - Excel 格式

## 數據格式

每條匯率數據包含：

```json
{
  "currency_pair": "USD/EUR",
  "rate": "0.9234",
  "change": "+0.0012",
  "timestamp": "2025-12-29T10:30:00"
}
```

## 注意事項

### API 方式
- ✅ **推薦使用 API 方式**：更簡單、更穩定、無需登入
- ⚠️ 免費 API 有配額限制（通常足夠個人使用）
- 📝 詳細說明請參考 [API使用說明.md](API使用說明.md)

### 網頁爬蟲方式
1. **需要登入**：`app.xe.com/activity` **必須登入**才能訪問。請使用 `--email` 和 `--password` 參數，或設置環境變數。

2. **登入憑證安全**：
   - 建議使用環境變數或 `.env` 檔案，避免在命令列中直接輸入密碼
   - `.env` 檔案已在 `.gitignore` 中，不會被提交到版本控制

3. **網站結構可能變化**：如果抓取失敗，可能需要：
   - 更新選擇器
   - 檢查網站是否有反爬蟲機制
   - 使用 `--no-headless` 查看實際頁面

4. **登入失敗處理**：
   - 使用 `--no-headless` 查看瀏覽器行為
   - 檢查帳號密碼是否正確
   - 查看控制台輸出的錯誤訊息

3. **速率限制**：請遵守網站的訪問頻率限制，避免過於頻繁的請求

## 故障排除

### 問題：無法抓取數據

**解決方案**：
1. 檢查網路連接
2. 嘗試使用 `--no-headless` 查看瀏覽器行為
3. 檢查網站是否需要登入
4. 查看控制台輸出的錯誤資訊

### 問題：Selenium 初始化失敗

**解決方案**：
1. 確保已安裝 Chrome 瀏覽器
2. 使用 `--no-selenium` 嘗試 requests 方法
3. 檢查 ChromeDriver 版本是否匹配

### 問題：找不到匯率數據

**解決方案**：
1. 網站結構可能已更改，需要更新程式碼
2. 使用瀏覽器開發者工具檢查頁面結構
3. 可能需要等待 JavaScript 載入完成（增加等待時間）

## 開發說明

### 專案結構

```
XE-Rate-Scraper/
├── xe_scraper.py      # 主程式
├── requirements.txt   # 依賴列表
├── README.md          # 說明文件
└── data/              # 輸出目錄（自動創建）
```

### 擴展功能

可以新增以下功能：
- 定時抓取（使用 cron 或 schedule）
- 數據儲存到資料庫
- 匯率變化通知
- 歷史數據對比

## 授權

MIT License

