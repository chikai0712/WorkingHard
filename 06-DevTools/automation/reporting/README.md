# Reporting Practical Skeleton

這裡放 incident / metrics / dashboard / reporting 的模板層級骨架。

## Files
- `generate_summary.py`: 報表入口
- `incident-summary.example.json`: incident 摘要範本
- `metric-snapshot.example.json`: metrics snapshot 範本
- `dashboard-metadata.example.yaml`: dashboard metadata 範本
- `examples/weekly-ops-review.md`: 週報範本

## Architecture Principles

### Reporting 是把訊號轉成決策材料
報表不只是把 log 或 metrics 再印一次，而是將 incident、可用性、容量、告警量與 follow-up 收斂成可判讀的輸出。

### Incident、Metrics、Dashboard metadata 分離
- incident summary 描述事件與影響
- metric snapshot 描述量化狀態
- dashboard metadata 描述觀測面板與責任歸屬

這樣拆開有助於日後整合不同資料來源，而不需要重寫整份報表。

### 報表模板化有助於固定 review cadence
如果每次 incident review 或 weekly ops review 都從空白開始，品質會不穩。模板化能讓 review 形成固定節奏與固定輸出欄位。

## Sequence Flow
1. 收集 incident、metrics 與 dashboard context
2. 依模板正規化資料
3. 產出 summary / weekly review / follow-up items
4. 提供給 on-call、platform team 或管理層做決策
