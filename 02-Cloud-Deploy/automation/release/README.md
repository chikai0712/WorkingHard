# Release Practical Skeleton

此目錄提供 build / deploy / rollback 的模板與 metadata 範本。

## Files
- `.env.example`: local shell settings
- `release.sh`: local release helper
- `release-manifest.example.yaml`: release metadata 範本
- `environments.example.yaml`: environment policy / strategy 範本
- `versions.example.env`: version metadata 範本

## Architecture Rationale

### Release metadata 外部化
版本、環境策略、部署對象、rollback 目標不應寫死在腳本中，而應外部化為 manifest / environment policy / version metadata。這樣可以：
- 降低腳本修改頻率
- 增加稽核可讀性
- 支援不同環境用不同策略

### Strategy per environment
`dev`、`staging`、`production` 的風險不同，因此策略也應不同。開發環境可以偏快，正式環境則應偏保守，例如 blue-green、人工 approval、smoke test 與 rollback threshold。

### Rollback 不是例外，是標準流程
此目錄預設 rollback 是 release 的一部分，而不是故障發生後才補救的臨時腳本。這樣在設計 release manifest 時，就會強迫定義 previous stable version、相容性與回復路徑。

## Shared Gate Mapping

release 流程現在對齊 shared gate framework：
- source gate：artifact metadata、release manifest、version traceability
- security gate：release approval、security exceptions、vulnerability threshold
- health gate：smoke test、post-deploy health signal、rollback trigger

共用模型可參考：
- `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md`
- `06-DevTools/automation/source-gate.example.yaml`
- `06-DevTools/automation/security-gate.example.yaml`
- `06-DevTools/automation/health-gate.example.yaml`

## Release Control Flow
1. 讀取 version metadata
2. 讀取 environment policy
3. 產出或確認 release manifest
4. 執行 build / deploy / rollback 導引
5. 保留後續可掛接 smoke test、approval、change record

## Sequence Flow
1. 從 CI 或 artifact registry 取得候選版本
2. 執行 source gate，確認 artifact / metadata 完整
3. 執行 security gate，確認例外與風險門檻
4. 讀取環境策略與 release manifest
5. 決定 deploy / hold / rollback 路徑
6. deploy 後執行 health gate 與驗證步驟

## Decision Matrix

| Condition | Decision | Rationale |
|---|---|---|
| 候選版本未通過 source gate | hold | 交付物或 metadata 不完整時不得進入 release |
| 候選版本未通過 security gate | hold 或 block | 存在安全風險或例外治理不足 |
| 目標環境需要 approval 但尚未核准 | hold | 符合正式環境變更控管 |
| 新版本與目前版本相容且風險可接受 | deploy | 條件符合可進入發布 |
| 發布後 health gate 不符門檻 | rollback 到 previous stable | 優先恢復服務穩定性 |

## Apply Workflow
1. 載入 version metadata 與 environment policy
2. 執行 source gate 與 security gate
3. 產生 release manifest
4. 決定 deploy strategy
5. 執行 deploy 並觀察 health signals
6. 執行 post-deploy health gate
7. 成功則結案，失敗則進入 rollback path

## Rollback Scenario
- 前提：已知 previous stable version 可用
- 觸發條件：smoke test fail、錯誤率飆升、核心功能不可用、approval 中止
- 處置：切回 previous stable，重做 post-deploy verification，保留 incident / change evidence

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 維護 release manifest / environment policy | Platform / DevOps | Technical Lead / Release Owner | Security, Service Owner | Stakeholders |
| 維護 source/security/health gate 規則 | Platform / DevOps | Release Owner | Security, Service Owner, SRE | Stakeholders |
| 核准 production deploy | Release Manager / Platform | Service Owner | Security, DBA, SRE | Stakeholders |
| 執行 rollback | Platform / On-call Engineer | Incident Commander / Service Owner | SRE, App Owner | Stakeholders |

## Suggested next extensions
- 加入實際 artifact registry metadata
- 加入 smoke test command hooks
- 加入 deployment approvals 與 change record integration
- 將 gate decision evidence 輸出為標準化報表
