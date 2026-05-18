# DB AI / RAG Skeleton

此目錄提供 `08-Database/DB-Automation` 的 AI 分析與 RAG 導入 skeleton。

## Files

- `DB-AI-RAG-SOURCE-CATALOG.md`: DB 專屬資料來源、敏感度與導入策略
- `db-rag-sources.example.yaml`: source catalog / ingestion policy 範例
- `db-event-summary.example.json`: DB 事件摘要資料範例
- `db-backup-summary.schema.json`: backup summary schema
- `db-migration-summary.schema.json`: migration summary schema
- `db-monitoring-summary.schema.json`: monitoring alert summary schema
- `db-remediation-summary.schema.json`: remediation summary schema
- `db-ansible-summary.schema.json`: ansible consistency summary schema
- `db-backup-summary.example.json`: backup summary example
- `db-backup-summary.mysql.example.json`: MySQL backup summary example
- `db-migration-summary.example.json`: migration summary example
- `db-migration-summary.mysql.example.json`: MySQL migration summary example
- `db-mysql-restore-evidence.schema.json`: MySQL restore evidence schema
- `db-mysql-restore-evidence.example.json`: MySQL restore evidence example
- `db-mysql-precheck-evidence.schema.json`: MySQL precheck evidence schema
- `db-mysql-precheck-evidence.example.json`: MySQL precheck evidence example
- `db-mysql-postcheck-evidence.schema.json`: MySQL postcheck evidence schema
- `db-mysql-postcheck-evidence.example.json`: MySQL postcheck evidence example
- `db-monitoring-evidence.schema.json`: monitoring evidence schema
- `db-monitoring-evidence.example.json`: monitoring evidence example
- `db-ansible-evidence.schema.json`: ansible evidence schema
- `db-ansible-evidence.example.json`: ansible evidence example
- `db-monitoring-summary.example.json`: monitoring summary example
- `db-remediation-summary.example.json`: remediation summary example
- `db-ansible-summary.example.json`: ansible summary example
- `validate_db_summary.py`: DB summary / evidence validator skeleton
- `ingest_db_summaries.py`: DB summary dataset ingestor skeleton（支援 `--include-evidence`、`--scan-dir`、`--scope-prefix`）
- `cleanup_producer_artifacts.py`: 清理舊 scoped producer artifact 目錄
- `producer-artifacts/`: 預設 producer artifact 掃描目錄
- `db-summary-dataset.example.json`: combined summary dataset output
- `db-summary-dataset.with-evidence.example.json`: combined summary + evidence dataset output
- `db-summary-dataset.latest-scoped.example.json`: latest scoped dataset output

本地查詢建議：
- 預設優先讀 latest scoped dataset，其次 scanned dataset：`python3 06-DevTools/automation/ai-rag/query_local_rag.py <query>`
- 查詢最新 scoped/scanned evidence：`python3 06-DevTools/automation/ai-rag/query_local_rag.py --include-evidence <query>`
- 僅查 scoped dataset、不混 chunk/example：`python3 06-DevTools/automation/ai-rag/query_local_rag.py --include-evidence --scoped-only <query>`
- 若 scoped / scanned dataset 不存在，會 fallback 到 example dataset

本地匯入建議：
- example only：`python3 08-Database/DB-Automation/ai-rag/ingest_db_summaries.py`
- example + evidence：`python3 08-Database/DB-Automation/ai-rag/ingest_db_summaries.py --include-evidence`
- 掃描 producer 輸出：`python3 08-Database/DB-Automation/ai-rag/ingest_db_summaries.py --scan-dir 08-Database/DB-Automation/ai-rag/producer-artifacts`
- 只掃描指定 scope：`python3 08-Database/DB-Automation/ai-rag/ingest_db_summaries.py --scan-dir 08-Database/DB-Automation/ai-rag/producer-artifacts --scope-prefix session-YYYYMMDD/action-... --include-evidence`
- 只輸出 scoped records：`python3 08-Database/DB-Automation/ai-rag/ingest_db_summaries.py --scan-dir 08-Database/DB-Automation/ai-rag/producer-artifacts --scope-prefix session-YYYYMMDD/action-... --include-evidence --scoped-only`
- 清理舊 scope：`python3 08-Database/DB-Automation/ai-rag/cleanup_producer_artifacts.py --keep 5 --dry-run`

## Scope

支援下列模組的知識導入規劃：
- `backup-recovery`
- `migration`
- `monitoring/k8s`
- `remediation`
- `ansible`

## Design Principles

### 1. schema-first event design
DB 維運事件如果沒有固定欄位，後續很難做檢索、比對與 recommendation。所以這裡先定義 schema，再談 producer 與 downstream consumers。

### 2. 證據資料與執行資料分離
AI 最適合讀的是 evidence、summary、check result，而不是直接擁有執行權限。這能降低誤判直接造成 production 變更的風險。

### 3. module-by-module onboarding
backup、migration、monitoring、remediation、ansible 的敏感度與資料型態不相同，因此不做單一全局事件格式，而是先以模組 schema 分開治理，再於平台層統一 recommendation contract。

另外，即使同屬 DB 維運，MSSQL 與 MySQL 的驗證證據也不完全相同，例如 MySQL 會更常需要 logical dump、binlog chain、replication lag 與 metadata lock 類型的摘要欄位，因此 examples 也保留 engine-specific 樣板。

### 4. 摘要結構優先於全文輸入
在 DB 場景中，摘要欄位如 `summary`、`recommended_checks`、`recommended_policy`、`risk_level` 通常比塞整份原始輸出更容易被檢索與審核。

MySQL restore / precheck / postcheck evidence 則作為第二層結構化證據，補充 summary 無法表達的 binlog replay、replica lag、metadata lock 與 smoke query 驗證細節。

同樣地，monitoring / ansible 也可提供獨立 evidence artifact，將 exporter target health、alert state、inventory mapping 與 policy alignment observation 以結構化欄位納入 scanner dataset。

## Guardrails

- 僅導入文件、模板與摘要化資料
- 不導入真實 DB credentials
- 不導入 raw production dump
- 不導入未遮罩的 PII / query output
- 不讓 AI 直接執行 production DB 變更

## Suggested Next Steps

1. 將 producer 輸出的 summary artifact 自動匯入 dataset
2. 讓 producer 直接輸出 evidence artifact，與目前的 MySQL evidence schema 對齊
3. 讓 `query_local_rag.py --include-evidence` 作為本地 evidence triage / review 入口
4. 將 dataset 與平台級 `control-plane` recommendation generation 串接
5. 再往後接 embedding / retrieval / 真實 RAG backend
6. 讓 control-plane action executor 可觸發 summary refresh 與 local dataset refresh
