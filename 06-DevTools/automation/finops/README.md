# FinOps Practical Skeleton

這裡放成本分析、閒置資源盤點、標籤稽核與預算告警的模板層級骨架。

## Files
- `.env.example`: 本地執行參數
- `idle_resource_report.py`: 報表入口
- `budget-thresholds.example.yaml`: 預算門檻範本
- `tag-audit-policy.example.yaml`: 標籤稽核範本
- `cost-dimensions.example.json`: 成本維度範本

## Architecture Principles

### 成本資料要先被結構化
FinOps 的難點不只是抓數字，而是讓成本能按 account、service、environment、owner、cost center 等維度切分。沒有維度模型，成本只會停留在總額，難以行動。

### 標籤治理是成本治理前提
若沒有一致的 tag policy，就無法把費用可靠地歸屬到團隊或服務。因此這個目錄把 tag audit policy 視為與 budget threshold 同等重要。

### 閒置資源盤點與預算門檻要分開
一個是找浪費來源，一個是做風險預警。兩者都屬於 FinOps，但不應混成單一判斷。這樣後續才能針對不同使用情境分別優化。

## Suggested workflow
1. 定義成本維度與標籤政策
2. 設定 budget thresholds
3. 盤點 idle / orphaned resources
4. 輸出 review report 給 FinOps / platform team

## Sequence Flow
1. 收集成本來源與資源清單
2. 依 cost dimensions 做聚合
3. 套用 tag audit policy 與 budget thresholds
4. 標記 idle / orphaned / missing-tag candidates
5. 產出 review report 與 follow-up 清單
