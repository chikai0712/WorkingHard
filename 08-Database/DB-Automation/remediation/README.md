# Auto-remediation Skeleton

此目錄放 DB / service 常見維運修復流程 skeleton，例如：
- service health recheck
- exporter restart flow
- failover checklist
- incident evidence collection

## Design Principles

### Auto-remediation 應從 evidence 開始
自動修復最怕的是誤判。因此第一步應先收集健康訊號、事件上下文與最近變更，再決定是否自動處置。

### Remediation policy 與執行動作分離
何時該修復、可以修到哪裡、什麼情況要升級人工處理，應是獨立 policy，而不是直接寫死在腳本裡。這樣才能避免每改一條規則就要重寫執行邏輯。

### 可回放、可追蹤
好的 remediation 設計應保留證據、動作與結果，方便 postmortem、稽核與規則微調。
