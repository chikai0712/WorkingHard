# 02-Cloud-Deploy — State

## Current Snapshot

- **Current Phase**: Phase 4 — 實機部署驗證
- **Status**: Pending user execution
- **Project Path**: `02-Cloud-Deploy/`
- **Active Module**: `02-Cloud-Deploy/ec2-simple-website/`
- **AWS Profile**: `new-website`
- **AWS Account Confirmed**: `146147823297`
- **Region**: `ap-northeast-1`

## Latest Log

### [2026-05-07 18:03] — 首頁加入 DNS / CDN 檢測面板
- **Phase**: Phase 3 — 本地驗證 / Phase 4 — 實機部署前準備
- **Status**: Complete
- **Done**: 更新 `ec2-simple-website/user_data.sh.tftpl`，首頁新增 DNS-over-HTTPS 查詢 CNAME/A/AAAA 與 HTTP header signature 判斷，可推測 CloudFront、Cloudflare、Fastly、Akamai、Vercel、Netlify 或 Direct / EC2-Nginx。
- **Next**: 使用者執行 `./deploy.sh` 或重新 `terraform apply`，讓 EC2 user data 產生新版首頁後進行實機驗證。
- **Blocker**: 瀏覽器不能直接執行系統 `dig`，因此採 DoH 模擬；若 CDN header 未暴露給瀏覽器，判斷會以 DNS CNAME 為主。

### [2026-05-07 17:55] — 新 AWS 帳號 EC2 模組初始化
- **Phase**: Phase 0-3 — Planning / Terraform EC2 模組 / 一鍵部署腳本 / 本地驗證
- **Status**: Complete
- **Done**: 建立 `02-Cloud-Deploy/.planning/` 文件；新增 `ec2-simple-website/` Terraform 模組與 `deploy.sh`；本地完成 `terraform fmt -check` 與 `bash -n deploy.sh`。使用者已驗證 AWS profile `new-website` 連到新帳號 `146147823297`。
- **Next**: 使用者在 `02-Cloud-Deploy/ec2-simple-website/` 執行 `./deploy.sh`，建立 EC2 + Nginx + Elastic IP，並用輸出的 URL 驗證網站。
- **Blocker**: 尚未實際 `terraform apply`；DNS `clouddeployment168.site` 管理位置尚未確認。

## Recovery Command

```bash
cd /Users/ckchiu/Desktop/Project/02-Cloud-Deploy/ec2-simple-website
export AWS_PROFILE=new-website
export AWS_REGION=ap-northeast-1
./deploy.sh
```

## Notes

- 不要在 `02-Cloud-Deploy/terraform-cdn-setup/` 使用新 AWS profile 執行 apply；該目錄是舊 AWS/GCP 混合雲架構。
- 第一版先用 `http://<Elastic-IP>` 測通網站。
- DNS 與 HTTPS 另開 Phase 處理。
