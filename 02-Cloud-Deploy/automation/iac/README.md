# Terraform / IaC Practical Skeleton

此目錄提供 Terraform / OpenTofu 的可套用模板層級骨架。

## Structure
- `terraform_wrapper.sh`: 本地操作入口，顯示 init/fmt/validate/plan/apply 導引
- `backends/`: backend 設定範本
- `environments/`: 各環境 tfvars 範例
- `modules/example-static-site/`: 最小 module scaffold

## Architecture Principles

### State、Environment、Module 分離
IaC 最容易失控的地方，是把 backend、環境值與資源定義混在一起。這裡刻意拆成：
- `backends/`: state 存放位置與 locking 策略
- `environments/`: 各環境變數
- `modules/`: 可重用的資源宣告

這種拆法能讓同一個 module 服務多個環境，同時保留 state 隔離。

### Plan-first 是核心安全邊界
IaC 的高風險點在於一次變更多個資源，因此 wrapper 優先暴露 `fmt`、`validate`、`plan`，而不是直接 `apply`。先看 diff，再做變更，是避免誤刪或錯配的第一道防線。

### Module 設計應保持最小表面積
範例 module 只保留必要變數與輸出，目的是示範可重用界面，而不是在第一版放進太多 provider-specific 細節。這樣後續可以擴充，但不會一開始就做成難以維護的大 module。

## Suggested workflow
1. 複製對應 backend / tfvars example
2. 依實際專案填入 provider、state 與變數
3. 使用 `terraform_wrapper.sh` 做 fmt / validate / plan
4. 經人工確認後，再到真實專案目錄執行 apply

## Sequence Flow
1. 定義 module 與 environment 變數
2. 初始化 backend 與 provider
3. 執行 validate / plan
4. 審查 plan diff
5. 通過後才在正式目錄或正式流程中 apply

## Decision Matrix

| Condition | Decision | Rationale |
|---|---|---|
| validate 失敗 | 禁止 plan / apply | 輸入或語法不正確時不應繼續 |
| plan 有高風險刪除或替換 | 進入人工 review | 需先確認 blast radius |
| plan 僅為預期增量變更 | 可進入 approval | 風險在可接受範圍內 |
| backend / state 不一致 | 先修正 state 問題，不 apply | 避免 state 汙染與誤變更 |

## Apply Workflow
1. 載入 backend 與 tfvars
2. 執行 fmt / validate / plan
3. 審查 plan diff 與 blast radius
4. 通過 approval 後於正式流程 apply
5. apply 後執行輸出檢查與 drift baseline 更新

## Fallback Scenario
- 觸發條件：plan diff 異常、apply 中斷、state lock 問題、資源替換風險過高
- 處置：停止 apply、保留 plan 證據、修正 backend/state/變數後重新驗證

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 維護 modules / tfvars / backend templates | Platform Engineer | Infra Owner | Security, App Owner | Stakeholders |
| 審查 plan diff | Platform / Reviewer | Infra Owner | Service Owner | Stakeholders |
| 核准 apply | Infra Owner / Change Approver | Service Owner | Security, Platform | Stakeholders |
- 不把真實 state backend credentials 寫入 repo
- 不在 skeleton 目錄直接 apply 到正式環境
- backend / tfvars 僅提供 example，不含真實 bucket / account 資訊
