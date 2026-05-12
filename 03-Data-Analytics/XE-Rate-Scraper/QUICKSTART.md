# 快速開始指南

## 🚀 快速啟動

### 方法 1: 使用啟動腳本（推薦）

```bash
cd /Users/ckchiu/Desktop/Project/XE-Rate-Scraper
./run.sh
```

### 方法 2: 手動安裝和執行

```bash
# 1. 進入專案目錄
cd /Users/ckchiu/Desktop/Project/XE-Rate-Scraper

# 2. 創建虛擬環境（可選但推薦）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 執行抓取腳本
python3 xe_scraper.py
```

## 📋 常用命令

### 基本抓取
```bash
python3 xe_scraper.py
```

### 顯示瀏覽器視窗（除錯用）
```bash
python3 xe_scraper.py --no-headless
```

### 僅使用 requests（不使用 Selenium）
```bash
python3 xe_scraper.py --no-selenium
```

### 指定輸出格式
```bash
# 僅輸出 JSON
python3 xe_scraper.py --format json

# 僅輸出 CSV
python3 xe_scraper.py --format csv

# 僅輸出 Excel
python3 xe_scraper.py --format excel
```

### 自訂輸出檔案名稱
```bash
python3 xe_scraper.py --output my_rates
# 將生成: my_rates.json, my_rates.csv, my_rates.xlsx
```

## 📊 輸出檔案

執行後會在當前目錄生成：
- `xe_rates_YYYYMMDD_HHMMSS.json` - JSON 格式
- `xe_rates_YYYYMMDD_HHMMSS.csv` - CSV 格式  
- `xe_rates_YYYYMMDD_HHMMSS.xlsx` - Excel 格式

## ⚠️ 注意事項

1. **首次執行**：Selenium 會自動下載 ChromeDriver，可能需要一些時間
2. **網路連接**：確保可以訪問 https://app.xe.com/activity
3. **登入要求**：如果網站需要登入，可能需要手動處理 cookies

## 🔧 故障排除

### 問題：ChromeDriver 下載失敗

**解決方案**：
- 手動下載 ChromeDriver 並放到 PATH
- 或使用 `--no-selenium` 選項

### 問題：無法抓取數據

**解決方案**：
1. 使用 `--no-headless` 查看瀏覽器行為
2. 檢查網站是否需要登入
3. 查看控制台輸出的錯誤資訊

### 問題：依賴安裝失敗

**解決方案**：
```bash
# 升級 pip
pip install --upgrade pip

# 單獨安裝失敗的套件
pip install selenium beautifulsoup4 requests pandas
```

## 📝 範例輸出

```
============================================================
🌐 XE.com 匯率抓取工具
============================================================
✅ Selenium WebDriver 初始化成功
🌐 正在訪問 https://app.xe.com/activity...
⏳ 等待頁面載入...
📊 找到 1 個表格

✅ 成功抓取 50 條匯率數據

📊 數據預覽:
   1. {'currency_pair': 'USD/EUR', 'rate': '0.9234', 'change': '+0.0012', 'timestamp': '2025-12-29T10:30:00'}
   2. {'currency_pair': 'USD/GBP', 'rate': '0.7891', 'change': '-0.0005', 'timestamp': '2025-12-29T10:30:00'}
   ...

✅ 數據已儲存到: xe_rates_20251229_103000.json
✅ 數據已儲存到: xe_rates_20251229_103000.csv
✅ 數據已儲存到: xe_rates_20251229_103000.xlsx
```

