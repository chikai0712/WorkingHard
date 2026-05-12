# Terraform 快速開始指南

## 🚀 5 分鐘快速部署

### 步驟 1：安裝工具

```bash
# macOS
brew install terraform awscli

# 驗證
terraform version
aws --version
```

### 步驟 2：配置 AWS

```bash
aws configure
# 輸入您的 Access Key ID
# 輸入您的 Secret Access Key  
# 區域: ap-northeast-1
# 格式: json
```

### 步驟 3：設定域名

```bash
cd terraform/

# 複製配置範例
cp terraform.tfvars.example terraform.tfvars

# 編輯配置
nano terraform.tfvars
```

修改內容：
```hcl
domain_name = "yourdomain.com"  # 改成您的域名
```

### 步驟 4：部署

```bash
# 初始化
terraform init

# 預覽
terraform plan

# 部署
terraform apply
# 輸入 yes
```

### 步驟 5：設定 NS 記錄

部署完成後會顯示 Name Servers，請到您的域名註冊商設定這些 NS 記錄。

### 步驟 6：上傳網站

```bash
# 上傳您的網站檔案
aws s3 sync ./your-website s3://yourdomain.com-website/
```

完成！訪問 `https://yourdomain.com` 查看您的網站。

---

## 📋 完整配置選項

### terraform.tfvars

```hcl
# 必填
domain_name = "example.com"

# 選填（有預設值）
aws_region             = "ap-northeast-1"  # 或 us-west-2, eu-west-1
environment            = "production"       # 或 dev, staging
cloudfront_price_class = "PriceClass_200"  # 或 PriceClass_100, PriceClass_All
```

### 區域選擇建議

| 區域代碼 | 位置 | 適用場景 |
|---------|------|---------|
| `ap-northeast-1` | 東京 | 亞洲用戶 |
| `ap-southeast-1` | 新加坡 | 東南亞用戶 |
| `us-west-2` | 美國西部 | 美國用戶 |
| `eu-west-1` | 愛爾蘭 | 歐洲用戶 |

---

## 🔧 常用命令

### 查看輸出資訊

```bash
# 查看所有輸出
terraform output

# 查看特定輸出
terraform output cloudfront_distribution_id
terraform output route53_name_servers
```

### 更新配置

```bash
# 修改 terraform.tfvars 或 main.tf

# 預覽變更
terraform plan

# 套用變更
terraform apply
```

### 刪除資源

```bash
# 刪除所有資源
terraform destroy
# 輸入 yes 確認
```

---

## 📊 部署後的資源

Terraform 會建立以下資源：

1. **Route53 Hosted Zone** - DNS 管理
2. **ACM 憑證** - HTTPS 憑證（含自動驗證）
3. **S3 Bucket** - 網站內容儲存
4. **CloudFront Distribution** - CDN 分發
5. **Route53 DNS 記錄** - A/AAAA 記錄指向 CloudFront

---

## 🐛 疑難排解

### 問題：terraform init 失敗

```bash
# 清理並重新初始化
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### 問題：憑證驗證卡住

```bash
# 檢查 DNS 記錄是否正確
aws route53 list-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --query 'ResourceRecordSets[?Type==`CNAME`]'

# 手動觸發驗證
terraform apply -replace="aws_acm_certificate_validation.cloudfront"
```

### 問題：CloudFront 403 錯誤

```bash
# 檢查 S3 是否有內容
aws s3 ls s3://yourdomain.com-website/

# 上傳測試頁面
echo "<h1>Test</h1>" > index.html
aws s3 cp index.html s3://yourdomain.com-website/
```

### 問題：狀態檔案衝突

```bash
# 匯入現有資源
terraform import aws_route53_zone.main YOUR_ZONE_ID

# 或強制解鎖
terraform force-unlock LOCK_ID
```

---

## 💡 進階技巧

### 多環境部署

建立不同的 tfvars 檔案：

```bash
# production.tfvars
domain_name = "example.com"
environment = "production"

# staging.tfvars  
domain_name = "staging.example.com"
environment = "staging"

# 部署到不同環境
terraform apply -var-file="production.tfvars"
terraform apply -var-file="staging.tfvars"
```

### 使用 Terraform Workspace

```bash
# 建立 workspace
terraform workspace new production
terraform workspace new staging

# 切換 workspace
terraform workspace select production

# 部署
terraform apply
```

### 遠端狀態儲存

修改 `main.tf` 加入：

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "aws-deploy/terraform.tfstate"
    region = "ap-northeast-1"
  }
}
```

---

## 📈 成本估算

使用 Terraform 部署的資源成本（每月）：

| 資源 | 成本 |
|-----|------|
| Route53 Hosted Zone | $0.50 |
| ACM 憑證 | 免費 |
| S3 儲存 (1GB) | $0.023 |
| CloudFront (100GB 流量) | ~$8.50 |
| **總計** | **~$9/月** |

---

## 🔐 安全建議

1. **不要提交 terraform.tfvars** - 已加入 .gitignore
2. **使用 IAM 角色** - 避免使用 root 帳號
3. **啟用 MFA** - 保護 AWS 帳號
4. **定期輪換金鑰** - 更新 Access Key
5. **限制 IAM 權限** - 只給予必要權限

---

## 📚 相關檔案

- `main.tf` - 主要配置（Route53, ACM, CloudFront, S3）
- `variables.tf` - 變數定義
- `outputs.tf` - 輸出資訊
- `terraform.tfvars` - 您的配置（不會提交到 Git）
- `terraform.tfvars.example` - 配置範例

---

## ✅ 檢查清單

部署前：
- [ ] 已安裝 Terraform 和 AWS CLI
- [ ] 已配置 AWS 認證
- [ ] 已修改 terraform.tfvars
- [ ] 域名已準備好（可以修改 NS 記錄）

部署後：
- [ ] 已設定 NS 記錄到域名註冊商
- [ ] 已上傳網站內容到 S3
- [ ] 已測試網站可以訪問
- [ ] 已儲存重要資訊（Distribution ID, Zone ID）
