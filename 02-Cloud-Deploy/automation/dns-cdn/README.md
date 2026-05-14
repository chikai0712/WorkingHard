# DNS / CDN Automation Skeleton

這裡放 DNS health check、CDN signature 檢測、failover decision skeleton。

建議後續擴充：
- Cloudflare / Route53 / NS provider adapters
- health check quorum logic
- dry-run / apply 分離

## Practical Templates
- `failover-policy.example.yaml`: failover 門檻與審批策略
- `providers/cloudflare-record.example.yaml`: Cloudflare record 範例
- `providers/route53-record.example.yaml`: Route53 record 範例
- `failover_check.py`: decision support 入口

## Architecture Principles

### 入口層控制必須比應用層更保守
DNS 與 CDN 位於流量入口，一次錯誤可能影響全域。因此這一層預設只做 health check、signature detection 與 decision support，不直接把 apply 與判斷混在一起。

### Provider adapter 與 decision engine 分離
不同 DNS/CDN provider 的 API 差異很大，所以應把「如何讀寫 provider」與「何時該切換」分開。前者是 adapter，後者是 decision engine。這樣後續才能支援多供應商而不重寫整個流程。

### Quorum 比單點判斷安全
單一健康檢查可能因網路或探測器本身異常而誤判。較穩健的設計應使用多探測點、多條件或時間窗口來決定是否切換。

## Sequence Flow
1. 讀取 failover policy
2. 收集 DNS / CDN health signals
3. 判斷是否達到 quorum 與切換條件
4. 對應 provider adapter 產生建議變更
5. 先輸出 dry-run decision，再交由人工 approval 或後續 apply workflow

## Decision Matrix

| Condition | Decision | Rationale |
|---|---|---|
| 單點探測失敗但未達 quorum | 觀察，不切換 | 避免單點誤判 |
| 多點失敗且達 failover threshold | manual approval 或受控 failover | 已達切換條件，但仍需控制風險 |
| provider record 與 policy 不一致 | 先修正設定，再評估切換 | 基礎資料不一致時不能直接決策 |
| CDN signature 不明 | 保守處理，先人工確認 | 避免對未知入口結構誤切 |

## Apply Workflow
1. 載入 failover policy 與 provider record
2. 取得 health signals 與 signature
3. 產生 decision output
4. 經 approval 後由 provider adapter 實際更新 record
5. 切換後持續觀察恢復狀況

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| 維護 failover policy 與 provider records | Platform / Network Engineer | Service Owner | DNS Admin, SRE | Stakeholders |
| 核准 failover | Incident Commander / Network Owner | Service Owner | Platform, Security | Stakeholders |
| 執行 revert | On-call Engineer | Incident Commander | Network Engineer, SRE | Stakeholders |
- 觸發條件：切換後仍不健康、指向錯誤、provider API 回應異常
- 處置：回復 primary record、擴大觀察窗口、保留探測與切換證據
