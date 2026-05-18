# DB-Automation — Roadmap

## Overview

重建最小骨架後，直接建立 Kubernetes 上的 Prometheus + Grafana DB 監控可套用版，支援 Helm / GitOps。

### Phase 0：最小重建 ✅
**Goal**: 重建 planning 與 monitoring 最小骨架。

- [x] 建立 `.planning/`
  - 驗證方式：`CONTEXT.md`、`ROADMAP.md`、`STATE.md` 存在。
  - 相關路徑：`08-Database/DB-Automation/.planning/`
- [x] 建立 `monitoring/k8s/` 基本目錄
  - 驗證方式：K8s 監控目錄存在。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/`

### Phase 1：K8s Prometheus + Grafana DB 監控 ✅
**Goal**: 建立 MSSQL / MySQL 的 K8s 監控骨架。

- [x] 建立 Prometheus / Grafana / exporter 結構
  - 驗證方式：存在 namespace、values、dashboards、rules。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/`
- [x] 建立標準模板與部署說明
  - 驗證方式：存在 dashboard provisioning 與 docs。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/grafana/`、`docs/`

### Phase 2：Helm / GitOps 可直接套用版 ✅
**Goal**: 建立 Kustomize overlays 與 GitOps manifests。

- [x] 建立 Helm values / release 使用方式
  - 驗證方式：存在可分環境套用的 values 檔。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/helm/`
- [x] 建立 Kustomize / Argo CD / Flux manifests
  - 驗證方式：存在 base、dev/prod overlays、Argo CD Application、Flux Kustomization。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/kustomize/`、`gitops/`

### Phase 3：網路設備一致化與 Ansible check ✅
**Goal**: 建立 Forti / Cisco / F5 的 check-only 自動化骨架。

- [x] 建立 Ansible inventory / vars 骨架
  - 驗證方式：存在設備分類、名稱/IP 環境變數欄位與內外網 LB 對應欄位。
  - 相關路徑：`08-Database/DB-Automation/ansible/inventory/`、`group_vars/`
- [x] 建立 playbook / roles / README
  - 驗證方式：存在 check-only playbook、vendor roles 與使用說明。
  - 相關路徑：`08-Database/DB-Automation/ansible/playbooks/`、`roles/`

### Phase 4：DB Backup + Migration 實戰版 skeleton 🔄
**Goal**: 讓 `backup-recovery/` 與 `migration/` 從初版 skeleton 提升到可套用模板層級。

- [x] 建立 backup / restore drill / checklist / retention 範本
  - 驗證方式：存在 backup metadata、restore checklist、retention policy 或對應範本。
  - 相關路徑：`08-Database/DB-Automation/backup-recovery/`
- [x] 建立 migration config / versioning / pre-post check 範本
  - 驗證方式：存在 migration conf、version SQL、pre/post check 範本或對應說明。
  - 相關路徑：`08-Database/DB-Automation/migration/`
- [x] 更新 shell skeleton 與實務 README
  - 驗證方式：`verify_backup.sh`、`migrate.sh` 可輸出新模板資訊，且 shell 語法檢查通過。
  - 相關路徑：`08-Database/DB-Automation/backup-recovery/`、`migration/`
- [x] 將 shared gates 套入 backup / migration / monitoring
  - 驗證方式：相關 README / 範本至少包含 source gate、security gate、health gate 的對應描述或欄位。
  - 相關路徑：`08-Database/DB-Automation/backup-recovery/`、`migration/`、`monitoring/k8s/`
- [x] 補齊 MySQL 專屬 backup / migration skeleton
  - 驗證方式：存在 MySQL 專屬 backup metadata / retention / restore drill、Flyway config、pre/post check、version SQL example 與 README 說明。
  - 相關路徑：`08-Database/DB-Automation/backup-recovery/`、`migration/`

### Phase 5：DB AI Analysis + RAG Enablement 🔄
**Goal**: 讓 DB 維運知識、事件摘要與變更證據可被平台 AI / RAG 層安全使用。

- [ ] 定義 DB AI / RAG source catalog
  - 驗證方式：存在 DB source catalog 或文件，區分 docs / events / validation evidence 與敏感度。
  - 相關路徑：`08-Database/DB-Automation/`
- [ ] 建立 DB dataset / metadata skeleton
  - 驗證方式：存在 dataset example config、metadata schema、ingestion guidance。
  - 相關路徑：`08-Database/DB-Automation/`
- [ ] 將 AI 導入策略連結到 backup / migration / monitoring / remediation / ansible
  - 驗證方式：文件明確列出各模組可供 AI 使用的資料與不可導入資料。
  - 相關路徑：`08-Database/DB-Automation/`
- [ ] 建立 DB summary schemas 與 evidence examples
  - 驗證方式：存在 backup / migration / monitoring / remediation / ansible 的 summary schema 或 evidence example。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 補齊 MySQL restore / precheck / postcheck evidence schemas
  - 驗證方式：存在 MySQL restore evidence、precheck evidence、postcheck evidence 的 schema 與 example。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 讓 summary ingestion 預設納入 MySQL examples
  - 驗證方式：`ingest_db_summaries.py` 產出的 dataset 包含 MySQL backup / migration summary example。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 升級 schema-aware validator，驗證 summary 與 evidence
  - 驗證方式：`validate_db_summary.py` 可依 schema 驗證 summary 與 MySQL evidence examples。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 讓 ingestion 可選擇納入 evidence records
  - 驗證方式：`ingest_db_summaries.py --include-evidence` 可輸出包含 evidence records 的 dataset。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 升級 query，辨識 summary / evidence records
  - 驗證方式：`query_local_rag.py` 可利用 `record_type` 與 evidence 內容提升命中結果可讀性。
  - 相關路徑：`06-DevTools/automation/ai-rag/`
- [x] 讓 backup / migration producer 直接輸出 evidence artifact
  - 驗證方式：`verify_backup.sh`、`migrate.sh` 可額外輸出符合 MySQL restore / precheck / postcheck schema 的 artifact。
  - 相關路徑：`08-Database/DB-Automation/backup-recovery/`、`migration/`
- [x] 讓 monitoring / ansible producer 輸出 schema-aligned artifact
  - 驗證方式：`generate_monitoring_summary.py`、`generate_ansible_summary.py` 可直接輸出 summary artifact。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/`、`ansible/`
- [x] 建立 directory scanner，自動匯入 producer 輸出
  - 驗證方式：`ingest_db_summaries.py --scan-dir ...` 可將 producer 目錄中的 summary / evidence artifact 納入 dataset。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 串接 control-plane action 後自動 producer output
  - 驗證方式：`db-ops` action 完成後會在 `producer-artifacts/` 產生對應 artifact。
  - 相關路徑：`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/`
- [x] 串接 control-plane action 後自動 scanner ingestion
  - 驗證方式：`db-ops` action 完成後，scanner dataset 會自動刷新並納入 producer 輸出。
  - 相關路徑：`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/`
- [x] 補齊 monitoring / ansible evidence schema 與 example
  - 驗證方式：存在 monitoring / ansible evidence schema 與 example，且 validator 可通過。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`
- [x] 讓 monitoring / ansible producer 輸出 evidence artifact
  - 驗證方式：`generate_monitoring_summary.py`、`generate_ansible_summary.py` 可額外輸出 evidence artifact。
  - 相關路徑：`08-Database/DB-Automation/monitoring/k8s/`、`ansible/`
- [x] 升級 scanner / control-plane 納入 monitoring / ansible evidence
  - 驗證方式：scanner dataset 與 control-plane refresh 可納入 monitoring / ansible evidence records。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`、`06-DevTools/automation/control-plane/`
- [x] 讓 query 優先讀 scanned dataset
  - 驗證方式：`query_local_rag.py --include-evidence` 可優先命中 scanned local artifacts。
  - 相關路徑：`06-DevTools/automation/ai-rag/`、`08-Database/DB-Automation/ai-rag/`
- [x] 讓 recommendation 優先使用 scanned dataset
  - 驗證方式：control-plane recommendation 可優先顯示 scanned dataset records 與最近 artifact metadata。
  - 相關路徑：`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/`
- [x] 加入 artifact namespacing 與 scoped output
  - 驗證方式：control-plane action 後會建立 scope 目錄並將 producer artifact 寫入該 scope。
  - 相關路徑：`06-DevTools/automation/control-plane/`、`08-Database/DB-Automation/ai-rag/producer-artifacts/`
- [x] 加入 cleanup / retention 與 scoped scanner ingestion
  - 驗證方式：ingestion 可掃描 scope 目錄，且 control-plane 可清理舊 scope 並產出 scoped dataset。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`、`06-DevTools/automation/control-plane/`
- [x] 讓 latest scoped dataset 採 scoped-only 輸出
  - 驗證方式：`db-summary-dataset.latest-scoped.example.json` 僅包含 scoped artifact records，不含 example dataset records。
  - 相關路徑：`08-Database/DB-Automation/ai-rag/`、`06-DevTools/automation/control-plane/`
- [x] 讓 query / recommendation 的 scoped 模式不混 example records
  - 驗證方式：`query_local_rag.py --scoped-only` 與 control-plane `latest_only=true` recommendation 僅反映 latest scoped dataset。
  - 相關路徑：`06-DevTools/automation/ai-rag/`、`06-DevTools/automation/control-plane/`
- [x] 重整 control-plane `server.py` 結構但不改功能
  - 驗證方式：compile / lint / 函式級驗證確認 API 與 scoped artifact / manifest / recommendation 行為維持不變。
  - 相關路徑：`06-DevTools/automation/control-plane/`

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0 最小重建 | 2/2 | ✅ Complete |
| Phase 1 K8s Prometheus + Grafana DB 監控 | 2/2 | ✅ Complete |
| Phase 2 Helm / GitOps 可直接套用版 | 2/2 | ✅ Complete |
| Phase 3 網路設備一致化與 Ansible check | 2/2 | ✅ Complete |
| Phase 4 DB Backup + Migration 實戰版 skeleton | 5/5 | ✅ Complete |
| Phase 5 DB AI Analysis + RAG Enablement | 20/24 | 🔄 In progress |
