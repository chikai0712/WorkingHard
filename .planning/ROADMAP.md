# Roadmap: CK 多專案工作區 GSD 整合

## Overview

此 Roadmap 記錄工作區層級的任務。每個具體的子專案（DNS 監控、遊戲、股票分析等）應在其子目錄下另建 `.planning/` 或直接在此 ROADMAP 新增 Phase。

目前目標：**建立穩固的 Spec-Driven 開發規範**，讓後續所有子專案的 Agent 工作都能遵循 GSD 流程執行，不再跑掉。

## Domain Expertise

- `./.cursor/get-shit-done/references/principles.md`
- `./.cursor/get-shit-done/references/checkpoints.md`
- `./.cursor/get-shit-done/references/git-integration.md`

## Phases

- [x] **Phase 1: GSD 框架整合** — 建立 Cursor Rules 並初始化 `.planning/` 目錄
- [ ] **Phase 2: 第一個子專案規格化** — 選定一個子專案，用 GSD 流程完整走一遍
- [ ] **Phase 3: 驗證與調整** — 根據實際使用回饋調整 Rules 與流程

## Phase Details

### Phase 1: GSD 框架整合 ✅
**Goal**: 讓 Cursor Agent 在每次 session 都能自動遵循 GSD 規範
**Depends on**: Nothing
**Plans**: 1 plan

Plans:
- [x] 01-01: 建立 `.cursor/rules/` 三個核心規則 + 初始化 `.planning/` 目錄

### Phase 2: 第一個子專案規格化
**Goal**: 選定一個子專案，完整執行 `/gsd/new-project` → `/gsd/create-roadmap` → `/gsd/plan-phase` → `/gsd/execute-phase` 流程
**Depends on**: Phase 1
**Research**: Unlikely (internal patterns)
**Plans**: TBD

Plans:
- [ ] 02-01: 選定子專案並執行 `/gsd/map-codebase`
- [ ] 02-02: 建立子專案 PROJECT.md 與 ROADMAP.md
- [ ] 02-03: 執行第一個 Phase Plan

### Phase 3: 驗證與調整
**Goal**: 根據實際使用回饋優化 Rules 與工作流程
**Depends on**: Phase 2
**Research**: Unlikely
**Plans**: 1-2 plans

Plans:
- [ ] 03-01: 評估 GSD 流程效果，調整 Cursor Rules
- [ ] 03-02: 更新 AGENTS.md 與工作區文件

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. GSD 框架整合 | 1/1 | Complete | 2026-03-12 |
| 2. 第一個子專案規格化 | 0/3 | Not started | - |
| 3. 驗證與調整 | 0/2 | Not started | - | 