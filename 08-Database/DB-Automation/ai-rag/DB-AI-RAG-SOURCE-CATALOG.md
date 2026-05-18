# DB AI and RAG Source Catalog

## Overview

此文件定義 `08-Database/DB-Automation` 在 AI 分析與 RAG 導入中的資料範圍、來源分類、敏感度與使用邊界。

目標是讓 DB 維運知識可被安全檢索與分析，同時避免把正式環境敏感資料直接導入模型或向量庫。

## Source Families

### 1. Document Knowledge Sources
適合直接做第一階段文件 RAG：
- `backup-recovery/README.md`
- `migration/README.md`
- `monitoring/k8s/README.md`
- `ansible/README.md`
- `remediation/README.md`
- `checklists/restore-drill-checklist.md`
- `rollback-guidelines.md`
- `flyway.conf.example`
- `precheck.example.sql`
- `postcheck.example.sql`

### 2. Event Summary Sources
不直接導入 raw events，而是導入整理後摘要：
- backup verification summary
- restore drill summary
- migration execution summary
- monitoring alert summary
- ansible consistency summary
- remediation execution summary

### Summary Producer Design Principle
各模組先在本地產生 summary artifact，再交給平台 ingestion / recommendation 層使用。這樣做的原因是：
- 可降低 raw payload 敏感度與噪音
- 可保留 module-specific schema
- 可讓 AI recommendation 與人工審批使用同一份可追蹤摘要
- 可在未接 LLM 前先完成資料治理與 UI 串接

目前 `backup-recovery`、`migration`、`monitoring/k8s`、`ansible` 都可直接輸出 schema-aligned local artifact，並可由 `ai-rag/ingest_db_summaries.py --scan-dir ...` 掃描匯入 dataset。

### 3. Evidence and Validation Sources
適合導入結構化摘要，而不是 raw payload：
- backup metadata summary
- retention compliance summary
- precheck / postcheck result summary
- replication / storage / health snapshot summary
- remediation result evidence
- MySQL restore drill evidence
- MySQL precheck / postcheck evidence

## Sensitivity Classification

### Allowed
- template SQL
- SOP / README / runbook
- checklist
- summarized validation results
- sanitized health evidence
- dashboard / alert metadata

### Restricted or Disallowed
- production DB credentials
- connection strings with secrets
- raw production dumps
- PII-bearing query output
- full raw logs with sensitive identifiers
- unmasked incident payloads

## Module Mapping

### backup-recovery
可導入：
- README
- retention policy template
- restore drill checklist
- backup metadata structure
- MySQL logical dump / binlog validation template
- MySQL restore evidence schema / example

不可直接導入：
- 真實 backup artifact
- 真實 bucket 路徑若含敏感命名
- 真實 restore target details

### migration
可導入：
- README
- rollback guideline
- precheck / postcheck SQL template
- versioning structure
- migration summary evidence
- MySQL-specific precheck / postcheck / version SQL examples
- MySQL precheck / postcheck evidence schema / example

不可直接導入：
- production schema snapshot
- raw data diff containing sensitive records
- credentials or DSN with secrets

### monitoring/k8s
可導入：
- README
- alert rule docs
- Helm values templates
- exporter deployment docs
- summarized alert snapshots

不可直接導入：
- real secret manifests
- production endpoint secrets
- unsanitized alert payloads with sensitive topology data

### remediation
可導入：
- README
- remediation policy docs
- summarized remediation outcomes

不可直接導入：
- direct execution secrets
- unrestricted action payloads

### ansible
可導入：
- README
- playbook usage docs
- check summary output schema

不可直接導入：
- management credentials
- complete device config backups
- raw inventory containing sensitive addressing if not sanitized

## Suggested DB RAG Use Cases

1. Migration risk review
2. Backup / restore readiness QA
3. Monitoring alert triage support
4. Remediation evidence summarization
5. Network consistency check interpretation for DB dependencies

## Ingestion Strategy

### Phase 1
只導入文件：
- README
- checklist
- rollback guideline
- SQL template

### Phase 2
導入摘要型資料：
- migration summary
- backup verification summary
- alert summary
- ansible consistency summary

### Phase 3
導入 evidence-level structured records：
- precheck result summary
- postcheck result summary
- restore evidence summary
- remediation outcome summary

## Output Contract Recommendation

DB 相關 AI 輸出建議固定欄位：

```json
{
  "summary": "...",
  "risk_level": "medium",
  "possible_causes": ["..."],
  "required_prechecks": ["..."],
  "rollback_references": ["..."],
  "human_approval_required": true
}
```

## Producer Alignment Notes
- `backup-recovery/verify_backup.sh` 現在可輸出 summary artifact，且在 MySQL 模式下可額外輸出 restore evidence artifact。
- `migration/migrate.sh` 現在可輸出 summary artifact，且在 MySQL `precheck` / `postcheck` 模式下可額外輸出 evidence artifact。
- 後續若接真實 producer，建議延續相同欄位契約，避免 ingestion / query 層再做轉換。
