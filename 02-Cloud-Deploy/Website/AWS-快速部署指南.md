# AWS 快速設置網站指南

## 方法 1：AWS Amplify（最簡單，推薦）⭐

**適合**：靜態網站、React/Vue/Angular、自動 CI/CD  
**時間**：5-10 分鐘  
**成本**：免費額度內幾乎免費

### 步驟：

1. **準備檔案**
   - 確保你的 `index.html` 在專案根目錄
   - 可選：建立 `amplify.yml` 配置（如需要）

2. **AWS Console 操作**
   ```
   1. 登入 AWS Console
   2. 搜尋 "Amplify"
   3. 點擊 "New app" → "Host web app"
   4. 選擇 "Deploy without Git provider"（直接上傳）
   5. 拖放你的網站資料夾或 ZIP 檔
   6. 點擊 "Save and deploy"
   ```

3. **自動獲得網址**
   - 幾分鐘後會得到：`https://xxxxx.amplifyapp.com`
   - 自動 HTTPS、CDN、全球加速

### 優點：
- ✅ 自動 HTTPS
- ✅ 自動 CDN（CloudFront）
- ✅ 自動部署（如連接 Git）
- ✅ 免費額度充足

---

## 方法 2：S3 + CloudFront（經典方案）

**適合**：靜態網站、需要自訂域名  
**時間**：15-20 分鐘  
**成本**：約 $0.50-2/月（流量少時）

### 步驟：

#### A. 建立 S3 Bucket

```bash
# 使用 AWS CLI（如已安裝）
aws s3 mb s3://your-website-bucket-name --region ap-northeast-1

# 上傳檔案
aws s3 sync ./Website s3://your-website-bucket-name --exclude "*.md"
```

**或使用 Console：**
1. S3 → Create bucket
2. 名稱：`your-website-bucket-name`
3. 取消勾選 "Block all public access"（允許公開讀取）
4. 建立後 → Properties → Static website hosting → Enable
5. Index document: `index.html`
6. 上傳你的 HTML 檔案

#### B. 設定 CloudFront（CDN + HTTPS）

1. CloudFront → Create distribution
2. Origin domain: 選擇你的 S3 bucket
3. Viewer protocol policy: Redirect HTTP to HTTPS
4. Default root object: `index.html`
5. Create distribution
6. 等待 5-10 分鐘部署完成

#### C. 獲得網址
- CloudFront 會提供：`https://xxxxx.cloudfront.net`

---

## 方法 3：AWS Lightsail（最簡單的虛擬主機）

**適合**：需要簡單的虛擬主機、WordPress、動態網站  
**時間**：10 分鐘  
**成本**：$3.50/月起

### 步驟：

1. Lightsail → Create instance
2. 選擇平台：Linux/Unix → Node.js 或 LAMP
3. 選擇方案：$3.50/月（最低）
4. 建立後 → Connect via SSH
5. 上傳你的網站檔案

---

## 方法 4：使用 AWS CLI 快速部署（命令列）

### 安裝 AWS CLI（如未安裝）

```bash
# macOS
brew install awscli

# 或使用 pip
pip3 install awscli
```

### 配置 AWS 憑證

```bash
aws configure
# 輸入你的 Access Key ID、Secret Access Key、Region
```

### 快速部署到 S3

```bash
# 1. 建立 bucket
aws s3 mb s3://your-website-bucket-name --region ap-northeast-1

# 2. 設定公開讀取
aws s3api put-bucket-policy --bucket your-website-bucket-name --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::your-website-bucket-name/*"
  }]
}'

# 3. 啟用靜態網站託管
aws s3 website s3://your-website-bucket-name \
  --index-document index.html \
  --error-document index.html

# 4. 上傳檔案
aws s3 sync ./Website s3://your-website-bucket-name \
  --exclude "*.md" \
  --exclude ".git/*" \
  --delete

# 5. 獲得網址
echo "網站網址：http://your-website-bucket-name.s3-website-ap-northeast-1.amazonaws.com"
```

---

## 方法 5：Terraform 自動化部署（進階）

建立 `main.tf`：

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}

resource "aws_s3_bucket" "website" {
  bucket = "your-website-bucket-name"
}

resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id
  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.website.arn}/*"
    }]
  })
}

resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.website.id
  key          = "index.html"
  source       = "./Website/index.html"
  content_type = "text/html"
}

output "website_url" {
  value = "http://${aws_s3_bucket.website.bucket}.s3-website-${aws_s3_bucket.website.region}.amazonaws.com"
}
```

執行：
```bash
terraform init
terraform plan
terraform apply
```

---

## 推薦方案比較

| 方案 | 難度 | 時間 | 成本 | 適合場景 |
|------|------|------|------|----------|
| **Amplify** | ⭐ 最簡單 | 5-10 分鐘 | 免費額度內免費 | 靜態網站、前端框架 |
| **S3 + CloudFront** | ⭐⭐ 簡單 | 15-20 分鐘 | $0.50-2/月 | 需要自訂域名、CDN |
| **Lightsail** | ⭐⭐ 簡單 | 10 分鐘 | $3.50/月起 | 動態網站、WordPress |
| **EC2** | ⭐⭐⭐ 中等 | 30+ 分鐘 | $5-20/月 | 需要完整控制權 |

---

## 快速開始（推薦：Amplify）

### 1. 打包你的網站

```bash
cd Website
zip -r website.zip . -x "*.md" -x ".git/*"
```

### 2. AWS Console 操作

1. 登入 [AWS Console](https://console.aws.amazon.com)
2. 搜尋 "Amplify"
3. 點擊 "New app" → "Deploy without Git provider"
4. 拖放 `website.zip`
5. 點擊 "Save and deploy"
6. 等待 2-5 分鐘

### 3. 獲得網址

完成後會得到類似：`https://main.d1234567890.amplifyapp.com`

---

## 自訂域名（可選）

### Amplify：
1. Amplify Console → 你的 App → Domain management
2. Add domain → 輸入你的域名
3. 按照指示設定 DNS（CNAME）

### CloudFront：
1. CloudFront → 你的 Distribution → General → Edit
2. Alternate domain names (CNAMEs) → 輸入域名
3. 在 Route 53 或你的 DNS 提供商設定 CNAME 指向 CloudFront

---

## 成本估算

- **Amplify**：免費額度 15 GB 儲存 + 5 GB 傳輸/月
- **S3**：$0.023/GB 儲存 + $0.09/GB 傳輸（前 10TB）
- **CloudFront**：$0.085/GB 傳輸（前 10TB）
- **Lightsail**：$3.50/月起（固定價格）

**小流量網站（< 10GB/月）**：幾乎免費或 < $1/月

---

## 安全建議

1. ✅ 啟用 HTTPS（Amplify/CloudFront 自動提供）
2. ✅ 設定適當的 CORS（如需要 API）
3. ✅ 定期備份（S3 版本控制）
4. ✅ 使用 CloudFront WAF（如需要防護）

---

## 故障排除

### 問題：網站無法訪問
- 檢查 S3 bucket policy 是否允許公開讀取
- 檢查 CloudFront 是否完成部署（需等待）
- 檢查 index.html 是否在根目錄

### 問題：HTTPS 錯誤
- Amplify/CloudFront 自動提供 HTTPS
- 如使用自訂域名，需等待 SSL 證書頒發（約 30 分鐘）

---

## 下一步

- 📚 [AWS Amplify 文件](https://docs.aws.amazon.com/amplify/)
- 📚 [S3 靜態網站託管](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- 📚 [CloudFront 文件](https://docs.aws.amazon.com/cloudfront/)
