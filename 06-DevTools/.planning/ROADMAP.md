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

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0 Planning 初始化 | 3/3 | ✅ Complete |
| Phase 1 共用 automation skeleton | 3/3 | ✅ Complete |
| Phase 2 FinOps + Reporting 實戰版 skeleton | 3/3 | ✅ Complete |
