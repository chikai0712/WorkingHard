# DB Migration Practical Skeleton

此目錄提供 migration config、version SQL、pre/post checks 與 rollback policy 的模板層級骨架。

## Files
- `migrate.sh`: migration helper
- `flyway.conf.example`: Flyway 配置範例
- `flyway.mysql.conf.example`: MySQL Flyway 配置範例
- `precheck.example.sql`: migration 前檢查 SQL 範本
- `precheck.mysql.example.sql`: MySQL migration 前檢查 SQL 範本
- `postcheck.example.sql`: migration 後檢查 SQL 範本
- `postcheck.mysql.example.sql`: MySQL migration 後檢查 SQL 範本
- `rollback-guidelines.md`: 回滾準則
- `sql/V001__init_example/001_create_sample_table.sql`: versioned SQL 範例
- `sql/V001__init_example/001_create_sample_table.mysql.sql`: MySQL versioned SQL 範例

## Architecture Principles

### Schema 變更必須版本化
migration 的核心不是「執行 SQL」，而是「可追蹤、可排序、可驗證」。因此版本號、命名規則與順序控制是第一原則。

### Pre-check / Post-check 是安全邊界
正式 migration 的風險不只在 SQL 本身，也在執行前後系統狀態是否健康。這就是為什麼 pre-check 與 post-check 要跟 migration 本體一起被設計，而不是事後補上。

同時，MSSQL 與 MySQL 的 pre/post checks 不應共用完全相同的 SQL，因此保留分流範本，讓 metadata lock、replication lag、binlog 或 SQL Server 專屬檢查可以各自演進。

### Rollback 要先定義，再上線
若 migration 是否可逆沒有先定義，上線後再想回退通常會太晚。因此這個目錄把 rollback guideline 視為與 version SQL 同等重要的文件。

## Shared Gate Mapping

migration 流程現在對齊 shared gate framework：
- source gate：version ordering、SQL metadata、pre/post-check 完整性
- security gate：高權限變更、例外治理、風險與審批條件
- health gate：pre-check / post-check DB 狀態驗證、應用相容性與 rollback trigger

共用模型可參考：
- `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md`
- `06-DevTools/automation/source-gate.example.yaml`
- `06-DevTools/automation/security-gate.example.yaml`
- `06-DevTools/automation/health-gate.example.yaml`

## Typical Flow
1. 讀取 migration config
2. 執行 source gate 檢查 version / SQL / metadata
3. 執行 health gate pre-check
4. 套用 versioned SQL
5. 執行 health gate post-check
6. 視情況進入 rollback 或結案

## Sequence Flow
1. 選定目標版本與 migration config
2. 執行 source gate，確認版本與 SQL metadata
3. 執行 pre-check 取得基線
4. 執行 security gate 審查高權限變更與例外
5. 套用版本化 SQL
6. 執行 post-check 與 health gate 驗證結果
7. 記錄成功、失敗或 rollback 決策

## Decision Matrix

| Condition | Decision | Rationale |
|---|---|---|
| source gate 不通過 | 禁止 migration | 版本、SQL 或 metadata 異常時不能推進 |
| health gate pre-check 不通過 | 禁止 migration | 基線異常時不能執行 schema 變更 |
| security gate 例外不完整 | hold 或 block | 高風險變更需先補治理條件 |
| migration 成功但 post-check 失敗 | 進入 rollback / incident handling | 代表變更已造成不一致或風險 |
| migration 不可逆 | 需先確認 restore plan | 不能在無恢復方案下直接執行 |
| 版本順序錯亂或基線不一致 | 先修復版本狀態 | 避免 schema history 汙染 |

## Apply Workflow
1. 載入 migration config 與目標版本
2. 執行 source gate
3. 執行 pre-check
4. 套用 migration
5. 執行 post-check
6. 依結果結案或 rollback

> 共用 gate 模型可參考 `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md`。對 migration 而言，通常會套用：
> - health gate：pre-check / post-check DB 狀態驗證
> - source gate：version SQL、順序與 metadata 完整性檢查
> - security gate：高權限變更、例外治理與弱點風險評估

## Rollback / Fallback Scenario
- 觸發條件：migration 中斷、post-check fail、應用不相容
- 處置：依 rollback guideline 回退；若不可逆，啟動 restore plan 與變更凍結

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 撰寫 migration 與 pre/post checks | DBA / Backend Engineer | DBA Lead / Service Owner | App Owner, SRE | Stakeholders |
| 維護 source/security/health gate 規則 | DBA / Platform Engineer | DBA Lead / Service Owner | Security, SRE | Stakeholders |
| 核准 production migration | DBA Lead / Change Approver | Service Owner | Security, Platform | Stakeholders |
| 執行 rollback 或 restore plan | DBA / On-call Engineer | Incident Commander / DBA Lead | App Owner, SRE | Stakeholders |

## Suggested Next Steps
1. `DB_ENGINE=mysql SUMMARY_OUT=... EVIDENCE_OUT=... ./migrate.sh precheck`
2. `DB_ENGINE=mysql SUMMARY_OUT=... EVIDENCE_OUT=... ./migrate.sh postcheck`
3. 視需要再讓 execution stage 也輸出對應 evidence artifact
4. 再將 artifact 對接 `ingest_db_summaries.py` 或 producer 目錄掃描流程

## Guardrails
- 不連接正式 DB
- 不在 skeleton 中執行真實 migration
- 僅提供版本控管與檢查模板
