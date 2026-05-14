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

### Environment overlay 是必要的
DB 監控通常在 dev / prod 的 retention、replica、告警門檻不同，因此 `base + overlays` 比單一 manifest 更可維護。

### GitOps 適合監控平面
監控資源本身也需要版本化與可追蹤，因此這裡同時提供 Argo CD / Flux 路徑，讓監控平面本身也能進入 declarative workflow。

## 推薦使用方式
1. 先套用 `base/namespace.yaml`
2. 使用 Helm 安裝 `kube-prometheus-stack`
3. 套用 exporters / monitors / rules
4. 使用 Kustomize overlays 區分 dev / prod
5. 若採 GitOps，改由 Argo CD 或 Flux 套用 overlays
