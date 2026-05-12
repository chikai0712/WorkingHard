# BCP-01: DNS 提供商服務中斷

## 📋 異常發現

### 用戶端現象
- **網站完全無法連線**：瀏覽器顯示「無法連線到此網站」或「DNS_PROBE_FINISHED_NXDOMAIN」
- **部分地區無法訪問**：特定區域用戶回報連線失敗，其他地區正常
- **連線超時**：網站載入時間過長，最終顯示連線逾時錯誤
- **間歇性連線失敗**：時好時壞，DNS 查詢成功率下降
- **手機 App 無法連線**：行動應用無法解析 API 端點

### 觸發情境
主要 DNS 提供商（如 Cloudflare、Google Cloud DNS、AWS Route53）發生大規模服務中斷，導致 DNS 解析完全失敗或嚴重延遲。

## 🔍 偵測與驗證流程

#### 監控服務檢查
- **監控服務**：外部監控回報 DNS 查詢失敗 | @BCP-DNS-Alert
- **告警條件**：
  - DNS 解析失敗率 >50% 持續 2 分鐘
  - 多個監控點同時回報異常
  - 解析延遲 >5 秒持續 1 分鐘
- **驗證告警有效性**：
  # 檢查監控服務本身是否正常
  curl -I https://monitoring-service.com/health
  # 檢查網站服務本身是否正常
  curl -I https://subdomain.example.com
  # 確認告警不是誤報
  # 測試主要 DNS 提供商
dig @1.1.1.1 example.com +short +timeout=3
dig @8.8.8.8 example.com +short +timeout=3
dig @208.67.222.222 example.com +short +timeout=3  

# 測試 DNS 伺服器（cloudflare）
dig @ns1.cloudflare.com example.com +short +timeout=3
dig @ns2.cloudflare.com example.com +short +timeout=3

# 檢查回應時間
dig @1.1.1.1 example.com +stats
```

**判斷標準**：
- ⚠️ **異常**：主要 DNS 提供商（Cloudflare）無回應或超時，google 與其他DNS 作業正常

## 👥 應變組織

| 角色 | 職責 | 聯絡方式 |
|------|------|----------|
| **事件指揮官(HOST)** | 統籌決策、對外溝通 | Slack |
| **IDC 工程師** | 確認異常狀況 | 通知Host是否啟用備援機制 |
| **產品TC** | 協助備用域名切換 | @BCP-DNS-team |
| **產品AM** | 客戶溝通、公告發布 | @BCP-Custom-team |

## 🚨 應變流程

### 階段一：確認與通報（0-5 分鐘）

1. **快速驗證異常**（參考上方「🔍 偵測與驗證流程」）
   - 確認符合「確認為 DNS 提供商服務中斷的條件」
   - 通知HOST目前狀況及判斷
   
   ```bash
   # 快速驗證命令
   dig @1.1.1.1 example.com +short +timeout=3
   dig @8.8.8.8 example.com +short +timeout=3
   dig +trace example.com
   curl -s https://www.cloudflarestatus.com/api/v2/status.json | jq '.status.indicator' (確認CF服務狀況，"none"、"minor"皆是正常)
   ```

2. **啟動事件通報**
   - 在 Slack `#bcp-infra-alert` 發布緊急通知
   - 觸發 BCP 通報流程告警（TP0 級別）
   - 電話通知事件指揮官、產品AM、產品TC、IDC 工程師
   - 記錄異常開始時間和初步影響範圍
   - 預估修復時間（公告用，通常 15-30 分鐘）

3. **對外公告（5 分鐘內）**
   - 更新 BCP 狀態頁：
   - 發布 BCP 公告（TG）
   - 使用「狀態頁更新模板」

### 階段二：切換備援 DNS&CDN（5-15 分鐘）

1. **啟用備援方案**
   - 切換至次要 DNS&CDN 提供商（如 Cloudflare → Route53）

2. **驗證切換結果**                           
   # 使用多個 DNS 伺服器驗證備用域名是否生效
   dig @ns-123.awsdns-12.com example.com
   dig @8.8.8.8 example.com +trace
   
   # 使用線上工具檢查全球解析
   # https://dnschecker.org
  
   確認網站是否已經經過備援CDN

### 階段三：監控主要DNS 是否恢復

### 階段四：通知產品AM 主要DNS已經恢復，安排切換時間

### 階段五：BCP 結束通報

### 階段六：Retro


**最後更新**：2026-11-25  
**審核者**：IDC Team Lead  
**版本**：1.0

