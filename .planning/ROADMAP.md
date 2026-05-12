# Roadmap: CK 多專案工作區

## Overview

工作區層級 Roadmap。每個子專案有**獨立的 ROADMAP.md**，此處只做索引。

**核心價值**: 讓 AI Agent 按規格執行，而不是按直覺亂跑。每個任務必須先有計畫，再有執行，最後有驗證。

---

## 子專案 ROADMAP 索引

| 專案 | ROADMAP 位置 | 狀態 | 進度 |
|------|-------------|------|------|
| **GlobalpingChecker V5** | `GlobalpingChecker/.planning/ROADMAP.md` | ⏸️ Paused | Phase 1 完成，Phase 2 待部署 |
| **Cloud Deploy** | `02-Cloud-Deploy/.planning/ROADMAP.md` | 🔄 In progress | Phase 4 — EC2 實機部署驗證 |
| **台指期監控系統** | `03-Data-Analytics/Stock_Analize/.planning/ROADMAP.md` | 🔄 In progress | Phase A — A-06b Windows 實機測試 |
| **Cloudflare DNS data** | `03-Data-Analytics/Cloudflare-DNS-data/.planning/ROADMAP.md` | 🔲 Pending | Phase 0 需求確認 |
| **XE-Rate-Scraper** | `03-Data-Analytics/XE-Rate-Scraper/.planning/ROADMAP.md` | ✅ Stable | Phase 1 完成 |

---

## 工作區層級 Phases

### Phase 1: GSD 框架整合 ✅
**Goal**: 建立 Cursor Rules，初始化 `.planning/` 目錄
- [x] 01-01: 建立 `.cursor/rules/` 三個核心規則
- [x] 01-02: 初始化根目錄 `.planning/`

### Phase 2: 子專案各自建立 Planning 目錄 ✅
**Goal**: 每個子專案都有獨立的 STATE.md + ROADMAP.md，確保切換專案時能接續
- [x] 02-01: `Stock_Analize/.planning/` 建立
- [x] 02-02: `GlobalpingChecker/.planning/` 建立
- [x] 02-03: `Cloudflare-DNS-data/.planning/` 建立
- [x] 02-04: `XE-Rate-Scraper/.planning/` 建立
- [x] 02-05: 根目錄 STATE.md / ROADMAP.md 改為索引模式
- [x] 02-06: `state-tracking.mdc` 更新子專案 planning 規則

### Phase 3: 驗證與調整 🔲
**Goal**: 根據實際使用回饋優化 Rules 與工作流程
- [ ] 03-01: 評估 GSD 流程效果，調整 Cursor Rules
- [ ] 03-02: 更新 AGENTS.md 與工作區文件

---

## Domain Expertise

- `./.cursor/get-shit-done/references/principles.md`
- `./.cursor/get-shit-done/references/checkpoints.md`

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| 1. GSD 框架整合 | 2/2 | ✅ Complete |
| 2. 子專案 Planning 目錄 | 6/6 | ✅ Complete |
| 3. 驗證與調整 | 1/3 | 🔄 In progress |
