# GlobalpingChecker — 開發狀態記錄

> 每次開發前先讀此檔案，了解上次停在哪裡。
> 恢復指令：`Read GlobalpingChecker/.planning/STATE.md and ROADMAP.md, then tell me current progress.`

## 專案基本資訊

- **路徑**: `GlobalpingChecker/`
- **開始日期**: 2026-03-12
- **開發者**: CK
- **目標**: 全球 DNS 汙染檢測系統，透過 Globalping API 多節點檢測域名解析結果

## 架構決策（已確定，勿更改）

| 元件 | 說明 |
|------|------|
| **後端** | FastAPI + APScheduler + PostgreSQL（Docker Compose） |
| **檢測引擎** | Globalping API（DNS 模式，不消耗 credits） |
| **節點池** | 動態節點池，優先 TOP ISP，Pass 1 ISP 多樣性 → Pass 2 城市多樣性 → Fallback |
| **排程** | 每日 AM 00:01（台北時間）全量重置 + 全量檢測，額度驅動輪詢 |
| **前端** | Dashboard HTML（JetBrains Mono + Inter，深色主題） |
| **部署** | AWS EC2 (54.238.247.106:8000)，`deploy/deploy-v5.sh` |
| **通知** | Telegram Bot（已設定，待 notifier.py 完整實作） |

## 當前進度

**版本**: V5
**Phase**: UI 修復 + 排程驗證
**Status**: **暫停中** (Paused)
**Last activity**: 2026-03-19 — 使用者決定暫停，轉往股票分析專案
**AWS 狀態**: EC2 服務仍在運行（54.238.247.106:8000）

### 暫停前最後狀態

- ISP 節點欄位修復已完成（本機），**尚未部署至 AWS**
- 時間顯示修復（`formatDate()` 補 `Z` 後綴）已完成，**尚未部署至 AWS**
- 排程時區修復（`ZoneInfo("Asia/Taipei")`）已完成，**尚未部署至 AWS**
- 所有修復只需執行 `bash deploy/deploy-v5.sh` 即可一次部署

### 恢復步驟

```bash
# 1. 部署最新版到 AWS（含 ISP 欄位修復 + 時間顯示修復 + 排程時區修復）
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v5
bash deploy/deploy-v5.sh

# 2. 觸發一次檢測驗證
curl -X POST http://54.238.247.106:8000/api/check/trigger

# 3. 觀察 Dashboard 確認：
#    - ISP 節點欄位正常顯示（非 ---）
#    - 時間顯示台北時間（非 UTC+8 偏差）
#    - AM 00:01 排程正常觸發
