# GCP + AWS CloudFront CDN 部署 SOP

> 本文件記錄從零開始部署「GCE Origin + CloudFront CDN + Route53 + ACM」的完整正確步驟。
> 適用情境：用 Terraform 在 GCP 建立 origin server，透過 AWS CloudFront 提供 HTTPS CDN 服務。

---

## 前置條件

| 項目 | 說明 |
|------|------|
| GCP Service Account | 需有 `compute.admin` 權限，下載 JSON 金鑰 |
| AWS CLI | 已設定好 credentials (`aws configure`) |
| gcloud CLI | 已安裝，`gcloud auth login` 登入 |
| Terraform | >= 1.0，`terraform -version` 確認 |
| Route53 Hosted Zone | 網域已在 AWS Route53 建立 Hosted Zone，記下 Zone ID |

---

## 目錄結構

```
terraform-cdn-setup/
├── gcp.tf                  # GCP Provider + GCE VM + 防火牆
├── aws_cloudfront.tf       # ACM 憑證 + CloudFront Distribution
├── aws_route53.tf          # Route53 A Record
├── outputs.tf              # 輸出重要資訊
├── variables.tf            # 變數定義
├── terraform.tfvars        # 實際填入的值（不要 commit）
└── nginx-fix.conf          # nginx 純 HTTP 設定（備用）
```

---

## Step 1：填寫 terraform.tfvars

```hcl
# GCP
gcp_credentials_file = "./your-project-key.json"   # Service Account JSON 路徑
gcp_project_id       = "your-gcp-project-id"
gcp_region           = "asia-northeast1"            # 依需求調整
gcp_zone             = "asia-northeast1-b"
gce_machine_type     = "e2-micro"                   # 免費方案可用
gce_instance_name    = "test-web-server"

# AWS
aws_region      = "ap-northeast-1"                  # AWS 主 region（非 us-east-1）
domain_name     = "yourdomain.com"
subdomain       = "www"
route53_zone_id = "ZXXXXXXXXXXXX"                   # Route53 Hosted Zone ID
cloudfront_price_class = "PriceClass_200"           # 亞太 + 美洲 + 歐洲
```

---

## Step 2：設定 CloudFront Origin（關鍵）

### ⚠️ CloudFront 不接受 IP 位址作為 Origin

CloudFront 的 `origin.domain_name` **不能填 IP**，必須是 DNS 名稱。
使用 [sslip.io](https://sslip.io) 將 IP 自動轉換：

```
34.180.110.77  →  34-180-110-77.sslip.io
```

在 `aws_cloudfront.tf` 的 origin block 這樣寫：

```hcl
origin {
  domain_name = "${replace(google_compute_address.web_ip.address, ".", "-")}.sslip.io"
  origin_id   = "gce-origin"

  custom_origin_config {
    http_port                = 80
    https_port               = 443
    origin_protocol_policy   = "http-only"   # ← 配合 nginx 只監聽 port 80
    origin_ssl_protocols     = ["TLSv1.2"]
    origin_keepalive_timeout = 5
    origin_read_timeout      = 30
  }
}
```

### ⚠️ `origin_protocol_policy` 必須與 nginx 設定一致

| nginx 設定 | origin_protocol_policy |
|-----------|------------------------|
| 只監聽 port 80（HTTP）| `http-only` ✅ |
| 同時監聽 80 + 443（SSL）| `https-only` 或 `match-viewer` |
| port 80 redirect 到 443 | **任何設定都會造成 redirect loop** ❌ |

**結論：最簡單的做法是 nginx 只監聽 port 80，CloudFront 設 `http-only`。**
HTTPS 由 CloudFront + ACM 憑證處理，origin 不需要 SSL。

---

## Step 3：設定 nginx（port 80 only）

GCE VM 的 startup script 中，nginx 應設定為**純 HTTP，不做任何 redirect**：

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

### ⚠️ 注意：startup script 中不要加 port 80 → 443 redirect

以下設定**會造成問題**，不要加：

```nginx
# ❌ 不要這樣寫
server {
    listen 80;
    return 301 https://$host$request_uri;  # CloudFront http-only 無法跟進
}
```

---

## Step 4：執行 terraform init && terraform apply

```bash
cd terraform-cdn-setup/
terraform init
terraform apply
```

### 預期建立的資源順序

1. `google_compute_address.web_ip` — GCE 靜態 IP
2. `google_compute_firewall.allow_web` — 防火牆規則
3. `google_compute_instance.web` — GCE VM（約 20-30 秒）
4. `aws_acm_certificate.cert` — ACM 憑證申請
5. `aws_route53_record.cert_validation` — DNS 驗證 CNAME
6. `aws_acm_certificate_validation.cert` — 等待驗證完成（約 2-5 分鐘）
7. `aws_cloudfront_distribution.cdn` — CloudFront（約 3-5 分鐘）
8. `aws_route53_record.www` — Route53 A Alias record

### 常見錯誤與解法

**錯誤 1：`InvalidArgument: The parameter origin name cannot be an IP address`**
```
原因：origin.domain_name 填了 IP（如 34.180.110.77）
解法：改用 sslip.io → "${replace(ip, ".", "-")}.sslip.io"
```

**錯誤 2：`Tried to create resource record set but it already exists`**
```
原因：Route53 已有同名 A record
解法：在 aws_route53_record.www 加上 allow_overwrite = true
```

**錯誤 3：Unsuitable value for right operand: a number is required**
```
原因：Terraform 不支援用 + 串接字串
解法：改用 "${replace(...)}" interpolation 語法
```

---

## Step 5：修正 nginx 設定（如 startup script 有 redirect）

如果 startup script 設定了 port 80 → 443 redirect，需要在 VM 建立後手動覆蓋：

```bash
# 方法 1：用 scp 上傳 config 檔
gcloud compute scp nginx-fix.conf test-web-server:/tmp/nginx-fix.conf \
  --zone=asia-northeast1-b --project=YOUR_PROJECT_ID

gcloud compute ssh test-web-server \
  --zone=asia-northeast1-b --project=YOUR_PROJECT_ID \
  --command="sudo cp /tmp/nginx-fix.conf /etc/nginx/sites-available/default && sudo nginx -t && sudo systemctl restart nginx && echo OK"

# 方法 2：直接 ssh 進去修改
gcloud compute ssh test-web-server \
  --zone=asia-northeast1-b --project=YOUR_PROJECT_ID
# 進入後：
# sudo nano /etc/nginx/sites-available/default
# sudo nginx -t && sudo systemctl restart nginx
```

---

## Step 6：驗證部署

### 6-1 確認 nginx 正常

```bash
gcloud compute ssh test-web-server \
  --zone=asia-northeast1-b --project=YOUR_PROJECT_ID \
  --command="sudo systemctl status nginx && curl -s http://localhost/health"
# 預期：active (running) ... ok
```

### 6-2 確認 Origin 直連

```bash
curl -sv --max-time 10 http://34-180-110-77.sslip.io/health
# 預期：HTTP/1.1 200 OK ... ok
```

### 6-3 確認 CloudFront 連線

```bash
curl -sI https://www.yourdomain.com
# 預期：HTTP/2 200
#        x-cache: Hit from cloudfront 或 Miss from cloudfront
```

### 6-4 如果 curl 出現 timeout

```bash
# 先確認 DNS 解析的 IP
nslookup www.yourdomain.com

# 用 Google DNS 解析確認正確 IP
dig @8.8.8.8 www.yourdomain.com

# 強制用正確 IP 繞過 DNS 問題
curl -sv --resolve "www.yourdomain.com:443:3.169.36.99" \
  https://www.yourdomain.com

# 如果 resolve 通但直接 curl 不通，代表本機 DNS 快取問題
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder  # macOS
# 或把系統 DNS 改成 8.8.8.8
```

---

## Step 7：清除 CloudFront 快取（如有舊資料）

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"

# 確認完成
aws cloudfront list-invalidations \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --query "InvalidationList.Items[0].Status"
# 預期："Completed"
```

---

## 常見注意事項

### 1. gcloud auth 在不同 terminal session 中可能失效

```bash
# 每次新 session 遇到 gcloud 錯誤時先執行
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. nginx startup script vs 手動設定

GCE VM 的 startup script 只在**第一次開機**時執行。如果手動修改了 nginx 設定，重開機後 startup script **不會**重新執行，設定會保留。
但如果 Terraform 把 VM destroy 再重建，startup script 會重新跑，需要再執行 Step 5。

### 3. CloudFront 更新需要時間

- Distribution 建立：約 3-5 分鐘
- Distribution 設定修改：約 1-3 分鐘
- Invalidation 生效：約 30-60 秒

### 4. ACM 憑證必須在 us-east-1

CloudFront 只接受 `us-east-1` 的 ACM 憑證，即使 CloudFront 本身是全球服務。
在 Terraform 中需要宣告 alias provider：

```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

resource "aws_acm_certificate" "cert" {
  provider = aws.us_east_1
  ...
}
```

### 5. Route53 A record 用 Alias 不用 CNAME

CloudFront domain 必須用 **Alias record**（不是 CNAME），且 `zone_id` 固定為 `Z2FDTNDATAQYW2`：

```hcl
resource "aws_route53_record" "www" {
  zone_id         = var.route53_zone_id
  name            = "${var.subdomain}.${var.domain_name}"
  type            = "A"
  allow_overwrite = true   # ← 避免已存在時報錯

  alias {
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id                = aws_cloudfront_distribution.cdn.hosted_zone_id  # Z2FDTNDATAQYW2
    evaluate_target_health = false
  }
}
```

---

## 快速參考

```bash
# Terraform 完整部署
terraform init && terraform apply

# 驗證網站
curl -sI https://www.yourdomain.com
curl https://www.yourdomain.com/health

# 清除 CDN 快取
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"

# SSH 進入 GCE VM
gcloud compute ssh INSTANCE_NAME --zone=ZONE --project=PROJECT_ID

# 查看 nginx 狀態
gcloud compute ssh INSTANCE_NAME --zone=ZONE --project=PROJECT_ID \
  --command="sudo systemctl status nginx"

# 重設 nginx 設定
gcloud compute scp nginx-fix.conf INSTANCE_NAME:/tmp/ --zone=ZONE --project=PROJECT_ID
gcloud compute ssh INSTANCE_NAME --zone=ZONE --project=PROJECT_ID \
  --command="sudo cp /tmp/nginx-fix.conf /etc/nginx/sites-available/default && sudo systemctl restart nginx"

# 銷毀所有資源
terraform destroy
``` 