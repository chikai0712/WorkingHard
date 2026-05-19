# STATE — DNS/CDN Monitor

## Current Task
## 任務：將 01-DNS-Monitoring 重新定位為 DNS/CDN Monitor，並規劃 Multi-CDN + RUM 動態選路架構
- 目標：把既有 `01-DNS-Monitoring/` 收斂成單一的 `DNS/CDN Monitor` 架構名稱，並建立由網站或 App 在 Loading 階段進行多 CDN 速度測試、每個 CDN 執行 3 次探測並取平均、再選擇最佳 CDN 的規格方案。
- 方法：先建立 planning 文件與分階段 roadmap，定義 naming、module boundaries、RUM probe、decision layer、policy layer、observability、fallback 與 rollout strategy；此輪只做文件與架構，不直接開發。
- 驗證：存在 `.planning/CONTEXT.md`、`ROADMAP.md`、`STATE.md`，且文件中已包含 User Story、Acceptance Criteria、風險與導入方向。
- 影響範圍：`01-DNS-Monitoring/.planning/`，未來可能影響相關 README、架構圖、前端 / App probe SDK 與 control plane 文件。

## User Story
身為網站或 App 的終端使用者，我希望系統能在載入初期測量多個 CDN 的實際速度，並自動選擇對我當下最快的 CDN，以便降低載入延遲並提升穩定性。

## Acceptance Criteria
1. 明確定義 `DNS/CDN Monitor` 的架構名稱，並保留 `01-DNS-Monitoring/` 為實體目錄名稱。
2. 明確定義 `GlobalpingChecker` 為 `01-DNS-Monitoring` 子模組，而非平行主專案。
3. 規格中明確描述 Multi-CDN RUM probe 流程：每個 CDN 測 3 次、計算平均值、選出最佳 CDN。
4. 規格中明確區分 DNS monitoring、CDN monitoring、RUM decisioning、policy control 與 observability 的責任邊界。
5. 文件中明確列出第一版僅做規劃，不直接實作 production routing、正式 SDK 或正式 CDN provider integration。

## API / Data Notes
- Input: DNS / CDN health、regional integrity signals、RUM probe results、policy rules、fallback rules
- Output: architecture docs、phase roadmap、future schema / API contract proposals
- Data Structure Changes: 本輪只新增 planning 文件
- Estimated Impact: Medium to Large
- Downstream Affected Use Cases: CDN routing、front-end loading bootstrap、regional performance optimization、control plane recommendation
- Required Verification: manual review of planning docs and architecture consistency

### [2026-05-18 15:10] — 完成 domain-monitoring-system API 落點規格
- **Phase**: Phase 7 — domain-monitoring-system API 落點規格
- **Status**: Complete
- **Done**: 讀取 `01-DNS-Monitoring/domain-monitoring-system/app/` 結構與 `main.py`、`models.py`、`schemas.py`、`database.py`，確認目前為單一 FastAPI app + module layout；據此在 `01-DNS-Monitoring/.planning/CONTEXT.md` 補齊 `probe-config` / `rum-events` 的 route、schema、storage 與 service 落點規格，建議 MVP 先把新 endpoint 掛在 `app/main.py`、schema 放 `app/schemas.py`、storage 先沿用 `MonitoringEvent` 並以 `event_type = "cdn_rum_decision"` 落在 `details` JSONB。
- **Next**: 若要更接近實作，可直接產出 `domain-monitoring-system/app/main.py`、`schemas.py`、`config.py` 的欄位級變更 spec，或開始做 mock endpoint implementation plan。
- **Blocker**: 尚未確認 `MonitoringEvent.domain_id` 對 app-side RUM event 的語意是否完全足夠；若未來一個 app 對應多個 CDN consumer context，可能需要 Beta 階段再拆專用 RUM event table。

### [2026-05-18 14:50] — 完成 DNS/CDN Monitor MVP 模組承接決策草案
- **Phase**: Phase 6 — MVP 模組承接決策草案
- **Status**: Complete
- **Done**: 在 `01-DNS-Monitoring/.planning/CONTEXT.md` 補齊 `DNS/CDN Monitor — MVP 模組承接決策草案`，定義承接原則、推薦方案（front-end/App 承接 probe SDK、`domain-monitoring-system` 承接 ingestion/logging、`GlobalpingChecker` 承接 external validation signals、control plane 承接 read-only dashboard）、替代方案與不建議方案，並列出風險與下一個執行步驟；同步在 `ROADMAP.md` 新增 Phase 6 並標記完成。
- **Next**: 讀 `01-DNS-Monitoring/domain-monitoring-system/` 現況，決定 `probe-config` 與 `rum-events` 最適合掛載的 API 模組位置，再產出該模組的 API 落點規格。
- **Blocker**: 尚未讀 `domain-monitoring-system` 內部程式結構，因此雖已決定它是推薦承接邊界，但還沒確認要掛在現有 app/router/service 的哪一層。

### [2026-05-18 14:35] — 完成 DNS/CDN Monitor MVP 實作規格草案
- **Phase**: Phase 5 — MVP 實作規格草案
- **Status**: Complete
- **Done**: 在 `01-DNS-Monitoring/.planning/CONTEXT.md` 補齊 `DNS/CDN Monitor — MVP 實作規格草案`，包含 MVP 目標 / 非目標、模組分工、probe SDK contract、`probe-config` / `rum-events` API contract、event ingestion 最小欄位集合、feature flag model、functional/data/risk validation 與後續拆解步驟；同步在 `ROADMAP.md` 新增 Phase 5 並標記完成。
- **Next**: 若進入真正執行，下一步應先選定 `domain-monitoring-system` 是否承接 ingestion API，再建立 Web probe JS skeleton 與 `probe-config` / `rum-events` mock endpoint。
- **Blocker**: 尚未確定 MVP 的實際承接程式位置與技術棧，例如 probe SDK 放在哪個前端專案、ingestion API 放在 `domain-monitoring-system` 的哪個模組、以及 event storage 採 table 還是 document-oriented schema。

### [2026-05-18 14:20] — 完成 DNS/CDN Monitor 的資料流、觀測性、治理與導入分解規格
- **Phase**: Phase 4 — 導入路線圖與實作前分解
- **Status**: Complete
- **Done**: 在 `01-DNS-Monitoring/.planning/CONTEXT.md` 補齊 RUM event schema 草案、probe/decision/experience/governance 四類 observability 指標、fallback / policy / rollout guardrails，以及與 front-end / App、DNS/CDN provider layer、後端與 control plane 的 downstream integration map；同步將 `ROADMAP.md` 的 Phase 3 與 Phase 4 標記完成。
- **Next**: 若要進入實作前一層，可開始拆 MVP 實作 spec，例如 probe SDK contract、decision API contract、event ingestion schema、feature flag model 與 logging pipeline。
- **Blocker**: 目前仍缺少第一版 MVP 的明確技術選型，例如 event ingestion 放在哪個模組、probe SDK 由哪個專案承接、以及 decision logging 要先落在 `domain-monitoring-system`、`GlobalpingChecker` 或新的 control-plane 邊界。

### [2026-05-18 14:05] — 補齊 DNS/CDN Monitor Phase 2 高階架構規格
- **Phase**: Phase 2 — Multi-CDN + RUM 高階架構規格
- **Status**: Complete
- **Done**: 在 `01-DNS-Monitoring/.planning/CONTEXT.md` 補齊 `DNS/CDN Monitor` 能力地圖、Multi-CDN + RUM 高階架構、資料流規格、前端 / App bootstrap 模式，以及 MVP / Beta / Production 導入方向；同步將 `ROADMAP.md` 的 Phase 1 與 Phase 2 標記完成，讓後續可直接進入資料流、觀測性與治理規格。
- **Next**: 補 RUM event schema 草案、observability / analytics 需求、fallback / policy guardrails，並定義與 control plane、DNS / CDN provider、App / Web frontend 的 downstream integration map。
- **Blocker**: 尚未決定第一版是否以 client-side local decision 為唯一 MVP，或保留最小 server-assisted recommendation 介面作為同時導入項。

### [2026-05-18 13:35] — 初始化 DNS/CDN Monitor planning 並建立 Multi-CDN RUM 規格任務
- **Phase**: Phase 1 — 命名與範圍重整規格
- **Status**: In progress
- **Done**: 在 `01-DNS-Monitoring/.planning/` 建立 `CONTEXT.md`、`ROADMAP.md`、`STATE.md`，將 `01-DNS-Monitoring` 對外定位統一為 `DNS/CDN Monitor`，並將 `GlobalpingChecker` 重新定義為子模組；同時建立 Multi-CDN + RUM 動態選路架構的規劃任務、Acceptance Criteria 與 phased roadmap。
- **Next**: 進一步補 `DNS/CDN Monitor` 的能力地圖、RUM probe / decision / policy / observability 高階架構圖與 MVP / Beta / Production rollout 規格。
- **Blocker**: 目前仍停留在規劃階段，尚未決定最終採用 client-side decision、server-assisted decision 或 hybrid 模式作為第一版落地方案。
