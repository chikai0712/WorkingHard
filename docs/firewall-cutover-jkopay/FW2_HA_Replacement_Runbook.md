# 街口支付 FW2（FortiGate HA）換機 Runbook（最小停機）

## 1. 目標與範圍
- 現況路徑：`External -> FW1 -> AP Switch -> FW2(HA) -> DB Switch/DB`
- 本次範圍：更換 `FW2`（舊 HA 叢集 -> 新 HA 叢集）
- 目標：最小停機、可快速回滾、交易不中斷或僅秒級抖動

## 2. 拓樸示意

### 2.1 目標拓樸（新 FW2 HA）
```text
External
  |
 FW1
  |
AP Switch
  |\
  | \__ to FW2-A (data)
  |____ to FW2-B (data)

FW2-A (Active) <----ha1/ha2----> FW2-B (Standby)
  |\
  | \__ to DB Switch (data)
  |____ to DB Switch (data)

DB Switch -> DB
```

### 2.2 連接原則（含原因）
- heartbeat 線：`FW2-A ha1 <-> FW2-B ha1`、`FW2-A ha2 <-> FW2-B ha2`（建議直連）
  - 原因：降低延遲與外部網路故障影響，避免 HA 誤判。
- 資料埠：A/B 都接 AP/DB switch
  - 原因：確保主備切換時資料路徑已就緒。
- switch host-facing 埠（接 FW）：`edge/portfast + bpdu guard`
  - 原因：link up 後立即 forwarding，避免 STP 等待；同時防止誤接交換器造成 loop。
- switch uplink（switch-to-switch）：**不要**設 edge/portfast
  - 原因：uplink 需要正常 STP 協商來防迴圈。

---

## 3. 名詞說明（Glossary）
- **HA（High Availability）**：高可用叢集，故障時由備機接手。
- **A-P（Active-Passive）**：單活單備模式，營運與排障最可預測。
- **heartbeat（hbdev）**：HA 成員之間存活/同步通道。
- **monitor interface**：業務埠健康檢查，異常可觸發 failover（不是 heartbeat）。
- **failover**：主備角色切換。
- **session pickup**：切換時盡量保留連線狀態，降低交易中斷。
- **override disable**：高優先節點恢復後不自動搶主，避免二次切換抖動。
- **RSTP/STP**：二層防迴圈機制。
- **portfast/edge**：讓終端埠 link up 立即 forwarding。
- **BPDU Guard**：edge 埠若收到 BPDU 立即保護性關閉。
- **SNAT**：改寫來源 IP（常影響 DB ACL 白名單）。
- **next-hop**：封包離開本設備後的下一站 IP。
- **connected route**：目的網段是本機直連介面，不需額外 next-hop。
- **smoke test（冒煙測試）**：快速驗證關鍵功能是否可用。

---

## 4. 重要觀念（避免切換踩雷）

### 4.1 `hbdev` vs `monitor`
- `hbdev`：HA 心跳通道（叢集互相存活檢查/同步）
- `monitor`：監控業務介面健康，異常可觸發 failover（不是 heartbeat）

### 4.2 `override disable`
- 意義：高優先節點恢復後**不自動搶主**，避免二次切換造成交易抖動。
- 原因：支付流量敏感，穩定優先於自動回切。

### 4.3 next-hop
- 若 FW 直連 DB 網段（connected route），通常不需要 next-hop。
- 若非直連網段，才需設定下一跳。
- 原因：避免路由誤走不同出口，導致 SNAT 改變或回程非對稱。

### 4.4 為何先小流量再全量
- 小流量可先驗證 policy/NAT/DB ACL 與交易鏈路，失敗可低成本回滾。
- 全量直接上線風險高，若有設定差異會放大影響面。

---

## 5. 建置步驟（A-P）

## Phase A：前置（T-7 ~ T-1）
1. 匯出舊 HA 設定與版本資訊
2. 新機升級到目標 FortiOS
3. 建立新 HA（獨立，不與舊 HA 混）
4. 完成介面對應表（舊 port -> 新 port）
5. 確認管理面（NTP/Syslog/SNMP）

> 為什麼：新舊型號/版本不同時，不能無腦整包搬遷，需先對齊基礎條件。

## Phase B：新 HA 建置（離線）
在兩台新機設定 HA（參數一致）：

```bash
config system ha
    set mode a-p
    set group-name "FW2-HA"
    set group-id 10
    set password <HA_PASSWORD>
    set hbdev "ha1" 100 "ha2" 50
    set session-pickup enable
    set session-pickup-connectionless enable
    set monitor "port3" "port4"
    set override disable
end
```

設定節點優先權（A 高、B 低）：

```bash
# FW2-A
config system ha
    set priority 200
end

# FW2-B
config system ha
    set priority 100
end
```

> 為什麼：先離線建置可把風險從正式環境移除，確保切換窗只做最少變更。

## Phase C：驗證叢集與路由/NAT

### C1. HA 狀態
```bash
get system ha status
diagnose sys ha status
```
檢查：2 節點、一主一備、in-sync、ha1/ha2 正常

### C2. 路由生效（實際出口）
```bash
get router info routing-table details <DB_IP>
get router info routing-table details <APP_IP>
```

### C3. NAT 命中（實際 SNAT）
```bash
diagnose sys session filter clear
diagnose sys session filter src <APP_IP>
diagnose sys session filter dst <DB_IP>
diagnose sys session list
```

必要時 flow debug：
```bash
diagnose debug reset
diagnose debug flow filter saddr <APP_IP>
diagnose debug flow filter daddr <DB_IP>
diagnose debug flow show function-name enable
diagnose debug flow trace start 20
diagnose debug enable
# 送測試流量
diagnose debug disable
diagnose debug reset
```

> 為什麼：Policy 看起來相同，不代表實際路由與 SNAT 一定相同，必須用 runtime 驗證。

## Phase D：APP -> DB 真實連線測試

### APP 主機
- Linux：`nc -vz <DB_IP> <DB_PORT>`
- Windows：`Test-NetConnection <DB_IP> -Port <DB_PORT>`

### DB 主機
```bash
sudo tcpdump -ni any host <APP_IP_or_SNAT_IP> and port <DB_PORT>
```

檢查：DB 看到的來源 IP 是否符合白名單。

> 為什麼：這是最直接驗證「交易鏈路是否真的可用」的方法。

---

## 6. 切換窗執行（正式）
1. 變更凍結、所有團隊待命（網路/DB/APP/監控）
2. 先小流量 smoke test（5~10 分鐘）
3. 正常後再放全量

> 為什麼：把影響分段，降低一次性全量切換風險。

---

## 7. Smoke Test（切換後 15 分鐘內）
1. HA 無 flap（Primary/Secondary 穩定）
2. App->DB 連線成功
3. 路由出口符合預期
4. SNAT 來源 IP 正確
5. 交易成功率達標、timeout/5xx 無異常升高
6. SNMP/Syslog/NTP 正常

---

## 8. 回滾條件（任一成立即回滾）
- 交易成功率持續低於門檻（例如 <97% 持續 5 分鐘）
- App->DB 大量失敗
- SNAT 與白名單不一致且短時間無法修復
- HA 持續 flap

> 為什麼：支付系統以交易成功與可用性為最高優先，先保服務再修問題。

---

## 9. 變更後收尾
1. 匯出新 HA 最終 config
2. 記錄切換時間與驗證證據
3. 高峰時段再做一次交易與 DB 指標複核

> 為什麼：確保離峰正常不代表高峰正常，需二次驗證。

---

## 10. 常見錯誤與對應症狀（現場排障速查）

### 10.1 SNAT 漂移（最常見）
- **症狀**：App 連 DB timeout、DB log 顯示來源 IP 不在白名單。
- **常見原因**：
  - 出口介面改變（同 policy 但 egress 不同）
  - 新機未綁定 ippool，退回使用介面 IP 做 SNAT
  - central-snat-map 順序/匹配條件與舊機不同
- **快速檢查**：
  - `get router info routing-table details <DB_IP>`
  - `show firewall policy` / `show firewall central-snat-map` / `show firewall ippool`
  - `diagnose sys session list` 或 `diagnose debug flow ...`
- **處置**：固定 SNAT（ippool）、校正路由出口、同步白名單來源 IP。

### 10.2 DB ACL 擋下連線
- **症狀**：TCP 建連失敗或 DB 報 `host not allowed` / `authentication failed`。
- **常見原因**：來源 IP（SNAT 後）與 DB 白名單不一致。
- **快速檢查**：
  - APP：`nc -vz <DB_IP> <DB_PORT>` / `Test-NetConnection ...`
  - DB：`tcpdump` 看來源 IP
  - DB 稽核/錯誤日誌
- **處置**：補白名單或修正 SNAT/路由，先恢復可用性再做最小範圍收斂。

### 10.3 HA flap（主備反覆切換）
- **症狀**：Primary/Secondary 反覆變動、交易偶發中斷。
- **常見原因**：
  - heartbeat 不穩（線材/路徑品質）
  - monitor 介面設定不當
  - `override enable` 導致恢復後搶主
- **快速檢查**：
  - `get system ha status`
  - `diagnose sys ha status`
- **處置**：
  - 檢查/更換 heartbeat 線並分離實體路徑
  - 關鍵業務埠才放入 monitor
  - 支付場景建議 `override disable`

### 10.4 STP/Portfast 誤設
- **症狀**：切換後短暫不通、或拓樸震盪。
- **常見原因**：
  - host-facing 埠未設 edge/portfast，link up 後等待 STP
  - uplink 誤設 edge/portfast，產生 loop 風險
  - 缺少 BPDU Guard，誤接交換器未被保護
- **快速檢查（Switch）**：
  - `show spanning-tree summary`
  - `show spanning-tree interface <port> detail`
- **處置**：
  - FW-facing 埠：edge/portfast + BPDU Guard
  - switch-to-switch uplink：正常 STP，勿設 edge

### 10.5 路由非對稱
- **症狀**：去程可達、回程丟包；應用端間歇 timeout。
- **常見原因**：新舊路由優先序/next-hop 差異，回程走不同路徑。
- **快速檢查**：
  - `get router info routing-table details <APP_IP>`
  - `get router info routing-table details <DB_IP>`
- **處置**：校正靜態路由/策略路由，確保回程對稱或符合 stateful 檢查要求。

### 10.6 管理面正常、業務面異常
- **症狀**：NTP/Syslog/SNMP 正常，但交易失敗。
- **說明**：管理面通不代表業務 policy/NAT/route 正確。
- **快速檢查**：
  - 先驗證 App->DB 交易鏈路與 SNAT
  - 再看管理面
- **處置**：以交易可用性指標（成功率、timeout、DB 連線）作為最終準則。

### 10.7 建議現場排障順序（30 秒決策）
1. 先看交易成功率是否持續異常
2. 查 HA 是否 flap
3. 查 App->DB 連線與 DB 端來源 IP
4. 查路由出口與 SNAT
5. 若未在短時間恢復，執行回滾

---

## 11. 故障 -> 指令 -> 判斷標準 -> 回復動作（On-call 快速表）

| 故障情境 | 優先檢查指令（在哪裡執行） | 判斷標準 | 回復動作 |
|---|---|---|---|
| App 無法連 DB（大量 timeout） | `nc -vz <DB_IP> <DB_PORT>`（APP）<br>`sudo tcpdump -ni any host <APP_IP_or_SNAT_IP> and port <DB_PORT>`（DB） | APP 連線失敗 + DB 看不到或來源 IP 錯誤 | 先確認 SNAT 與白名單；短時間無法修復即回滾 |
| SNAT 漂移疑慮 | `get router info routing-table details <DB_IP>`（FW）<br>`diagnose sys session list`（FW）<br>`diagnose debug flow ...`（FW） | 實際 egress 或 SNAT IP 與設計不一致 | 修正 route/ippool/central-snat-map；必要時回滾 |
| HA 主備反覆切換（flap） | `get system ha status`（FW）<br>`diagnose sys ha status`（FW） | 角色在短時間內多次變動 | 檢查 heartbeat 線路、monitor 介面；穩定前先降載或回滾 |
| 切換後短暫不通（疑似 STP） | `show spanning-tree summary`（Switch）<br>`show spanning-tree interface <port> detail`（Switch） | FW-facing 埠未 edge/portfast 或 uplink 誤設 edge | FW-facing 改 edge/portfast + BPDU Guard；uplink 恢復正常 STP |
| 管理面正常但交易失敗 | `show firewall policy`（FW）<br>`diagnose debug flow ...`（FW）<br>`nc -vz ...`（APP） | NTP/Syslog 正常但 policy/NAT/route 不通 | 以交易鏈路結果為準，優先修復業務路徑 |
| 路由非對稱 | `get router info routing-table details <APP_IP>`（FW）<br>`get router info routing-table details <DB_IP>`（FW） | 去回程路徑不同且 session 異常 | 校正靜態/策略路由，恢復對稱後重測 |

### 11.1 建議決策門檻（可放在變更會議）
- **立即回滾**：
  - 交易成功率持續低於門檻（例：<97% 持續 5 分鐘）
  - HA 持續 flap 無法在 3 分鐘內穩定
  - DB 來源 IP 與白名單不一致且短時間無法調整
- **可持續觀察**：
  - 單次短抖動，2~3 分鐘內恢復且 KPI 回到基準
  - 僅非關鍵服務告警，不影響交易主鏈路

---

## 12. 影響 AP 與 DB 的規劃重點（跨平台）

> 本章補充「不只 FW 本身」，而是切換時對 AP 與 DB 端的連動影響。建議納入變更會議分工（網路/系統/DBA/SRE）。

### 12.1 AP 側（來源端）共同檢查
- **來源網段與路由可達**：AP/APP 所在網段到 DB 網段的去回程一致。
- **SNAT 後來源一致性**：FW 切換前後，DB 看到的來源 IP 不變（或白名單同步更新）。
- **連線池與重試策略**：App 連 DB 的 timeout、retry、circuit breaker 不要過度敏感。
- **觀測與追溯**：保留 AP/APP 真實來源 IP 對應（FW log + DHCP/AP 控制器 + 時間同步）。

### 12.2 DB 側（目的端）共同檢查
- **ACL/白名單**：允許 FW SNAT IP（建議過渡期舊+新同時允許）。
- **必要埠**：僅開放必要 DB 埠與複寫/監控埠（最小權限）。
- **連線與性能**：切換後即看連線數、慢查詢、P95/P99 延遲、錯誤率。
- **審計與日誌**：確保可透過 FW session/log 反查真實來源。

---

### 12.3 依部署型態的影響點

#### A) DB 在實體機（Bare Metal）
- **網卡與交換器協商**：speed/duplex/MTU 一致，避免丟包與重傳。
- **Bonding/LACP 一致性**：主機 bonding 與 switch LACP 參數一致。
- **心跳網路隔離**（若 DB 叢集）：避免與業務流量共用造成誤判。
- **切換檢查**：
  - `ss -lntp | grep <DB_PORT>`（服務在 listen）
  - `tcpdump`（確認來源 IP 與封包連續）

**為什麼要做**：實體機問題多半直接反映在鏈路層與驅動層，會放大為 DB 連線抖動。

#### B) DB 在 VMware
- **Port Group / VLAN 對齊**：vSwitch/dvSwitch 與 FW policy 路徑一致。
- **vMotion/DRS 變更凍結**：切換窗避免同時遷移造成雙重變因。
- **Snapshot 控制**：避免長時間 snapshot 造成 I/O stun。
- **資源保留**：DB VM 設 CPU/Memory reservation，避免切換時資源爭用。
- **切換檢查**：
  - VM 內 `nc`/`Test-NetConnection`
  - vCenter 看 VM 網卡連線與事件告警

**為什麼要做**：虛擬化層會引入額外變數（遷移、資源爭用、虛擬交換器設定），需在切換窗排除。

#### C) DB 在 Kubernetes（StatefulSet）
- **Service 路徑確認**：ClusterIP/Headless 與外部 AP 流量路徑一致。
- **NetworkPolicy 對齊**：FW 放行不代表 K8s 內部 policy 放行，兩邊都要檢查。
- **Probe 門檻調整**：readiness/liveness 避免過敏，避免短抖動觸發重啟。
- **PDB/反親和性**：避免切換期間同時驅逐多個 DB Pod。
- **conntrack 觀察**：大規模重連時注意節點 conntrack 壓力。
- **切換檢查**：
  - `kubectl get pod -n <ns> -o wide`
  - `kubectl get endpoints -n <ns>`
  - `kubectl logs` 檢查連線錯誤

**為什麼要做**：K8s 有「網路策略 + 調度 + 健康檢查」三層行為，任何一層過敏都會放大切換影響。

---

### 12.4 建議分工（會議可直接使用）
- **網路組（FW/Switch）**：路由、NAT、HA、STP、Trunk/LACP
- **AP/應用組**：連線池、重試、timeout、交易冒煙
- **DBA/平台組**：ACL、服務健康、性能指標、慢查詢、複寫延遲
- **SRE/監控組**：NTP 同步、告警門檻、儀表板與回滾門檻

---

## 13. 三階段 AP 與 DB 檢查清單（可打勾）

> 建議欄位：`結果(Pass/Fail)`、`執行人`、`時間`、`證據連結`。  
> 先小流量、後全量；任一關鍵項失敗，停止下一階段。

### 13.1 切換前（Pre-Cutover）

#### AP / 應用側
- [ ] 已確認 AP/APP 到 DB 的目標清單（FQDN/IP/Port）完整。
- [ ] APP 連線池參數已檢查（timeout/retry/最大連線）避免過度敏感。
- [ ] 關鍵交易冒煙腳本可執行（登入/查詢/交易）。
- [ ] AP/APP 網段與 DB 網段路由可達性確認。
- [ ] 時間同步（NTP）正常，便於跨系統對時排障。

#### DB 側（共通）
- [ ] DB ACL 白名單已包含新舊 SNAT（建議過渡期同時允許）。
- [ ] 必要 DB 埠/複寫埠/監控埠確認。
- [ ] DB 服務健康（listen 正常、無異常錯誤累積）。
- [ ] 已準備即時觀測指標（連線數、慢查詢、P95/P99、錯誤率）。

#### DB 在實體機
- [ ] NIC speed/duplex/MTU 與 switch 一致。
- [ ] Bonding/LACP 設定與交換器一致。
- [ ] 若有 DB 心跳網路，已確認與業務網路隔離。

#### DB 在 VMware
- [ ] Port Group / VLAN / dvSwitch 設定核對完成。
- [ ] 切換窗已凍結 vMotion/DRS（避免雙重變因）。
- [ ] 無長時間 snapshot（避免 I/O stun）。
- [ ] DB VM 有 CPU/Memory reservation（若有規範）。

#### DB 在 Kubernetes
- [ ] Service（ClusterIP/Headless）與流量路徑已確認。
- [ ] NetworkPolicy 已對齊 FW 放行策略。
- [ ] PDB/反親和性策略正常，避免同時驅逐。
- [ ] readiness/liveness probe 門檻已評估，不過度敏感。

---

### 13.2 切換中（In-Cutover）

#### AP / 應用側
- [ ] 先執行小流量冒煙（非全量）。
- [ ] APP 到 DB TCP 測試成功（`nc` / `Test-NetConnection`）。
- [ ] 交易流程冒煙至少 3~5 筆成功。
- [ ] APP 端 timeout/5xx 未明顯上升。

#### DB 側（共通）
- [ ] DB 端抓包確認來源 IP 為預期 SNAT。
- [ ] DB 日誌無 ACL/認證拒絕異常激增。
- [ ] 連線數與錯誤率維持在可接受區間。

#### DB 在實體機
- [ ] 主機網卡無 error/drop 激增。
- [ ] DB 進程/埠 listen 持續正常。

#### DB 在 VMware
- [ ] vCenter 無網卡斷線/主機遷移異常事件。
- [ ] VM 內連線測試持續成功。

#### DB 在 Kubernetes
- [ ] Pod 狀態穩定（無大量重啟）。
- [ ] Endpoints 正常，服務端點完整。
- [ ] 無 conntrack 壓力異常告警。

---

### 13.3 切換後（Post-Cutover 15~60 分鐘）

#### AP / 應用側
- [ ] 小流量觀察通過後，已放行全量流量。
- [ ] 交易成功率恢復/維持基準值。
- [ ] 應用錯誤率（timeout/5xx）恢復正常。
- [ ] AP/APP 鏈路與路徑穩定，無間歇性中斷。

#### DB 側（共通）
- [ ] DB 連線數、慢查詢、P95/P99、錯誤率均正常。
- [ ] 若有複寫，延遲與狀態正常。
- [ ] DB 稽核可追溯（FW log 可反查真實來源）。

#### DB 在實體機
- [ ] NIC/Bonding 持續穩定，無重協商與丟包。

#### DB 在 VMware
- [ ] ESXi/VM 事件無異常，資源爭用未惡化。

#### DB 在 Kubernetes
- [ ] Pod/Service/Endpoints 持續健康。
- [ ] 無大量重試風暴或探針誤殺。

---

### 13.4 回滾觸發（任一成立）
- [ ] 交易成功率低於門檻（例：<97% 且持續 5 分鐘）。
- [ ] DB 來源 IP 不符白名單且短時間無法修復。
- [ ] HA 持續 flap 無法在 3 分鐘內穩定。
- [ ] AP/APP -> DB 大量連線失敗。

> 執行原則：先保交易可用性，再做根因修復。

---

## 14. SOP 升級版（最短停機導向）

> 目標：把「切換本身」與「快取/連線收斂」分開處理，將可見中斷壓到秒級。

### 14.1 切換前（T-60 ~ T-5）

#### A. 目標與解析一致性
- [ ] AP/APP -> DB 目標清單以 FQDN 為主，避免硬編碼 IP。
- [ ] 盤點並清除主機 `hosts` 覆寫（Linux: `/etc/hosts`、Windows hosts）。
- [ ] （K8s/Java）確認 DNS 快取 TTL 不會過長（避免抱住舊 IP）。

**為什麼**：切換後若仍解析舊位址，會出現「只有部分節點失敗」的隱性故障。

#### B. 連線池與重試風暴防護
- [ ] APP 連線池 timeout/retry/max-conn 已調整為切換友善值。
- [ ] 避免無上限重試；確認有 backoff。
- [ ] （K8s）檢查 liveness/readiness probe，避免切換瞬間誤殺 Pod。

**為什麼**：切換短抖動若遇到激進重試，容易放大成全站雪崩。

#### C. 路由與白名單
- [ ] 路由實際出口（runtime）與設計一致。
- [ ] SNAT 後來源 IP 已與 DB 白名單對齊（建議過渡期舊+新雙允許）。
- [ ] DB 必要埠、複寫埠、監控埠核對。

**為什麼**：Policy 一樣不代表實際 egress/SNAT 一樣。

#### D. 平台差異先排雷
- [ ] 實體機：NIC/Bonding/MTU/LACP 一致。
- [ ] VMware：PortGroup/VLAN 對齊，凍結 vMotion/DRS，避免 snapshot stun。
- [ ] K8s：NetworkPolicy 與 Egress 白名單、PDB、Endpoints 準備完成。

#### E. 對時與觀測
- [ ] FW/AP/DB/SIEM 全部 NTP 同步。
- [ ] 冒煙測試腳本自動化可執行（非人工點擊）。
- [ ] Dashboard 就緒：交易成功率、5xx、DB 連線、慢查詢、延遲。

---

### 14.2 切換中（T0 ~ T+10）

#### A. 先小流量，再全量
- [ ] 切換完成後先導入小流量（灰度）。
- [ ] 即刻執行冒煙測試（登入/查詢/交易至少 3~5 筆）。
- [ ] 核對 DB 端來源 IP（SNAT）是否正確。

#### B. 快取收斂加速
- [ ] 觀察 ARP/CAM 收斂是否完成（必要時依規範執行快取刷新）。
- [ ] 確認 STP 無額外等待（FW-facing 為 edge/portfast，uplink 正常 STP）。

#### C. 10 分鐘決策門檻
- [ ] 交易成功率達基準。
- [ ] timeout/5xx 無持續上升。
- [ ] DB 連線與錯誤率在可接受範圍。

**不達標**：停止放量，進入回滾判定。

---

### 14.3 切換後（T+10 ~ T+60）

#### A. 連線/快取清理策略（依平台）
- [ ] K8s：必要時針對受影響 deployment 分批 `rollout restart`（避免一次全重啟）。
- [ ] VMware/實體：必要時重啟應用服務清除殭屍連線（非優先，先觀測後執行）。
- [ ] 僅在指標異常時執行強制清理，避免製造第二次抖動。

#### B. 指標與日誌核對
- [ ] 5 分鐘窗口：交易成功率、5xx、DB active connections。
- [ ] Log 關鍵字監控：`SQLException`、`Connection refused`、`timeout`。
- [ ] FW log 可追溯真實來源（src/transip/sessionid）。

#### C. 完成條件（Go）
- [ ] 連續 30 分鐘穩定（含至少一次交易尖峰段）。
- [ ] 無重大告警、無 HA flap、無 ACL 拒絕激增。
- [ ] 允許下線舊 cluster。

---

### 14.4 回滾 SOP（最短路徑）
1. 停止放量（回到舊路徑/舊叢集）。
2. 保留現場證據（FW flow debug、DB log、監控截圖）。
3. 恢復交易後再做 RCA（避免邊救火邊改設定）。

**回滾觸發（任一成立）**：
- 交易成功率 <97% 持續 5 分鐘
- HA flap 持續 3 分鐘以上
- DB 白名單/SNAT 不一致且短時間無法修正
- AP/APP -> DB 連線失敗持續擴大

---

## 15. 權限與資安管控（Automation Governance）

> 適用於有使用 Jenkins/GitLab CI、Ansible、vCenter、HAProxy API 進行切換自動化的情境。目標是避免「腳本誤觸發」與「權限過大」造成事故擴散。

### 15.1 權責分離（RBAC + SoD）

#### A. Infra / SRE（定義權）
- 允許：撰寫與維護 Playbook/Pipeline、維運執行節點。
- 限制：不得直接在 Production 任意觸發切換。
- 控制：變更必須經 Merge Request + 審批後才能進入可執行流程。

#### B. AP Owner / 維運主管（審批與執行權）
- 允許：在 CI/CD 介面選擇已核准流程執行。
- 限制：不可修改 Pipeline 原始碼，不持有底層密碼。
- 控制：需雙人審批（4-eyes principle）後才能執行正式切換。

#### C. SecOps / NetOps（監控與中止權）
- 允許：查核審計軌跡、監控異常、強制中止作業。
- 控制：異常重啟/異常流量時可緊急停用 Pipeline 或網路路徑。

**為什麼要做**：把「寫腳本」與「按下執行」拆開，可顯著降低內部誤操作與帳號被盜後的破壞面。

---

### 15.2 Secrets 管理（禁止硬編碼）
- [ ] 不得在 Playbook/Pipeline/Repo 內硬寫帳密或 Token。
- [ ] 使用 Jenkins Credentials 或 GitLab CI Variables（遮罩輸出）。
- [ ] 企業級建議：導入 Vault/CyberArk，使用短時效動態憑證。
- [ ] 審計要求：所有密鑰存取都有可追蹤紀錄（誰、何時、用途）。

**為什麼要做**：避免憑證外流造成長期橫向滲透。

---

### 15.3 最小權限服務帳號（Least Privilege）

#### vCenter 服務帳號（範例：`svc_ansible_rebooter`）
- 允許：指定 AP Cluster 的 `Power On/Off/Reset`、讀取狀態。
- 禁止：刪除 VM、修改儲存、變更網路拓樸、接觸 DB VM。

#### HAProxy API Token
- 允許：切換後端 member 狀態（`READY/MAINT`）。
- 禁止：修改核心路由設定與全域配置。

**為什麼要做**：即使執行節點被入侵，也僅能做有限動作，無法擴大破壞。

---

### 15.4 網路微切分（Micro-segmentation）

建議拓樸：
```text
[使用者/AP Owner PC]
    | 443 (UI only)
[GitLab/Jenkins]
    | 22/443 (controlled)
[Runner/Ansible Bastion]
    |--> vCenter API:443
    |--> HAProxy API:<custom>
```

控制原則：
- [ ] 使用者端只可到 CI/CD Web UI。
- [ ] CI/CD 只可呼叫受控 Runner。
- [ ] Runner 僅可連必要 API 端點（vCenter/HAProxy），其餘全拒。
- [ ] Runner 不可直接連 DB 業務網段。

**為什麼要做**：把「大腦（Pipeline）」與「肌肉（執行節點）」隔離，降低單點失守造成全域失控。

---

### 15.5 審計與追溯（Audit Trail）
- [ ] 每次切換保留：工單號、審批人、執行人、執行時間、git commit SHA。
- [ ] 保留執行輸出（stdout/stderr）、關鍵命令結果與監控截圖。
- [ ] 保留回滾操作記錄與RCA結論。

**為什麼要做**：滿足稽核與事後鑑識，避免「做了但說不清」。

---

### 15.6 Break-Glass 緊急程序（最後保險）

觸發條件（範例）：
- CI/CD 系統故障（憑證過期、平台不可用）
- Pipeline 無法啟動且業務中斷風險高

程序要求：
1. 由主管雙簽核啟用 Break-Glass。
2. 從實體保險箱或 PAM 緊急群組領用臨時高權限帳號。
3. 以手動方式執行最小必要操作（如切換 HAProxy member、重啟指定 AP VM）。
4. 作業完成立即回收/旋轉密碼與 Token。
5. 補齊完整事後審計與RCA。

**為什麼要做**：避免過度依賴自動化導致「工具掛了就無法救災」。

---

### 15.7 權限管控檢查清單（可打勾）
- [ ] 已完成 RBAC 與 SoD 分離（定義權/執行權/中止權）。
- [ ] Production 切換需雙人審批。
- [ ] Secrets 未硬編碼，且使用受管平台。
- [ ] vCenter/HAProxy 服務帳號為最小權限。
- [ ] Runner 網段已微切分，僅開必要連線。
- [ ] 變更可追溯（工單、commit、日誌、截圖）。
- [ ] Break-Glass 已演練且可在規定時間內啟動。
