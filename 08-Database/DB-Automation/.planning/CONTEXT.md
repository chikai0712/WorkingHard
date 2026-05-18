# DB-Automation — Context

## 專案範圍

`08-Database/DB-Automation/` 用於建立資料庫自動化、監控與維運骨架。

目前這一輪聚焦於：
- MSSQL / MySQL 監控
- Kubernetes 部署
- Prometheus + Grafana
- 業界常見 exporter 與 dashboard 模板
- Helm / GitOps 可直接套用版
- Database backup / recovery 驗證 skeleton
- DB migration skeleton
- Auto-remediation 與維運檢查 skeleton

## 當前任務規格

## 任務：網路設備一致化與 Ansible check 骨架
- 目標：針對 FortiGate FW、Cisco Core / L2 / L3 Switch、F5 內外網 LB 建立一致化管理骨架，將設備名稱與 IP 抽成環境變數，並以 Ansible 框架執行檢查。
- 方法：建立 `ansible/` 結構、inventory、group_vars、host_vars 範例、roles 與 playbook，先支援設備分類、環境變數化與 check-only 流程，不直接更動設備設定。
- 驗證：存在 Ansible inventory、vars、playbooks、roles、README，且可依設備類型區分 Forti / Cisco / F5，並保留內外網 LB 對應欄位。
- 影響範圍：`08-Database/DB-Automation/ansible/`、`.planning/`。

## 任務：K8s Helm / GitOps DB 監控可套用版
- 目標：在 `DB-Automation` 中建立可直接套用的 Kubernetes 監控骨架，涵蓋 MSSQL 與 MySQL，並支援 Helm / Kustomize / Argo CD / Flux 路線。
- 方法：建立 namespace、Helm values、exporter manifests、PrometheusRule、Grafana provisioning、Kustomize base/overlays、Argo CD Application 與 Flux Kustomization 範例。
- 驗證：存在 `.planning/` 文件、`monitoring/k8s/` 監控目錄、Helm values、Kustomize overlays 與 GitOps manifests。
- 影響範圍：`08-Database/DB-Automation/.planning/`、`08-Database/DB-Automation/monitoring/k8s/`。

## 任務：建立 DB AI 分析與 RAG 導入規格
- 目標：在 `DB-Automation` 範圍內定義可被 AI 分析與 RAG 使用的 DB 維運知識來源、事件摘要模型與安全邊界，支援 migration、backup、monitoring、remediation 與 network check 場景。
- 方法：先整理文件型知識、監控事件型知識、變更與驗證型知識的資料來源與 metadata；以 example config 與設計文件方式建立導入 skeleton，不直接連線真實 DB、真實告警平台或正式資料集。
- 驗證：存在 DB AI / RAG 導入文件、dataset/source example config，且 planning 文件同步更新。
- 影響範圍：`08-Database/DB-Automation/.planning/`、`08-Database/DB-Automation/` 文件層。

## 任務：補齊整個專案缺少的 MySQL skeleton
- 目標：補齊 `DB-Automation` 內 backup / recovery、migration 與 AI / RAG 文件中缺少的 MySQL 專屬骨架，讓專案不只在監控層有 MySQL，也能在資料維運模板層對齊。
- 方法：盤點所有僅有 MSSQL 或僅有通用模板的檔案；補上 MySQL 專屬 `.env` / metadata / retention / restore drill / Flyway config / precheck / postcheck / version SQL example，以及在 AI / RAG 文件與 examples 中補上 MySQL 專屬來源與摘要範例；維持 skeleton 模式，不連真實 DB。
- 驗證：存在 MySQL 專屬 backup / migration 範本與 README 說明，AI / RAG 文件能明確列出 MySQL 來源與摘要樣板，且 planning 文件同步更新。
- 影響範圍：`08-Database/DB-Automation/backup-recovery/`、`migration/`、`ai-rag/`、`.planning/`。

## 任務：補齊 MySQL evidence schemas 與 dataset ingestion
- 目標：讓 MySQL restore evidence、precheck/postcheck evidence 也能以結構化 schema / example 進入 `ai-rag/`，並讓 summary ingestion 預設收進新的 MySQL summary examples。
- 方法：在 `ai-rag/` 新增 MySQL restore evidence schema / example、MySQL precheck evidence schema / example、MySQL postcheck evidence schema / example；更新 README、source catalog 與 ingestion 腳本，將 MySQL summary example 也納入 combined dataset。
- 驗證：存在 MySQL evidence schema / example 檔案，`ingest_db_summaries.py` 會輸出包含 MySQL backup / migration summaries 的 dataset，且 planning 文件同步更新。
- 影響範圍：`08-Database/DB-Automation/ai-rag/`、`.planning/`。

## 任務：升級 schema-aware validator 與 evidence ingestion
- 目標：讓 `validate_db_summary.py` 能依 schema 驗證 summary 與 evidence examples，並讓 `ingest_db_summaries.py` 可選擇把 evidence records 一起收進 dataset。
- 方法：實作不依賴外部套件的輕量 schema validator，支援目前 schema 所需的 `type`、`required`、`properties`、`items`、`enum`、`const`；將 summary 與 evidence example 對應到 schema 檔；在 ingestion 腳本加入可選參數控制是否一併收 evidence records，並更新 dataset example 與 README 說明。
- 驗證：`validate_db_summary.py` 成功驗證 summary 與 evidence examples；`ingest_db_summaries.py` 在預設與含 evidence 模式皆可成功產出 dataset；planning 文件同步更新。
- 影響範圍：`08-Database/DB-Automation/ai-rag/`、`.planning/`。

## 任務：升級 evidence-aware query 與 producer artifact output
- 目標：讓 `query_local_rag.py` 能辨識 summary 與 evidence records 的差異，並讓 `backup-recovery/verify_backup.sh`、`migration/migrate.sh` 可直接輸出更貼近 schema 的 summary / evidence artifact。
- 方法：在 query 端納入 `record_type` 與 evidence 欄位文字，改善 evidence 可搜尋性；在 backup / migration producer 加入 summary 以外的 evidence output 路徑與 payload 生成，至少支援 MySQL restore evidence 與 MySQL pre/postcheck evidence skeleton。
- 驗證：query 可命中 evidence records 並顯示 record 類型；backup / migration 腳本可輸出符合既有 summary / evidence schema 的 artifact example；planning 文件同步更新。
- 影響範圍：`06-DevTools/automation/ai-rag/`、`08-Database/DB-Automation/backup-recovery/`、`08-Database/DB-Automation/migration/`、`.planning/`。

## 任務：讓 monitoring / ansible producer 輸出 artifact 並支援 directory scanner
- 目標：讓 `monitoring/k8s/generate_monitoring_summary.py`、`ansible/generate_ansible_summary.py` 也能直接輸出 schema-aligned artifact，並讓 `ingest_db_summaries.py` 可掃描 producer 目錄自動匯入這些輸出。
- 方法：擴充 monitoring / ansible producer 的輸出模式與預設 artifact path；在 `ai-rag/` 補 producer artifact 目錄與 directory scanner 邏輯，讓 ingestion 可從指定目錄收集 summary / evidence records，並保留 example-based fallback。
- 驗證：monitoring / ansible producer 可輸出 summary artifact；`ingest_db_summaries.py --scan-dir ...` 可將 producer 輸出匯入 dataset；planning 文件同步更新。
- 影響範圍：`08-Database/DB-Automation/monitoring/k8s/`、`ansible/`、`ai-rag/`、`.planning/`。

## 任務：串接 control-plane action 後自動 producer + scanner ingestion
- 目標：讓 control-plane 在 `db-ops` action 完成後，不只 refresh example dataset，而是先輸出對應 producer artifact 到 `producer-artifacts/`，再觸發 scanner ingestion。
- 方法：更新 `06-DevTools/automation/control-plane/server.py` 的 post-action refresh 流程，根據 action 映射執行 backup / migration / monitoring / ansible producer，將 artifact 寫入 `08-Database/DB-Automation/ai-rag/producer-artifacts/`，之後再執行 validator 與 `ingest_db_summaries.py --scan-dir ...`。
- 驗證：control-plane 執行 `db-ops` action 後，`producer-artifacts/` 會出現對應 artifact，且 scanner dataset 會刷新並納入這些輸出。
- 影響範圍：`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/`、`.planning/`。

## 任務：補齊 monitoring / ansible evidence schemas 與 artifact output
- 目標：讓 `monitoring/k8s` 與 `ansible` 不只提供 summary artifact，也能提供結構化 evidence artifact，讓 scanned dataset 與 query/recommendation 對各模組更一致。
- 方法：在 `ai-rag/` 新增 monitoring / ansible evidence schema 與 example；更新對應 producer 支援 evidence 輸出；升級 validator、scanner 與 control-plane producer mapping，讓本地 action refresh 也能納入這兩類 evidence。
- 驗證：`generate_monitoring_summary.py`、`generate_ansible_summary.py` 可輸出 summary + evidence artifact；`validate_db_summary.py` 可驗證新 schema/example；`ingest_db_summaries.py --scan-dir ... --include-evidence` 可匯入新 evidence records。
- 影響範圍：`08-Database/DB-Automation/monitoring/k8s/`、`ansible/`、`ai-rag/`、`06-DevTools/automation/control-plane/`、`.planning/`。

## 任務：讓 query / recommendation 優先讀 scanned dataset
- 目標：讓 `query_local_rag.py` 與 control-plane recommendation 優先使用 `db-summary-dataset.scanned.example.json`，使本地 AI/RAG 回應更貼近最新 producer / action 結果，而不是以 example dataset 為主。
- 方法：在 query 端加入 scanned dataset 優先載入邏輯，必要時再 fallback 到 example datasets；在 control-plane recommendation 組裝中，先讀 scanned dataset 與最近 action 相關 records，再補 example summaries 作為回退來源。
- 驗證：`query_local_rag.py --include-evidence` 能命中 scanned local artifacts；control-plane recommendation 可優先顯示 scanned dataset 內容，且 planning 文件同步更新。
- 影響範圍：`06-DevTools/automation/ai-rag/`、`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/`、`.planning/`。

## 任務：加入 producer artifact namespacing / cleanup / scoped dataset
- 目標：讓 `producer-artifacts/` 不再使用單一平面檔名累積，而是依 action / 時間建立 scope，並可自動清理舊 scope，同時產出 scoped dataset 供 recommendation / query 使用。
- 方法：在 control-plane 為每次 action 建立 scope 目錄與 scoped dataset 路徑；讓 producer output 寫入該 scope；在 ingestion 補 recursive scan 與 scope/filter 參數；加入簡單 retention cleanup 規則，保留最近 N 個 scope；並讓 latest scoped dataset 成為優先讀取來源之一。
- 驗證：control-plane action 後會建立新的 scope 目錄與 scoped dataset；舊 scope 可依 retention 規則清理；query / recommendation 可優先讀取 latest scoped dataset。
- 影響範圍：`06-DevTools/automation/control-plane/`、`06-DevTools/automation/ai-rag/`、`08-Database/DB-Automation/ai-rag/`、`.planning/`。

## 任務：讓 latest scoped query / recommendation 不混 example records
- 目標：讓 `db-summary-dataset.latest-scoped.example.json` 只包含最近 action scope 的 records，且 query / recommendation 在 scoped 模式下不混入 example dataset 或 chunk examples。
- 方法：在 ingestion 加入 scoped-only 輸出模式；control-plane 產生 latest scoped dataset 時使用 scoped-only；query 增加 scoped-only 模式並在 latest scoped dataset 存在時可只讀該 dataset；recommendation 在 `latest_only=true` 時只讀 latest scoped dataset。
- 驗證：latest scoped dataset 僅包含 scoped artifact records；`query_local_rag.py --scoped-only` 不混入 example records；control-plane `latest_only=true` recommendation 僅反映 latest scoped dataset。
- 影響範圍：`08-Database/DB-Automation/ai-rag/`、`06-DevTools/automation/ai-rag/`、`06-DevTools/automation/control-plane/`、`.planning/`。

## 任務：重整 control-plane server.py 結構但不改功能
- 目標：將 `06-DevTools/automation/control-plane/server.py` 從壓縮寫法整理為可維護結構，不改變既有 API、scoped artifact、manifest、history、query/recommendation 與 refresh 行為。
- 方法：保留現有功能與回傳格式，將常數、helper、action/recommendation/manifest/history 邏輯拆成具名函式與清晰資料結構；整理 import、命名與 handler 內容；以 compile、lint 與函式級驗證確認行為等價。
- 驗證：`server.py` compile 通過、lint 無誤；函式級驗證確認 `db-ops` action、latest scoped dataset、recommendation source 與 manifest output 行為不變。
- 影響範圍：`06-DevTools/automation/control-plane/`、`.planning/`。

## 技術限制

- 不直接寫入真實帳密
- Secret 以 Kubernetes Secret / External Secret 路線處理
- 第一版先建立可套用骨架，不直接連線真實 DB
- backup / recovery / migration / remediation 第一版只提供 skeleton 與範例設定，不對正式 DB 執行操作

## Forbidden Zones

- 不提交真實 DB credentials
- 不假設 MSSQL 與 MySQL 使用完全相同 exporter
- 不在第一版硬綁單一雲平台
