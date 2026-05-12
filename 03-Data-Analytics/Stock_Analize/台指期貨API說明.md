# 台指期貨 API 說明

## 📡 API 端點總覽

所有期貨相關 API 的前綴為 `/api/futures`

---

## 1. 期貨每日交易資料

### `GET /api/futures/daily`

取得期貨每日交易資料（包含價格、成交量、未平倉量等）

**查詢參數**:
- `symbol` (string, 預設: "TX"): 期貨代號
  - `TX` = 台指期貨
  - `MTX` = 小型台指期貨
- `start_date` (date, 可選): 開始日期 (YYYY-MM-DD)
- `end_date` (date, 可選): 結束日期 (YYYY-MM-DD)
- `limit` (int, 預設: 30): 限制筆數 (1-365)

**回應範例**:
```json
{
  "status": "success",
  "symbol": "TX",
  "data": [
    {
      "date": "2025-12-18",
      "contract_code": "202512F3",
      "open": 27447.45,
      "high": 27569.44,
      "low": 27350.77,
      "close": 27469.0,
      "settlement": 27469.0,
      "change": -56.64,
      "change_percent": -0.21,
      "volume": 123456,
      "open_interest": 987654
    }
  ],
  "total": 1
}
```

---

## 2. 三大法人買賣超

### `GET /api/futures/institutional`

取得三大法人（外資、投信、自營商）買賣超資料

**查詢參數**:
- `market_type` (string, 預設: "weighted"): 市場類型
  - `weighted` = 加權指數
  - `otc` = 櫃買指數
- `start_date` (date, 可選): 開始日期
- `end_date` (date, 可選): 結束日期
- `limit` (int, 預設: 30): 限制筆數

**回應範例**:
```json
{
  "status": "success",
  "market_type": "weighted",
  "data": [
    {
      "date": "2025-12-18",
      "market_type": "weighted",
      "foreign": {
        "buy": 1581.05,
        "sell": 1849.46,
        "net": -268.41
      },
      "trust": {
        "buy": 216.33,
        "sell": 178.86,
        "net": 37.47
      },
      "dealer": {
        "buy": 292.18,
        "sell": 220.83,
        "net": 71.35,
        "self_buy": 132.94,
        "self_sell": 31.46,
        "self_net": 101.48,
        "hedge_buy": 159.24,
        "hedge_sell": 189.37,
        "hedge_net": -30.13
      },
      "total_net": -159.60
    }
  ],
  "total": 1
}
```

---

## 3. 期貨未平倉量

### `GET /api/futures/open-interest`

取得期貨未平倉量資料（包含三大法人、十大交易人、散戶）

**查詢參數**:
- `symbol` (string, 預設: "TX"): 期貨代號
- `start_date` (date, 可選): 開始日期
- `end_date` (date, 可選): 結束日期
- `limit` (int, 預設: 30): 限制筆數

**回應範例**:
```json
{
  "status": "success",
  "symbol": "TX",
  "data": [
    {
      "date": "2025-12-18",
      "foreign": {
        "oi": -28731,
        "oi_change": 301
      },
      "trust": {
        "oi": 25526,
        "oi_change": 346
      },
      "dealer": {
        "oi": -1344,
        "oi_change": -1265
      },
      "top5": {
        "oi": -4249,
        "oi_change": 1029
      },
      "top10": {
        "oi": -3220,
        "oi_change": null
      },
      "top5_special": {
        "oi": -5546,
        "oi_change": 5546
      },
      "top10_special": {
        "oi": 0,
        "oi_change": null
      },
      "retail": {
        "oi": 12274,
        "oi_change": -2921
      }
    }
  ],
  "total": 1
}
```

---

## 4. 融資融券餘額

### `GET /api/futures/margin-trading`

取得融資融券餘額資料

**查詢參數**:
- `market_type` (string, 預設: "weighted"): 市場類型
  - `weighted` = 加權指數
  - `otc` = 櫃買指數
- `start_date` (date, 可選): 開始日期
- `end_date` (date, 可選): 結束日期
- `limit` (int, 預設: 30): 限制筆數

**回應範例**:
```json
{
  "status": "success",
  "market_type": "weighted",
  "data": [
    {
      "date": "2025-12-18",
      "market_type": "weighted",
      "margin": {
        "balance": 3323.8,
        "change": 2.1
      },
      "short_selling": {
        "balance": 300546,
        "change": -1484
      },
      "securities_lending": {
        "sell": 1424344,
        "change": 8547
      },
      "index": {
        "price": 27468.53,
        "change_percent": -0.21
      }
    }
  ],
  "total": 1
}
```

---

## 5. 選擇權未平倉量

### `GET /api/futures/options/open-interest`

取得選擇權未平倉量資料

**查詢參數**:
- `period` (string, 預設: "monthly"): 期間類型
  - `weekly` = 周選擇權
  - `monthly` = 月選擇權
- `start_date` (date, 可選): 開始日期
- `end_date` (date, 可選): 結束日期
- `limit` (int, 預設: 30): 限制筆數

---

## 6. 選擇權履約價分布

### `GET /api/futures/options/strike-data`

取得選擇權各履約價的買權OI和賣權OI分布（用於繪製選擇權分布圖）

**查詢參數**:
- `period` (string, 預設: "weekly"): 期間類型
  - `weekly` = 周選擇權
  - `monthly` = 月選擇權
- `contract_code` (string, 可選): 合約代號 (如: 202512F3)
- `target_date` (date, 可選): 目標日期 (YYYY-MM-DD)，預設為今天
- `strike_range` (string, 可選): 履約價範圍 (例如: 26800-28400)

**回應範例**:
```json
{
  "status": "success",
  "date": "2025-12-18",
  "contract_code": "202512F3",
  "contract_period": "weekly",
  "index_price": 27469.0,
  "strike_data": [
    {
      "strike_price": 26800,
      "call": {
        "oi": 2,
        "oi_change": 2,
        "volume": 0
      },
      "put": {
        "oi": 2307,
        "oi_change": 1176,
        "volume": 0
      }
    },
    {
      "strike_price": 27000,
      "call": {
        "oi": 25,
        "oi_change": 20,
        "volume": 0
      },
      "put": {
        "oi": 3803,
        "oi_change": 2554,
        "volume": 0
      }
    },
    {
      "strike_price": 28200,
      "call": {
        "oi": 10873,
        "oi_change": 9753,
        "volume": 0
      },
      "put": {
        "oi": 94,
        "oi_change": 39,
        "volume": 0
      }
    }
  ],
  "total": 35
}
```

---

## 7. 選擇權每日交易資料

### `GET /api/futures/options/daily`

取得選擇權每日交易資料（歷史）

**查詢參數**:
- `period` (string, 預設: "monthly"): 期間類型
- `start_date` (date, 可選): 開始日期
- `end_date` (date, 可選): 結束日期
- `limit` (int, 預設: 30): 限制筆數

---

## 📚 使用範例

### 使用 curl

```bash
# 取得期貨每日資料
curl "http://localhost:8000/api/futures/daily?symbol=TX&limit=10"

# 取得三大法人買賣超
curl "http://localhost:8000/api/futures/institutional?market_type=weighted&limit=30"

# 取得選擇權履約價分布（周選擇權）
curl "http://localhost:8000/api/futures/options/strike-data?period=weekly&target_date=2025-12-18"

# 取得融資融券餘額
curl "http://localhost:8000/api/futures/margin-trading?market_type=weighted&limit=30"
```

### 使用 JavaScript (Axios)

```javascript
import axios from 'axios';

// 取得期貨每日資料
const response = await axios.get('/api/futures/daily', {
  params: {
    symbol: 'TX',
    limit: 10
  }
});

// 取得選擇權履約價分布
const strikeData = await axios.get('/api/futures/options/strike-data', {
  params: {
    period: 'weekly',
    target_date: '2025-12-18'
  }
});
```

---

## 🔄 資料更新說明

- **即時資料**: 盤中每 5 分鐘更新
- **盤後資料**: 收盤後（15:35）更新
- **開盤前**: 每天 08:40 預先更新

所有資料來源自：
- 台灣期貨交易所 (TAIFEX)
- 台灣證券交易所 (TWSE)
- 櫃買中心 (TPEX)

