# AI / RAG Skeleton

此目錄提供平台級 AI 分析與 RAG foundation 的最小 skeleton。

## Files

- `AI-RAG-ARCHITECTURE.md`: 平台級 AI / RAG 架構設計
- `rag-datasets.example.yaml`: dataset source catalog 範例
- `metadata-schema.example.json`: metadata schema 範例
- `ingest_documents.py`: 文件正規化 ingestion skeleton
- `sanitize_records.py`: 去敏感與最小遮罩 skeleton
- `validate_metadata.py`: metadata 完整性驗證 skeleton
- `emit_chunks.py`: chunk 輸出 skeleton
- `embed_records.py`: placeholder embedding skeleton
- `write_pgvector.py`: pgvector payload writer skeleton
- `write_faiss.py`: FAISS payload writer skeleton
- `run_local_rag_pipeline.py`: 本地 pipeline runner
- `query_local_rag.py`: 本地 retrieval query skeleton
- `score_retrieval.py`: retrieval evaluation scorer skeleton
- `query_pgvector_payload.py`: pgvector payload query skeleton
- `query_faiss_payload.py`: FAISS payload query skeleton
- `chunking-policy.example.yaml`: chunking policy 範例
- `evaluation-questions.example.json`: retrieval evaluation / gold set 範例

## Intended Use

第一版用途：
- 定義哪些文件與摘要資料可導入 RAG
- 定義 metadata 與索引策略
- 給未來 ingestion pipeline、embedding job、vector store 初始化使用

## Design Principles

### 1. 先標準化，再向量化
RAG 品質通常不是先輸在模型，而是先輸在資料。這個 skeleton 先把流程拆成：
- normalize
- sanitize
- validate
- chunk

這樣做的原因是讓每一階段都可以單獨檢查、重跑與審核，而不是把所有責任塞進單一 ingestion script。

### 2. 先摘要化，再導入事件
對維運 / DB 場景來說，raw logs、raw payload、raw query output 通常噪音高且敏感度高，因此這裡優先使用摘要化資料與 evidence summary，而不是直接把全量事件倒進向量庫。

### 3. metadata 是治理邊界
AI 能不能安全地檢索，不只取決於模型，也取決於 metadata 是否完整。`project`、`module`、`sensitivity`、`source_type` 是後續 access control、filter 與 traceability 的基礎。

### 4. chunking 與 retrieval 分離
chunking policy 用獨立 YAML 定義，而不是硬編碼在所有程式中，目的是讓後續可依文件類型、事件類型、語言內容做差異化調整。

## Guardrails

- 不直接導入 secrets、token、private keys
- 不直接導入 raw production DB dump
- 不直接導入未去敏感的 raw log 與 SQL 結果
- 所有新資料源應先做敏感度標記與 human review

## Suggested Flow

```text
ingest_documents.py
  -> sanitize_records.py
  -> validate_metadata.py
  -> emit_chunks.py
  -> embed_records.py
  -> write_pgvector.py / write_faiss.py
  -> validate_db_summary.py
  -> ingest_db_summaries.py
```

也可直接執行：

```text
run_local_rag_pipeline.py
```

本地檢索與評估可再執行：

```text
query_local_rag.py <query>
score_retrieval.py
query_pgvector_payload.py <query>
query_faiss_payload.py <query>
```

## Next Steps

1. 以 `run_local_rag_pipeline.py` 驗證整條本地 pipeline
2. 將 DB summary dataset 與 schema-aware event ingestors 串起來
3. 建立真正的 embedding adapter
4. 接入 control plane recommendation source / evidence tracing
