# Network Automation Skeleton

這裡放 firewall / security group / ACL / route rule 的 check-only skeleton。

第一版僅提供：
- desired state placeholder
- drift check 入口
- dry-run apply placeholder

## Practical Templates
- `policies/desired-rules.example.yaml`: desired state 範例
- `check_rules.sh`: drift / review 入口

## Architecture Principles

### Desired state 應先於命令列操作
網路規則最怕的是「臨場逐條改」，因為很難回顧與比對。這裡以 desired state 為核心，先描述預期規則，再用檢查邏輯比對現況。

### Check-only 是第一階段
網路變更風險高，特別是 ACL、route、firewall policy 可能直接影響服務可達性。因此第一版只做 drift check 與 dry-run placeholder，避免在設計未成熟前直接下變更。

### 規則模型化有助於稽核
把規則轉成結構化資料後，後續才能做版本控管、差異比對、審批與回滾。這也是 network-as-code 能真正落地的前提。

## Sequence Flow
1. 載入 desired rules
2. 從雲端或設備端收集 current state
3. 做結構化 diff
4. 輸出 review 結果與 drift 項目
5. 後續再由人工或變更流程決定是否 apply

## Decision Matrix
- drift 不影響服務：可排入一般變更窗口
- drift 涉及 ingress / db / admin access：需人工 review
- desired state 本身不完整：禁止 apply
- current state 無法完整取得：先補資料，不做變更

## Apply Workflow
1. 載入 desired state
2. 收集 current state
3. 產生 diff 報表
4. 經 review / approval 決定是否套用
5. 套用後再次比對確認 drift 消失

## Fallback Scenario
- 觸發條件：套用後流量中斷、ACL 誤封鎖、路由異常
- 處置：回復前版規則、驗證關鍵連線、保留變更與比對紀錄
