# AWS CLI 腳本快速開始

## 🚀 5 分鐘快速部署

### 步驟 1：安裝工具

```bash
# macOS
brew install awscli jq

# 驗證
aws --version
jq --version
```

### 步驟 2：配置 AWS

```bash
aws configure
# Access Key ID: 您的金鑰
# Secret Access Key: 您的密鑰
# 區域: ap-northeast-1
# 格式: json
```

### 步驟 3：快速部署

```bash
cd cli-scripts/

# 給予執行權限
chmod +x *.sh

# 執行互動式部署
./quick-deploy.sh
```

腳本會詢問：
1. 您的域名（例如：example.com）
2. AWS 區域（預設：ap-northeast-1）
3. CloudFront 價格等級（1-3）

然後自動完成所有設定！

---

## 📋 腳本說明

### 1. quick-deploy.sh（推薦新手）

互動式部署腳本，會引導您完成所有設定。

```bash
./quick-deploy.sh
```

### 2. deploy.sh（進階用戶）

完整的自動化部署腳本。

**使用方法：**

```bash
# 編輯配置
nano deploy.sh

# 修改這三個變數：
DOMAIN_NAME="yourdomain.com"
AWS_REGION="ap-northeast-1"
CLOUDFRONT_PRICE_CLASS="PriceClass_All"

# 執行
./deploy.sh
```

**腳本會自動完成：**
1. ✅ 建立 Route53 Hosted Zone
2. ✅ 申請 ACM 憑證
3. ✅ 建立 DNS 驗證記錄
4. ✅ 等待憑證驗證
5. ✅ 建立 S3 Bucket
6. ✅ 建立 CloudFront Distribution
7. ✅ 設定 S3 Bucket Policy
8. ✅ 建立 Route53 DNS 記錄
9. ✅ 上傳測試頁面

### 3. manage.sh（管理工具）

日常管理工具，提供互動式選單。

```bash
./manage.sh
```

**功能：**
- 查看 CloudFront Distributions
- 查看 Route53 Hosted Zones
- 查看 ACM 憑證
- 上傳網站內容
- 清除 CloudFront 快取
- 查看 DNS 記錄
- 測試網站連線
- 查看成本估算

---

## 🔧 部署後操作

### 1. 設定 Name Servers

部署完成後，腳本會顯示 Name Servers：

```
Name Servers（請到域名註冊商設定）：
┌────────────────────────────────┐
│ ns-123.awsdns-12.com          │
│ ns-456.awsdns-45.net          │
│ ns-789.awsdns-78.org          │
│ ns-012.awsdns-01.co.uk        │
└────────────────────────────────┘
```

**請到您的域名註冊商（GoDaddy、Namecheap 等）設定這些 NS 記錄。**

### 2. 上傳您的網站

```bash
# 上傳整個資料夾
aws s3 sync ./your-website s3://yourdomain.com-website/

# 或使用管理工具
./manage.sh
# 選擇 4) 上傳網站內容到 S3
```

### 3. 清除快取（更新內容後）

```bash
# 手動清除
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"

# 或使用管理工具
./manage.sh
# 選擇 5) 清除 CloudFront 快取
```

---

## 📊 重要資訊儲存位置

部署過程中，腳本會將重要資訊儲存在 `/tmp/` 目錄：

```bash
/tmp/zone_id.txt       # Route53 Zone ID
/tmp/cert_arn.txt      # ACM 憑證 ARN
/tmp/dist_id.txt       # CloudFront Distribution ID
/tmp/dist_domain.txt   # CloudFront 域名
/tmp/dist_arn.txt      # CloudFront ARN
```

**建議：** 部署完成後，將這些資訊記錄下來！

---

## 🐛 疑難排解

### 問題：AWS CLI 認證失敗

```bash
# 檢查認證
aws sts get-caller-identity

# 重新配置
aws configure
```

### 問題：jq 命令找不到

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### 問題：憑證驗證超時

```bash
# 檢查 DNS 記錄
aws route53 list-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID

# 手動檢查驗證記錄
dig _acm-validation.yourdomain.com CNAME
```

### 問題：CloudFront 建立失敗

```bash
# 檢查 ACM 憑證狀態
aws acm describe-certificate \
  --certificate-arn YOUR_CERT_ARN \
  --region us-east-1

# 確認憑證已驗證
aws acm list-certificates \
  --region us-east-1 \
  --certificate-statuses ISSUED
```

### 問題：S3 Bucket 名稱已被使用

修改 `deploy.sh` 中的 `BUCKET_NAME`：

```bash
BUCKET_NAME="${DOMAIN_NAME}-website-$(date +%s)"
```

---

## 💡 進階用法

### 只執行特定步驟

編輯 `deploy.sh`，註解掉不需要的函數：

```bash
main() {
    # create_hosted_zone        # 跳過
    # request_certificate       # 跳過
    # create_validation_records # 跳過
    create_s3_bucket            # 只執行這個
    # ...
}
```

### 批次部署多個域名

建立配置檔案 `domains.txt`：

```
example1.com
example2.com
example3.com
```

建立批次腳本：

```bash
#!/bin/bash
while read domain; do
    sed -i '' "s/^DOMAIN_NAME=.*/DOMAIN_NAME=\"$domain\"/" deploy.sh
    ./deploy.sh
done < domains.txt
```

### 自訂 S3 內容

修改 `deploy.sh` 中的 `upload_test_page()` 函數，上傳您自己的內容。

---

## 🔄 更新與維護

### 更新網站內容

```bash
# 方法 1：使用 AWS CLI
aws s3 sync ./website s3://yourdomain.com-website/ --delete

# 方法 2：使用管理工具
./manage.sh
# 選擇 4) 上傳網站內容到 S3

# 清除快取
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

### 查看資源狀態

```bash
./manage.sh
# 選擇對應的選項查看各種資源
```

### 刪除資源

**注意：** 刪除順序很重要！

```bash
# 1. 刪除 Route53 記錄（保留 NS 和 SOA）
aws route53 list-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID

# 2. 停用並刪除 CloudFront
aws cloudfront get-distribution-config \
  --id YOUR_DIST_ID > dist-config.json
# 修改 Enabled 為 false
aws cloudfront update-distribution --id YOUR_DIST_ID --if-match ETAG --distribution-config file://dist-config.json
# 等待停用完成
aws cloudfront delete-distribution --id YOUR_DIST_ID --if-match ETAG

# 3. 刪除 S3 Bucket
aws s3 rm s3://yourdomain.com-website/ --recursive
aws s3api delete-bucket --bucket yourdomain.com-website

# 4. 刪除 ACM 憑證
aws acm delete-certificate \
  --certificate-arn YOUR_CERT_ARN \
  --region us-east-1

# 5. 刪除 Route53 Hosted Zone
aws route53 delete-hosted-zone --id YOUR_ZONE_ID
```

---

## 📈 成本估算

```bash
./manage.sh
# 選擇 8) 查看資源成本估算
```

**典型小型網站（每月）：**
- Route53: $0.50
- S3 儲存 (1GB): $0.023
- CloudFront (100GB): ~$8.50
- **總計: ~$9/月**

---

## ✅ 檢查清單

部署前：
- [ ] 已安裝 AWS CLI 和 jq
- [ ] 已配置 AWS 認證
- [ ] 已準備好域名
- [ ] 已修改腳本中的域名配置

部署後：
- [ ] 已記錄所有重要 ID 和 ARN
- [ ] 已設定 NS 記錄到域名註冊商
- [ ] 已上傳網站內容
- [ ] 已測試網站可訪問
- [ ] 已清除 CloudFront 快取

---

## 🆚 與 Terraform 比較

| 特性 | CLI 腳本 | Terraform |
|-----|---------|-----------|
| 學習曲線 | 簡單 | 中等 |
| 可重複性 | 中等 | 優秀 |
| 版本控制 | 困難 | 容易 |
| 狀態管理 | 手動 | 自動 |
| 適用場景 | 一次性部署 | 長期維護 |

**建議：**
- 快速測試 → 使用 CLI 腳本
- 生產環境 → 使用 Terraform
