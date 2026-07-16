# RedSaaS 本地靶場操作說明

## 快速啟動

```bash
cd lab/docker
docker compose up -d
docker compose ps   # 確認所有服務正常
```

## 服務清單

| 服務 | URL | 帳密 |
|------|-----|------|
| crAPI（API 靶場） | http://localhost:8888 | 自行註冊 |
| crAPI MailHog（信箱） | http://localhost:8025 | 無需登入 |
| DVWA（網頁靶場） | http://localhost:8080 | admin / password |
| DefectDojo（漏洞管理） | http://localhost:8001 | admin / defectdojo |

## 跑第一次掃描

```bash
# 對 crAPI 跑所有博弈 templates
docker compose run --rm nuclei \
  -t /templates/gambling/ \
  -u http://crapi-web \
  -o /output/crapi-result.json \
  -json

# 對 DVWA 跑通用 templates
docker compose run --rm nuclei \
  -t /templates/generic/ \
  -u http://dvwa \
  -o /output/dvwa-result.json \
  -json
```

## 把掃描結果匯入 DefectDojo

```bash
# 取得 DefectDojo API Token（首次登入後從 Profile 頁面取得）
export DD_TOKEN="your-token-here"

# 匯入 Nuclei 結果
curl -X POST http://localhost:8001/api/v2/import-scan/ \
  -H "Authorization: Token $DD_TOKEN" \
  -F "scan_type=Nuclei Scan" \
  -F "file=@./scan-results/crapi-result.json" \
  -F "engagement=1" \
  -F "product_name=RedSaaS Lab Test"
```

## 驗證 Template 準確度

跑完掃描後，記錄以下資訊到 `knowledge-base/attack-patterns/` 對應文件：

```
Template 名稱：
測試目標：
True Positive（正確命中）：0 / N
False Positive（誤報）：0 / N
漏掉的漏洞（False Negative）：0 / N
調整建議：
```

## 停止環境

```bash
docker compose down          # 停止但保留資料
docker compose down -v       # 停止並清除所有資料（重置靶場）
```
