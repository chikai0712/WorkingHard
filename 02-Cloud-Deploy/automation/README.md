# Cloud Deploy Automation Skeleton

這個目錄放雲部署相關的自動化 skeleton。

## Modules
- `cicd/`: CI/CD pipeline 範例
- `release/`: build / deploy / rollback skeleton
- `iac/`: IaC 驗證與 wrapper scripts
- `config-mgmt/`: configuration management skeleton
- `dns-cdn/`: DNS / CDN health check 與 failover 範例
- `network/`: firewall / network rule automation skeleton
- `security/`: security scanning 整合 CI/CD 範例

## Architecture Principles

### 1. Pipeline、Release、Infrastructure 分層
這一層刻意把 CI/CD、Release、IaC、Config Management、DNS/CDN、Network、Security 拆開，而不是做成單一大腳本。
原因是它們的生命週期與風險不同：
- `cicd/` 關注建置與驗證
- `release/` 關注版本推進與回滾
- `iac/` 關注資源宣告與 state
- `config-mgmt/` 關注主機或設備配置一致性
- `dns-cdn/` 關注流量入口與切換判斷
- `network/` 關注 rule drift 與 desired state
- `security/` 關注 policy gate 與掃描輸出

### 2. 先 check，再 apply
所有子模組優先採用 dry-run、check-only、plan-first 的模式。這樣可以先驗證輸入、環境與預期輸出，再決定是否對正式環境變更。

### 3. 將 environment-specific data 與 logic 分離
腳本本身只保留流程控制與欄位約定；真實帳號、API token、backend、var-file、策略值與環境差異，應落在 example config 或後續外部 secret/config system。

### 4. 小模組、可替換
這些 skeleton 的目標不是綁死某個雲或某個 CI provider，而是提供可替換的接點。後續可以按專案需要替換成 AWS、GCP、Cloudflare、GitHub Actions、GitLab CI 或其他實際供應商。

## Control Flow
常見流程會是：
1. 在 `cicd/` 做 lint / test / build
2. 在 `release/` 決定版本、策略與 gate
3. 在 `iac/` 做 fmt / validate / plan
4. 在 `config-mgmt/` 做 drift / check-mode
5. 在 `dns-cdn/`、`network/`、`security/` 補入口層與治理層控制

## Guardrails
- 僅提供 skeleton / dry-run / example
- 不含真實 cloud credentials
- 不直接對正式環境執行變更
- 正式 apply / deploy / cutover 應在專案化流程中另行控管
