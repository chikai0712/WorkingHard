# HAR Tools

HAR (HTTP Archive) 分析與轉換工具集。

## 工具列表

### `har_to_csv.py` — 完整轉換工具

命令列工具，將 `.har` 文件轉換為 CSV，包含 22 個欄位的完整請求/時序資訊。

**輸出欄位**：序號、請求時間、方法、URL、狀態碼、請求/響應大小、耗時、DNS時間、連接時間、SSL時間、送/等/收時間、內容類型、資源類型、優先級、IP地址、服務器、緩存狀態

```bash
# 指定輸出路徑
python3 har_to_csv.py input.har output.csv

# 自動生成同名 CSV
python3 har_to_csv.py input.har
```

---

### `har_analyzer.py` — 輕量分析工具

自動掃描當前目錄下的 `.har` 檔，輸出網頁結構分析 CSV（需要 `pandas`）。

**輸出欄位**：StartedTime、Method、URL、Path、Status、MimeType、Wait_TTFB、TransferSize、Initiator

```bash
# 將 .har 檔放在同目錄下，直接執行
python3 har_analyzer.py
# 輸出：website_structure_analysis.csv
```

**安裝依賴**：
```bash
pip install pandas
```

## 原始來源

- `har_to_csv.py` — 原位於 `GlobalpingChecker/scripts/utils/`
- `har_analyzer.py` — 原位於 `01-DNS-Monitoring/domain-monitoring-system/`
