# API 文檔

## 基礎信息

- **Base URL**: `http://localhost:8080/api/v1`
- **Content-Type**: `application/json`

## 注單 API

### 1. 創建注單

**POST** `/orders`

**Request Body:**
```json
{
  "user_id": 12345,
  "game_type": "slot",
  "bet_amount": 100.00,
  "order_no": "ORDER_20250101_001"
}
```

**Response:**
```json
{
  "message": "注單創建成功",
  "order_no": "ORDER_20250101_001"
}
```

### 2. 查詢注單

**GET** `/orders/:order_no`

**Response:**
```json
{
  "id": 1,
  "user_id": 12345,
  "order_no": "ORDER_20250101_001",
  "game_type": "slot",
  "bet_amount": 100.00,
  "win_amount": 0,
  "status": "pending",
  "bet_time": "2025-01-01T10:00:00Z",
  "created_at": "2025-01-01T10:00:00Z"
}
```

### 3. 查詢注單列表

**GET** `/orders?user_id=12345&status=pending&page=1&page_size=20`

**Query Parameters:**
- `user_id` (optional): 用戶 ID
- `order_no` (optional): 注單號
- `status` (optional): 狀態 (pending, settled, cancelled)
- `start_time` (optional): 開始時間
- `end_time` (optional): 結束時間
- `page` (required): 頁碼
- `page_size` (required): 每頁數量

**Response:**
```json
{
  "orders": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 4. 結算注單

**PUT** `/orders/:order_no/settle`

**Request Body:**
```json
{
  "win_amount": 150.00
}
```

**Response:**
```json
{
  "message": "結算成功",
  "order_no": "ORDER_20250101_001"
}
```

## 錯誤碼

- `400`: 請求參數錯誤
- `404`: 資源不存在
- `429`: 請求過於頻繁（限流）
- `500`: 服務器內部錯誤
- `504`: 請求超時

