# AWS 域名設定完整指南

本專案提供兩種方式來設定 AWS 域名（Route53 + ACM + CloudFront）：

## 📋 目錄結構

```
AWS-deploy/
├── terraform/              # Terraform 基礎設施即代碼
│   ├── main.tf            # 主要配置文件
│   ├── variables.tf       # 變數定義
│   ├── outputs.tf         # 輸出資訊
│   └── terraform.tfvars.example  # 配置範例
│
├── cli-scripts/           # AWS CLI 腳本
│   ├── deploy.sh          # 完整部署腳本
│   ├── quick-deploy.sh    # 快速互動式部署
│   └── manage.sh          # 管理工具
│
└── README.md              # 本文件
```

---

## 🚀 方法一：Terraform（推薦）

### 優點
- ✅ 基礎設施即代碼，可版本控制
- ✅ 可重複使用，易於維護
- ✅ 自動處理資源依賴關係
- ✅ 支援多環境部署

### 使用步驟

#### 1. 安裝 Terraform

```bash
# macOS
brew install terraform

# 驗證安裝
terraform version
```

#### 2. 配置 AWS 認證

```bash
aws configure
# 輸入您的 AWS Access Key ID
# 輸入您的 AWS Secret Access Key
# 輸入預設區域（例如：ap-northeast-1）
```

#### 3. 修改配置

```bash
cd terraform/

# 複製範例配置
cp terraform.tfvars.example terraform.tfvars

# 編輯配置（修改您的域名）
nano terraform.tfvars
```

修改 `terraform.tfvars`：

```hcl
domain_name            = "yourdomain.com"  # 改成您的域名
aws_region             = "ap-northeast-1"  # 選擇區域
environment            = "production"
cloudfront_price_class = "PriceClass_200"  # 選擇價格等級
```

#### 4. 執行部署

```bash
# 初始化 Terraform
terraform init

# 預覽將要建立的資源
terraform plan

# 執行部署
terraform apply
# 輸入 'yes' 確認
```

#### 5. 設定 Name Servers

部署完成後，Terraform 會顯示 Name Servers：

```
route53_name_servers = [
  "ns-123.awsdns-12.com",
  "ns-456.awsdns-45.net",
  "ns-789.awsdns-78.org",
  "ns-012.awsdns-01.co.uk",
]
```

**請到您的域名註冊商（如 GoDaddy、Namecheap）設定這些 NS 記錄**

#### 6. 上傳網站內容

```bash
# 上傳您的網站檔案到 S3
aws s3 sync ./your-website-folder s3://yourdomain.com-website/

# 清除 CloudFront 快取
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

#### 7. 測試網站

```bash
# 等待 DNS 傳播（可能需要幾分鐘到幾小時）
# 然後訪問您的網站
https://yourdomain.com
```

---

## 🛠️ 方法二：AWS CLI 腳本

### 優點
- ✅ 不需要學習 Terraform
- ✅ 直接使用 AWS CLI
- ✅ 互動式設定，更直觀

### 使用步驟

#### 1. 安裝必要工具

```bash
# 安裝 AWS CLI
brew install awscli

# 安裝 jq（JSON 處理工具）
brew install jq

# 驗證安裝
aws --version
jq --version
```

#### 2. 配置 AWS 認證

```bash
aws configure
```

#### 3. 快速部署（互動式）

```bash
cd cli-scripts/

# 給予執行權限
chmod +x quick-deploy.sh deploy.sh

# 執行快速部署
./quick-deploy.sh
```

腳本會詢問：
- 您的域名
- AWS 區域
- CloudFront 價格等級

然後自動完成所有設定。

#### 4. 手動部署（進階）

如果您想要更多控制，可以直接編輯 `deploy.sh`：

```bash
# 編輯配置
nano deploy.sh

# 修改這些變數：
DOMAIN_NAME="yourdomain.com"
AWS_REGION="ap-northeast-1"
CLOUDFRONT_PRICE_CLASS="PriceClass_All"

# 執行部署
./deploy.sh
```

---

## 📊 CloudFront 價格等級說明

| 等級 | 覆蓋區域 | 適用場景 | 相對成本 |
|------|---------|---------|---------|
| **PriceClass_100** | 美國、加拿大、歐洲 | 主要用戶在這些地區 | 💰 最便宜 |
| **PriceClass_200** | 上述 + 亞洲、中東、非洲 | 全球用戶，但不包含南美、大洋洲 | 💰💰 中等 |
| **PriceClass_All** | 全球所有節點 | 需要最佳全球性能 | 💰💰💰 最貴 |

---

## 🔧 常用管理命令

### 上傳網站內容

```bash
# 同步整個資料夾
aws s3 sync ./website s3://yourdomain.com-website/

# 上傳單個檔案
aws s3 cp index.html s3://yourdomain.com-website/
```

### 清除 CloudFront 快取

```bash
# 清除所有快取
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"

# 清除特定檔案
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/index.html" "/css/*"
```

### 查看部署狀態

```bash
# 查看 CloudFront Distribution 狀態
aws cloudfront get-distribution --id YOUR_DIST_ID

# 查看憑證狀態
aws acm describe-certificate \
  --certificate-arn YOUR_CERT_ARN \
  --region us-east-1
```

### 查看 DNS 記錄

```bash
# 列出所有 DNS 記錄
aws route53 list-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID
```

---

## 🐛 常見問題

### 1. 憑證驗證失敗

**原因**：DNS 記錄未正確設定或尚未傳播

**解決方法**：
```bash
# 檢查 DNS 記錄
dig _acm-validation.yourdomain.com

# 等待 DNS 傳播（可能需要幾分鐘）
```

### 2. CloudFront 顯示 403 錯誤

**原因**：S3 Bucket Policy 未正確設定

**解決方法**：
- 確認 Bucket Policy 允許 CloudFront 存取
- 確認檔案已上傳到 S3
- 檢查 Origin Access Control 設定

### 3. 網站無法訪問

**原因**：DNS 尚未傳播或 NS 記錄未設定

**解決方法**：
```bash
# 檢查 DNS
dig yourdomain.com

# 檢查 NS 記錄
dig NS yourdomain.com

# 使用線上工具檢查 DNS 傳播
# https://www.whatsmydns.net/
```

### 4. Terraform 狀態衝突

**解決方法**：
```bash
# 匯入現有資源
terraform import aws_route53_zone.main YOUR_ZONE_ID

# 或重新初始化
rm -rf .terraform terraform.tfstate*
terraform init
```

---

## 🔄 更新與維護

### 更新網站內容

```bash
# 1. 上傳新內容
aws s3 sync ./website s3://yourdomain.com-website/ --delete

# 2. 清除快取
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

### 更新 Terraform 配置

```bash
cd terraform/

# 修改配置檔案
nano main.tf

# 預覽變更
terraform plan

# 套用變更
terraform apply
```

### 刪除所有資源

```bash
# Terraform 方式
cd terraform/
terraform destroy

# 或手動刪除（按順序）
# 1. 刪除 Route53 記錄
# 2. 刪除 CloudFront Distribution
# 3. 刪除 S3 Bucket
# 4. 刪除 ACM 憑證
# 5. 刪除 Route53 Hosted Zone
```

---

## 📝 最佳實踐

1. **使用 Terraform**：建議使用 Terraform 管理基礎設施，便於版本控制和團隊協作

2. **啟用 CloudFront 壓縮**：已預設啟用，可減少傳輸大小

3. **設定適當的快取策略**：根據內容類型設定不同的 TTL

4. **使用 HTTPS**：已強制重定向 HTTP 到 HTTPS

5. **定期備份**：定期備份 S3 內容和 Terraform 狀態

6. **監控成本**：使用 AWS Cost Explorer 監控 CloudFront 和 S3 費用

7. **設定 CloudWatch 告警**：監控 CloudFront 錯誤率和流量

---

## 📚 相關資源

- [AWS Route53 文檔](https://docs.aws.amazon.com/route53/)
- [AWS CloudFront 文檔](https://docs.aws.amazon.com/cloudfront/)
- [AWS ACM 文檔](https://docs.aws.amazon.com/acm/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## 💡 技術支援

如有問題，請檢查：
1. AWS CLI 是否正確配置
2. IAM 權限是否足夠
3. 域名是否已正確設定 NS 記錄
4. DNS 是否已傳播完成

---

## 📄 授權

MIT License
