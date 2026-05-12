# 第三方監控服務檢測工具使用指南

## 📋 目錄

1. [快速開始](#快速開始)
2. [獲取 API 憑證](#獲取-api-憑證)
3. [配置環境變數](#配置環境變數)
4. [執行檢測](#執行檢測)
5. [查看結果](#查看結果)
6. [常見問題](#常見問題)

---

## 🚀 快速開始

### 1. 複製配置文件

```bash
cd domain-monitoring-system
cp env.monitoring.example .env.monitoring
```

### 2. 編輯配置文件

```bash
nano .env.monitoring
# 或使用你喜歡的編輯器
```

### 3. 執行檢測腳本

```bash
chmod +x check_monitoring_services.sh
./check_monitoring_services.sh
```

---

## 🔑 獲取 API 憑證

### ThousandEyes

#### 步驟 1：註冊試用帳號
1. 訪問：https://www.thousandeyes.com/signup
2. 填寫資訊（使用公司郵箱更容易通過）
3. 選擇 "Free Trial"（14 天免費）

#### 步驟 2：獲取 API Token
1. 登入 https://app.thousandeyes.com
2. 點擊右上角頭像
3. 選擇 **Account Settings**
4. 左側選單選擇 **Users and Roles** → **Profile**
5. 找到 **OAuth Bearer Token** 區塊
6. 點擊 **Show** 或 **Generate New Token**
7. 複製 Token

#### 步驟 3：填入配置文件
```bash
THOUSANDEYES_API_TOKEN="你的Token"
```

---

### Catchpoint

#### 步驟 1：註冊試用帳號
1. 訪問：https://www.catchpoint.com/free-trial
2. 填寫資訊
3. 選擇 "30-Day Free Trial"

#### 步驟 2：獲取 API 憑證
1. 登入 https://portal.catchpoint.com
2. 點擊左側選單 **Settings**
3. 選擇 **API**
4. 點擊 **Add API Consumer**
5. 填寫名稱（例如：DNS Monitoring）
6. 複製 **Client ID** 和 **Client Secret**

#### 步驟 3：填入配置文件
```bash
CATCHPOINT_API_KEY="你的Client ID"
CATCHPOINT_API_SECRET="你的Client Secret"
```

---

### Pingdom

#### 步驟 1：註冊試用帳號
1. 訪問：https://www.pingdom.com/free
2. 填寫資訊
3. 選擇 "30-Day Free Trial"

#### 步驟 2：獲取 API Token
1. 登入 https://my.pingdom.com
2. 點擊 **Settings**
3. 選擇 **Pingdom API**
4. 點擊 **Add API Token**
5. 填寫名稱和權限
6. 複製 Token

#### 步驟 3：填入配置文件
```bash
PINGDOM_API_TOKEN="你的Token"
```

---

## ⚙️ 配置環境變數

### 完整配置範例

```bash
# ThousandEyes
THOUSANDEYES_API_TOKEN="abc123def456ghi789"

# Catchpoint
CATCHPOINT_API_KEY="client-id-12345"
CATCHPOINT_API_SECRET="secret-67890"

# Pingdom
PINGDOM_API_TOKEN="pingdom-token-abcdef"

# 測試配置
TEST_DOMAIN="yourdomain.com"
TEST_INTERVAL=300
TARGET_REGIONS="VN,ID,SG,TH,PH"
```

### 配置說明

| 變數 | 必填 | 說明 |
|------|------|------|
| `THOUSANDEYES_API_TOKEN` | 否 | ThousandEyes API Token |
| `CATCHPOINT_API_KEY` | 否 | Catchpoint Client ID |
| `CATCHPOINT_API_SECRET` | 否 | Catchpoint Client Secret |
| `PINGDOM_API_TOKEN` | 否 | Pingdom API Token |
| `TEST_DOMAIN` | 否 | 要測試的域名 |
| `TEST_INTERVAL` | 否 | 測試間隔（秒） |
| `TARGET_REGIONS` | 否 | 目標地區代碼 |

**注意**：至少需要配置一個服務的 API 憑證

---

## 🔍 執行檢測

### 基本執行

```bash
./check_monitoring_services.sh
```

### 輸出範例

```
╔═══════════════════════════════════════════════════╗
║     第三方監控服務檢測工具                        ║
║     支援：ThousandEyes, Catchpoint, Pingdom      ║
╚═══════════════════════════════════════════════════╝

✓ 已載入環境變數

=== ThousandEyes 檢測 ===

1. 獲取可用的監控節點...
✓ 節點列表已保存到 thousandeyes_agents.json

東南亞節點：
Singapore - Singapore (SG)
Hong Kong - Hong Kong (HK)
Tokyo - Tokyo (JP)

2. 獲取現有測試...
✓ 測試列表已保存到 thousandeyes_tests.json

=== Catchpoint 檢測 ===

1. 獲取 Access Token...
✓ Access Token 已獲取

2. 獲取監控節點列表...
✓ 節點列表已保存到 catchpoint_nodes.json

東南亞節點：
Singapore Backbone - Singapore, Singapore
Jakarta Backbone - Jakarta, Indonesia

=== Pingdom 檢測 ===

1. 獲取探測點列表...
✓ 探測點列表已保存到 pingdom_probes.json

亞太探測點：
Singapore - Singapore, Singapore
Tokyo - Tokyo, Japan

✓ 報告已生成：monitoring_services_report_20260224_140530.md

✓ 所有檢測完成！
```

---

## 📊 查看結果

### 生成的文件

執行後會生成以下文件：

```
domain-monitoring-system/
├── thousandeyes_agents.json      # ThousandEyes 節點列表
├── thousandeyes_tests.json       # ThousandEyes 測試列表
├── catchpoint_nodes.json         # Catchpoint 節點列表
├── catchpoint_tests.json         # Catchpoint 測試列表
├── pingdom_probes.json           # Pingdom 探測點列表
├── pingdom_checks.json           # Pingdom 檢查列表
└── monitoring_services_report_*.md  # 綜合報告
```

### 查看節點列表

#### 使用 jq 查看（推薦）

```bash
# 安裝 jq
brew install jq  # macOS
# 或
sudo apt-get install jq  # Ubuntu

# 查看 ThousandEyes 節點
cat thousandeyes_agents.json | jq '.agents[] | {name: .agentName, location: .location, country: .countryId}'

# 查看 Catchpoint 節點
cat catchpoint_nodes.json | jq '.[] | {name: .name, city: .city, country: .country}'

# 篩選越南和印尼節點
cat thousandeyes_agents.json | jq '.agents[] | select(.countryId == "VN" or .countryId == "ID")'
```

#### 直接查看 JSON

```bash
# 使用 less 查看
less thousandeyes_agents.json

# 使用 cat 查看
cat thousandeyes_agents.json
```

### 查看報告

```bash
# 查看最新報告
ls -t monitoring_services_report_*.md | head -1 | xargs cat

# 或使用編輯器打開
code monitoring_services_report_*.md
```

---

## 🔍 分析節點列表

### 關鍵信息檢查清單

#### ThousandEyes
```bash
# 檢查是否有越南節點
cat thousandeyes_agents.json | jq '.agents[] | select(.countryId == "VN")'

# 檢查是否有印尼節點
cat thousandeyes_agents.json | jq '.agents[] | select(.countryId == "ID")'

# 檢查節點類型
cat thousandeyes_agents.json | jq '.agents[] | {name: .agentName, type: .agentType, network: .network}'
```

#### Catchpoint
```bash
# 檢查越南節點
cat catchpoint_nodes.json | jq '.[] | select(.country == "Vietnam")'

# 檢查印尼節點
cat catchpoint_nodes.json | jq '.[] | select(.country == "Indonesia")'

# 檢查 ISP 信息
cat catchpoint_nodes.json | jq '.[] | {name: .name, isp: .isp, type: .nodeType}'
```

---

## ❓ 常見問題

### Q1: API Token 無效

**錯誤信息**：
```
✗ 無法連接到 ThousandEyes API
```

**解決方法**：
1. 確認 Token 是否正確複製（沒有多餘空格）
2. 確認試用帳號是否已激活
3. 檢查 Token 是否已過期
4. 重新生成 Token

### Q2: 找不到越南/印尼節點

**可能原因**：
1. 試用帳號可能無法訪問所有節點
2. 需要升級到付費方案
3. 該服務確實沒有這些地區的節點

**解決方法**：
1. 聯繫銷售團隊確認
2. 查看服務的節點覆蓋地圖
3. 考慮使用其他服務

### Q3: jq 命令找不到

**錯誤信息**：
```
jq: command not found
```

**解決方法**：
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# CentOS/RHEL
sudo yum install jq
```

### Q4: 權限被拒絕

**錯誤信息**：
```
Permission denied: ./check_monitoring_services.sh
```

**解決方法**：
```bash
chmod +x check_monitoring_services.sh
```

### Q5: 如何創建測試？

**ThousandEyes**：
1. 登入 Web 界面
2. 點擊 "Cloud & Enterprise Agents" → "Test Settings"
3. 點擊 "Add New Test"
4. 選擇測試類型（HTTP Server, DNS, etc.）
5. 選擇要使用的 Agents
6. 保存測試

**Catchpoint**：
1. 登入 Web 界面
2. 點擊 "Tests" → "Add Test"
3. 選擇測試類型
4. 選擇監控節點
5. 配置測試參數
6. 保存測試

---

## 📝 下一步

### 1. 分析節點列表
- 確認是否有越南/印尼節點
- 確認節點類型（Cloud vs ISP）
- 記錄可用的 ISP 列表

### 2. 評估服務
- 比較不同服務的節點覆蓋
- 評估價格 vs 功能
- 決定是否值得付費

### 3. 配置監控
- 在 Web 界面創建測試
- 設定告警規則
- 整合到現有系統

### 4. 生成報告
- 整理節點列表
- 記錄 ISP 覆蓋情況
- 制定決策建議

---

## 📞 需要幫助？

如果遇到問題，請：

1. 檢查生成的 JSON 文件
2. 查看錯誤信息
3. 參考常見問題
4. 聯繫服務提供商的支援團隊

---

## 📄 相關文檔

- [ThousandEyes API 文檔](https://developer.thousandeyes.com/)
- [Catchpoint API 文檔](https://support.catchpoint.com/hc/en-us/sections/360004068372-API)
- [Pingdom API 文檔](https://docs.pingdom.com/api/)

