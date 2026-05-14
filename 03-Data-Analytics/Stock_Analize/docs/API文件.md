# API 文件

## 基礎資訊

- **Base URL**: `http://localhost:8000/api`
- **API 版本**: v1
- **回應格式**: JSON

## 認證

目前為開發階段，暫不需要認證。未來可加入 JWT Token 認證。

---

## 端點列表

### 1. 股票列表

#### 取得所有監控股票

```http
GET /api/stocks
```

**回應範例**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "symbol": "2330",
      "market": "TW",
      "name": "台積電",
      "industry": "半導體",
      "current_price": 580.0,
      "change": 5.0,
      "change_percent": 0.87,
      "volume": 12345678,
      "updated_at": "2025-12-17T09:30:00Z"
    }
  ],
  "total": 10
}
```

#### 取得特定股票資訊

```http
GET /api/stocks/{symbol}
```

**參數**:
- `symbol` (path): 股票代號，例如 "2330" 或 "AAPL"

**回應範例**:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "symbol": "2330",
    "market": "TW",
    "name": "台積電",
    "industry": "半導體",
    "description": "台灣積體電路製造股份有限公司",
    "website": "https://www.tsmc.com",
    "current_price": 580.0,
    "change": 5.0,
    "change_percent": 0.87,
    "volume": 12345678,
    "updated_at": "2025-12-17T09:30:00Z"
  }
}
```

#### 新增監控股票

```http
POST /api/stocks
```

**請求體**:
```json
{
  "symbol": "2317",
  "market": "TW",
  "name": "鴻海"
}
```

**回應範例**:
```json
{
  "status": "success",
  "message": "股票已新增",
  "data": {
    "id": 2,
    "symbol": "2317",
    "market": "TW",
    "name": "鴻海"
  }
}
```

#### 移除監控股票

```http
DELETE /api/stocks/{symbol}
```

**回應範例**:
```json
{
  "status": "success",
  "message": "股票已移除"
}
```

---

### 2. 價格資料

#### 取得最新價格

```http
GET /api/stocks/{symbol}/price
```

**回應範例**:
```json
{
  "status": "success",
  "data": {
    "symbol": "2330",
    "date": "2025-12-17",
    "open": 575.0,
    "high": 582.0,
    "low": 574.0,
    "close": 580.0,
    "volume": 12345678,
    "change": 5.0,
    "change_percent": 0.87,
    "updated_at": "2025-12-17T09:30:00Z"
  }
}
```

#### 取得歷史價格資料

```http
GET /api/stocks/{symbol}/history
```

**查詢參數**:
- `start_date` (optional): 開始日期，格式 YYYY-MM-DD
- `end_date` (optional): 結束日期，格式 YYYY-MM-DD
- `limit` (optional): 限制筆數，預設 100
- `offset` (optional): 偏移量，預設 0

**回應範例**:
```json
{
  "status": "success",
  "data": [
    {
      "date": "2025-12-17",
      "open": 575.0,
      "high": 582.0,
      "low": 574.0,
      "close": 580.0,
      "volume": 12345678
    },
    {
      "date": "2025-12-16",
      "open": 570.0,
      "high": 576.0,
      "low": 569.0,
      "close": 575.0,
      "volume": 9876543
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

---

### 3. 技術指標

#### 取得所有技術指標

```http
GET /api/stocks/{symbol}/indicators
```

**查詢參數**:
- `date` (optional): 查詢日期，格式 YYYY-MM-DD，預設為最新日期

**回應範例**:
```json
{
  "status": "success",
  "data": {
    "symbol": "2330",
    "date": "2025-12-17",
    "indicators": {
      "MA5": 575.5,
      "MA10": 572.3,
      "MA20": 568.9,
      "RSI": 65.5,
      "MACD": 2.3,
      "MACD_signal": 1.8,
      "MACD_hist": 0.5
    }
  }
}
```

#### 取得特定技術指標

```http
GET /api/stocks/{symbol}/indicators/{indicator_type}
```

**參數**:
- `symbol` (path): 股票代號
- `indicator_type` (path): 指標類型（MA/RSI/MACD/Bollinger）

**查詢參數**:
- `period` (optional): 計算週期，例如 MA 的週期
- `start_date` (optional): 開始日期
- `end_date` (optional): 結束日期

**回應範例** (MA 指標):
```json
{
  "status": "success",
  "data": {
    "symbol": "2330",
    "indicator_type": "MA",
    "period": 5,
    "values": [
      {"date": "2025-12-17", "value": 575.5},
      {"date": "2025-12-16", "value": 574.2},
      {"date": "2025-12-15", "value": 573.8}
    ]
  }
}
```

---

### 4. 儀表板統計

#### 取得儀表板摘要

```http
GET /api/dashboard/summary
```

**回應範例**:
```json
{
  "status": "success",
  "data": {
    "total_stocks": 10,
    "total_value": 5800000.0,
    "total_change": 50000.0,
    "total_change_percent": 0.87,
    "gaining_stocks": 6,
    "losing_stocks": 3,
    "unchanged_stocks": 1,
    "updated_at": "2025-12-17T09:30:00Z"
  }
}
```

#### 取得漲幅排行榜

```http
GET /api/dashboard/top-gainers
```

**查詢參數**:
- `limit` (optional): 返回筆數，預設 10

**回應範例**:
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "2330",
      "name": "台積電",
      "change": 5.0,
      "change_percent": 0.87,
      "current_price": 580.0
    }
  ]
}
```

#### 取得跌幅排行榜

```http
GET /api/dashboard/top-losers
```

**查詢參數**:
- `limit` (optional): 返回筆數，預設 10

---

## 錯誤回應

### 標準錯誤格式

```json
{
  "status": "error",
  "error_code": "STOCK_NOT_FOUND",
  "message": "找不到指定的股票",
  "details": {}
}
```

### 常見錯誤碼

| 錯誤碼 | HTTP 狀態碼 | 說明 |
|--------|------------|------|
| `INVALID_SYMBOL` | 400 | 無效的股票代號 |
| `STOCK_NOT_FOUND` | 404 | 找不到股票 |
| `DATA_FETCH_FAILED` | 500 | 資料抓取失敗 |
| `DATABASE_ERROR` | 500 | 資料庫錯誤 |
| `RATE_LIMIT_EXCEEDED` | 429 | 請求過於頻繁 |

---

## 速率限制

- **一般 API**: 每分鐘 60 次請求
- **資料抓取 API**: 每分鐘 10 次請求

---

## 資料格式說明

### 日期時間格式
- 日期：`YYYY-MM-DD`（例如：2025-12-17）
- 時間：ISO 8601 格式（例如：2025-12-17T09:30:00Z）

### 價格格式
- 所有價格為小數點後 2 位（例如：580.00）
- 使用台幣（TWD）或美元（USD）取決於市場

### 百分比格式
- 漲跌幅百分比為小數點後 2 位（例如：0.87）

