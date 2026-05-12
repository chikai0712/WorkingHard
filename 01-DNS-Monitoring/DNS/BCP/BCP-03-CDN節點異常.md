# BCP-03: CDN 節點異常導致全球服務延遲/失效

## 📋 異常發現

### 用戶端現象
CDN 提供商（Cloudflare / Mlytics / CDNetwork） 出現節點異常或回源鏈路故障，導致：
- 靜態資源載入失敗或大量 5xx
- 動態 API 延遲變高

### 觸發情境
CDN 提供商（Cloudflare / Mlytics / CDNetwork） 出現節點異常或回源鏈路故障

## 🔍 偵測與驗證流程

#### 手動檢查
- `mtr edge.example.com` 比對路由是否繞遠
- 走 CDN（正常 DNS）
  ```bash
  curl -I https://example.com
  ```
- 強制打 origin（跳過 CDN）
  ```bash
  curl -I https://example.com --resolve example.com:443:ORIGIN_IP
  ```

## 👥 應變組織
| 角色 | 職責 | 聯絡方式 |
|------|------|----------|
| **事件指揮官(HOST)** | 決策優先順序、對外公告核准 | Slack |
| **IDC/網路工程師** | 檢查回源、切換 CDN | @BCP-Infra |
| **產品AM** | 評估業務影響、同步各產品線 | @BCP-AM |
| **產品TC** | 確認服務 | @BCP-Custom-team |

## 🚨 應變流程

### 階段一：確認與通報（0-5 分鐘）

1. **分辨 CDN/Origin 問題**
   - 比對 CDN 與直接回源的 latency/HTTP code
   - 查 CDN 狀態頁 / PagerDuty Edge 告警
2. **啟動通報**
   - Slack `#bcp-alert` @HOST @BCP-Infra
   - 觸發 P1（CDN-EDGE-FAIL）
   - Slack 通知 HOST 與 產品，確認公告
3. **公告**

### 階段二：緊急處理（5-30 分鐘）

1. **啟用備援CDN**

2. **驗證**
   ```bash
   curl -I https://example.com
   curl -I https://example.com --resolve example.com:443:ORIGIN_IP
   ```

### 階段三：監控與服務恢復（30-60 分鐘）

### 階段四：通知產品AM 並安排驗證

### 階段五：BCP 結束通報

1. **條件**
   - 所有驗證流程通過，Host 宣布 BCP 結束

### 階段六：Retro

---

**最後更新**：2026-11-25  
**審核者**：IDC Team Lead  
**版本**：1.0
