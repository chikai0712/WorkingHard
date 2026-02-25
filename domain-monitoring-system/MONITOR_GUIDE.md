# 🌐 DNS 監控器使用指南

## 📋 功能說明

DNS 監控器頁面可以：
- ✅ 顯示所有 DNS 伺服器列表
- ✅ 按國家/地區分類查看
- ✅ 顯示 DNS 健康狀態
- ✅ 顯示回應時間
- ✅ 按 ISP 分組顯示
- ✅ 實時統計數據

---

## 🚀 快速開始

### 步驟 1：導入越南和印尼 DNS

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

🎉 導入完成！
```

### 步驟 2：重啟 API 服務

```bash
docker-compose restart api
```

### 步驟 3：訪問 Monitor 頁面

打開瀏覽器訪問：
```
http://localhost:8000/monitor.html
```

---

## 📊 已導入的 DNS 列表

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

## 🎨 Monitor 頁面功能

### 1. 統計卡片

顯示：
- 總 DNS 數量
- 健康 DNS 數量
- 國家覆蓋數
- ISP 數量

### 2. 國家標籤

點擊不同國家標籤可以過濾顯示：
- 🌍 全部
- 🇻🇳 越南
- 🇮🇩 印尼

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

## 🔧 手動導入（如果腳本失敗）

### 方法 1：直接執行 SQL

```bash
# 複製文件到容器
docker cp dns_vietnam_indonesia.sql $(docker-compose ps -q db):/tmp/

# 執行導入
docker-compose exec db psql -U postgres -d domain_monitoring -f /tmp/dns_vietnam_indonesia.sql
```

### 方法 2：從外部執行

```bash
docker-compose exec -T db psql -U postgres -d domain_monitoring < dns_vietnam_indonesia.sql
```

---

## ✅ 驗證導入

### 查看導入的 DNS 數量

```bash
docker-compose exec db psql -U postgres -d domain_monitoring -c "
SELECT country_code, COUNT(*) as count 
FROM nameservers 
WHERE country_code IN ('VN', 'ID') 
GROUP BY country_code;
"
```

### 查看詳細列表

```bash
docker-compose exec db psql -U postgres -d domain_monitoring -c "
SELECT dns_server, isp, region, country_code 
FROM nameservers 
WHERE country_code IN ('VN', 'ID') 
ORDER BY country_code, isp;
"
```

---

## 🎯 使用場景

### 場景 1：檢測域名在越南的可訪問性

1. 訪問 Monitor 頁面
2. 點擊 🇻🇳 越南 標籤
3. 查看所有越南 DNS 伺服器
4. 使用這些 DNS 檢測域名

### 場景 2：檢測域名在印尼的可訪問性

1. 訪問 Monitor 頁面
2. 點擊 🇮🇩 印尼 標籤
3. 查看所有印尼 DNS 伺服器
4. 使用這些 DNS 檢測域名

### 場景 3：比對不同 ISP 的解析結果

1. 查看同一國家不同 ISP 的 DNS
2. 比較解析結果
3. 識別特定 ISP 的封鎖

---

## 📈 後續擴展

### 增加更多國家

編輯 `dns_vietnam_indonesia.sql`，添加其他國家的 DNS：

```sql
-- 泰國 DNS
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('203.113.131.1', 'regional', 'TOT', 'Bangkok', 'TH', true);

-- 菲律賓 DNS
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('202.90.128.6', 'regional', 'PLDT', 'Manila', 'PH', true);
```

### 自動健康檢查

系統會自動檢查 DNS 健康狀態（每小時一次），Monitor 頁面會顯示最新狀態。

---

## 🐛 故障排除

### 問題 1：Monitor 頁面顯示空白

**解決方法**：
```bash
# 檢查 API 是否正常
curl http://localhost:8000/api/nameservers

# 重啟 API
docker-compose restart api
```

### 問題 2：DNS 數量為 0

**解決方法**：
```bash
# 檢查資料庫
docker-compose exec db psql -U postgres -d domain_monitoring -c "SELECT COUNT(*) FROM nameservers;"

# 重新導入
./import_dns_quick.sh
```

### 問題 3：統計數據不正確

**解決方法**：
```bash
# 檢查資料庫欄位
docker-compose exec db psql -U postgres -d domain_monitoring -c "\d nameservers"

# 確認欄位存在：dns_type, isp, region, country_code
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
```

### 按類型過濾

```bash
curl http://localhost:8000/api/nameservers?dns_type=regional
```

### 獲取統計數據

```bash
curl http://localhost:8000/api/nameservers/stats
```

---

## 🎉 完成！

現在你可以：
1. ✅ 查看越南和印尼的 DNS 列表
2. ✅ 監控 DNS 健康狀態
3. ✅ 使用這些 DNS 檢測域名
4. ✅ 分析不同 ISP 的解析結果

訪問 Monitor 頁面開始使用：
**http://localhost:8000/monitor.html**

