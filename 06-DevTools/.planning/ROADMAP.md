# DevTools — Roadmap

## Overview

建立可重用的開發工具與平台自動化 skeleton，先以規格化目錄與樣板腳本為主，不接真實環境。

### Phase 0：Planning 初始化
**Goal**: 建立 `06-DevTools` 子專案 planning 文件。

- [x] 建立 `.planning/CONTEXT.md`
  - 驗證方式：檔案存在且包含任務規格、限制與 Forbidden Zones。
  - 相關路徑：`06-DevTools/.planning/CONTEXT.md`
- [x] 建立 `.planning/ROADMAP.md`
  - 驗證方式：存在 phases、驗證方式與進度表。
  - 相關路徑：`06-DevTools/.planning/ROADMAP.md`
- [x] 建立 `.planning/STATE.md`
  - 驗證方式：記錄當前任務、User Story、Acceptance Criteria 與下一步。
  - 相關路徑：`06-DevTools/.planning/STATE.md`

### Phase 1：共用 automation skeleton
**Goal**: 建立 FinOps / Reporting / Shared utilities 骨架。

- [x] 建立 `automation/shared/`
  - 驗證方式：存在共用 shell / Python helper skeleton 與 `.env.example`。
  - 相關路徑：`06-DevTools/automation/shared/`
- [x] 建立 `automation/finops/`
  - 驗證方式：存在成本盤點、閒置資源報表 skeleton 與 README。
  - 相關路徑：`06-DevTools/automation/finops/`
- [x] 建立 `automation/reporting/`
  - 驗證方式：存在 log / metrics / dashboard / reporting skeleton 與 README。
  - 相關路徑：`06-DevTools/automation/reporting/`

### Phase 2：FinOps + Reporting 實戰版 skeleton 🔄
**Goal**: 讓 `automation/finops/` 與 `automation/reporting/` 從初版 skeleton 提升到可套用模板層級。

- [x] 建立成本報表 / 預算門檻 / 標籤稽核模板
  - 驗證方式：存在 FinOps config、budget thresholds、tag audit 或對應範本。
  - 相關路徑：`06-DevTools/automation/finops/`
- [x] 建立 incident / metrics / dashboard reporting 模板
  - 驗證方式：存在 incident summary、metric snapshot、dashboard metadata 或對應範本。
  - 相關路徑：`06-DevTools/automation/reporting/`
- [x] 更新 Python skeleton 與 README
  - 驗證方式：`idle_resource_report.py` 與 `generate_summary.py` 可輸出新模板資訊，且 Python 語法檢查通過。
  - 相關路徑：`06-DevTools/automation/finops/`、`reporting/`

### Phase 3：防禦工具整合到 Git 工作流 🔄
**Goal**: 以防禦導向方式整合 repo-level security scanning。

- [x] 建立 GitHub Actions 掃描 workflow
  - 驗證方式：存在 workflow，包含 secret scanning、SAST、vulnerability scan 階段。
  - 相關路徑：`.github/workflows/`
- [x] 建立 gitleaks / semgrep / trivy 設定檔
  - 驗證方式：存在對應設定檔與基本規則/排除說明。
  - 相關路徑：repo root、`06-DevTools/automation/`
- [x] 補使用說明與 guardrails
  - 驗證方式：存在 README 或總覽文件說明如何在防禦情境下使用。
  - 相關路徑：`06-DevTools/automation/`

### Phase 4：Cross-Project Health / Source / Security Gates 🔄
**Goal**: 建立跨專案共用的健康檢測、源碼檢測與資安 gate 模型。

- [x] 建立 shared gate framework 與 decision model
  - 驗證方式：存在共用 framework 文件，說明 health/source/security gate 的事件、輸入、輸出與 block/hold/rollback 模型。
  - 相關路徑：`06-DevTools/automation/`
- [x] 建立 health / source / security gate 範本
  - 驗證方式：存在 YAML/JSON/example config，描述檢測項目、門檻、事件與後續決策。
  - 相關路徑：`06-DevTools/automation/`
- [x] 讓 `02` 與 `08` 文件引用 shared gate model
  - 驗證方式：`02-Cloud-Deploy` 與 `08-Database/DB-Automation` 至少有總覽或 README 引用 shared gate framework。
  - 相關路徑：`02-Cloud-Deploy/automation/`、`08-Database/DB-Automation/`

### Phase 5：Unified Automation Management UI 🔄
**Goal**: 建立跨專案統一管理介面第一版。

- [x] 建立 Web UI skeleton 與 module dashboard
  - 驗證方式：存在前端頁面，可顯示模組總覽、gate 狀態與模組細節卡片。
  - 相關路徑：`06-DevTools/automation/control-plane/`
- [x] 建立 mock actions 與 local data model
  - 驗證方式：存在本地 data source 與基本操作按鈕，可顯示 mock action result。
  - 相關路徑：`06-DevTools/automation/control-plane/`
- [x] 補使用說明與架構定位
  - 驗證方式：存在 README 或說明文件，描述 UI 範圍、限制與後續真實接線方向。
  - 相關路徑：`06-DevTools/automation/control-plane/`
- [x] 將 module state 抽成 JSON data source
  - 驗證方式：存在獨立 JSON data source，前端可讀取並渲染；失敗時有 fallback 行為。
  - 相關路徑：`06-DevTools/automation/control-plane/`
- [x] 接上本地 dry-run adapters
  - 驗證方式：存在受控本地 adapter，可針對既有 skeleton 執行 dry-run 命令並回傳結果；UI 可顯示真實本地 dry-run output。
  - 相關路徑：`06-DevTools/automation/control-plane/`

### Phase 6：AI Analysis Architecture + RAG Foundation 🔄
**Goal**: 建立跨 `06-DevTools` 與 `08-Database/DB-Automation` 的 AI 分析與 RAG 骨架規格。

- [x] 建立平台級 AI / RAG 架構文件
  - 驗證方式：存在 architecture 文件，定義 data sources、ingestion、metadata、retrieval、orchestration、governance 與導入 phases。
  - 相關路徑：`06-DevTools/automation/`
- [x] 建立 RAG dataset / ingestion skeleton
  - 驗證方式：存在 example config、dataset source、metadata schema 或對應 skeleton。
  - 相關路徑：`06-DevTools/automation/`
- [x] 建立 DB 專屬 AI / RAG 導入文件與來源清單
  - 驗證方式：存在 DB 專屬文件，說明 migration / backup / monitoring / remediation / ansible 的可導入資料與安全邊界。
  - 相關路徑：`08-Database/DB-Automation/`
- [x] 建立 ingestion script skeleton、evaluation examples 與 control-plane AI recommendation 規格
  - 驗證方式：存在 ingestion script / chunking policy / evaluation questions、DB summary schema，以及 control-plane AI recommendation API / UI 規格文件。
  - 相關路徑：`06-DevTools/automation/ai-rag/`、`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/`

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0 Planning 初始化 | 3/3 | ✅ Complete |
| Phase 1 共用 automation skeleton | 3/3 | ✅ Complete |
| Phase 2 FinOps + Reporting 實戰版 skeleton | 3/3 | ✅ Complete |
| Phase 3 防禦工具整合到 Git 工作流 | 3/3 | ✅ Complete |
| Phase 4 Cross-Project Health / Source / Security Gates | 3/3 | ✅ Complete |
| Phase 5 Unified Automation Management UI | 5/5 | ✅ Complete |
| Phase 6 AI Analysis Architecture + RAG Foundation | 4/4 | ✅ Complete |
