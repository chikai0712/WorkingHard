# 登入網站演示 - SentinelJS 指紋識別

這是一個集成了 SentinelJS 指紋識別功能的登入網站演示，可以用於測試和演示瀏覽器指紋識別技術。

## 功能特點

- ✅ 完整的登入系統界面
- ✅ 自動集成 SentinelJS 指紋識別庫
- ✅ 登入時自動收集和發送指紋數據
- ✅ RESTful API 接口
- ✅ 壓測工具（使用 Puppeteer 模擬瀏覽器登入）
- ✅ 登入記錄和指紋數據存儲

## 快速開始

### 1. 安裝依賴

```bash
cd login-demo
npm install
```

### 2. 啟動服務器

```bash
npm start
```

服務器將在 `http://localhost:3000` 啟動。

### 3. 訪問網站

打開瀏覽器訪問 `http://localhost:3000`，你會看到登入頁面。

### 4. 測試登入

- **用戶名**: 任意（至少 1 個字符）
- **密碼**: 任意（至少 6 個字符）

登入時，系統會自動：
1. 等待 SentinelJS 收集指紋數據
2. 將指紋數據連同登入信息發送到服務器
3. 顯示指紋哈希值

## API 接口

### POST /api/login

登入接口，接收用戶名、密碼和指紋數據。

**請求體:**
```json
{
  "username": "testuser",
  "password": "testpass123",
  "fingerprint": { ... },  // SentinelJS Fingerprint 對象（可選）
  "sentinel": { ... }       // SentinelJS Sentinel 對象（可選）
}
```

**響應:**
```json
{
  "success": true,
  "message": "登入成功",
  "sessionId": "1234567890",
  "fingerprintHash": "...",
  "sentinelHash": "..."
}
```

### GET /api/logs

獲取登入記錄。

**查詢參數:**
- `limit`: 返回記錄數量（默認: 100）

**響應:**
```json
{
  "success": true,
  "count": 10,
  "logs": [ ... ]
}
```

### GET /api/fingerprints

獲取指紋數據記錄。

**查詢參數:**
- `limit`: 返回記錄數量（默認: 100）

### DELETE /api/logs

清除所有登入記錄和指紋數據（僅用於測試）。

## 壓測工具

使用 Puppeteer 模擬瀏覽器登入，可以測試多個並發登入請求。

### 安裝壓測工具依賴

```bash
npm install
```

### 使用方法

```bash
# 基本用法（10 次登入，3 個並發）
node load-test.js

# 自定義參數
node load-test.js --count 20 --concurrent 5

# 無頭模式（不顯示瀏覽器窗口）
node load-test.js --count 50 --headless

# 自定義 URL 和用戶名
node load-test.js --url http://localhost:3000 --username myuser --password mypass123
```

### 壓測工具選項

- `--url <url>`: 目標網站 URL（默認: http://localhost:3000）
- `--count <number>`: 登入次數（默認: 10）
- `--concurrent <number>`: 並發數（默認: 3）
- `--delay <ms>`: 每次登入間隔，毫秒（默認: 1000）
- `--username <name>`: 用戶名（默認: testuser）
- `--password <pass>`: 密碼（默認: testpass123）
- `--headless`: 無頭模式（默認: false）
- `--help`: 顯示幫助信息

### 壓測示例

```bash
# 輕量壓測：20 次登入，5 個並發
node load-test.js --count 20 --concurrent 5

# 中等壓測：50 次登入，10 個並發，無頭模式
node load-test.js --count 50 --concurrent 10 --headless

# 重度壓測：100 次登入，20 個並發，無頭模式，快速間隔
node load-test.js --count 100 --concurrent 20 --delay 500 --headless
```

## 項目結構

```
login-demo/
├── server.js           # Express 服務器
├── load-test.js        # Puppeteer 壓測工具
├── package.json        # 項目配置
├── README.md          # 說明文檔
├── public/            # 靜態文件
│   ├── index.html    # 登入頁面
│   ├── app.js        # 前端 JavaScript
│   └── style.css     # 樣式文件
└── logs/             # 日誌文件（自動生成）
```

## SentinelJS 集成

網站使用 CDN 加載 SentinelJS：

```html
<script src="https://abrahamjuliot.github.io/creepjs/creep.js" defer></script>
```

如果需要使用本地文件，可以修改 `public/index.html`：

```html
<!-- 使用本地文件 -->
<script src="../creepjs/docs/creep.js" defer></script>
```

SentinelJS 會在頁面加載後自動收集指紋數據，並將結果存儲在：
- `window.Fingerprint` - 完整的指紋數據
- `window.Sentinel` - 穩定的指紋數據（過濾掉謊言）

## 數據存儲

目前數據存儲在內存中，重啟服務器後會丟失。實際應用中應該：

1. 使用數據庫（如 MongoDB、PostgreSQL）
2. 實現持久化存儲
3. 添加數據分析功能

日誌文件會自動保存到 `logs/` 目錄，文件名格式：`login-YYYY-MM-DDTHH-mm-ss.json`

## 開發

### 開發模式

```bash
npm run dev
```

使用 `--watch` 模式，代碼變更後自動重啟。

### 自定義配置

可以通過環境變量配置：

```bash
PORT=3000 npm start
```

## 注意事項

1. **安全性**: 此演示僅用於測試，不適合生產環境
2. **密碼驗證**: 當前只檢查密碼長度，實際應用中應該使用加密和數據庫驗證
3. **CORS**: 已啟用 CORS，允許跨域請求
4. **性能**: 大量並發請求可能會影響性能，建議使用負載均衡

## 故障排除

### SentinelJS 加載失敗

如果看到 "SentinelJS 加載超時" 的提示：

1. 檢查網絡連接
2. 確認 CDN 可訪問：https://abrahamjuliot.github.io/creepjs/creep.js
3. 嘗試使用本地文件

### 壓測工具無法運行

1. 確保已安裝 Puppeteer：`npm install`
2. Puppeteer 會自動下載 Chromium，可能需要一些時間
3. 如果下載失敗，可以手動設置 `PUPPETEER_SKIP_DOWNLOAD=true` 並使用系統 Chrome

### 端口被占用

修改 `server.js` 中的端口號，或使用環境變量：

```bash
PORT=3001 npm start
```

## 許可證

與 SentinelJS 主項目相同。

## 相關項目

- [SentinelJS](https://github.com/abrahamjuliot/CreepJS) - 瀏覽器指紋識別庫
- [Puppeteer](https://github.com/puppeteer/puppeteer) - 無頭瀏覽器工具

