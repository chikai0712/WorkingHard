# DevTools — Context

## 專案範圍

`06-DevTools/` 用於集中存放可重用的開發工具、維運腳本、報表工具與平台自動化骨架。

本輪任務聚焦於建立跨專案可重用的 automation skeleton，涵蓋：
- FinOps 成本分析與閒置資源盤點
- Log / Metrics / Dashboard / Reporting 自動化
- 共用 shell / Python automation utilities
- 後續可被 `02-Cloud-Deploy/`、`08-Database/DB-Automation/`、`01-DNS-Monitoring/` 引用的共用模板

## 當前任務規格

## 任務：建立平台級自動化 skeleton 與共用工具目錄
- 目標：在不接觸真實 secrets、雲帳號與正式環境的前提下，建立可擴充的自動化腳本骨架與目錄規劃。
- 方法：建立 `.planning/` 與 `automation/` 目錄，先放置 skeleton README、範例 `.env.example`、shell / Python 樣板與 reporting / finops 子模組結構。
- 驗證：存在 `.planning/CONTEXT.md`、`ROADMAP.md`、`STATE.md`，以及 `automation/finops/`、`automation/reporting/`、`automation/shared/` 等基礎結構。
- 影響範圍：`06-DevTools/.planning/`、`06-DevTools/automation/`、根目錄 `.planning/STATE.md`。

## 技術限制

- 不提交真實雲端 credentials、API token、SSH keys、DB 密碼
- 第一版只建立 skeleton，不直接連線正式 AWS / GCP / Cloudflare / DB
- 盡量使用 shell / Python 作為通用腳本語言
- 需保留 `.env.example` 與 `config.example.*` 型態的範例配置

## Forbidden Zones

- 不覆寫既有 `06-DevTools/scripts/` 中已在使用的部署腳本
- 不把個人機器路徑、帳號資訊或存取憑證寫入 repo
- 不假設所有專案共用同一種部署方式或單一雲平台
