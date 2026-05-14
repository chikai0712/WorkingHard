# Terraform CDN Setup — 部署資訊總覽

> 最後更新：2026-03-24
> 狀態：✅ 全部部署完成

---

## 架構圖

```
瀏覽器
  │  HTTPS (TLSv1.3 / HTTP/2)
  ▼
Route53 — www.clouddeployment168.site (A Alias)
  │
  ▼
CloudFront Distribution E1R2TGVSGFDRHF
  │  d3607y2v0cwxbj.cloudfront.net
  │  HTTP only → port 80
  ▼
sslip.io DNS — 34-180-110-77.sslip.io → 34.180.110.77
  │
  ▼
GCE VM — test-web-server (asia-northeast1-b)
  │  nginx 1.22.1, port 80
  ▼
/var/www/html/index.html
```

---

## GCP — GCE Origin

| 項目 | 值 |
|------|----|
| Project ID | `future-union-463404-t9` |
| VM 名稱 | `test-web-server` |
| Zone | `asia-northeast1-b`（東京）|
| Machine Type | `e2-micro` |
| OS | Debian 12 |
| 靜態 IP | `34.180.110.77` |
| Origin Domain | `34-180-110-77.sslip.io` |
| Web Server | nginx 1.22.1，port 80 HTTP only |
| 健康檢查端點 | `http://34.180.110.77/health` → `ok` |
| Service Account | `future-union-463404-t9-f3ce49c36a69.json` |

### 防火牆規則

| 規則名稱 | 方向 | 允許 | 來源 | 目標 Tag |
|----------|------|------|------|----------|
| `test-web-server-allow-web` | INGRESS | TCP 80, 443 | `0.0.0.0/0` | `allow-cloudfront` |
| `default-allow-ssh` | INGRESS | TCP 22 | `0.0.0.0/0` | — |
| `default-allow-icmp` | INGRESS | ICMP | `0.0.0.0/0` | — |

### nginx 設定（`/etc/nginx/sites-available/default`）

```nginx
server {
    listen 80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;

    location /health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### SSH 連線指令

```bash
gcloud compute ssh test-web-server \
  --zone=asia-northeast1-b \
  --project=future-union-463404-t9
```

---

## AWS — ACM 憑證

| 項目 | 值 |
|------|----|
| ARN | `arn:aws:acm:us-east-1:232313329609:certificate/dc7ecf08-776e-4b03-a913-750443028603` |
| Region | `us-east-1`（CloudFront 限制）|
| Domain | `www.clouddeployment168.site` |
| 驗證方式 | DNS 驗證（CNAME 加到 Route53）|
| 憑證狀態 | 有效 ✅ |
| 有效期限 | 2026-03-23 ~ 2026-10-06 |
| 發行機構 | Amazon RSA 2048 M01 |
| 最低 TLS 版本 | TLSv1.2_2021 |

---

## AWS — CloudFront Distribution

| 項目 | 值 |
|------|----|
| Distribution ID | `E1R2TGVSGFDRHF` |
| Domain | `d3607y2v0cwxbj.cloudfront.net` |
| Alias | `www.clouddeployment168.site` |
| 狀態 | `Deployed` ✅ |
| Price Class | `PriceClass_200`（亞太 + 美洲 + 歐洲）|
| IPv6 | 啟用 |
| HTTP 版本 | HTTP/2 |
| Default Root Object | `index.html` |

### Origin 設定

| 項目 | 值 |
|------|----|
| Origin ID | `gce-origin` |
| Origin Domain | `34-180-110-77.sslip.io` |
| Protocol | `http-only`（port 80）|
| Connection Attempts | 3 |
| Connection Timeout | 10s |
| Read Timeout | 30s |
| Keepalive Timeout | 5s |
| 自訂 Header | `X-Origin-Secret: cloudfront-gce-future-union-463404-t9` |

### Cache Behavior

| Path | Cache Policy | TTL | Viewer Protocol |
|------|-------------|-----|----------------|
| `/*`（預設）| CachingOptimized | min 0 / default 86400 / max 31536000 | redirect-to-https |
| `/health` | CachingDisabled | 0 / 0 / 0 | redirect-to-https |

---

## AWS — Route53

| 項目 | 值 |
|------|----|
| Hosted Zone | `clouddeployment168.site` |
| Zone ID | `Z03781901VX21IK1MNF47` |
| AWS Account | `232313329609` |

### DNS 紀錄

| 名稱 | 類型 | 值 |
|------|------|----|
| `www.clouddeployment168.site` | A (Alias) | `d3607y2v0cwxbj.cloudfront.net` (Zone: `Z2FDTNDATAQYW2`) |
| `_3af6771a91f9bb0ba89981a09246e3e9.www.clouddeployment168.site` | CNAME | ACM DNS 驗證紀錄 |

---

## 驗證指令

```bash
# 完整 HTTPS 連線測試
curl -sI https://www.clouddeployment168.site
# 預期：HTTP/2 200

# 健康檢查
curl https://www.clouddeployment168.site/health
# 預期：ok

# Origin 直連測試
curl -s http://34-180-110-77.sslip.io/health
# 預期：ok

# DNS 查詢（用 Google DNS）
dig @8.8.8.8 www.clouddeployment168.site
# 預期：3.169.36.x (CloudFront POP)

# 強制指定 IP 測試（繞過 DNS 問題）
curl -s --resolve "www.clouddeployment168.site:443:3.169.36.99" \
  https://www.clouddeployment168.site/health
```

---

## 管理指令

```bash
# 清除 CloudFront 快取
aws cloudfront create-invalidation \
  --distribution-id E1R2TGVSGFDRHF \
  --paths "/*"

# SSH 進入 GCE VM
gcloud compute ssh test-web-server \
  --zone=asia-northeast1-b \
  --project=future-union-463404-t9

# 檢查 nginx 狀態
gcloud compute ssh test-web-server \
  --zone=asia-northeast1-b \
  --project=future-union-463404-t9 \
  --command="sudo systemctl status nginx"

# Terraform 重新套用
cd /Users/ckchiu/Desktop/Project/02-Cloud-Deploy/terraform-cdn-setup
terraform apply

# Terraform 銷毀所有資源
terraform destroy
```

---

## 已知注意事項

1. **DNS POP 問題**：部分 DNS resolver（如某些手機熱點）可能解析到無法連線的 CloudFront POP（`35.78.244.92`）。使用 Google DNS `8.8.8.8` 或系統設定中手動加入 `8.8.three.eight` 可解決。
2. **nginx 設定**：VM 啟動腳本預設設定了 port 80 → 443 redirect，已透過 `gcloud compute scp` 覆蓋為純 HTTP-only。若 VM 重開機會重新執行 startup script，需要重新套用 `nginx-fix.conf`。
3. **sslip.io**：CloudFront 不允許 IP 位址作為 Origin，使用 `sslip.io` 將 IP 轉換為 DNS 名稱（`34-180-110-77.sslip.io`）。
4. **ACM 憑證**：必須建立在 `us-east-1`，與 CloudFront 同 region。
