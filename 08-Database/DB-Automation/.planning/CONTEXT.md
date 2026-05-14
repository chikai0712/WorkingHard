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

## 技術限制

- 不直接寫入真實帳密
- Secret 以 Kubernetes Secret / External Secret 路線處理
- 第一版先建立可套用骨架，不直接連線真實 DB
- backup / recovery / migration / remediation 第一版只提供 skeleton 與範例設定，不對正式 DB 執行操作

## Forbidden Zones

- 不提交真實 DB credentials
- 不假設 MSSQL 與 MySQL 使用完全相同 exporter
- 不在第一版硬綁單一雲平台
