# Multi-NS 驗證專案

## 📋 專案概述

本專案旨在驗證 GoDaddy 域名註冊商是否允許設定兩組 Name Server（NS），其中一組為 Cloudflare Free DNS，另一組為其他 DNS 服務提供商。

---

## 📁 文件結構

```
Multi-NS/
├── README.md                           # 本文件
├── GoDaddy_Cloudflare_Multi_NS_驗證方案.md  # 詳細驗證方案
├── DNS故障切換驗證方法.md                  # 故障切換驗證方法（新增）
├── 官方技術文件彙整.md                    # 官方技術文件資料
└── ...
```

---

## 🎯 驗證目標

1. **技術可行性**: 驗證 GoDaddy 是否允許設定混合的 Name Server
2. **功能完整性**: 驗證混合 Name Server 設定是否影響 Cloudflare 功能
3. **穩定性**: 驗證混合 Name Server 設定的穩定性和一致性
4. **性能**: 驗證混合 Name Server 設定的查詢性能和延遲

---

## ⚠️ 重要警告

根據 DNS 標準（RFC 1034/1035）和各大 DNS 提供商的官方文檔：

**不建議混合使用不同提供商的 Name Server**

原因：
1. DNS 記錄必須在所有 Name Server 之間保持完全一致
2. 不同提供商的 DNS 設定可能不同步，導致解析不一致
3. Cloudflare 要求完全接管域名的 DNS 管理權
4. 混合使用可能導致 Cloudflare 功能無法正常工作

**本驗證僅供技術研究使用，不建議在生產環境中採用混合 Name Server 設定。**

---

## 📚 快速開始

### 1. 閱讀驗證方案

詳細的驗證方案請參考：[GoDaddy_Cloudflare_Multi_NS_驗證方案.md](./GoDaddy_Cloudflare_Multi_NS_驗證方案.md)

### 2. 故障切換驗證（推薦）

**重要：** 在設定 Multi-NS 後，必須驗證故障切換功能是否正常。

三種驗證方法請參考：[DNS故障切換驗證方法.md](./DNS故障切換驗證方法.md)

**快速開始：**
1. 先執行「方法三：架構驗證」確保配置正確
2. 再執行「方法一：本機防火牆模擬」快速測試
3. 最後執行「方法二：子網域測試」驗證真實環境

### 3. 查看官方文件

官方技術文件彙整請參考：[官方技術文件彙整.md](./官方技術文件彙整.md)

### 4. 執行驗證

按照驗證方案中的步驟執行測試，並記錄結果。

---

## 🔍 驗證階段

### 階段一：技術可行性驗證
- 驗證 GoDaddy 是否允許設定混合 Name Server
- 驗證兩個 Name Server 是否能正常回應查詢

### 階段二：實際運行驗證
- DNS 記錄一致性測試
- DNS 記錄更新同步測試
- **故障切換測試**（詳見 [DNS故障切換驗證方法.md](./DNS故障切換驗證方法.md)）
- Cloudflare 服務功能驗證

### 階段三：性能與穩定性監控
- DNS 查詢成功率監控
- DNS 解析延遲監控
- 記錄一致性監控
- 故障恢復時間測試

---

## 📊 驗證標準

### 成功標準

1. ✅ GoDaddy 允許設定混合 Name Server
2. ✅ 兩個 Name Server 都能正常回應查詢
3. ✅ DNS 記錄在所有 Name Server 之間保持一致（100%）
4. ✅ DNS 記錄更新能夠正確同步
5. ✅ 故障切換功能正常
6. ✅ Cloudflare 功能不受影響
7. ✅ 查詢成功率 > 99.9%
8. ✅ 查詢延遲在可接受範圍內

### 失敗標準

1. ❌ GoDaddy 不允許設定混合 Name Server
2. ❌ DNS 查詢失敗或返回錯誤
3. ❌ DNS 記錄不一致（> 1%）
4. ❌ DNS 記錄更新無法同步
5. ❌ 故障切換失敗
6. ❌ Cloudflare 功能異常
7. ❌ 查詢成功率 < 99%
8. ❌ 查詢延遲過高（P95 > 500ms）

---

## 🛠️ 測試工具

### DNS 查詢工具

- **dig**: 標準 DNS 查詢工具
- **nslookup**: DNS 查詢工具
- **host**: DNS 查詢工具

### DNS 監控工具

- **DNS Checker**: https://www.whatsmydns.net/
- **MXToolbox**: https://mxtoolbox.com/DNSLookup.aspx
- **DNS Propagation Checker**: https://dnschecker.org/

### 自動化驗證腳本

- **verify-dns-config.sh**: DNS 架構配置自動驗證腳本
  ```bash
  ./verify-dns-config.sh yourdomain.com ns-11.awsdns-11.com ns-cloud-c1.googledomains.com
  ```

---

## 📝 測試記錄

測試記錄請使用驗證方案中提供的測試記錄模板，記錄所有測試結果和觀察到的現象。

---

## 🔄 後續行動

### 如果驗證成功

1. 謹慎評估風險
2. 建立監控機制
3. 建立應急預案

### 如果驗證失敗

1. 採用標準方案（使用單一 DNS 提供商）
2. 考慮替代方案

詳細建議請參考驗證方案文檔。

---

## 📞 相關資源

### 官方支援

- **GoDaddy 技術支援**: https://www.godaddy.com/zh/help/contact-us
- **Cloudflare 技術支援**: https://support.cloudflare.com/

### 技術文件

- **GoDaddy DNS 文件**: https://www.godaddy.com/help/categories/dns
- **Cloudflare DNS 文件**: https://developers.cloudflare.com/dns/

### 社區討論

- **Stack Overflow**: https://stackoverflow.com/questions/tagged/dns
- **Cloudflare Community**: https://community.cloudflare.com/

---

**最後更新**: 2025-12-29  
**專案版本**: v1.1

