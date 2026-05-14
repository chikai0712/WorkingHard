# ROADMAP — Cloudflare DNS data

## 專案目標

透過 Cloudflare API 抓取多帳號下所有 Zone 的 DNS 資訊，整合成可分析的報表。

## 成功條件（Definition of Done）

1. 執行一個腳本即可抓取所有帳號、所有 Zone 的 DNS 資訊
2. 輸出 CSV / Excel，欄位包含：帳號、Zone 名稱、記錄類型、記錄名稱、記錄值、TTL
3. 支援多帳號（`CF_ACCOUNTS_JSON` 環境變數）
4. 速率限制自動重試，不中斷

## Phase 0：需求確認 🔲

| 任務 | 狀態 | 說明 |
|------|------|------|
| 0-01 | 🔲 | 確認需求：DNS Records vs DNS Analytics vs 兩者 |
| 0-02 | 🔲 | 確認輸出格式與欄位 |
| 0-03 | 🔲 | 確認帳號設定方式 |

## Phase 1：DNS Records 抓取腳本 🔲

| 任務 | 狀態 | 說明 |
|------|------|------|
| 1-01 | 🔲 | 新增 `cloudflare_dns_records.py` — 抓取所有 Zone 的 DNS 記錄清單 |
| 1-02 | 🔲 | 整合多帳號支援（`CF_ACCOUNTS_JSON`） |
| 1-03 | 🔲 | 輸出 CSV / Excel |
| 1-04 | 🔲 | 速率限制重試邏輯 |

## Phase 2：整合報表（選配）🔲

| 任務 | 狀態 | 說明 |
|------|------|------|
| 2-01 | 🔲 | 合併 DNS Records + DNS Analytics 到同一報表 |
| 2-02 | 🔲 | 加入 Mlytics 資料欄位（選配） |

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0: 需求確認 | 0/3 | 🔲 Pending |
| Phase 1: DNS Records 腳本 | 0/4 | 🔲 Not started |
| Phase 2: 整合報表 | 0/2 | 🔲 Not started |
