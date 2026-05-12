# Cloudflare DNS data — 開發狀態記錄

> 每次開發前先讀此檔案，了解上次停在哪裡。
> 恢復指令：`Read 03-Data-Analytics/Cloudflare-DNS-data/.planning/STATE.md and ROADMAP.md, then tell me current progress.`

## 專案基本資訊

- **路徑**: `03-Data-Analytics/Cloudflare-DNS-data/`
- **開始日期**: 2026-03-25
- **開發者**: CK
- **目標**: 抓取 Cloudflare 帳號下所有 Zone 的 DNS 資訊（查詢量、記錄清單、Analytics）

## 架構決策（已確定，勿更改）

| 元件 | 說明 |
|------|------|
| **認證方式** | API Token（Bearer，優先）或 Global API Key（相容），從環境變數 `CF_ACCOUNTS_JSON` 讀取 |
| **多帳戶支援** | `CF_ACCOUNTS_JSON` 為 JSON 陣列，支援多組帳號同時查詢 |
| **輸出格式** | pandas DataFrame → CSV / Excel / 印出 |
| **日期範圍** | 預設過去 30 天（UTC），可調整 |
| **速率限制處理** | 指數退避 + 隨機抖動，最多重試 3 次 |

## 現有腳本盤點

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `cloudflare_report_Global_Key_final.py` | 可用 | 多帳戶 HTTP + DNS 指標收集，支援雙認證模式 |
| `cloudflare_report_Global_Key_final (DNS).py` | 可用 | DNS 專版（僅抓 DNS Analytics） |
| `cloudflare_dns_query_count.py` | 可用 | DNS 查詢量統計 |
| `mlytics_report.py` | 可用 | Mlytics CDN 報表（獨立功能） |
| `hello.py` | 測試用 | 基本 API 連線測試 |
| `ENV_TEMPLATE.md` | 參考 | 環境變數設定範本 |

## 當前進度

**Phase**: 0 — 需求確認
**Status**: Pending（尚未正式開始新功能開發）
**Last activity**: 2026-03-25 — 初次探索腳本結構

### 已知狀況

- 主腳本 `cloudflare_report_Global_Key_final.py` 已可執行，需設定 `CF_ACCOUNTS_JSON`
- DNS 記錄清單（`/zones/{zone_id}/dns_records`）尚未整合到主報表腳本
- 目前腳本抓的是 Analytics（查詢量統計），非 DNS 記錄本身

### 下一步

- 確認需求：是要抓 **DNS Analytics（查詢量）** 還是 **DNS Records（記錄清單）**，或兩者都要
- 確認輸出：CSV / Excel / 印出 / 存入資料庫
- 確認帳號數量與環境變數設定方式

---

## 開發日誌

### [2026-03-26 17:50] — 執行測試遇到網路阻塞
- **Phase**: 1
- **Status**: Blocked
- **Done**:
  - 確認需求：只查 `infa-tech@568win.com` 帳號的 DNS 查詢量統計
  - 確認 `.env` 已設定 Global API Key
  - 嘗試執行 `cloudflare_dns_query_count.py`
- **Next**: 網路恢復後直接執行腳本（需 unset proxy 或開啟 VPN）
- **Blocker**: 系統 Proxy `127.0.0.1:57171` 未運行，直連 DNS 也失敗，機器目前無網路

---

### [2026-03-25] — 初次探索
- **Phase**: 0
- **Status**: Complete
- **Done**:
  - 盤點現有腳本結構
  - 確認雙認證模式（API Token / Global Key）
  - 確認多帳戶支援架構（`CF_ACCOUNTS_JSON`）
- **Next**: 與使用者確認具體需求（DNS Records vs DNS Analytics）
- **Blocker**: 需確認需求方向
