# Automation Control Plane

這是第一版統一管理介面 skeleton，用來集中查看與操作跨專案 automation 模組。

## Scope

目前 UI 以本地 JSON data source 模擬以下模組：
- CI / Jenkins Entry
- Release Control
- IaC Control
- DB Backup / Migration / Monitoring

## Design Principles

### 1. Control plane 與 action executor 分離
UI 與 recommendation panel 負責展示與輔助判讀，不直接等於執行權限。真正的動作仍透過受控白名單 adapter 觸發，避免把分析層與執行層混在一起。

### 2. Recommendation only by default
AI recommendation 的角色是幫助使用者快速定位原因、檢查項與相關文件，而不是直接替代變更審批與正式操作。

### 3. Shared vocabulary across modules
控制平面沿用 `pass / hold / block / rollback / fallback` 的決策語言，讓 Cloud / DB / Shared tooling 在同一個介面中仍能對齊治理語意。

### 4. 先 mock contract，再接真實 backend
先固定 `/api/actions` 與 `/api/recommendations` 的契約，可以讓前端、文件、RAG、summary producer 先對齊，再逐步接真實模型或事件來源。

### 5. Action 後 recommendation refresh
Control plane 在 action 完成後應重新載入 recommendation，而不是維持舊資料。這樣做可讓 dry-run、summary artifact 與 recommendation panel 保持同一個觀察節奏，即使現在仍是本地 skeleton，也先建立 refresh contract。

### 6. Action history 保存 explainable snapshot
除了即時 recommendation，control plane 也應保留最近幾次 action 的 recommendation source、policy、evidence count 與 top retrieval evidence snapshot，避免操作後上下文立即消失，讓使用者能回看本地判讀依據。

## What It Shows
- 模組清單
- gate 狀態（source / security / health）
- AI recommendation panel
- 基本 mock actions
- action result 面板
- recent action history snapshots

## Data Source Model
- `data/modules.json`: 模組狀態與 gate 資料來源
- `app.js`: 優先讀取 JSON，失敗時 fallback 到內建最小 state

這讓後續可以逐步改成：
- 由 shared gate config 生成
- 由本地掃描結果匯入
- 由真實 API 狀態驅動

## Local Dry-Run Adapter
- `server.py`: 本地控制平面 server，提供靜態頁面、`/api/actions` 與 `/api/recommendations`
- `/api/actions`: 僅允許白名單中的安全 skeleton dry-run 命令
- `/api/recommendations`: 提供本地 mock recommendation payload，對齊 AI / RAG recommendation contract
- DB 相關 action 完成後，server 會自動執行本地 summary validate / ingest refresh
- monitoring / ansible 類型的 action 也會將 producer artifact 寫入 `producer-artifacts/`
- action history 會持久化到 `data/action-history.json`，並支援依 module 篩選、排序與清除
- recommendation 會優先以最近 action 的 scoped artifacts 與 action scope 建立本地判讀內容，降低 example 與舊 artifact 混雜
- `producer-artifacts/` 會以 `session/action` 子目錄命名，並保留最近幾個 session，避免長期堆積與不同 action 檔名碰撞
- 每次 action 會產出 `action-manifest.json`，供 recommendation 與 history snapshot 共用同一份 action metadata
- manifest 會附帶 artifact file count / total bytes，以及 latest-scoped / scanned dataset 的 checksum、record count、size 摘要
- history 支援 only-changed diff 與固定兩筆 A/B compare，方便追蹤 recommendation / evidence 變化
- recommendation 會附帶 top retrieval evidence 與 schema/artifact metadata，幫助使用者理解本地 recommendation 依據
- 若 API 不可用，前端會自動 fallback 到 mock action result 與 fallback recommendation

### Supported Safe Commands
- `02-Cloud-Deploy/automation/cicd/pipeline.sh` for `run-source`, `run-security`, `run-health`
- `02-Cloud-Deploy/automation/release/release.sh status|deploy` for `prepare-release`, `review-approval`, `run-smoke`
- `02-Cloud-Deploy/automation/iac/terraform_wrapper.sh . plan|apply-dry-run` for `run-plan`, `run-policy`, `run-post-apply`
- `08-Database/DB-Automation/backup-recovery/verify_backup.sh`
- `08-Database/DB-Automation/migration/migrate.sh precheck`
- `08-Database/DB-Automation/monitoring/k8s/generate_monitoring_summary.py`
- `08-Database/DB-Automation/ansible/generate_ansible_summary.py`

### Start Locally
```bash
python3 "/Users/ckchiu/Desktop/Project/06-DevTools/automation/control-plane/server.py"
```

然後開啟：
- `http://127.0.0.1:8765`

## What It Does Not Do Yet
- 不直接呼叫 Jenkins 正式 job
- 不直接呼叫 GitHub Actions
- 不直接連線 AWS / GCP / Cloudflare / DB
- 不執行真實 deploy、migration、restore、failover

## File Layout
- `index.html`: 主畫面
- `styles.css`: UI 樣式
- `app.js`: JSON loader、fallback state 與 API/mock actions
- `server.py`: 本地靜態 server + dry-run adapter
- `data/modules.json`: 本地 JSON data source
- `AI-RECOMMENDATION-SPEC.md`: AI recommendation API / UI contract
- `recommendation-response.example.json`: recommendation response example

## Next Expansion Ideas
- 接 shared gate example config 產生動態狀態
- 接 Jenkins / GitHub API 做真實 pipeline status
- 接 shell / Python skeleton 做受控 mock-run / dry-run
- 加入操作歷史、RACI owner 與 approval panel
- 新增 filter/search 與 module detail subviews
- 接入 AI recommendation panel 與 `/api/recommendations` mock/backend adapter
- 以 confidence / recommended_policy / related_artifacts 呈現 AI 輔助判讀
- 從本地 summary JSON artifacts 生成 recommendation，再逐步切換到真實 RAG backend
- 顯示 recommendation source、evidence count 與 artifact count，提升可審核性與 traceability
- 顯示 top retrieval evidence / score，逐步走向 explainable recommendation
