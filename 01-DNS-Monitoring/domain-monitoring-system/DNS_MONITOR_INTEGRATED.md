# 🌐 DNS 監控器整合指南

## ✅ 已完成的整合

DNS 監控器功能已經整合到主 Dashboard 頁面中，作為一個獨立的標籤頁。

---

## 📋 功能說明

### Dashboard 現在包含 4 個標籤頁：

1. **📊 總覽** - 域名監控總覽、即時測試、圖表
2. **🌐 DNS 監控器** - DNS 伺服器列表和狀態 ⭐ 新增
3. **🔔 告警列表** - 所有告警信息
4. **📝 監控事件** - 最近的監控事件

---

## 🚀 快速開始

### 步驟 1：導入 DNS 清單（可先 VN/ID，再擴充亞洲）

```bash
cd /Users/ckchiu/Desktop/Project/domain-monitoring-system

# 執行快速導入腳本
./import_dns_quick.sh
```

**預期輸出**：
```
🌐 開始導入越南和印尼 DNS 列表...
📋 複製 SQL 文件到資料庫容器...
⚙️  執行 SQL 導入...
✅ 驗證導入結果...

country_code | count
-------------|------
ID           | 10
VN           | 10

🎉 VN/ID 導入完成！
```

#### （建議）導入更多亞洲國家/地區 DNS（增量、不刪除 VN/ID）

```bash
chmod +x import_dns_asia_quick.sh
./import_dns_asia_quick.sh
```

### 步驟 2：重啟 API 服務

```bash
docker-compose restart api
```

### 步驟 3：訪問 Dashboard

打開瀏覽器訪問：
```
http://localhost:8000/
```

然後點擊 **🌐 DNS 監控器** 標籤。

---

## 🎨 DNS 監控器功能

### 1. 統計卡片

顯示：
- 總 DNS 數量
- 健康 DNS 數量
- 國家覆蓋數
- ISP 數量

### 2. 國家過濾器

點擊不同國家按鈕可以過濾顯示（依資料庫實際導入的國家為準）：
- 🌍 全部
- 🇻🇳 越南 (10)
- 🇮🇩 印尼 (10)
- 🇹🇼 台灣 (...)
- 🇭🇰 香港 (...)
- 🇯🇵 日本 (...)
- 🇰🇷 韓國 (...)
- 🇸🇬 新加坡 (...)
- 🇲🇾 馬來西亞 (...)
- 🇨🇳 中國 (...)

### 3. DNS 卡片

每個 DNS 卡片顯示：
- IP 地址
- 地區
- 類型（國際/中國 ISP/區域）
- 回應時間
- 健康狀態
- 最後檢查時間

### 4. ISP 分組

按 ISP 分組顯示，每組顯示：
- ISP 名稱
- 健康 DNS 數量 / 總數
- 該 ISP 的所有 DNS 伺服器

---

## 📊 已導入的 DNS 列表（示例）

### 🇻🇳 越南 DNS (10 個)

| ISP | DNS 伺服器 | 地區 |
|-----|-----------|------|
| **VNPT** | 203.162.4.191, 203.162.4.190 | Hanoi |
| **VNPT** | 203.113.131.1, 203.113.131.2 | Ho Chi Minh |
| **Viettel** | 203.113.131.1, 203.113.131.2 | Hanoi |
| **Viettel** | 123.30.128.15, 123.30.128.16 | Ho Chi Minh |
| **FPT** | 210.245.24.20, 210.245.24.21 | Hanoi |
| **VDC** | 14.225.5.5, 14.225.5.6 | Hanoi |

### 🇮🇩 印尼 DNS (10 個)

| ISP | DNS 伺服器 | 地區 |
|-----|-----------|------|
| **Telkom** | 202.134.0.155, 202.134.2.5 | Jakarta |
| **Telkom** | 203.130.193.74, 203.130.206.250 | Surabaya |
| **Indosat** | 202.155.0.15, 202.155.0.19 | Jakarta |
| **Indosat** | 202.155.46.66, 202.155.46.77 | Bandung |
| **XL Axiata** | 202.152.0.2, 202.152.2.2 | Jakarta |
| **Biznet** | 103.10.67.200, 103.10.67.201 | Jakarta |

---

## 🎯 使用場景

### 場景 1：查看所有 DNS 伺服器

1. 訪問 Dashboard：http://localhost:8000/
2. 點擊 **🌐 DNS 監控器** 標籤
3. 查看所有 DNS 伺服器列表

### 場景 2：查看特定國家/地區的 DNS

1. 進入 DNS 監控器標籤
2. 點擊任一國家按鈕（例如 🇹🇼 台灣 / 🇭🇰 香港 / 🇯🇵 日本 / 🇻🇳 越南 / 🇮🇩 印尼）
3. 查看該國家的所有 DNS 伺服器

### 場景 3：檢查 DNS 健康狀態

1. 進入 DNS 監控器標籤
2. 查看統計卡片中的健康 DNS 數量
3. 查看每個 DNS 卡片的狀態標記
   - ✓ 健康（綠色）
   - ✗ 異常（紅色）

### 場景 4：查看特定 ISP 的 DNS

1. 進入 DNS 監控器標籤
2. 滾動到對應的 ISP 區塊
3. 查看該 ISP 的所有 DNS 伺服器

---

## 🔧 手動導入（如果腳本失敗）

### 方法 1：直接執行 SQL

```bash
# 複製文件到容器
docker cp dns_vietnam_indonesia.sql dms-postgres:/tmp/

# 執行導入
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -f /tmp/dns_vietnam_indonesia.sql
```

### 方法 2：從外部執行

```bash
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring < dns_vietnam_indonesia.sql
```

---

## ✅ 驗證導入

### 查看導入的 DNS 數量

```bash
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -c "
SELECT country_code, COUNT(*) as count 
FROM nameservers 
WHERE country_code IN ('VN', 'ID', 'TW', 'HK', 'JP', 'KR', 'SG', 'MY', 'CN') 
GROUP BY country_code;
"
```

**輸出說明**：
- 如果你只導入 `dns_vietnam_indonesia.sql`，通常只會看到 `VN/ID` 的統計。
- 如果你另外導入 `dns_asia_isps_public.sql`（`./import_dns_asia_quick.sh`），就會多出 `TW/HK/JP/KR/SG/MY/CN` 等國家/地區。

### 查看詳細列表

```bash
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -c "
SELECT dns_server, isp, region, country_code 
FROM nameservers 
WHERE country_code IN ('VN', 'ID', 'TW', 'HK', 'JP', 'KR', 'SG', 'MY', 'CN') 
ORDER BY country_code, isp;
"
```

---

## 📈 後續擴展

### 增加更多國家

建議新增到 `dns_asia_isps_public.sql`（增量匯入檔），添加其他國家的 DNS：

```sql
-- 例：新增一筆公開 DNS（請確保該 IP 確實為公開 Resolver，且不與既有 dns_server 重複）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('203.0.113.10', 'regional', 'ExampleISP', 'ExampleISP', 'ExampleRegion', 'XX', true)
ON CONFLICT (dns_server) DO NOTHING;
```

然後重新執行導入腳本。

---

## 🐛 故障排除

### 問題 1：DNS 監控器標籤顯示空白

**解決方法**：
```bash
# 檢查 API 是否正常
curl http://localhost:8000/api/nameservers

# 檢查統計 API
curl http://localhost:8000/api/nameservers/stats

# 重啟 API
docker-compose restart api
```

### 問題 2：DNS 數量為 0

**解決方法**：
```bash
# 檢查資料庫
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -c "SELECT COUNT(*) FROM nameservers;"

# 重新導入
./import_dns_quick.sh
```

### 問題 3：統計數據不正確

**解決方法**：
```bash
# 檢查資料庫欄位
docker-compose exec -T postgres psql -U dms_user -d domain_monitoring -c "\d nameservers"

# 確認欄位存在：dns_type, isp, region, country_code
```

### 問題 4：標籤切換不工作

**解決方法**：
```bash
# 清除瀏覽器緩存
# 或強制刷新：Ctrl+Shift+R (Windows/Linux) 或 Cmd+Shift+R (Mac)

# 檢查瀏覽器控制台是否有 JavaScript 錯誤
```

---

## 📝 API 端點

### 獲取所有 DNS

```bash
curl http://localhost:8000/api/nameservers
```

### 按國家過濾

```bash
curl http://localhost:8000/api/nameservers?country_code=VN
curl http://localhost:8000/api/nameservers?country_code=ID
curl http://localhost:8000/api/nameservers?country_code=TW
curl http://localhost:8000/api/nameservers?country_code=HK
curl http://localhost:8000/api/nameservers?country_code=JP
curl http://localhost:8000/api/nameservers?country_code=KR
curl http://localhost:8000/api/nameservers?country_code=SG
curl http://localhost:8000/api/nameservers?country_code=MY
curl http://localhost:8000/api/nameservers?country_code=CN
```

### 按類型過濾

```bash
curl http://localhost:8000/api/nameservers?dns_type=regional
```

### 獲取統計數據

```bash
curl http://localhost:8000/api/nameservers/stats
```

**返回格式**：
```json
{
  "by_country": [
    {"country_code": "VN", "total": 10, "healthy": 10},
    {"country_code": "ID", "total": 10, "healthy": 10}
  ],
  "by_type": [
    {"dns_type": "regional", "total": 20, "healthy": 20}
  ],
  "by_isp": [
    {"isp": "VNPT", "country_code": "VN", "total": 4, "healthy": 4},
    ...
  ]
}
```

---

## 🎉 完成！

現在你可以：
1. ✅ 在 Dashboard 中查看 DNS 列表
2. ✅ 按國家過濾 DNS
3. ✅ 監控 DNS 健康狀態
4. ✅ 查看不同 ISP 的 DNS
5. ✅ 在一個頁面中管理所有功能

訪問 Dashboard 開始使用：
**http://localhost:8000/**

點擊 **🌐 DNS 監控器** 標籤查看 DNS 列表！

