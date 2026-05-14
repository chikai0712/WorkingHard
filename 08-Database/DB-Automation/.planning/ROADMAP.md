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

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0 最小重建 | 2/2 | ✅ Complete |
| Phase 1 K8s Prometheus + Grafana DB 監控 | 2/2 | ✅ Complete |
| Phase 2 Helm / GitOps 可直接套用版 | 2/2 | ✅ Complete |
| Phase 3 網路設備一致化與 Ansible check | 2/2 | ✅ Complete |
| Phase 4 DB Backup + Migration 實戰版 skeleton | 3/3 | ✅ Complete |
