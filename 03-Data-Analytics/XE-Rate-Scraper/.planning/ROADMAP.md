# ROADMAP — XE-Rate-Scraper

## 專案目標

穩定抓取 XE.com 匯率資料，提供多種輸出格式，未來可加入排程與通知功能。

## 成功條件（Definition of Done）

1. `xe_table_scraper.py` 可穩定抓取 TWD 對主要貨幣匯率
2. 支援指定日期 / 30 天平均查詢
3. 輸出 CSV / JSON / Excel

## Phase 1：基礎功能 ✅ 完成

| 任務 | 狀態 | 說明 |
|------|------|------|
| 1-01 | ✅ | 公開頁面爬蟲 `xe_table_scraper.py` |
| 1-02 | ✅ | API 方式 `xe_api_scraper.py` |
| 1-03 | ✅ | Selenium 爬蟲 + cookies 登入 |
| 1-04 | ✅ | JSON / CSV / Excel 輸出 |
| 1-05 | ✅ | 完整文件 |

## Phase 2：排程與自動化 🔲（選配）

| 任務 | 狀態 | 說明 |
|------|------|------|
| 2-01 | 🔲 | 加入每日定時排程（cron / schedule） |
| 2-02 | 🔲 | 儲存至 SQLite / PostgreSQL |
| 2-03 | 🔲 | 匯率變化超過閾值時 Telegram 通知 |
| 2-04 | 🔲 | 歷史匯率趨勢圖（matplotlib） |

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 1: 基礎功能 | 5/5 | ✅ Complete |
| Phase 2: 排程與自動化 | 0/4 | 🔲 Not started |
