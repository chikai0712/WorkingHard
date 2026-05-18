# DevTools — Context

## 專案範圍

`06-DevTools/` 用於集中存放可重用的開發工具、維運腳本、報表工具與平台自動化骨架。

本輪任務聚焦於建立跨專案可重用的 automation skeleton，涵蓋：
- FinOps 成本分析與閒置資源盤點
- Log / Metrics / Dashboard / Reporting 自動化
- 共用 shell / Python automation utilities
- 後續可被 `02-Cloud-Deploy/`、`08-Database/DB-Automation/`、`01-DNS-Monitoring/` 引用的共用模板

## 當前任務規格

## 任務：建立統一 automation management UI
- 目標：提供一個統一 Web UI，集中查看與操作 shared health/source/security gates 與各 automation 模組，第一版先支援狀態總覽、模組列表、gate 狀態與 mock actions。
- 方法：在 `06-DevTools/automation/` 下建立 web UI skeleton，優先讀取本地 example config / 文件結構產生 dashboard，不直接連線真實 Jenkins、GitHub、雲端或資料庫系統。
- 驗證：存在 UI 目錄與前端檔案；可顯示模組卡片、gate 狀態、基本操作按鈕與 mock result 區塊；planning 與說明文件同步更新。
- 影響範圍：`06-DevTools/.planning/`、`06-DevTools/automation/`。

## 任務：建立跨專案 health / source / security gate 共用框架
- 目標：在 `02-Cloud-Deploy`、`06-DevTools`、`08-Database/DB-Automation` 的 automation 流程中，建立一致的健康檢測、源碼檢測與資安檢測治理模型，作為後續各模組套用基礎。
- 方法：先在 `06-DevTools/automation/` 建立 shared gate framework、事件與 decision model、共用設定範本與使用說明；再由其他子專案 README / 總覽文件引用該模型。
- 驗證：存在 shared gate framework 文件、health/security/source config 範本、總覽文件更新，且 `02` / `08` 至少有文件層引用。
- 影響範圍：`06-DevTools/automation/`、`06-DevTools/.planning/`、`02-Cloud-Deploy/automation/` 文件、`08-Database/DB-Automation/` 文件。

## 任務：整合防禦導向安全工具到 Git 工作流
- 目標：在不加入攻擊工具、不寫入真實 secrets 的前提下，將防禦導向的程式碼與供應鏈掃描整合到目前 Git repo。
- 方法：建立 root-level GitHub Actions workflow，整合 secret scanning、SAST 與 container/filesystem vulnerability scanning 的模板；將對應設定檔與使用說明放在 `06-DevTools/automation/` 範圍內管理。
- 驗證：存在 `.github/workflows/` 掃描 workflow、`gitleaks` / `semgrep` / `trivy` 設定檔、README 說明與 planning 更新。
- 影響範圍：`.github/workflows/`、repo root 安全設定檔、`06-DevTools/automation/`、`06-DevTools/.planning/`。

## 任務：建立平台級自動化 skeleton 與共用工具目錄
- 目標：在不接觸真實 secrets、雲帳號與正式環境的前提下，建立可擴充的自動化腳本骨架與目錄規劃。
- 方法：建立 `.planning/` 與 `automation/` 目錄，先放置 skeleton README、範例 `.env.example`、shell / Python 樣板與 reporting / finops 子模組結構。
- 驗證：存在 `.planning/CONTEXT.md`、`ROADMAP.md`、`STATE.md`，以及 `automation/finops/`、`automation/reporting/`、`automation/shared/` 等基礎結構。
- 影響範圍：`06-DevTools/.planning/`、`06-DevTools/automation/`、根目錄 `.planning/STATE.md`。

## 任務：建立 AI 分析架構與 RAG knowledge layer
- 目標：為 `06-DevTools` 與 `08-Database/DB-Automation` 的 automation 模組建立共用 AI 分析層與 RAG 知識層規格，支援 SOP 檢索、異常分析、變更風險輔助與 gate recommendation。
- 方法：先在 `06-DevTools/automation/` 定義平台級 AI / RAG architecture、ingestion pipeline、metadata schema、retrieval / orchestration pattern 與治理原則；再由 `08-Database/DB-Automation` 定義 DB 專屬資料來源、知識分層與導入策略。第一版以文件與 skeleton 為主，不直接接真實 LLM API、正式 DB 或 production data。
- 驗證：存在 AI / RAG 架構文件、RAG ingestion / dataset example config、DB 專屬資料來源與導入說明；planning 文件同步更新。
- 影響範圍：`06-DevTools/.planning/`、`06-DevTools/automation/`、`08-Database/DB-Automation/.planning/`、`08-Database/DB-Automation/` 文件。

## 技術限制

- 不提交真實雲端 credentials、API token、SSH keys、DB 密碼
- 第一版只建立 skeleton，不直接連線正式 AWS / GCP / Cloudflare / DB
- 盡量使用 shell / Python 作為通用腳本語言
- 需保留 `.env.example` 與 `config.example.*` 型態的範例配置

## Forbidden Zones

- 不覆寫既有 `06-DevTools/scripts/` 中已在使用的部署腳本
- 不把個人機器路徑、帳號資訊或存取憑證寫入 repo
- 不假設所有專案共用同一種部署方式或單一雲平台
