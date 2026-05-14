# Helm Usage

## Install kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n db-monitoring \
  --create-namespace \
  -f values.common.yaml \
  -f values.dev.yaml
```

## Notes

- `values.common.yaml` 放共用設定
- `values.dev.yaml` / `values.prod.yaml` 覆蓋不同環境
- 真實密碼與 secrets 請改由 Secret / ExternalSecret 注入
