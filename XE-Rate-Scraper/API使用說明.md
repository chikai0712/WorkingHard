# 匯率 API 使用說明

## 🎯 為什麼使用 API？

相比網頁爬蟲，使用 API 有以下優點：

- ✅ **更穩定**：不需要處理登入、2FA、反爬蟲等問題
- ✅ **更快速**：直接獲取數據，無需等待頁面載入
- ✅ **更可靠**：官方 API 通常有更好的穩定性
- ✅ **更簡單**：無需處理複雜的網頁結構
- ✅ **更合規**：使用官方 API 符合服務條款

---

## 🚀 快速開始

### 方法 1: ExchangeRate-API.com（推薦，無需註冊）

**最簡單的方式，完全免費，無需 API Key**：

```bash
python3 xe_api_scraper.py --provider exchangerate-api --base USD
```

**特點**：
- ✅ 無需註冊
- ✅ 無需 API Key
- ✅ 每月 1,500 次免費請求
- ✅ 支援 160+ 種貨幣

### 方法 2: Open Exchange Rates（需要註冊）

**免費配額：每月 1,000 次請求**：

1. **註冊並獲取 API Key**：
   - 訪問：https://openexchangerates.org/
   - 註冊免費帳號
   - 獲取 API Key

2. **設置 API Key**：
   ```bash
   export EXCHANGE_RATE_API_KEY=your-api-key-here
   ```

3. **使用**：
   ```bash
   python3 xe_api_scraper.py --provider openexchangerates --base USD
   ```

### 方法 3: Fixer.io（需要註冊）

**免費配額：每月 100 次請求**：

1. **註冊並獲取 API Key**：
   - 訪問：https://fixer.io/
   - 註冊免費帳號
   - 獲取 API Key

2. **使用**：
   ```bash
   python3 xe_api_scraper.py --provider fixer --api-key your-api-key --base USD
   ```

---

## 📋 完整參數說明

```bash
python3 xe_api_scraper.py [選項]

選項：
  --provider {exchangerate-api,openexchangerates,fixer}
                        選擇 API 提供者（預設：exchangerate-api）
  
  --api-key API_KEY      API Key（Open Exchange Rates 和 Fixer 需要）
  
  --base BASE           基準貨幣（預設：USD）
                        例如：USD, EUR, GBP, TWD, JPY 等
  
  --format {json,csv,excel,all}
                        輸出格式（預設：all）
  
  --output OUTPUT       輸出檔案名稱（不含副檔名）
```

---

## 💡 使用範例

### 範例 1: 獲取美元匯率（最簡單）

```bash
python3 xe_api_scraper.py
```

### 範例 2: 以台幣為基準

```bash
python3 xe_api_scraper.py --base TWD
```

### 範例 3: 只輸出 JSON

```bash
python3 xe_api_scraper.py --format json
```

### 範例 4: 指定輸出檔案名稱

```bash
python3 xe_api_scraper.py --output my_rates
```

### 範例 5: 使用 Open Exchange Rates

```bash
export EXCHANGE_RATE_API_KEY=your-key
python3 xe_api_scraper.py --provider openexchangerates
```

---

## 📊 輸出格式

### JSON 格式

```json
{
  "base": "USD",
  "date": "2025-12-29",
  "rates": {
    "EUR": 0.9234,
    "GBP": 0.7891,
    "TWD": 31.234,
    ...
  },
  "timestamp": "2025-12-29T10:30:00",
  "source": "ExchangeRate-API.com"
}
```

### CSV 格式

```csv
base_currency,target_currency,rate,date,timestamp,source
USD,EUR,0.9234,2025-12-29,2025-12-29T10:30:00,ExchangeRate-API.com
USD,GBP,0.7891,2025-12-29,2025-12-29T10:30:00,ExchangeRate-API.com
...
```

### Excel 格式

與 CSV 相同，但以 Excel 格式保存。

---

## 🔄 與網頁爬蟲的比較

| 特性 | API 方式 | 網頁爬蟲方式 |
|------|---------|-------------|
| 穩定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 複雜度 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 成本 | 免費（有限制） | 免費 |
| 合規性 | ✅ 完全合規 | ⚠️ 需注意 |
| 需要登入 | ❌ 不需要 | ✅ 需要 |
| 需要 2FA | ❌ 不需要 | ✅ 需要 |

---

## 🎯 建議

### 如果您需要：

1. **簡單快速獲取匯率** → 使用 ExchangeRate-API.com（無需註冊）
2. **更多免費配額** → 註冊 Open Exchange Rates（1,000/月）
3. **特定貨幣對** → 使用 API 方式更簡單
4. **定期自動化** → API 方式更穩定可靠

### 如果 API 配額不足：

- 可以結合使用多個 API
- 或考慮付費方案
- 或回到網頁爬蟲方式（使用 Cookies）

---

## 📝 注意事項

1. **API 配額限制**：
   - ExchangeRate-API.com: 1,500/月（無需註冊）
   - Open Exchange Rates: 1,000/月（需註冊）
   - Fixer.io: 100/月（需註冊）

2. **數據更新頻率**：
   - 大多數 API 每小時或每天更新
   - 如果需要即時數據，可能需要付費方案

3. **貨幣支援**：
   - 不同 API 支援的貨幣數量不同
   - ExchangeRate-API.com: 160+
   - Open Exchange Rates: 200+

---

## 🔧 故障排除

### 問題：API 請求失敗

**解決方案**：
- 檢查網路連接
- 確認 API Key 正確（如果需要）
- 檢查 API 配額是否用盡

### 問題：找不到某些貨幣

**解決方案**：
- 確認該 API 支援該貨幣
- 嘗試使用其他 API 提供者
- 檢查貨幣代碼是否正確（例如：TWD 不是 TWD$）

---

## 📚 相關文檔

- [xe_api_research.md](xe_api_research.md) - API 研究報告
- [README.md](README.md) - 主文檔

---

**最後更新**: 2025-12-29

