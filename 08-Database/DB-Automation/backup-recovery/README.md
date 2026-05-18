# Database Backup / Recovery Practical Skeleton

此目錄提供 backup / checksum / restore drill / retention policy 的模板層級骨架。

## Files
- `.env.example`: 本地驗證參數
- `.env.mysql.example`: MySQL 本地驗證參數範例
- `verify_backup.sh`: 檢查入口
- `backup-metadata.example.json`: 備份中繼資料範本
- `backup-metadata.mysql.example.json`: MySQL 備份中繼資料範本
- `retention-policy.example.yaml`: 保留策略範本
- `retention-policy.mysql.example.yaml`: MySQL 保留策略範本
- `checklists/restore-drill-checklist.md`: 還原演練檢查清單
- `checklists/restore-drill-checklist.mysql.md`: MySQL 還原演練檢查清單

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

另外，MSSQL 與 MySQL 的備份型態不完全相同，因此額外提供 MySQL 專屬 metadata / retention / restore drill 範本，避免把 logical dump、binlog chain 驗證與 `.bak` 類型流程混為一談。

### Restore drill 才是最終驗證
真正能證明備份可靠的，不是排程成功，而是能在隔離環境完成 restore 並驗證資料完整性。因此這個目錄把 restore drill 視為核心流程，而不是附屬文件。

## Shared Gate Mapping

backup / recovery 流程現在對齊 shared gate framework：
- source gate：backup metadata、checksum、時間戳與保留資訊完整性
- security gate：加密策略、例外治理、敏感資料保護與存取邊界
- health gate：restore drill、checksum verify、RTO/RPO 與 post-restore verification

共用模型可參考：
- `06-DevTools/automation/SHARED-GATE-FRAMEWORK.md`
- `06-DevTools/automation/source-gate.example.yaml`
- `06-DevTools/automation/security-gate.example.yaml`
- `06-DevTools/automation/health-gate.example.yaml`

## Suggested workflow
1. 產出或收集 backup metadata
2. 執行 source gate，驗證檔案存在、大小、checksum、timestamp
3. 執行 security gate，確認加密、保留與例外治理
4. 執行 health gate，完成 restore drill checklist
5. 記錄 RTO / RPO / 驗證結果

## Sequence Flow
1. 備份排程產出 artifact 與 metadata
2. source gate 讀取 metadata 與 retention policy
3. 進行 checksum / 存在性 / 時間點檢查
4. security gate 驗證加密與敏感資料保護條件
5. 依排程或演練窗口執行 restore drill 與 health gate
6. 產出驗證證據與後續改善項

## Decision Matrix
- source gate 不完整：視為不可信
- metadata 完整但無 restore drill 證據：要求補 health gate
- security gate 例外不完整：hold 或 block
- restore drill 成功：可維持現行策略
- restore drill 失敗：進入改善與風險升級

## Apply Workflow
1. 收集 backup metadata
2. 比對 retention policy
3. 執行 source gate 與 security gate
4. 執行 restore drill 或演練檢查
5. 執行 health gate 與 post-restore verification
6. 產出 RTO/RPO 與改善報告

## Fallback Scenario
- 觸發條件：checksum 不符、檔案損毀、restore 失敗
- 處置：標記備份不可用、改測其他備份副本、升級事件並修正保留/驗證策略

## Suggested Next Steps
1. `DB_ENGINE=mysql SUMMARY_OUT=... EVIDENCE_OUT=... ./verify_backup.sh`
2. `DB_ENGINE=mysql SUMMARY_OUT=... EVIDENCE_OUT=... ./migrate.sh precheck`
3. `DB_ENGINE=mysql SUMMARY_OUT=... EVIDENCE_OUT=... ./migrate.sh postcheck`
4. 再將輸出的 artifact 對接 `ingest_db_summaries.py` 或 producer 目錄掃描流程

## Guardrails
- 不碰正式 DB
- 不執行真實 restore
- 僅提供模板與流程對照
