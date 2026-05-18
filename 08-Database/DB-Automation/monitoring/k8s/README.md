# Kubernetes Prometheus + Grafana 監控骨架

此目錄提供 MSSQL / MySQL 的 K8s 監控與 GitOps 可套用骨架。

## 內容

- `base/`：namespace 等共用資源
- `helm/`：Helm values 與安裝說明
- `kustomize/`：base 與 dev/prod overlays
- `gitops/argocd/`：Argo CD Application 範例
- `gitops/flux/`：Flux Kustomization / HelmRelease 範例
- `grafana/`：datasource / dashboards provisioning
- `exporters/`：MSSQL / MySQL exporters
- `rules/`：PrometheusRule
- `docs/`：部署說明

## Architecture Principles

### 收集、儲存、展示、告警分層
監控系統應至少分成：
- exporters：把 DB 指標暴露出來
- Prometheus：收集與儲存時間序列
- Grafana：展示與探索
- PrometheusRule / Alertmanager：把資料轉成可行動的告警

### Monitoring summary producer 是 AI 導入橋接層
對 AI / RAG 來說，直接吃整份 Prometheus target 狀態或 raw alert payload 並不理想，因此這裡補 `generate_monitoring_summary.py`，先把 exporter / target / alert evidence 摘要化，再交由平台層 recommendation 與檢索流程使用。

### Environment overlay 是必要的
DB 監控通常在 dev / prod 的 retention、replica、告警門檻不同，因此 `base + overlays` 比單一 manifest 更可維護。

### GitOps 適合監控平面
監控資源本身也需要版本化與可追蹤，因此這裡同時提供 Argo CD / Flux 路徑，讓監控平面本身也能進入 declarative workflow。

## Shared Gate Mapping

monitoring 流程現在對齊 shared gate framework：
- source gate：manifest、values、overlay、rule schema 完整性
- security gate：secrets 邊界、告警對外整合、映像與依賴風險
- health gate：exporter readiness、Prometheus target health、rule firing 與 dashboard 可用性

共用模型可參考：
- `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md`
- `06-DevTools/automation/source-gate.example.yaml`
- `06-DevTools/automation/security-gate.example.yaml`
- `06-DevTools/automation/health-gate.example.yaml`

## 推薦使用方式
1. 先套用 `base/namespace.yaml`
2. 執行 source gate，確認 Helm values / overlays / manifests 完整
3. 執行 security gate，確認 secrets、映像與整合邊界
4. 使用 Helm 安裝 `kube-prometheus-stack`
5. 套用 exporters / monitors / rules
6. 使用 Kustomize overlays 區分 dev / prod
7. 若採 GitOps，改由 Argo CD 或 Flux 套用 overlays
8. deploy 後執行 health gate，驗證 targets / dashboards / alerts
