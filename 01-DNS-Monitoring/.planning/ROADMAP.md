# DNS/CDN Monitor — Roadmap

## Overview

將 `01-DNS-Monitoring/` 在架構與規劃層統一定位為 **DNS/CDN Monitor**，整合既有 DNS / Domain 監控、區域完整性探測、HA / Multi-NS 驗證與 CDN 相關能力，並為未來的 **Multi-CDN + RUM 動態選路** 建立完整規格。

### Phase 0：Planning 初始化
**Goal**: 建立 `01-DNS-Monitoring` 子專案 planning 文件。

- [x] 建立 `.planning/CONTEXT.md`
  - 驗證方式：檔案存在且包含任務規格、限制與 Forbidden Zones。
  - 相關路徑：`01-DNS-Monitoring/.planning/CONTEXT.md`
- [x] 建立 `.planning/ROADMAP.md`
  - 驗證方式：存在 phases、驗證方式與進度表。
  - 相關路徑：`01-DNS-Monitoring/.planning/ROADMAP.md`
- [x] 建立 `.planning/STATE.md`
  - 驗證方式：記錄當前任務、User Story、Acceptance Criteria 與下一步。
  - 相關路徑：`01-DNS-Monitoring/.planning/STATE.md`

### Phase 1：命名與範圍重整規格
**Goal**: 將 `01-DNS-Monitoring` 在規劃層重新定位為 `DNS/CDN Monitor`。

- [x] 定義統一命名規則
  - 驗證方式：文件中明確說明 `DNS/CDN Monitor` 為架構名稱、`01-DNS-Monitoring/` 為目錄名稱。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 `GlobalpingChecker` 的新角色邊界
  - 驗證方式：文件中明確標示其為 `01-DNS-Monitoring` 子模組，而非平行主專案。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 整理現有子模組能力地圖
  - 驗證方式：文件中列出 Domain Monitoring、Regional Integrity Checks、Multi-NS / HA、Host DNS、CDN / failover 相關能力。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

### Phase 2：Multi-CDN + RUM 高階架構規格
**Goal**: 定義由網站或 App 啟動階段進行 Multi-CDN RUM 探測並選擇最佳 CDN 的高階架構。

- [x] 定義 RUM probe 流程
  - 驗證方式：文件中明確描述每個 CDN 執行 3 次探測、取平均值的流程。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 Decision Layer 與 Policy Layer
  - 驗證方式：文件中明確區分 probe、ranking、policy、fallback 與前端載入流程。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義前端 / App bootstrap 模式
  - 驗證方式：文件中列出 Web、App、Hybrid 三種可能模式與建議採用方向。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

### Phase 3：資料流、觀測性與治理規格
**Goal**: 定義 RUM-based Multi-CDN decisioning 的資料流、紀錄欄位、觀測性與治理邊界。

- [x] 定義 RUM event schema 草案
  - 驗證方式：文件中列出至少 region、isp、device、cdn、latency、fallback_reason 等欄位。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 observability / analytics 需求
  - 驗證方式：文件中列出 performance、availability、decision accuracy、fallback frequency 等觀測需求。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義治理與風險控制
  - 驗證方式：文件中明確列出 probe 成本、cache 影響、誤判風險與 production rollout guardrails。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

### Phase 4：導入路線圖與實作前分解
**Goal**: 將規格收斂成後續實作可用的 phased rollout plan。

- [x] 定義 MVP
  - 驗證方式：文件中明確列出第一版僅做 client probe + local ranking + server logging。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 Beta / Production 路線
  - 驗證方式：文件中列出 recommendation-only、server-assisted decision、controlled routing rollout 的階段。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 downstream integration map
  - 驗證方式：文件中說明未來與 control plane、DNS / CDN provider、App / Web frontend 的整合點。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

### Phase 5：MVP 實作規格草案
**Goal**: 針對第一版 Multi-CDN + RUM MVP，定義可實作的模組分工、SDK / API / ingestion contract 與驗證方式。

- [x] 定義 MVP 模組分工
  - 驗證方式：文件中明確區分 front-end/App probe SDK、`domain-monitoring-system`、`GlobalpingChecker`、control plane 的責任。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 probe SDK contract
  - 驗證方式：文件中存在 probe config、輸入規則與 probe output contract。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 decision API 與 event ingestion contract
  - 驗證方式：文件中存在 `probe-config`、`rum-events` API contract 與最小欄位集合。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 MVP 驗證方式與 feature flag model
  - 驗證方式：文件中存在 functional、data、risk validation 與 rollout flags。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

### Phase 6：MVP 模組承接決策草案
**Goal**: 為第一版 MVP 明確指定既有模組的承接責任，避免實作落點混亂。

- [x] 定義承接決策原則
  - 驗證方式：文件中明確列出最小改動、讀寫分離、避免角色混淆與保留演進路徑等原則。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義推薦承接方案
  - 驗證方式：文件中明確指定 front-end/App、`domain-monitoring-system`、`GlobalpingChecker`、control plane 各自責任。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義替代方案與不建議方案
  - 驗證方式：文件中列出 Option B / Option C 與其優缺點。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義風險與下一步
  - 驗證方式：文件中列出風險、緩解方式與下一個執行步驟。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

### Phase 7：domain-monitoring-system API 落點規格
**Goal**: 依現有 FastAPI 結構，定義 `probe-config` 與 `rum-events` 的具體 route / schema / storage 落點。

- [x] 盤點現有 app/router/model/schema 結構
  - 驗證方式：文件中明確說明 `app/main.py`、`models.py`、`schemas.py`、`database.py` 的現況與限制。
  - 相關路徑：`01-DNS-Monitoring/domain-monitoring-system/app/`
- [x] 定義 `probe-config` API 落點
  - 驗證方式：文件中明確指定 `GET /api/v1/cdn/probe-config` 的 route 與 schema 落點。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義 `rum-events` API 與 storage 落點
  - 驗證方式：文件中明確指定 `POST /api/v1/cdn/rum-events` 的 route、schema 與 `MonitoringEvent` 落點策略。
  - 相關路徑：`01-DNS-Monitoring/.planning/`
- [x] 定義禁止先做的重構範圍與實作前驗證清單
  - 驗證方式：文件中列出 forbidden scope 與 implementation readiness checklist。
  - 相關路徑：`01-DNS-Monitoring/.planning/`

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0 Planning 初始化 | 3/3 | ✅ Complete |
| Phase 1 命名與範圍重整規格 | 3/3 | ✅ Complete |
| Phase 2 Multi-CDN + RUM 高階架構規格 | 3/3 | ✅ Complete |
| Phase 3 資料流、觀測性與治理規格 | 3/3 | ✅ Complete |
| Phase 4 導入路線圖與實作前分解 | 3/3 | ✅ Complete |
| Phase 5 MVP 實作規格草案 | 4/4 | ✅ Complete |
| Phase 6 MVP 模組承接決策草案 | 4/4 | ✅ Complete |
| Phase 7 domain-monitoring-system API 落點規格 | 4/4 | ✅ Complete |
