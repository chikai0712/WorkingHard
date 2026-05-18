# Automation Architecture Overview

這份文件整理目前工作區內 automation skeleton 的整體設計原理、模組分層與典型流程。

## Scope

目前涵蓋三大區塊：
- `02-Cloud-Deploy/automation/`
- `08-Database/DB-Automation/`
- `06-DevTools/automation/`

## Layered Architecture

### 1. Delivery Layer
位於 `02-Cloud-Deploy/automation/`，處理：
- CI/CD
- Release
- IaC
- Configuration Management
- DNS/CDN
- Network
- Security

這一層負責把「程式與基礎設施如何被安全交付」拆成多個獨立控制面。

### 2. Reliability / Data Layer
位於 `08-Database/DB-Automation/`，處理：
- Backup / Recovery
- Migration
- Remediation
- Monitoring
- Network device consistency

這一層負責把資料可靠性、變更安全性與維運修復流程模型化。

### 3. Shared / Governance Layer
位於 `06-DevTools/automation/`，處理：
- Shared utilities
- FinOps
- Reporting

這一層不直接改變業務系統，而是提供共用能力、治理模型與決策輸出。

## Core Design Principles

### Plan / Check / Review before Apply
整套設計幾乎都先走：
1. 定義期望狀態或策略
2. 收集現況
3. 做 diff / plan / evaluation
4. 交由人工或正式流程決定 apply

這是整個 automation tree 最重要的安全邊界。

### Policy 與 Execution 分離
不論是 release、network、security、backup retention 或 FinOps tagging，規則與執行邏輯都是分離的。這讓規則能被審查、版本化與替換，而不需要重寫所有腳本。

### Provider / Vendor Adapter 分離
DNS/CDN、network device、CI provider、IaC backend 都使用 adapter 思維。這樣後續可以替換 Cloudflare / Route53、Forti / Cisco / F5、GitHub / GitLab，而不重構整個控制流。

### Templates First
目前 repository 以 skeleton / template 為主，而不是直接綁真實環境。目標是先穩定資料模型、目錄結構與控制流程，再逐步接正式帳號與 pipeline。

## Cross-Layer Decision Model

整體可抽象成同一套決策模型：
1. 收集訊號或現況
2. 套用 policy / threshold / desired state
3. 得到 `pass / hold / rollback / fallback / block` 結論
4. 再決定是否 apply

這個模型可同時適用於：
- CI/CD：pass / hold
- Release：deploy / hold / rollback
- IaC：apply / hold / re-plan
- DNS/CDN：switch / observe / revert
- Network：apply / review / revert
- Security：pass / warn / block
- Backup：trusted / untrusted / re-drill
- Migration：apply / rollback / restore

## Decision Matrix Summary

| Layer | Typical Inputs | Decision Outputs | High-Risk Outcome |
|---|---|---|---|
| CI/CD | lint, test, build, artifact metadata | pass, hold | artifact 不可信 |
| Release | version, environment policy, health checks | deploy, hold, rollback | 發布後服務不健康 |
| IaC | plan diff, state health, tfvars | apply, hold, re-plan | 誤刪/誤替換資源 |
| DNS/CDN | probes, quorum, provider records | observe, switch, revert | 錯誤切流造成全域影響 |
| Network | desired rules, current state diff | apply, review, revert | ACL/route 錯誤中斷服務 |
| Security | findings, policy gate, exceptions | pass, warn, block | 高風險漏洞被放行 |
| Backup | artifact, metadata, restore drill | trusted, untrusted, re-drill | 備份不可還原 |
| Migration | pre-check, version SQL, post-check | apply, rollback, restore | schema 改壞且不可逆 |

## Typical End-to-End Flow

一個典型的新服務交付流程可以是：
1. `cicd/` 驗證原始碼並產出 artifact
2. `release/` 準備版本與部署策略
3. `iac/` 產生 infrastructure plan
4. `config-mgmt/` 驗證主機/節點配置一致性
5. `security/` 執行掃描與 gate
6. `dns-cdn/` / `network/` 處理入口與規則層風險
7. `backup-recovery/` / `migration/` 驗證資料層變更
8. `reporting/` 產出營運與變更摘要
9. `finops/` 回頭檢查成本與資源利用率

## Apply Workflow Meta-Pattern

跨模組大致都遵循：
1. 定義 policy / desired state / metadata
2. 收集 current state / findings / health signals
3. 產出 diff / plan / report
4. 做 decision review
5. 才進入 apply 或正式變更
6. 變更後再做 verification / rollback decision

## Shared Gate Framework

跨專案的 health / source / security 檢測模型統一收斂在：
- `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md`
- `06-DevTools/automation/health-gate.example.yaml`
- `06-DevTools/automation/source-gate.example.yaml`
- `06-DevTools/automation/security-gate.example.yaml`

這些 shared gates 提供一致的：
- pre-change / post-change gate 觀念
- `pass / hold / block / rollback / fallback` 決策輸出
- 對 CI/CD、release、IaC、backup、migration 等模組的統一治理語言

## RACI Model

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 維護技術模板與 skeleton | Platform / DevOps Engineer | Technical Lead | Security, DBA, Network | Stakeholders |
| 核准 production 變更 | Service Owner / Change Approver | Service Owner | Platform, Security, DBA | Stakeholders |
| 執行緊急 rollback / fallback | On-call Engineer / Domain Owner | Incident Commander | Platform, DBA, Network, Security | Stakeholders |
| 維護治理規則與 gate | Security / Platform / DBA 各領域 Owner | Domain Owner | Service Owner | Stakeholders |

## Why This Matters

這樣的拆法有幾個好處：
- 不同風險層可獨立演進
- 文件與模板可以先落地，再逐步接實系統
- 跨專案時可以重複利用相同原理與檔案結構
- 對外說明時不只是在展示腳本，而是在展示完整的 automation architecture thinking
