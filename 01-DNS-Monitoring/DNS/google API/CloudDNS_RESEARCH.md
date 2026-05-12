# Cloud DNS 研究與 Python 串接策略

## 1. Cloud DNS 限制、配額與實務注意事項

| 類別 | 預設限制（2025-11 官方文件） | 補充說明 |
| --- | --- | --- |
| Managed zones | 每專案 10,000（公有+私有總和，可申請提高） | `gcloud dns managed-zones list` 可檢查現況 |
| Private zone 連接 VPC | 每 zone 最多 5,000 VPC 網路 | 實務上建議用專用共享 VPC 精簡授權 |
| Resource record sets | 每 zone 100,000 個 RRset | 同一名稱/類型/資料視為單一 RRset |
| 單次變更 (changes.create) | 新增+刪除共 1,000 RRset 或 1 MB JSON（擇一） | 超過需批次拆分；API 速率預設 120 req/min/project |
| 支援記錄類型 | A, AAAA, CAA, CNAME, MX, NAPTR, NS, PTR, SOA, SPF, SRV, TXT | DNSKEY、DS 需啟用 DNSSEC |
| TTL | 1 秒 ～ 2,147,483,647 秒 | TTL < 30 秒在 GFE 上可能被提升為 30 秒 |

- **傳播延遲**：Google edge 60 秒內通常可見，但全球 DNS 快取依 TTL 仍有延遲；計畫變更時需預留時間。
- **權限與 API**：需啟用 `dns.googleapis.com`，常用 IAM 角色：`roles/dns.admin`（完全管理）、`roles/dns.reader`、`roles/dns.editor`。自動化建議使用獨立 Service Account + 最小權限。
- **變更一致性**：`changes.create` 採最終一致性；對同一 RRset 同時送出多筆會以最後成功的操作為準。建議在送出後用 `changes.get` 或 `managedZones.operations` 輪詢狀態。
- **衝突/錯誤**：若嘗試刪除不存在的 RRset 或新增重複項目，API 會回傳 `HTTP 412/409`。應以「先讀（list/lookup）→ 計算差異 → 送出變更」方式確保冪等。
- **DNSSEC**：啟用後 RRset 更新需額外考量 key rollover，`dns.managedZoneOperations` 也會增加延遲。
- **計費**：依每月 Managed zone 數量與查詢次數計費；zone 類型（公有/私有）價格不同。大量記錄更新須評估 `changes.create` API 速率與對應費用。
- **監控**：可透過 Cloud Monitoring 指標 `dns.googleapis.com/changes_count`, `.../responses_count` 追蹤用量；建議設定 quota 逼近告警。

### 認證與環境建議
1. 建立專用 Service Account，指派 `roles/dns.admin` 或以 IAM Conditions 限縮專案/zone。
2. 將金鑰放入 Secret Manager 或 CI/CD Provider，執行時透過 Workload Identity Federation 或 OIDC 取用，避免裸露 JSON 金鑰。
3. 在本機/開發環境使用 Application Default Credentials (`gcloud auth application-default login`) 減少金鑰散布。

### 常見實務風險
- 大量更新時容易碰到 quota，須實作節流與指數退避。
- Private zone 掛載多 VPC 時，誤刪 zone 會導致跨環境解析中斷；建議在自動化前加上「最少一層人工審核」或 `--dry-run` 模式。
- 變更 SOA/NS 記錄需小心：Cloud DNS 會自動管理 zone apex 的 SOA/NS，手動覆寫會被拒絕。

## 2. Python 串接策略

### 套件選擇
- **首選**：`google-api-python-client` + Discovery Document `dns:v1`，支援全部 API surface（含 changes、policies）。
- **替代**：`google-cloud-dns`（Community wrapper）功能較基本，若需政策與授權網路等高階功能，建議直接使用 REST/HTTP via `googleapiclient.discovery.build`.
- 用 `google-auth`（Service Account、ADC、Workload Identity）取得 Credentials；配合 `google.auth.transport.requests.AuthorizedSession` 以便重試與逾時控制。

### 流程設計
1. **初始化**
   - 載入專案 ID、預設地區、Zone 命名規則。
   - 建立共用 `DnsClient`（包裝 `discovery.build("dns","v1")`）。
2. **Zone 管理**
   - `ensure_managed_zone(zone_name, dns_name, visibility, labels)`：若不存在則建立；存在則比對設定並回報差異。
3. **記錄更新**
   - `calculate_rrset_diff(desired_rrsets, current_rrsets)`：產出 additions/deletions。
   - `upsert_record_set(zone_name, rrset)`：單筆更新；批次則使用 `bulk_apply_changes(zone, additions, deletions)`。
4. **提交與輪詢**
   - `submit_change(zone_name, additions, deletions)` → 回傳 change id。
   - `wait_change(zone_name, change_id, timeout=120)`：每 5 秒查詢一次直到 `status=done` 或逾時。
5. **錯誤處理**
   - 封裝 `googleapiclient.errors.HttpError`，對 429/5xx 進行指數退避（初始 1s，最大 32s）。
   - 對 412（precondition failed）自動重新讀取狀態後重試一次。

### 示意程式

```python
from google.oauth2 import service_account
from googleapiclient import discovery

SCOPES = ["https://www.googleapis.com/auth/ndev.clouddns.readwrite"]

def build_dns_client(credential_path: str):
    creds = service_account.Credentials.from_service_account_file(
        credential_path, scopes=SCOPES
    )
    return discovery.build("dns", "v1", credentials=creds, cache_discovery=False)

def create_managed_zone(dns, project, zone_body):
    request = dns.managedZones().insert(project=project, body=zone_body)
    return request.execute()

def upsert_rrset(dns, project, zone, additions=None, deletions=None):
    body = {"additions": additions or [], "deletions": deletions or []}
    request = dns.changes().create(project=project, managedZone=zone, body=body)
    change = request.execute()
    while change["status"] != "done":
        change = dns.changes().get(
            project=project, managedZone=zone, changeId=change["id"]
        ).execute()
    return change
```

> 實務上應包裝上述函式，加入輸入驗證、差異運算與重試控制，並在 CI/CD 中以 staging 專案進行整合測試。

### 測試與驗證
- 單元測試：可用 `httpretty` 或 `responses` 模擬 Cloud DNS REST API，驗證 JSON payload。
- 整合測試：指向專用測試專案 + 自動建立/銷毀 `example.test.` zone，確保無殘留。
- 監控：在程式中發佈 `change_latency_seconds` 指標到 Cloud Monitoring，搭配 quota 告警。

## 3. 下一步建議
1. 依據以上策略撰寫實際 `dns_client.py`，實作 `DnsManager` 類別與 CLI（如 `python dns_client.py apply --zone foo --file records.yaml`）。
2. 建立 `records.example.yaml` 範本，描述欲同步的 RRset（name/type/ttl/data），並撰寫差異計算邏輯。
3. 製作 GitHub Actions / Cloud Build workflow：部署前先在 staging 專案 dry-run，通過後才對 production zone 套用。
4. 撰寫操作文件：包含 IAM 權限需求、如何擴充 quota，以及 incident runbook（rollback 流程、變更監看）。

