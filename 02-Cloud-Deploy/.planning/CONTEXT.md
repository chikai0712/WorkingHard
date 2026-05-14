# 02-Cloud-Deploy — Context

## 專案範圍

`02-Cloud-Deploy` 用於雲端部署與網站驗證相關資源。目前保留既有目錄：

- `terraform-cdn-setup/`：舊架構，GCP GCE Origin + AWS CloudFront + Route53，使用舊 AWS/GCP 資源。
- `Website/terraform/`：S3 + CloudFront 靜態網站實驗配置。
- `Website/`：EC2/Nginx 手動部署與 DNS 測試腳本。
- `ec2-simple-website/`：新 AWS 帳號專用，從零建立 EC2 + Nginx 簡易網站。

## 當前任務規格

## 任務：新 AWS 帳號一鍵新建 EC2 簡易網站
- 目標：使用新的 AWS 帳號在東京區域建立一個簡易 EC2 + Nginx 靜態網站，不依賴舊 EC2、舊 AWS 帳號或舊 GCP 資源。
- 方法：新增 `ec2-simple-website/` Terraform 模組，建立 EC2、Security Group、Key Pair、Elastic IP，並用 user data 安裝 Nginx 與首頁。
- 驗證：`aws sts get-caller-identity` 指向新帳號 `146147823297`，`terraform plan` 成功，部署後可用 `http://<Elastic-IP>` 開啟網站。
- 影響範圍：`02-Cloud-Deploy/.planning/*`、`02-Cloud-Deploy/ec2-simple-website/*`、根目錄 `.planning/STATE.md`、`.planning/ROADMAP.md`。

## 技術限制

- 新 AWS profile：`new-website`。
- AWS Region：`ap-northeast-1`。
- 第一版只做 HTTP，HTTPS 與網域接回在第二階段處理。
- 不要在 `terraform-cdn-setup/` 目錄使用新 AWS profile 執行 `terraform apply`，該目錄會讀舊 AWS/GCP state。

## Forbidden Zones

- 不修改 `terraform-cdn-setup/` 的既有 Terraform state 或舊混合雲架構。
- 不提交或寫入任何 AWS Access Key、Secret Access Key、GCP JSON key、`.pem` private key。
- 不把 SSH 來源永久設為開放全網，除非使用者明確要求；預設由部署腳本偵測目前 public IP 並寫入 `terraform.tfvars`。
- 不自動操作 DNS 或 Route53，除非確認網域管理權在新 AWS 帳號。

## 後續擴充

- 將 `clouddeployment168.site` 或 `www.clouddeployment168.site` A record 指向 Elastic IP。
- 加入 Certbot HTTPS 或 CloudFront + ACM。
- 若網站變成純靜態正式站，可評估改回 S3 + CloudFront 降低維護成本。
