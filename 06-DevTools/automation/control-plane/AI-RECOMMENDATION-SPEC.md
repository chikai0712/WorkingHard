# AI Recommendation API and UI Spec

## Overview

此文件定義 `control-plane` 在接入 AI recommendation 時的 API contract 與 UI 呈現原則。

第一版維持 recommendation only，不直接自動執行 deploy、migration、restore、failover 或 remediation action。

## API Endpoint

### `GET /api/recommendations`

查詢指定 module 的 AI recommendation。

#### Query Parameters
- `module_id`: required
- `context_type`: optional, e.g. `runbook-qa`, `alert-triage`, `change-risk`

#### Example Response

```json
{
  "module_id": "db-migration",
  "context_type": "change-risk",
  "summary": "Precheck summary suggests approval and storage review before migration window.",
  "possible_causes": [
    "Pending DBA approval",
    "Storage threshold close to warning level"
  ],
  "recommended_checks": [
    "Review precheck output",
    "Validate rollback artifact readiness",
    "Confirm backup verification status"
  ],
  "related_artifacts": [
    "08-Database/DB-Automation/migration/README.md",
    "08-Database/DB-Automation/migration/rollback-guidelines.md"
  ],
  "confidence": "medium",
  "recommended_policy": "hold",
  "human_approval_required": true,
  "generated_at": "2026-05-17T12:30:00Z"
}
```

## UI Model

### Recommendation Panel
每個 module detail view 建議增加：
- AI Summary
- Confidence badge
- Recommended policy badge
- Recommendation source badge
- Evidence count badge
- Related artifact count badge
- Possible causes list
- Recommended checks list
- Related artifacts list
- Top retrieval evidence list with score
- Human approval required flag

### Visual States
- `confidence = high`: green/blue
- `confidence = medium`: amber
- `confidence = low`: gray + 顯示 manual review required
- `recommended_policy = pass|hold|block|rollback|fallback`

## Interaction Rules

- recommendation 僅作為輔助資訊
- 若 `confidence = low`，預設顯示 manual review 提示
- 若 `recommended_policy = block|rollback`，需顯示 escalation 提醒
- UI 不可把 recommendation 視為已執行 action

## Interaction Notes
- 使用者切換 module 時，前端重新請求 `/api/recommendations`
- 使用者觸發 `/api/actions` 後，前端應再次請求 recommendation，以反映新的 summary / dry-run context
- recommendation panel 應能區分 `local-summary-artifacts`、`static-mock`、`frontend-fallback` 等來源
- 若後端可用，recommendation 應可帶回 top retrieval evidence 與 score，讓使用者理解建議背後的本地依據
- retrieval evidence 應盡可能附帶 `schema_file` 與 `artifact_source` metadata，提升 traceability
- recommendation 在 action 完成後，應優先以最近 action 相關 artifact 與 action scope 建立 scoped analysis，降低過舊 sample 的干擾
- action history 應保存 recommendation snapshot，至少包含 policy、source、evidence/artifact count、retrieval evidence、scoped artifact list、action scope 與 action manifest metadata
- action history 若需跨刷新保留，應有本地持久化 API 或 JSON data source，且支援 filter / sort / clear / compare / only-changed 基本管理能力
- action manifest 應成為 recommendation、history 與 artifact scope 的共享對齊來源，避免多處以不同欄位推測同一 action 上下文

## Backend Notes

後端可先以本地 JSON / mock adapter 回傳 recommendation，之後再接：
- RAG retrieval results
- summarization model
- policy post-processor
- approval workflow integration

## Local Recommendation Generation Principle

在尚未接真實 LLM 前，control-plane 應先能從本地 summary artifacts 生成 deterministic recommendation。這樣做的好處是：
- 先驗證 UI 與 recommendation contract
- 先驗證 summary schema 是否足夠支撐 decisioning
- 避免在治理邊界與資料品質尚未穩定前，過早依賴模型生成
- 可讓 mock / local / future-LLM 三種模式共用同一份輸出格式
