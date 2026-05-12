# BCP-02: DNS 記錄被惡意修改/劫持

## 📋 異常發現

### 用戶端現象
- **網站被導向陌生頁面**：瀏覽器顯示未知品牌或釣魚頁

### 觸發情境
DNS 提供商 API 金鑰外洩、弱密碼被暴力破解或供應商帳號遭入侵，導致 A/CNAME/MX 等記錄被惡意改寫，流量遭劫持至攻擊者掌控的主機。亦可能在**特定 ISP/地區**遭到路由或快取污染，僅該 ISP 的遞迴 DNS 返回惡意 IP，造成「部分國家才劫持、公司內網正常」的錯覺。

## 🔍 偵測與驗證流程

#### 監控服務檢查
- **監控服務**：DNS 監控（@BCP-DNS-Alert）
- **驗證告警有效性**：
  ```bash
  dig @1.1.1.1 example.com +short +timeout=3
  dig @8.8.8.8 example.com +short +timeout=3
  ```
- **判斷標準**：
  - ⚠️ **異常**：公共與權威 DNS 同時返回未知 IP、Audit Log 有未授權存取
  - 🔴 **嚴重**：多筆記錄遭竄改

#### ISP 劫持劇本（domain DNS 記錄於單一 ISP 被劫持）
- **快速確認**：
  ```bash
  dig @168.95.1.1 example.com +short +ttlid   # ISP DNS（中華電信）
  dig @1.1.1.1 example.com +short +ttlid      # 公共 DNS
  mtr -T example.com                          # 觀察異常路由
  ```

## 👥 應變組織

| 角色 | 職責 | 聯絡方式 |
|------|------|----------|
| **事件指揮官(HOST)** | 決策、對外交付、核准公告 | Slack |
| **IDC 工程師** | 回滾記錄、驗證全球解析、封鎖惡意 IP | @BCP-infra-alert |
| **產品TC** | 驗證備援域名/服務、協助流量切換 | @BCP-DNS-team |
| **產品AM** | 客戶同步、公告撰寫與 FAQ | @BCP-Custom-team |

## 🚨 應變流程

### 階段一：確認與通報（0-5 分鐘）

1. **快速驗證異常**
   ```bash
   python dns_manager.py show --zone example.com --fields name,type,value,ttl
   dig @1.1.1.1 login.example.com +short +ttlid
   dig +trace example.com
   dig @168.95.1.1 login.example.com +short +ttlid   # 指定被回報的 ISP
   ```
   - 列出受影響記錄、TTL、實際返回值
   - ISP DNS 異常，啟動通報流程
2. **啟動事件通報**
   - Slack `#bcp-infra-alert` @HOST @SecOps @BCP-DNS-team
   - 觸發 TP1 告警（DNS-HIJACK）
   - Slack 通知事件指揮官(HOST)、產品AM、產品TC、IDC
   - 紀錄開始時間、受影響域名、預估影響面(哪些客戶)
3. **對外公告（5 分內）**
   - 狀態頁貼出「DNS 記錄異常，已緊急回滾」
   - TG 發送短訊，通知用戶留意釣魚風險

### 階段二：更換新域名（20-60 分鐘）
- 更換新域名

### 階段四：對外同步

### 階段五：BCP 結束通報
- 條件：回滾完成、監控 30 分鐘無異常、AM 簽核
- 狀態頁更新為「已恢復」，附上實際影響與補償措施

### 階段六：Retro
- 24h 內完成事後檢討：憑證/金鑰管理、審核流程
- 建議改善：兩段式核准、自動化 Record Hash Monitoring、API Key 最小權限


---

**最後更新**：2026-11-25  
**審核者**：IDC Team Lead  
**版本**：1.0
