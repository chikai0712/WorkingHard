# 02-Cloud-Deploy — Roadmap

## Overview

雲端部署子專案，當前重點是使用新的 AWS 帳號在東京區域從零建立 EC2 + Nginx 簡易網站。

## 當前計畫：新 AWS 帳號 EC2 簡易網站

### Phase 0：Planning 初始化 ✅
**Goal**: 補齊子專案 planning 文件並記錄新 EC2 任務規格。

- [x] 建立 `.planning/CONTEXT.md`
  - 驗證方式：檔案存在且包含任務規格、限制與 Forbidden Zones。
  - 相關路徑：`02-Cloud-Deploy/.planning/CONTEXT.md`
- [x] 建立 `.planning/ROADMAP.md`
  - 驗證方式：列出 Phase 0-4 與 Progress 表格。
  - 相關路徑：`02-Cloud-Deploy/.planning/ROADMAP.md`
- [x] 建立 `.planning/STATE.md`
  - 驗證方式：記錄本次任務起點與下一步。
  - 相關路徑：`02-Cloud-Deploy/.planning/STATE.md`

### Phase 1：Terraform EC2 模組 ✅
**Goal**: 新增一個不依賴舊帳號/舊 state 的 EC2 網站模組。

- [x] 建立 `ec2-simple-website/main.tf`
  - 驗證方式：包含 AWS provider、AMI lookup、Key Pair、Security Group、EC2、Elastic IP。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/main.tf`
- [x] 建立 `variables.tf` 與 `outputs.tf`
  - 驗證方式：輸入可調整，輸出網站 URL、Elastic IP 與 SSH 指令。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/variables.tf`、`outputs.tf`
- [x] 建立 `terraform.tfvars.example`
  - 驗證方式：提供 `new-website` profile、東京區域與 SSH CIDR 範例。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/terraform.tfvars.example`

### Phase 2：一鍵部署腳本 ✅
**Goal**: 提供部署入口，避免使用者在錯誤目錄執行 Terraform。

- [x] 建立 `deploy.sh`
  - 驗證方式：檢查 AWS/Terraform、產生 SSH key、偵測 public IP、產生 tfvars、執行 init/plan/apply。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/deploy.sh`

### Phase 3：本地驗證 ✅
**Goal**: 確認 Terraform 檔案格式與部署腳本語法。

- [x] 執行 `terraform fmt -check`
  - 驗證方式：格式檢查通過。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/*.tf`
- [x] 執行 shell 語法檢查
  - 驗證方式：`bash -n deploy.sh` 通過。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/deploy.sh`
- [x] 新增 DNS / CDN 檢測面板
  - 驗證方式：`user_data.sh.tftpl` 通過 shell 語法檢查，頁面提供 DNS-over-HTTPS 查詢與 CDN signature 判斷。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/user_data.sh.tftpl`

### Phase 4：實機部署驗證 🔲
**Goal**: 使用新 AWS 帳號實際建立 EC2 網站。

- [ ] 執行一鍵部署
  - 驗證方式：`./deploy.sh` 完成並輸出 `website_url`。
  - 相關路徑：`02-Cloud-Deploy/ec2-simple-website/deploy.sh`
- [ ] 驗證網站
  - 驗證方式：`curl http://<Elastic-IP>` 回傳 HTML，瀏覽器可開啟。
  - 相關路徑：Terraform outputs。
- [ ] 規劃 DNS 接回
  - 驗證方式：確認 `clouddeployment168.site` DNS 管理位置與 A record 設定方式。
  - 相關路徑：待確認。

### Phase 5：CI/CD + Release 實戰版 skeleton 🔄
**Goal**: 讓 `automation/cicd/` 與 `automation/release/` 從 dry-run 提升到可套用模板層級。

- [x] 建立 GitHub Actions / GitLab CI 範例 pipeline
  - 驗證方式：存在 workflow / pipeline 樣板，包含 lint、test、build、artifact 與 deploy gate 階段。
  - 相關路徑：`02-Cloud-Deploy/automation/cicd/`
- [x] 建立 release metadata / environment config 範例
  - 驗證方式：存在 `manifest`、`versions`、`environments` 類型樣板。
  - 相關路徑：`02-Cloud-Deploy/automation/release/`
- [x] 更新 shell skeleton 以支援新模板
  - 驗證方式：`pipeline.sh` 與 `release.sh` 可輸出對應模板資訊，且 shell 語法檢查通過。
  - 相關路徑：`02-Cloud-Deploy/automation/cicd/`、`release/`

### Phase 6：Terraform / IaC 實戰版 skeleton 🔄
**Goal**: 讓 `automation/iac/` 從單純 wrapper 提升到可套用 Terraform/OpenTofu 模板層級。

- [x] 建立 backend / tfvars / module scaffold 範本
  - 驗證方式：存在 backend、environment tfvars、module 最小範本與使用說明。
  - 相關路徑：`02-Cloud-Deploy/automation/iac/`
- [x] 更新 wrapper 以支援 init / plan / apply-dry-run 導引
  - 驗證方式：`terraform_wrapper.sh` 可顯示 backend / tfvars / var-file / planfile 相關資訊，且 shell 語法檢查通過。
  - 相關路徑：`02-Cloud-Deploy/automation/iac/terraform_wrapper.sh`
- [x] 建立實務 README 與工作流說明
  - 驗證方式：README 說明目錄用途、建議流程與 guardrails。
  - 相關路徑：`02-Cloud-Deploy/automation/iac/README.md`

### Phase 7：DNS/CDN + Network/Security 實戰版 skeleton 🔄
**Goal**: 讓 `dns-cdn/`、`network/`、`security/` 從初版 skeleton 提升到可套用模板層級。

- [x] 建立 DNS/CDN failover policy 與 provider record 範本
  - 驗證方式：存在 failover policy、provider record 範本與更新後的 `failover_check.py`。
  - 相關路徑：`02-Cloud-Deploy/automation/dns-cdn/`
- [x] 建立 network desired-state 與 security policy/report schema 範本
  - 驗證方式：存在 desired rules、policy gate、report schema 範本與更新後腳本。
  - 相關路徑：`02-Cloud-Deploy/automation/network/`、`security/`
- [x] 補 sequence flow 與實務 README 說明
  - 驗證方式：README 補上 practical templates、sequence flow 與架構原理。
  - 相關路徑：`02-Cloud-Deploy/automation/dns-cdn/`、`network/`、`security/`

## Progress

| Phase | 完成 | 狀態 |
|-------|------|------|
| Phase 0 Planning 初始化 | 3/3 | ✅ Complete |
| Phase 1 Terraform EC2 模組 | 3/3 | ✅ Complete |
| Phase 2 一鍵部署腳本 | 1/1 | ✅ Complete |
| Phase 3 本地驗證 | 3/3 | ✅ Complete |
| Phase 4 實機部署驗證 | 0/3 | 🔲 Pending |
| Phase 5 CI/CD + Release 實戰版 skeleton | 3/3 | ✅ Complete |
| Phase 6 Terraform / IaC 實戰版 skeleton | 3/3 | ✅ Complete |
| Phase 7 DNS/CDN + Network/Security 實戰版 skeleton | 3/3 | ✅ Complete |
