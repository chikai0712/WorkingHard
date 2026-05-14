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

### [2026-05-14 13:28] — 將 decision matrix 表格化並補 RACI
- **Phase**: Phase 7 — DNS/CDN + Network/Security 實戰版 skeleton / 文件強化
- **Status**: Complete
- **Done**: 將 `release/`、`iac/`、`dns-cdn/`、`security/` README 中的 decision matrix 改為表格格式，並補上各模組的 RACI 章節，讓決策與責任分工更接近正式設計文件。
- **Next**: 若需要，可再將 `network/`、`backup-recovery/` 也轉成完整表格版 decision matrix，並補 change governance / break-glass 章節。
- **Blocker**: 無

### [2026-05-14 13:15] — 補 decision matrix 與 apply/rollback workflow 文件
- **Phase**: Phase 7 — DNS/CDN + Network/Security 實戰版 skeleton / 文件強化
- **Status**: Complete
- **Done**: 更新 `automation/cicd/`、`release/`、`iac/`、`dns-cdn/`、`network/`、`security/` README，補上 decision matrix、apply workflow、rollback/fallback scenario；同步更新 `06-DevTools/automation/AUTOMATION-ARCHITECTURE-OVERVIEW.md`，加入 cross-layer decision model 與 apply workflow meta-pattern。
- **Next**: 若需要，可再補表格化 decision matrix、圖像化 sequence diagram、RACI 與 change governance 章節。
- **Blocker**: 無

### [2026-05-14 13:00] — 完成 DNS/CDN + Network/Security 實戰版與 sequence flow 文件補強
- **Phase**: Phase 7 — DNS/CDN + Network/Security 實戰版 skeleton
- **Status**: Complete
- **Done**: 在 `automation/dns-cdn/` 新增 `failover-policy.example.yaml`、Cloudflare/Route53 provider record 範本並更新 `failover_check.py`；在 `automation/network/` 新增 `policies/desired-rules.example.yaml` 並更新 `check_rules.sh`；在 `automation/security/` 新增 `policy-gate.example.yaml`、`report-schema.example.yaml` 並更新 `scan.sh`。同時補強多個 README 的 sequence flow，並在 `06-DevTools/automation/` 新增 `AUTOMATION-ARCHITECTURE-OVERVIEW.md` 作為總覽文件。已完成 shell / Python / 模板結構檢查。
- **Next**: 若需要，可再補 decision matrix、apply workflow、sequence diagram 圖像版與 provider-specific adapters 的更完整實作。
- **Blocker**: 目前仍為模板層級，不含真實 provider credentials、正式 scanner integration 或 production apply flow。

### [2026-05-14 12:40] — 強化 automation README 架構原理與設計說明
- **Phase**: Phase 6 — Terraform / IaC 實戰版 skeleton / 文件強化
- **Status**: Complete
- **Done**: 更新 `02-Cloud-Deploy/automation/` 下各 README，補上模組分層、control flow、plan-first、provider adapter、security gate 等架構原理與設計邊界說明。
- **Next**: 若需要，可再為 `dns-cdn/`、`network/`、`security/` 補更細的 sequence diagram、decision matrix 或 apply workflow。
- **Blocker**: 無

### [2026-05-14 11:55] — 完成 Terraform / IaC 實戰版 skeleton 第一輪
- **Phase**: Phase 6 — Terraform / IaC 實戰版 skeleton
- **Status**: Complete
- **Done**: 在 `02-Cloud-Deploy/automation/iac/` 新增 `backends/s3.backend.example.hcl`、`environments/dev|staging|prod/terraform.tfvars.example`、`modules/example-static-site/` 最小 module scaffold，並更新 `README.md` 與 `terraform_wrapper.sh`，支援 init / validate / plan / apply-dry-run 導引。已完成 shell 語法檢查與模板基本結構檢查。
- **Next**: 可再補 remote state 多 provider 範例、OpenTofu 分支、module version pinning、pre-commit / tfsec / checkov 範例與真實專案接線說明。
- **Blocker**: 目前仍為模板層級，不含真實 backend bucket、state key、credentials 或正式 apply 流程。

### [2026-05-14 11:48] — 啟動 Terraform / IaC 實戰版 skeleton
- **Phase**: Phase 6 — Terraform / IaC 實戰版 skeleton
- **Status**: In progress
- **Done**: 確認將 `automation/iac/` 從單一 wrapper 提升到可套用模板層級，目標包含 backend、tfvars、module scaffold 與更完整的 wrapper 導引。
- **Next**: 建立 backend / tfvars / module 範本，更新 README 與 `terraform_wrapper.sh`。
- **Blocker**: 無

### [2026-05-14 11:40] — 完成 CI/CD + Release 實戰版 skeleton 第一輪
- **Phase**: Phase 5 — CI/CD + Release 實戰版 skeleton
- **Status**: Complete
- **Done**: 在 `02-Cloud-Deploy/automation/cicd/` 新增 `README.md`、`github-actions-example.yml`、`gitlab-ci-example.yml`，並更新 `pipeline.sh` 顯示可用模板；在 `automation/release/` 新增 `README.md`、`release-manifest.example.yaml`、`environments.example.yaml`、`versions.example.env`，並更新 `release.sh` 顯示 metadata 模板位置。已完成 shell 語法檢查與模板基本結構檢查。
- **Next**: 可繼續補 reusable workflow、container build/push 範例、artifact registry metadata、smoke test hooks 與 production approval gate。
- **Blocker**: 目前仍是模板層級，未接真實 GitHub/GitLab secrets、registry、runner 或 deployment target。

### [2026-05-14 11:32] — 啟動 CI/CD + Release 實戰版 skeleton
- **Phase**: Phase 5 — CI/CD + Release 實戰版 skeleton
- **Status**: In progress
- **Done**: 確認將 `automation/cicd/` 與 `automation/release/` 從第一版 dry-run skeleton 提升到可套用模板層級，目標包含 GitHub Actions、GitLab CI、release metadata 與 environment config 範例。
- **Next**: 建立 pipeline 樣板、release manifest / versions / environments 範例，並同步更新 shell skeleton。
- **Blocker**: 無

### [2026-05-14 11:20] — 建立 Cloud Deploy automation skeleton 第一版
- **Phase**: Phase 4 — 實機部署驗證 / 新增 automation skeleton
- **Status**: In progress
- **Done**: 建立 `02-Cloud-Deploy/automation/` 與子目錄 `cicd/`、`release/`、`iac/`、`config-mgmt/`、`dns-cdn/`、`network/`、`security/`，加入 README、`.env.example` 與 dry-run shell / Python skeleton，並完成基本語法檢查。
- **Next**: 可再補 GitHub Actions / GitLab CI YAML 範例、Terraform backend 範本、Cloudflare / Route53 adapters、security scan policy gate 與 network desired-state schema。
- **Blocker**: 目前僅為 skeleton，不連接真實 CI provider、cloud account 或 DNS/CDN API。

### [2026-05-14 11:10] — 新增 Cloud Deploy automation skeleton 規格
- **Phase**: Phase 0-4 — 既有 EC2 網站任務 / 新增 automation skeleton 規劃
- **Status**: In progress
- **Done**: 擴充 `02-Cloud-Deploy/.planning/CONTEXT.md`，將 `automation/` 納入專案範圍，預計承接 CI/CD、Build/Deploy/Rollback、IaC、Configuration Management、DNS/CDN、Security 與 Network automation skeleton。
- **Next**: 如獲確認，於 `02-Cloud-Deploy/automation/` 建立 skeleton 結構與 README，不影響既有 `ec2-simple-website/` 任務。
- **Blocker**: 無

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
