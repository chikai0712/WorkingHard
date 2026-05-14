# Security Automation Skeleton

這裡放 security scanning 整合 CI/CD 的樣板。

第一版僅提供：
- 掃描階段定義
- 報告輸出 skeleton
- policy gate placeholder

## Practical Templates
- `policies/policy-gate.example.yaml`: 嚴重度與例外治理規則
- `policies/report-schema.example.yaml`: 報告結構範本
- `scan.sh`: 掃描與 gate 導引入口

## Architecture Principles

### 掃描、報告、阻擋分三層
安全自動化不應只有「掃描一下」。較完整的流程應拆成：
1. 掃描層：收集 SAST / dependency / secret / container findings
2. 報告層：將結果正規化、彙總與分類
3. Policy gate：依嚴重度、範圍與例外規則決定是否阻擋

### Security gate 需要可解釋性
如果 pipeline 被擋下來，開發與維運必須知道是什麼規則造成阻擋。因此這一層要能清楚表達 threshold、例外條件與 remediation 建議。

### 先 policy，再 tooling
工具會換，但 policy 應先穩定。這也是為什麼這個 skeleton 先保留 gate placeholder 與輸出結構，而不是直接綁死某個單一掃描器。

## Sequence Flow
1. 定義掃描範圍與 policy gate
2. 執行掃描器並收集 findings
3. 依 report schema 正規化結果
4. 套用 severity / exception policy
5. 輸出 warning、block 或 remediation 建議

## Decision Matrix

| Condition | Decision | Rationale |
|---|---|---|
| 出現 critical finding | block | 高嚴重度風險不可直接放行 |
| 僅有 high / medium 且 policy 允許 | warn 或 hold | 視治理規則決定是否暫停 |
| 例外條件存在但沒有 ticket / expiry | block | 不可接受無期限例外 |
| 掃描結果不完整 | hold | 避免在資訊不足下誤放行 |

## Apply Workflow
1. 載入 policy gate 與 report schema
2. 執行掃描
3. 彙整 findings
4. 套用 gate 規則
5. 輸出 block / warn / pass decision

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 維護 policy gate 與 schema | Security Engineer | Security Owner | Platform, Dev Lead | Stakeholders |
| 解讀 findings 並決定 block / warn | Security Engineer / Platform | Security Owner | Service Owner | Stakeholders |
| 核准例外 | Security Owner | Risk Owner / Service Owner | Platform, Auditor | Stakeholders |
- 觸發條件：scanner 異常、結果不一致、policy 誤擋關鍵發布
- 處置：進入人工審查、記錄例外、補強規則後再重跑
