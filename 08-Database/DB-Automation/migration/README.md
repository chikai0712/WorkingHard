# DB Migration Practical Skeleton

此目錄提供 migration config、version SQL、pre/post checks 與 rollback policy 的模板層級骨架。

## Files
- `migrate.sh`: migration helper
- `flyway.conf.example`: Flyway 配置範例
- `precheck.example.sql`: migration 前檢查 SQL 範本
- `postcheck.example.sql`: migration 後檢查 SQL 範本
- `rollback-guidelines.md`: 回滾準則
- `sql/V001__init_example/001_create_sample_table.sql`: versioned SQL 範例

## Architecture Principles

### Schema 變更必須版本化
migration 的核心不是「執行 SQL」，而是「可追蹤、可排序、可驗證」。因此版本號、命名規則與順序控制是第一原則。

### Pre-check / Post-check 是安全邊界
正式 migration 的風險不只在 SQL 本身，也在執行前後系統狀態是否健康。這就是為什麼 pre-check 與 post-check 要跟 migration 本體一起被設計，而不是事後補上。

### Rollback 要先定義，再上線
若 migration 是否可逆沒有先定義，上線後再想回退通常會太晚。因此這個目錄把 rollback guideline 視為與 version SQL 同等重要的文件。

## Typical Flow
1. 讀取 migration config
2. 執行 pre-check
3. 套用 versioned SQL
4. 執行 post-check
5. 視情況進入 rollback 或結案

## Sequence Flow
1. 選定目標版本與 migration config
2. 執行 pre-check 取得基線
3. 套用版本化 SQL
4. 執行 post-check 驗證結果
5. 記錄成功、失敗或 rollback 決策

## Decision Matrix

| Condition | Decision | Rationale |
|---|---|---|
| pre-check 不通過 | 禁止 migration | 基線異常時不能執行 schema 變更 |
| migration 成功但 post-check 失敗 | 進入 rollback / incident handling | 代表變更已造成不一致或風險 |
| migration 不可逆 | 需先確認 restore plan | 不能在無恢復方案下直接執行 |
| 版本順序錯亂或基線不一致 | 先修復版本狀態 | 避免 schema history 汙染 |

## Apply Workflow
1. 載入 migration config 與目標版本
2. 執行 pre-check
3. 套用 migration
4. 執行 post-check
5. 依結果結案或 rollback

## Rollback / Fallback Scenario
- 觸發條件：migration 中斷、post-check fail、應用不相容
- 處置：依 rollback guideline 回退；若不可逆，啟動 restore plan 與變更凍結

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 撰寫 migration 與 pre/post checks | DBA / Backend Engineer | DBA Lead / Service Owner | App Owner, SRE | Stakeholders |
| 核准 production migration | DBA Lead / Change Approver | Service Owner | Security, Platform | Stakeholders |
| 執行 rollback 或 restore plan | DBA / On-call Engineer | Incident Commander / DBA Lead | App Owner, SRE | Stakeholders |

## Guardrails
- 不連接正式 DB
- 不在 skeleton 中執行真實 migration
- 僅提供版本控管與檢查模板
