# AI Analysis Architecture and RAG Foundation

## Overview

此文件定義 `06-DevTools` 與 `08-Database/DB-Automation` 共用的 AI 分析架構與 RAG foundation，目標是讓平台維運、IT 自動化與 DB 維運知識能在受控前提下被 AI 用於檢索、摘要、異常分析與決策建議。

第一版聚焦於：
- 文件型知識檢索
- 事件摘要型知識分析
- DB 維運與變更證據輔助判讀
- AI recommendation only，不直接自動執行 production action

## Goals

1. 建立跨專案共用的 AI / RAG 分層架構。
2. 定義可導入與不可導入的資料範圍。
3. 建立最小 ingestion / dataset / metadata skeleton。
4. 為後續 control plane 接入 AI recommendation 預留一致輸出格式。

## Layered Architecture

### 1. Data Source Layer

資料來源分成三大類：

#### A. Document Knowledge
- architecture overview
- runbooks
- SOP / checklists
- README / operational notes
- backup / restore / migration guidance
- monitoring and alert rule docs
- shared gate framework docs

#### B. Operational Event Summaries
- gate evaluation summaries
- deployment / dry-run summaries
- incident summaries
- alert summaries
- validation result summaries

#### C. Evidence and Validation Data
- backup verification evidence
- migration precheck / postcheck summaries
- monitoring health snapshots
- ansible consistency check summaries
- remediation outcome summaries

## 2. Ingestion and Normalization Layer

標準流程：
1. source discovery
2. format normalization
3. sensitivity review / masking
4. metadata enrichment
5. chunking
6. embedding
7. index payload generation
8. indexing

### Pipeline Stages and Design Rationale
- `ingest_documents.py`: 將 repo 文件正規化成可追蹤 record
- `sanitize_records.py`: 在 early stage 去除明顯敏感字串，避免敏感內容往下游擴散
- `validate_metadata.py`: 在 chunk/embedding 前先保證治理欄位齊全
- `emit_chunks.py`: 將可檢索內容切成穩定 chunk
- `embed_records.py`: 先以 placeholder embedding 契約驗證 downstream writer
- `write_pgvector.py` / `write_faiss.py`: 先輸出 index payload，再決定正式後端

這樣拆分的設計原理是讓 ingestion、governance、retrieval storage 三個責任邊界分離，未來切換 embedding model 或 vector store 時，不需要整條 pipeline 重寫。

### Normalization Principles
- 原始 production secrets 不入庫
- 原始 DB dump 不入庫
- 原始全量 log 不直接進 RAG，先摘要化
- SQL 僅導入模板、SOP、已去敏感的檢查語句
- 每個文件 / 事件都需帶 metadata

### Metadata Schema

```json
{
  "doc_id": "db-migration-readme",
  "project": "08-Database/DB-Automation",
  "module": "migration",
  "source_type": "runbook",
  "environment": "template",
  "sensitivity": "internal",
  "tags": ["db", "migration", "rollback"],
  "owner": "platform-dba",
  "updated_at": "2026-05-17",
  "chunk_strategy": "heading-based"
}
```

## 3. Retrieval and Knowledge Layer

### Index Strategy

建議至少分三個 index：
- `docs-index`
- `ops-events-index`
- `db-operations-index`

### Retrieval Strategy
- vector retrieval：語意相似查詢
- keyword retrieval：保留關鍵字精準匹配
- metadata filters：project / module / sensitivity / source_type
- optional reranking：第二階段導入

### Suggested Storage Options
- PoC: FAISS / Chroma
- Formalized deployment: pgvector / Qdrant / OpenSearch vector

### Vector Store Design Principles
- `pgvector` 適合 metadata filter 與 DBA/平台團隊的既有操作習慣
- `FAISS` 適合本地 PoC、離線驗證與不依賴外部服務的開發流程
- 先產出 `vector payload`，再寫入正式後端，能降低 storage lock-in
- embedding 契約與 vector writer 分離，可讓模型替換不影響 storage schema

若以目前工作區與 DB 團隊操作習慣考量，正式化可優先考慮 `pgvector`。

## 4. Analysis and Orchestration Layer

AI 不只做問答，還要支援結構化分析：

### Capabilities
- Runbook QA
- Alert triage assistant
- Change risk analysis
- Evidence summarization
- Gate recommendation support

### Output Contract

```json
{
  "summary": "...",
  "possible_causes": ["..."],
  "recommended_checks": ["..."],
  "related_artifacts": ["..."],
  "confidence": "medium",
  "recommended_policy": "hold"
}
```

### Guardrails
- recommendation only by default
- human approval before real action
- action executor 與 analysis engine 分離
- 對高敏感資料查詢加 metadata filter 與 access policy

## 5. Governance and Security

### Allowed Data
- SOP / runbooks / docs
- template SQL
- sanitized incident summaries
- summarized gate outcomes
- summarized validation evidence
- dashboard metadata

### Disallowed Data
- secrets / tokens / keys
- production DB credentials
- raw customer data
- full production dump
- unmasked SQL query results containing sensitive fields
- raw logs with sensitive identifiers when not sanitized

### Governance Controls
- ingestion allowlist
- sensitivity labeling
- human review on new source onboarding
- retrieval logging
- evaluation set for answer quality
- fallback to manual SOP when confidence too low

## 6. Rollout Phases

### Phase A — Document RAG
先導入文件與 SOP：
- README
- runbooks
- architecture docs
- checklist
- shared gate docs

### Phase B — Ops Event Intelligence
導入摘要化事件：
- alert summary
- incident summary
- gate result summary
- dry-run summary

### Phase C — DB Operational Intelligence
導入 DB 專屬知識與證據：
- backup verification summary
- migration validation summary
- monitoring health evidence
- remediation outcome summary

### Phase D — AI-assisted Decisioning
將 recommendation 接回 control plane，但維持：
- human-in-the-loop
- no auto-apply to production
- policy-driven execution boundary

## Suggested Integration Points

### With `06-DevTools`
- control-plane UI 顯示 AI recommendation
- reporting 模組輸出可被 ingestion 的 summary
- shared gates 提供標準 decision vocabulary

### With `08-Database/DB-Automation`
- backup-recovery 提供 restore evidence summary
- migration 提供 precheck / postcheck / rollback knowledge
- monitoring 提供 alert rule docs 與 health summaries
- ansible / remediation 提供 consistency / outcome summaries

## Validation Criteria

- 架構文件可明確區分 data, retrieval, analysis, governance 四層
- 能明確說明哪些資料禁止導入
- 存在 dataset / source / metadata example config
- 可支持後續 PoC 接入 embedding model 與 vector store
