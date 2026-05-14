# XE-Rate-Scraper — 開發狀態記錄

> 每次開發前先讀此檔案，了解上次停在哪裡。
> 恢復指令：`Read 03-Data-Analytics/XE-Rate-Scraper/.planning/STATE.md and ROADMAP.md, then tell me current progress.`

## 專案基本資訊

- **路徑**: `03-Data-Analytics/XE-Rate-Scraper/`
- **開發者**: CK
- **目標**: 抓取 XE.com 匯率資料，支援公開頁面爬蟲 + API 兩種方式

## 架構決策（已確定，勿更改）

| 方式 | 腳本 | 說明 |
|------|------|------|
| **推薦：公開頁面爬蟲** | `xe_table_scraper.py` | 無需登入，支援歷史日期、多貨幣、30天平均 |
| **推薦：免費 API** | `xe_api_scraper.py` | ExchangeRate-API.com，無需註冊 |
| 網頁爬蟲（需登入） | `xe_scraper.py` | Selenium + requests，支援 cookies 登入 |
| 手動登入輔助 | `manual_login_helper.py` | 保存 cookies 給 xe_scraper.py 使用 |

## 現有腳本盤點

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `xe_table_scraper.py` | 可用 | 公開頁面爬蟲，推薦主力腳本 |
| `xe_api_scraper.py` | 可用 | API 方式抓匯率 |
| `xe_scraper.py` | 可用 | 完整爬蟲（含登入功能） |
| `manual_login_helper.py` | 可用 | 手動登入 + cookies 保存 |
| `test_login.py` | 測試用 | 登入流程測試 |
| `test_page_access.py` | 測試用 | 頁面存取測試 |
| `test_selenium_only.py` | 測試用 | Selenium 基本測試 |
| `requirements.txt` | 可用 | 依賴：selenium, requests, beautifulsoup4, pandas, openpyxl |

## 當前進度

**Phase**: 完成（基礎功能已可用）
**Status**: Stable — 維護中
**Last activity**: 2026-03（初次建立）

### 已知狀況

- `xe_table_scraper.py` 是最穩定的方式，無需登入、支援歷史查詢
- `xe_scraper.py` 登入功能因 XE.com 反爬蟲機制，穩定性較低
- 尚未加入定時排程（cron / schedule）
- 尚未整合資料庫儲存

### 下一步（視需求而定）

- 加入定時排程（每日自動抓取）
- 加入資料庫儲存（SQLite 或 PostgreSQL）
- 加入匯率變化 Telegram 通知

---

## 開發日誌

### [2026-03] — 初版完成
- **Phase**: 1
- **Status**: Complete
- **Done**:
  - 建立四種抓取方式（公開頁面 / API / Selenium / Cookies）
  - 支援 JSON / CSV / Excel 輸出
  - 完整文件（README + 各方法說明 MD）
- **Next**: 視需求加入排程 + 資料庫儲存
- **Blocker**: 無
