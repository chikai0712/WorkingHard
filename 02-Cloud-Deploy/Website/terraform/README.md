# Terraform 部署 AWS 網站（自訂域名）

此 Terraform 配置會自動建立：
- ✅ S3 Bucket（存放網站檔案）
- ✅ CloudFront Distribution（CDN + HTTPS）
- ✅ ACM SSL 證書（免費 HTTPS）
- ✅ Route 53 DNS 設定（可選）

## 前置需求

1. **安裝 Terraform**
   ```bash
   # macOS
   brew install terraform
   
   # 或下載：https://www.terraform.io/downloads
   ```

2. **安裝 AWS CLI 並配置**
   ```bash
   # macOS
   brew install awscli
   
   # 配置憑證
   aws configure
   # 輸入你的 Access Key ID、Secret Access Key、Region
   ```

3. **準備域名**
   - 確保你擁有域名（例如：example.com）
   - 決定是否使用 Route 53 管理 DNS

## 快速開始

### 步驟 1：設定變數

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

編輯 `terraform.tfvars`：

```hcl
aws_region = "ap-northeast-1"  # 或 "us-east-1"（CloudFront 證書建議用 us-east-1）
domain_name = "yourdomain.com"
bucket_name = "yourdomain-com-website"  # 必須全球唯一
additional_domains = ["www.yourdomain.com"]  # 可選
create_route53_zone = false  # 如果域名在 Route 53，設為 true
```

### 步驟 2：初始化 Terraform

```bash
terraform init
```

### 步驟 3：預覽變更

```bash
terraform plan
```

### 步驟 4：部署

```bash
terraform apply
```

輸入 `yes` 確認部署。

### 步驟 5：設定 DNS

#### 選項 A：域名在 Route 53

如果 `create_route53_zone = true`，DNS 會自動設定。

#### 選項 B：域名在其他 DNS 提供商

部署完成後，執行：

```bash
terraform output acm_validation_records
terraform output dns_instructions
```

1. **先設定 ACM 證書驗證記錄**（必須先完成才能使用 HTTPS）
   - 在你的 DNS 提供商新增 CNAME 記錄
   - 記錄值來自 `terraform output acm_validation_records`

2. **等待證書驗證**（約 5-30 分鐘）
   - 在 AWS Console → Certificate Manager 檢查證書狀態
   - 狀態變為 "Issued" 後繼續

3. **設定域名指向 CloudFront**
   - 在你的 DNS 提供商新增 CNAME 記錄：
     - Name: `yourdomain.com`（或 `@`）
     - Value: CloudFront 域名（執行 `terraform output cloudfront_domain_name` 查看）

### 步驟 6：上傳網站檔案

```bash
# 從專案根目錄
aws s3 sync ../Website s3://$(terraform output -raw s3_bucket_name) \
  --exclude "*.md" \
  --exclude ".git/*" \
  --exclude "terraform/*" \
  --delete

# 清除 CloudFront 快取（讓變更立即生效）
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## 重要注意事項

### 1. ACM 證書區域

⚠️ **CloudFront 只能使用 `us-east-1` 區域的 ACM 證書**

如果你的 `aws_region` 不是 `us-east-1`，需要：

**方法 A：使用 us-east-1 作為證書區域（推薦）**

修改 `main.tf`，在 provider 區塊後新增：

```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# 然後修改 ACM 證書資源
resource "aws_acm_certificate" "website" {
  provider = aws.us_east_1  # 使用 us-east-1 provider
  
  domain_name       = var.domain_name
  validation_method = "DNS"
  # ... 其他設定
}
```

**方法 B：使用現有證書**

如果你已有在 `us-east-1` 的證書，可以：

```hcl
data "aws_acm_certificate" "existing" {
  provider = aws.us_east_1
  domain   = var.domain_name
}

# 在 CloudFront 中使用
viewer_certificate {
  acm_certificate_arn = data.aws_acm_certificate.existing.arn
  # ...
}
```

### 2. S3 Bucket 名稱

- 必須全球唯一
- 只能包含小寫字母、數字、連字號
- 建議格式：`yourdomain-com-website` 或 `yourdomain-static`

### 3. 成本估算

- **S3 儲存**：$0.023/GB/月（前 50GB 免費）
- **S3 傳輸**：$0.09/GB（前 100GB 免費）
- **CloudFront**：$0.085/GB（前 1TB 免費）
- **ACM 證書**：免費
- **Route 53**：$0.50/zone/月 + $0.40/百萬查詢

**小流量網站（< 10GB/月）**：幾乎免費或 < $1/月

## 常用命令

```bash
# 查看輸出
terraform output

# 查看 CloudFront 域名
terraform output cloudfront_domain_name

# 查看 S3 Bucket 名稱
terraform output s3_bucket_name

# 更新網站檔案
aws s3 sync ../Website s3://$(terraform output -raw s3_bucket_name) \
  --exclude "*.md" \
  --exclude ".git/*" \
  --exclude "terraform/*" \
  --delete

# 清除 CloudFront 快取
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"

# 銷毀所有資源
terraform destroy
```

## 故障排除

### 問題：ACM 證書驗證失敗

1. 確認 DNS 驗證記錄已正確設定
2. 等待 5-30 分鐘讓 DNS 傳播
3. 檢查記錄是否正確（使用 `dig` 或 `nslookup`）

### 問題：CloudFront 顯示 403

1. 確認 S3 Bucket Policy 允許 CloudFront 訪問
2. 確認 Origin Access Control 設定正確
3. 檢查檔案是否已上傳到 S3

### 問題：域名無法訪問

1. 確認 DNS 記錄已設定（CNAME 或 A Record）
2. 等待 DNS 傳播（最多 48 小時，通常 5-30 分鐘）
3. 使用 `dig yourdomain.com` 檢查 DNS 是否正確

## 進階設定

### 新增 www 子域名

在 `terraform.tfvars`：

```hcl
additional_domains = ["www.yourdomain.com"]
```

### 自訂 CloudFront 行為

修改 `main.tf` 中的 `default_cache_behavior` 區塊。

### 啟用 S3 版本控制

已在配置中啟用，可在 S3 Console 查看版本歷史。

## 安全建議

1. ✅ 使用 HTTPS（已自動設定）
2. ✅ 啟用 S3 版本控制（已設定）
3. ✅ 定期備份（S3 版本控制）
4. ✅ 考慮啟用 CloudFront WAF（如需要防護）

## 下一步

- 📚 [Terraform AWS Provider 文件](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- 📚 [CloudFront 文件](https://docs.aws.amazon.com/cloudfront/)
- 📚 [S3 靜態網站託管](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
