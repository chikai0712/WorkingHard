# GitOps Deployment Notes

## Kustomize

- `kustomize/base/`：共用基礎資源
- `kustomize/overlays/dev/`：開發環境
- `kustomize/overlays/prod/`：正式環境

## Argo CD

- 套用 `gitops/argocd/application-dev.yaml`
- 套用 `gitops/argocd/application-prod.yaml`

## Flux

- 套用 `gitops/flux/kustomization-dev.yaml`
- 套用 `gitops/flux/kustomization-prod.yaml`

## 注意事項

- Helm chart 本體使用 `kube-prometheus-stack`
- 真實 exporter credentials 請改接 Secret / ExternalSecret
- 若 MSSQL 跑在 Windows host，建議另外部署 `windows_exporter`
