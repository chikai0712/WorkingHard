# Shared Health / Source / Security Gates

這份文件定義跨專案 automation 可共用的 gate framework，用於在 apply / deploy / failover / migration 前後加入一致的健康檢測、源碼檢測與資安檢測。

## Gate Families

### 1. Health Gates
檢查系統是否處於可接受的執行狀態。

典型項目：
- endpoint health
- readiness / liveness
- smoke tests
- dependency reachability
- post-change verification
- restore / migration 後驗證

### 2. Source Gates
檢查源碼與交付物是否符合基本品質與可追溯性要求。

典型項目：
- lint
- unit / integration tests
- build success
- artifact completeness
- manifest / metadata validation

### 3. Security Gates
檢查是否存在阻止變更推進的安全風險。

典型項目：
- secret scanning
- SAST / code pattern scanning
- dependency / filesystem / image vulnerability scanning
- policy gate / exception validation
- credentials boundary review

## Unified Decision Model

所有 gate 都應輸出一致的決策結果：
- `pass`: 可繼續下一步
- `hold`: 暫停，等待人工 review / 補充資訊
- `block`: 明確禁止推進
- `rollback`: 變更已發生，需回退
- `fallback`: 改走替代路徑或保守模式

## Evaluation Order
1. 收集 signal / evidence
2. 套用 health / source / security policy
3. 產出 gate result
4. 記錄 evidence 與 metadata
5. 決定 apply / deploy / switch / migrate 是否繼續
6. 變更後再做 post-change gates

## Event Model

| Event Type | Typical Trigger | Example Outcome |
|---|---|---|
| pre-change | deploy / apply / migrate 前 | pass / hold / block |
| in-change | build / apply / migration 過程中 | hold / block / rollback |
| post-change | deploy / failover / migration 後 | pass / rollback / fallback |
| periodic | scheduled verification | pass / hold / create incident |

## Shared Inputs
- policy / threshold config
- current state / findings / metrics
- artifact / build metadata
- environment context
- exception / approval metadata

## Shared Outputs
- gate decision
- evidence path / report
- owner / escalation target
- required next action

## Example Mapping by Domain

| Domain | Health Gate | Source Gate | Security Gate |
|---|---|---|---|
| CI/CD | build agent / service availability | lint, test, build, artifact | secrets, SAST, dependency scan |
| Release | smoke test, rollout health | release manifest, version metadata | approval, vuln threshold, secret exposure |
| IaC | state/backend reachability | validate, plan integrity | tfsec/trivy/checkov-like policy gate |
| DNS/CDN | probe quorum, failover health | policy / record schema validation | provider credential boundary |
| Backup | restore drill, checksum verify | metadata completeness | retention / encryption policy |
| Migration | pre/post-check DB health | version ordering, SQL checks | privileged change / exception review |

## Guardrails
- 不把 gate 與真實 secrets 綁死在模板中
- 不把通知或報表誤當成最終控制邏輯
- 高風險模組需同時有 pre-change 與 post-change gate
- 安全例外必須有 ticket、owner 與 expiry
