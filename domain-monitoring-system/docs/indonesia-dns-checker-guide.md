# 印尼 ISP DNS 查詢工具使用指南

## 🚀 快速開始

### 1. 賦予執行權限
```bash
chmod +x check_indonesia_dns.sh
```

### 2. 查詢單個域名
```bash
./check_indonesia_dns.sh google.com
```

### 3. 批量查詢多個域名
```bash
./check_indonesia_dns.sh -f domains.txt
```

---

## 📋 功能特色

✅ **支援印尼前10大ISP** - 涵蓋 80%+ 市場份額
✅ **即時DNS解析檢測** - 3秒超時，快速響應
✅ **彩色輸出** - 清晰的視覺化結果
✅ **統計分析** - 成功率、IP一致性檢查
✅ **自動報告** - 生成 TXT 和 CSV 報告
✅ **批量檢測** - 支援域名列表文件

---

## 🌐 涵蓋的印尼 ISP

### 行動網路運營商
- **Telkomsel** (50% 市場份額) - 2個DNS
- **Indosat Ooredoo** (20% 市場份額) - 2個DNS
- **XL Axiata** (15% 市場份額) - 2個DNS

### 固網寬頻運營商
- **Telkom Indonesia (IndiHome)** - 2個DNS
- **Biznet** - 2個DNS
- **First Media** - 2個DNS
- **MyRepublic** - 2個DNS
- **CBN (Cyber)** - 2個DNS

**總計：16 個 DNS 伺服器**

---

## 💻 使用範例

### 範例 1：檢測單個域名

```bash
./check_indonesia_dns.sh example.com
```

**輸出範例：**
```
╔═══════════════════════════════════════════════════════════╗
║         印尼 ISP DNS 查詢工具                             ║
║         Indonesia Top 10 ISP DNS Checker                 ║
╚═══════════════════════════════════════════════════════════╝

檢測域名：example.com
使用印尼前10大ISP的DNS伺服器

狀態 | ISP 名稱           | DNS 伺服器      | 解析結果
-----|---------------------|-----------------|------------------
✓ Biznet-1           | 202.169.224.68  | 93.184.216.34
✓ Biznet-2           | 202.169.224.69  | 93.184.216.34

✓ CBN-1              | 202.158.3.6     | 93.184.216.34
✓ CBN-2              | 202.158.3.7     | 93.184.216.34

✓ First-Media-1      | 203.130.193.74  | 93.184.216.34
✓ First-Media-2      | 203.130.206.250 | 93.184.216.34

✓ Indosat-1          | 202.155.0.10    | 93.184.216.34
✓ Indosat-2          | 202.155.0.15    | 93.184.216.34

✓ MyRepublic-1       | 103.10.66.66    | 93.184.216.34
✓ MyRepublic-2       | 103.10.67.67    | 93.184.216.34

✓ Telkom-1           | 202.134.0.155   | 93.184.216.34
✓ Telkom-2           | 202.134.1.10    | 93.184.216.34

✓ Telkomsel-1        | 202.3.208.5     | 93.184.216.34
✓ Telkomsel-2        | 202.3.208.6     | 93.184.216.34

✓ XL-Axiata-1        | 202.152.0.2     | 93.184.216.34
✓ XL-Axiata-2        | 202.152.2.2     | 93.184.216.34

═══════════════════════════════════════════════════════════
統計結果

域名：example.com
總檢測數：16
成功：16 | 失敗：0 | 超時：0
成功率：100.0%

✓ 所有印尼ISP都能正常解析此域名

✓ 所有ISP解析結果一致
  IP: 93.184.216.34

✓ 報告已保存：indonesia_dns_report_example.com_20260302_143025.txt
```

---

### 範例 2：批量檢測多個域名

#### 步驟 1：創建域名列表文件

```bash
cat > domains.txt << EOF
google.com
facebook.com
youtube.com
twitter.com
instagram.com
EOF
```

#### 步驟 2：執行批量檢測

```bash
./check_indonesia_dns.sh -f domains.txt
```

**輸出範例：**
```
╔═══════════════════════════════════════════════════════════╗
║         印尼 ISP DNS 查詢工具                             ║
║         Indonesia Top 10 ISP DNS Checker                 ║
╚═══════════════════════════════════════════════════════════╝

批量檢測模式
讀取域名列表：domains.txt

檢測: google.com
  成功率: 100.0%

檢測: facebook.com
  成功率: 93.8%

檢測: youtube.com
  成功率: 100.0%

檢測: twitter.com
  成功率: 87.5%

檢測: instagram.com
  成功率: 100.0%

✓ 批量報告已保存：indonesia_dns_batch_report_20260302_143530.csv
```

#### 步驟 3：查看 CSV 報告

```bash
cat indonesia_dns_batch_report_*.csv
```

**CSV 內容：**
```csv
Domain,Total,Success,Failed,Timeout,Success_Rate
google.com,16,16,0,0,100.0%
facebook.com,16,15,1,0,93.8%
youtube.com,16,16,0,0,100.0%
twitter.com,16,14,0,2,87.5%
instagram.com,16,16,0,0,100.0%
```

---

## 📊 結果解讀

### 狀態符號

| 符號 | 意義 | 說明 |
|------|------|------|
| ✓ | 成功 | DNS 解析成功 |
| ✗ | 失敗 | DNS 解析失敗 |
| ⏱ | 超時 | DNS 查詢超時（3秒） |

### 成功率判斷

| 成功率 | 狀態 | 建議 |
|--------|------|------|
| 100% | ✓ 完美 | 所有ISP都能訪問 |
| 80-99% | ⚠ 良好 | 大部分ISP能訪問 |
| 50-79% | ⚠ 警告 | 約半數ISP能訪問 |
| < 50% | ✗ 嚴重 | 可能被封鎖或污染 |

### IP 一致性

- **所有ISP解析結果一致** ✓ - 正常情況
- **發現 2-3 個不同結果** ⚠ - 可能有CDN或負載均衡
- **發現多個不同結果** ✗ - 可能存在DNS劫持或污染

---

## 🔧 進階用法

### 1. 只檢測特定 ISP

編輯腳本，註釋掉不需要的 ISP：

```bash
declare -A INDONESIA_DNS=(
    # 只保留 Telkomsel
    ["Telkomsel-1"]="202.3.208.5"
    ["Telkomsel-2"]="202.3.208.6"
    
    # 註釋掉其他 ISP
    # ["Indosat-1"]="202.155.0.10"
    # ...
)
```

### 2. 增加超時時間

修改腳本中的 `timeout` 變數：

```bash
query_dns() {
    local timeout=5  # 改為 5 秒
    ...
}
```

### 3. 導出為 JSON

```bash
./check_indonesia_dns.sh google.com | tee result.txt
# 然後手動轉換或使用 jq 處理
```

---

## 🛠️ 故障排除

### 問題 1：找不到 dig 命令

**錯誤信息：**
```
✗ 找不到 dig 命令
```

**解決方法：**
```bash
# macOS
brew install bind

# Ubuntu/Debian
sudo apt-get install dnsutils

# CentOS/RHEL
sudo yum install bind-utils
```

### 問題 2：所有查詢都超時

**可能原因：**
1. 網路連接問題
2. 防火牆阻擋 DNS 查詢（UDP 53）
3. DNS 伺服器不可用

**解決方法：**
```bash
# 測試網路連接
ping 8.8.8.8

# 測試 DNS 查詢
dig @8.8.8.8 google.com

# 檢查防火牆
sudo iptables -L | grep 53
```

### 問題 3：權限被拒絕

**錯誤信息：**
```
Permission denied: ./check_indonesia_dns.sh
```

**解決方法：**
```bash
chmod +x check_indonesia_dns.sh
```

---

## 📈 整合到監控系統

### 1. 定時執行（Cron）

```bash
# 編輯 crontab
crontab -e

# 每小時檢測一次
0 * * * * /path/to/check_indonesia_dns.sh yourdomain.com >> /var/log/indonesia_dns.log 2>&1

# 每天早上 9 點批量檢測
0 9 * * * /path/to/check_indonesia_dns.sh -f /path/to/domains.txt
```

### 2. 整合到 Python 腳本

```python
import subprocess
import json

def check_indonesia_dns(domain):
    result = subprocess.run(
        ['./check_indonesia_dns.sh', domain],
        capture_output=True,
        text=True
    )
    return result.stdout

# 使用
output = check_indonesia_dns('example.com')
print(output)
```

### 3. 整合到現有監控系統

```bash
# 在 app/tasks.py 中添加
from celery import shared_task
import subprocess

@shared_task
def check_indonesia_isp_dns(domain):
    """使用印尼ISP DNS檢測域名"""
    result = subprocess.run(
        ['./check_indonesia_dns.sh', domain],
        capture_output=True,
        text=True,
        cwd='/path/to/domain-monitoring-system'
    )
    
    # 解析結果並保存到數據庫
    # ...
    
    return result.stdout
```

---

## 📝 輸出文件說明

### 單個域名報告（TXT）

**文件名格式：** `indonesia_dns_report_{domain}_{timestamp}.txt`

**內容範例：**
```
印尼 ISP DNS 查詢報告
=====================

域名: example.com
檢測時間: 2026-03-02 14:30:25

檢測結果：
----------
Telkomsel-1          | 202.3.208.5     | ✓ | 93.184.216.34
Telkomsel-2          | 202.3.208.6     | ✓ | 93.184.216.34
...

統計：
------
總檢測數: 16
成功: 16
失敗: 0
超時: 0
成功率: 100.0%
```

### 批量檢測報告（CSV）

**文件名格式：** `indonesia_dns_batch_report_{timestamp}.csv`

**可用於：**
- Excel 分析
- 數據可視化
- 趨勢分析
- 自動化報告

---

## 🎯 使用場景

### 1. 域名上線前檢測
```bash
# 檢查新域名在印尼的可訪問性
./check_indonesia_dns.sh newdomain.com
```

### 2. 故障排查
```bash
# 用戶報告無法訪問，檢查是否是 ISP 問題
./check_indonesia_dns.sh problematic-domain.com
```

### 3. 定期監控
```bash
# 每天檢測關鍵域名
./check_indonesia_dns.sh -f critical-domains.txt
```

### 4. DNS 污染檢測
```bash
# 檢查 IP 一致性，發現污染
./check_indonesia_dns.sh suspicious-domain.com
```

---

## 🔗 相關工具

- `check_monitoring_services.sh` - ThousandEyes/Catchpoint 檢測
- `check_dns_monitoring.sh` - 通用 DNS 監控
- 現有的域名監控系統

---

## 📞 需要幫助？

如果遇到問題：
1. 檢查 dig 是否已安裝
2. 確認網路連接正常
3. 查看生成的報告文件
4. 檢查 DNS 伺服器是否可達

---

**提示**：這個工具專門針對印尼市場，如果需要越南或其他地區的版本，可以修改 DNS 列表。

