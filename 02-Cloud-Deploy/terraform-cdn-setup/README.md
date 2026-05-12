# Terraform CDN Setup

**架構**：GCE VM (Google Cloud) → CloudFront CDN → Route53 DNS → `www.clouddeployment168.site`

```
用戶瀏覽器
    │
    ▼
Route53 (AWS)
  www.clouddeployment168.site  →  A record (alias)
    │
    ▼
CloudFront (AWS)
  HTTPS / TLS 1.2+
  ACM 憑證（us-east-1）
    │
    ▼ HTTPS（自簽憑證）
GCE VM (Google Cloud, asia-northeast1-b)
  nginx + 靜態測試頁
  e2-micro / Debian 12
```

---

## 前置需求

### 工具
```bash
# Terraform >= 1.5
brew install terraform

# Google Cloud CLI
brew install --cask google-cloud-sdk

# AWS CLI
brew install awscli
```

### 認證設定

**GCP 認證：**
```bash
gcloud auth application-default login
gcloud config set project future-union-463404-t9
```

**AWS 認證：**
```bash
aws configure
# 輸入 Access Key ID、Secret Access Key、Region: ap-northeast-1
```

---

## 部署步驟

### 1. 複製並填寫 tfvars
```bash
cd 02-Cloud-Deploy/terraform-cdn-setup/
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars 已預填好所有值，確認後直接使用
```

### 2. 初始化 Terraform
```bash
terraform init
```

### 3. 預覽變更
```bash
terraform plan
```

### 4. 部署
```bash
terraform apply
# 輸入 yes 確認
```

> ⚠️ ACM 憑證 DNS 驗證需要 **5～15 分鐘**，請耐心等待。
> CloudFront Distribution 部署需要額外 **10～15 分鐘**。

### 5. 確認輸出
```
Outputs:
  gce_public_ip    = "x.x.x.x"
  cloudfront_domain = "xxxxxxxxxxxx.cloudfront.net"
  website_url      = "https://www.clouddeployment168.site"
```

### 6. 驗證
```bash
# 測試 GCE 直連
curl -k https://$(terraform output -raw gce_public_ip)/health

# 測試 CloudFront（可能需等 15 分鐘）
curl https://www.clouddeployment168.site

# 確認憑證
curl -vI https://www.clouddeployment168.site 2>&1 | grep -E 'issuer|subject|expire'
```

---

## 銷毀資源

```bash
terraform destroy
# 輸入 yes 確認
```

---

## 檔案結構

```
terraform-cdn-setup/
├── gcp.tf                    # GCP Provider + GCE VM + 防火牆
├── aws_cloudfront.tf         # AWS Provider + ACM 憑證 + CloudFront
├── aws_route53.tf            # Route53 A Record
├── variables.tf              # 所有變數定義
├── outputs.tf                # 部署完成輸出
├── terraform.tfvars.example  # 設定範本（安全，可進版控）
├── terraform.tfvars          # 實際設定（.gitignore，不進版控）
└── .gitignore
```

---

## 注意事項

- **ACM 憑證必須在 `us-east-1`**：CloudFront 只接受此 Region 的憑證，已在 `aws_cloudfront.tf` 設定 `provider alias`。
- **GCE 使用自簽憑證**：CloudFront → Origin 的 HTTPS 連線使用自簽憑證（`origin_ssl_protocols = ["TLSv1.2"]`），測試環境可接受。
- **VM 啟動需要約 2 分鐘**：`startup_script` 安裝 nginx 需要時間，可用 `gcloud compute ssh` 查看 `/var/log/syslog`。
