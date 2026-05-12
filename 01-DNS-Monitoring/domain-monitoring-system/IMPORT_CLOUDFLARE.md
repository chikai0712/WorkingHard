# 從 Cloudflare DNS 備份匯入域名

## 步驟 1: 從 Google Sheets 匯出 CSV

1. 開啟你的 Google Sheets (CF DNS backup Plan)
2. 點選「檔案」→「下載」→「逗號分隔值 (.csv)」
3. 將檔案儲存為 `cloudflare_backup.csv`

## 步驟 2: 上傳 CSV 到伺服器

```bash
# 複製 CSV 到專案目錄
cp ~/Downloads/cloudflare_backup.csv /Users/ckchiu/Desktop/Project/domain-monitoring-system/
```

## 步驟 3: 匯入域名

```bash
cd /Users/ckchiu/Desktop/Project/domain-monitoring-system

# 執行匯入腳本
docker-compose exec api python import_cloudflare.py cloudflare_backup.csv
```

## 步驟 4: 自動解析並更新 IP (可選)

匯入後,所有域名的 IP 預設為 `0.0.0.0`,你可以:

### 選項 A: 自動解析當前 IP

```bash
# 自動查詢每個域名的當前 IP 並更新
docker-compose exec api python update_domain_ips.py
```

### 選項 B: 手動更新特定域名

```bash
# 使用 API 更新
curl -X PUT http://localhost:8000/api/domains/1 \
  -H "Content-Type: application/json" \
  -d '{
    "expected_ips": ["1.2.3.4", "5.6.7.8"]
  }'
```

## 步驟 5: 驗證匯入結果

```bash
# 查看已匯入的域名數量
curl http://localhost:8000/api/domains | jq 'length'

# 查看前 10 個域名
curl http://localhost:8000/api/domains?limit=10 | jq '.[].domain'

# 查看啟用的域名
curl http://localhost:8000/api/domains | jq '.[] | select(.is_active==true) | .domain'
```

## 注意事項

1. **狀態對應**:
   - `active` → 啟用監控
   - `pending` → 暫停監控

2. **預設 NS 記錄**:
   - 所有域名預設使用 Cloudflare NS: `ns1.cloudflare.com`, `ns2.cloudflare.com`
   - 如需修改,請使用 API 更新

3. **IP 白名單**:
   - 初始匯入時 IP 為 `0.0.0.0`
   - 建議執行 `update_domain_ips.py` 自動解析
   - 或手動更新重要域名的 IP

4. **關鍵字監控**:
   - 初始匯入時關鍵字為空
   - 可稍後針對重要域名設定關鍵字

## 範例輸出

```
開始匯入: cloudflare_backup.csv
==================================================
✅ 新增域名: 78wwin.com (狀態: active)
✅ 新增域名: 1bez.com (狀態: active)
✅ 新增域名: 789wwin.live (狀態: active)
⏸️ 新增域名: acemm.com (狀態: pending)
⚠️  域名已存在: example.com
...

==================================================
匯入完成!
  ✅ 成功新增: 150 個
  ⚠️  跳過重複: 5 個
  ❌ 錯誤: 0 個
==================================================

⚠️  重要提醒:
  1. 所有域名的 expected_ips 預設為 '0.0.0.0'
  2. 請使用 API 更新每個域名的正確 IP 白名單
  3. 可以使用以下命令查看已匯入的域名:
     curl http://localhost:8000/api/domains
```

## 故障排除

### 問題: CSV 格式錯誤

如果匯入失敗,檢查 CSV 檔案:

```bash
# 查看前幾行
head -5 cloudflare_backup.csv

# 確認編碼
file cloudflare_backup.csv
```

### 問題: 域名格式不正確

腳本會自動跳過無效域名,查看日誌中的警告訊息。

### 問題: 大量域名匯入很慢

這是正常的,系統會逐一處理每個域名以確保資料正確性。

