# Database Backup / Recovery Practical Skeleton

此目錄提供 backup / checksum / restore drill / retention policy 的模板層級骨架。

## Files
- `.env.example`: 本地驗證參數
- `verify_backup.sh`: 檢查入口
- `backup-metadata.example.json`: 備份中繼資料範本
- `retention-policy.example.yaml`: 保留策略範本
- `checklists/restore-drill-checklist.md`: 還原演練檢查清單

## Architecture Principles

### 備份驗證不等於備份存在
很多環境只確認檔案有產生，但真正的可靠性應包含：
- 備份檔可被識別
- metadata 完整
- checksum 或等價驗證存在
- 有 restore drill 證據

### Metadata、Policy、Checklist 分離
這裡刻意把：
- `backup-metadata` 視為事實紀錄
- `retention-policy` 視為治理規則
- `restore-drill-checklist` 視為操作驗證

這種拆法有助於將「備份是否存在」與「備份是否可信」區分開來。

### Restore drill 才是最終驗證
真正能證明備份可靠的，不是排程成功，而是能在隔離環境完成 restore 並驗證資料完整性。因此這個目錄把 restore drill 視為核心流程，而不是附屬文件。

## Suggested workflow
1. 產出或收集 backup metadata
2. 驗證檔案存在、大小、checksum、timestamp
3. 執行 restore drill checklist
4. 記錄 RTO / RPO / 驗證結果

## Sequence Flow
1. 備份排程產出 artifact 與 metadata
2. 驗證流程讀取 metadata 與 retention policy
3. 進行 checksum / 存在性 / 時間點檢查
4. 依排程或演練窗口執行 restore drill checklist
5. 產出驗證證據與後續改善項

## Decision Matrix
- 有備份但無 metadata / checksum：視為不可信
- metadata 完整但無 restore drill 證據：要求補演練
- restore drill 成功：可維持現行策略
- restore drill 失敗：進入改善與風險升級

## Apply Workflow
1. 收集 backup metadata
2. 比對 retention policy
3. 驗證 artifact 完整性
4. 執行 restore drill 或演練檢查
5. 產出 RTO/RPO 與改善報告

## Fallback Scenario
- 觸發條件：checksum 不符、檔案損毀、restore 失敗
- 處置：標記備份不可用、改測其他備份副本、升級事件並修正保留/驗證策略

## Guardrails
- 不碰正式 DB
- 不執行真實 restore
- 僅提供模板與流程對照
