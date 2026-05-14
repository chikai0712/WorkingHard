# TWSE 即時 API 整合說明

## 📋 概述

已整合台灣證券交易所 (TWSE) 的即時行情 API，提供約 **20 秒延遲**的即時交易資料（相比 yfinance 的 15-20 分鐘延遲大幅改善）。

---

## ✅ 已實作功能

### 1. TWSE 即時 API 客戶端

**檔案**: `backend/crawler/twse_realtime.py`

**功能**:
- ✅ 取得單一股票即時行情
- ✅ 取得多檔股票即時行情
- ✅ 取得每日收盤行情
- ✅ 自動解析和格式化資料

**API 端點**:
- 即時行情: `https://www.twse.com.tw/rwd/zh/realtimeTrading/STOCK_DAY`
- 每日行情: `https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY`

---

### 2. 整合到 StockCrawler

**檔案**: `backend/crawler/stock_crawler.py`

**變更**:
- ✅ 新增 `use_realtime` 參數
- ✅ 支援 TWSE 即時 API 和 yfinance 兩種資料來源
- ✅ 自動回退機制（TWSE 失敗時使用 yfinance）

---

### 3. 定時任務支援

**檔案**: `backend/scheduler/tasks.py`

**變更**:
- ✅ 支援透過環境變數切換資料來源
- ✅ 自動選擇最佳資料來源

---

## 🔧 配置方式

### 方法一：使用環境變數（推薦）

在 `backend/.env` 文件中設定：

```env
# 使用 TWSE 即時 API（約 20 秒延遲）
USE_TWSE_REALTIME=True

# 或使用 yfinance（15-20 分鐘延遲）
USE_TWSE_REALTIME=False
```

**預設值**: `False`（使用 yfinance）

---

### 方法二：程式碼中指定

```python
from crawler.stock_crawler import StockCrawler

# 使用 TWSE 即時 API
crawler = StockCrawler(db, use_realtime=True)

# 使用 yfinance
crawler = StockCrawler(db, use_realtime=False)
```

---

## 📊 資料來源比較

| 特性 | TWSE API | yfinance |
|------|----------|----------|
| **延遲時間** | 約 20 秒 | 15-20 分鐘 |
| **資料來源** | 台灣證交所官方 | Yahoo Finance |
| **穩定性** | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **支援市場** | 僅台股 | 全球股市 |
| **歷史資料** | 有限 | 完整 |
| **費用** | 免費 | 免費 |
| **速率限制** | 有（需控制請求頻率） | 有 |

---

## 🚀 使用範例

### 1. 測試 TWSE 即時 API

```bash
cd backend
source venv/bin/activate
python scripts/test_twse_realtime.py
```

### 2. 使用即時 API 更新股票

```python
from database.session import SessionLocal
from crawler.stock_crawler import StockCrawler

db = SessionLocal()
crawler = StockCrawler(db, use_realtime=True)  # 使用即時 API
results = crawler.update_all_stocks()
```

### 3. 手動更新（使用即時 API）

在 `backend/.env` 中設定：
```env
USE_TWSE_REALTIME=True
```

然後執行：
```bash
cd backend
python scripts/update_all.py
```

---

## 📝 API 回應格式

### 即時行情資料結構

```python
{
    'symbol': '2330',
    'date': date(2025, 12, 22),
    'timestamp': datetime(2025, 12, 22, 14, 30, 0),
    'open': 580.0,
    'high': 585.0,
    'low': 578.0,
    'close': 582.0,
    'volume': 15000000,  # 成交股數
    'turnover': 8730000000,  # 成交金額
    'change': 2.0,
    'change_percent': 0.34,
    'transaction_count': 15000  # 成交筆數
}
```

---

## ⚠️ 注意事項

### 1. 速率限制

TWSE API 有請求頻率限制，建議：
- 單一請求之間間隔至少 **0.5 秒**
- 避免過於頻繁的請求
- 程式碼中已內建延遲機制

### 2. 交易時間

- 即時資料僅在交易時間內（09:00-13:30）可用
- 非交易時間可能無法取得資料
- 系統會自動回退到每日行情 API

### 3. 錯誤處理

- 如果 TWSE API 失敗，系統會自動回退到 yfinance
- 確保系統在兩種資料來源之間可以無縫切換

### 4. 資料格式

- TWSE API 返回的資料格式與 yfinance 不同
- 系統已自動轉換為統一格式
- 確保與現有資料庫結構相容

---

## 🧪 測試

### 測試腳本

執行測試腳本驗證 API 功能：

```bash
cd backend
python scripts/test_twse_realtime.py
```

**測試項目**:
1. ✅ 單一股票即時行情
2. ✅ 每日行情
3. ✅ 多檔股票批次查詢

---

## 🔄 切換資料來源

### 從 yfinance 切換到 TWSE 即時 API

1. 編輯 `backend/.env`:
   ```env
   USE_TWSE_REALTIME=True
   ```

2. 重啟後端服務:
   ```bash
   ./stop.sh
   ./start.sh
   ```

3. 或手動更新測試:
   ```bash
   cd backend
   source venv/bin/activate
   python scripts/update_all.py
   ```

### 從 TWSE 切換回 yfinance

1. 編輯 `backend/.env`:
   ```env
   USE_TWSE_REALTIME=False
   ```

2. 重啟服務

---

## 📊 效能建議

### 最佳實踐

1. **交易時間使用 TWSE 即時 API**
   - 延遲較短（約 20 秒）
   - 資料較即時

2. **非交易時間或歷史資料使用 yfinance**
   - 歷史資料較完整
   - 不需要即時性

3. **混合使用**
   - 可以在程式碼中根據時間自動切換
   - 交易時間用 TWSE，其他時間用 yfinance

---

## 🐛 故障排除

### 問題 1: 無法取得即時資料

**可能原因**:
- 非交易時間
- 網路連線問題
- API 端點變更

**解決方法**:
- 檢查是否在交易時間內
- 檢查網路連線
- 查看錯誤訊息

### 問題 2: 資料格式錯誤

**可能原因**:
- TWSE API 回應格式變更
- 欄位名稱不匹配

**解決方法**:
- 檢查 `twse_realtime.py` 中的欄位映射
- 根據實際 API 回應調整解析邏輯

### 問題 3: 請求被限制

**可能原因**:
- 請求過於頻繁

**解決方法**:
- 增加請求間隔時間
- 減少同時請求的股票數量

---

## 📚 參考資源

1. **TWSE API 文件**:
   - https://www.twse.com.tw/rwd/zh/apiInfo

2. **API 端點**:
   - 即時行情: `/rwd/zh/realtimeTrading/STOCK_DAY`
   - 每日行情: `/rwd/zh/afterTrading/STOCK_DAY`

---

## ✅ 整合檢查清單

- [x] 創建 TWSE 即時 API 客戶端
- [x] 整合到 StockCrawler
- [x] 支援環境變數配置
- [x] 實作自動回退機制
- [x] 創建測試腳本
- [x] 更新定時任務支援
- [ ] 生產環境測試
- [ ] 效能優化

---

**最後更新**: 2025-12-22  
**版本**: v1.0

