# ROADMAP — GlobalpingChecker V5

## 專案目標

全球 DNS 汙染檢測系統：透過 Globalping API 多 ISP 節點定期檢測域名 DNS 解析結果，異常時 Telegram 告警。

## 成功條件（Definition of Done）

1. AWS EC2 服務穩定運行，每日 AM 00:01 自動全量檢測 498 個域名
2. Dashboard 正確顯示各域名節點檢測結果（ISP / 城市 / TOP 排名 / 狀態）
3. 時間顯示正確（台北時間，非 UTC 偏差）
4. 額度不足時自動等待整點恢復後繼續

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| V4 | 2026-02 | 初版 |
| V4.1 | 2026-03 | 節點池 + 多國支援 |
| V5 | 2026-03-12 | 全面重寫：ISP 多樣性、Dashboard 重設計、排程時區修復 |

## Phase 1：V5 核心功能 ✅

| 任務 | 狀態 | 說明 |
|------|------|------|
| 01 | ✅ | V5 目錄結構與核心模組 |
| 02 | ✅ | Docker 修復、NodePool schema、HTTP 400 修復 |
| 03 | ✅ | Dashboard 重設計 + 排程簡化 |
| 04 | ✅ | AWS EC2 部署 |
| 05 | ✅ | ISP 節點多樣性修復（Pass 1/2/Fallback） |
| 06 | ✅ | 額度驅動輪詢 + 整點等待 |
| 07 | ✅ | 歷史資料常態顯示（`/api/recent-results`） |
| 08 | ✅ | 排程時區修復（ZoneInfo Asia/Taipei） |
| 09 | ✅ | 時間顯示修復（formatDate Z 後綴） |

## Phase 2：待部署驗證 ⏸️ 暫停中

| 任務 | 狀態 | 說明 |
|------|------|------|
| 10 | 🔲 | 執行 `bash deploy/deploy-v5.sh` 部署所有修復到 AWS |
| 11 | 🔲 | 驗證 Dashboard 時間顯示正確（台北時間） |
| 12 | 🔲 | 驗證 ISP 節點欄位正常顯示（非 ---） |
| 13 | 🔲 | 驗證 AM 00:01 排程正常觸發（台北時間） |

## Phase 3：功能完善（選配）

| 任務 | 狀態 | 說明 |
|------|------|------|
| 14 | 🔲 | 實作 `notifier.py` Telegram 真正告警推播 |
| 15 | 🔲 | 新增多國家支援（MY / PH 開關） |
| 16 | 🔲 | AWS 雙按鈕顯示問題確認修復 |

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 1: V5 核心功能 | 9/9 | ✅ Complete |
| Phase 2: 部署驗證 | 0/4 | ⏸️ Paused |
| Phase 3: 功能完善 | 0/3 | 🔲 Not started |
