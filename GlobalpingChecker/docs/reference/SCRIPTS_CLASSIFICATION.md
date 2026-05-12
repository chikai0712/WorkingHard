# GlobalpingChecker 項目腳本分類報告

## 📊 腳本總覽

### 統計
- **Shell 腳本**: 28 個
- **Python 腳本**: 2 個
- **總計**: 30 個腳本

---

## 🎯 按功能分類

### 1️⃣ 核心檢測腳本（8個）⭐ 主要

#### 最新版本（V3.x）
1. **id_globalping_multi_v3.3_Telegram.sh** ⭐ 當前使用
   - V3.3 版本
   - Telegram 通知整合
   - 完整的狀態分類
   - 建議: 保留在 `scripts/detection/`

2. **id_globalping_multi_v3.2_Slack.sh**
   - V3.2 版本
   - Slack 通知整合
   - 建議: 移至 `scripts/detection/`

3. **id_globalping_multi_v3.1_Token.sh**
   - V3.1 版本
   - API Token 支持
   - 建議: 移至 `scripts/detection/legacy/`

4. **id_globalping_multi_v3.0.sh**
   - V3.0 版本
   - 基礎版本
   - 建議: 移至 `scripts/detection/legacy/`

#### 舊版本（V1.x - V2.x）
5. **id_globalping_multi_v2.0.sh**
   - V2.0 版本
   - 建議: 移至 `scripts/detection/legacy/`

6. **id_globalping_multi_v4.0.sh**
   - V4.0 實驗版本
   - 建議: 移至 `scripts/detection/experimental/`

7. **id_globalping_auto_retry.sh**
   - 自動重試版本
   - 建議: 移至 `scripts/detection/`

8. **id_globalping_cli.sh**
   - CLI 工具版本
   - 建議: 移至 `scripts/detection/`

---

### 2️⃣ 智能分區檢測（2個）⭐ 最新

1. **smart-zone-check.sh** ⭐ 最新系統
   - 智能分區檢測
   - 異常區/正常區管理
   - SQLite 數據庫
   - 建議: 保留在 `scripts/detection/`

2. **domain-status-manager.sh** ⭐ 管理工具
   - 域名狀態管理
   - 統計查詢
   - 手動調整
   - 建議: 保留在 `scripts/management/`

---

### 3️⃣ 額度管理（3個）

1. **smart-check.sh**
   - 智能額度檢查
   - 閾值判斷
   - 建議: 移至 `scripts/quota/`

2. **auto-quota-check.sh**
   - 自動額度檢查
   - 持續監控
   - 建議: 移至 `scripts/quota/`

3. **check-api-quota.sh**
   - API 額度查詢
   - 建議: 移至 `scripts/quota/`

---

### 4️⃣ 通知系統（2個）

1. **telegram-notify.sh**
   - Telegram 通知函數庫
   - 建議: 移至 `scripts/notification/`

2. **slack-notify.sh**
   - Slack 通知函數庫
   - 建議: 移至 `scripts/notification/`

---

### 5️⃣ 配置與設置（3個）

1. **setup-telegram.sh**
   - Telegram 配置向導
   - 建議: 移至 `scripts/setup/`

2. **setup-slack.sh**
   - Slack 配置向導
   - 建議: 移至 `scripts/setup/`

3. **verify_setup.sh**
   - 驗證配置
   - 建議: 移至 `scripts/setup/`

---

### 6️⃣ 工具腳本（5個）

1. **show_globalping_nodes.sh**
   - 顯示可用節點
   - 建議: 移至 `scripts/utils/`

2. **cleanup_scripts.sh**
   - 清理腳本
   - 建議: 移至 `scripts/utils/`

3. **verify_scripts.sh**
   - 驗證腳本
   - 建議: 移至 `scripts/utils/`

4. **dns_test_indonesia.sh**
   - 印尼 DNS 測試
   - 建議: 移至 `scripts/utils/`

5. **view_db.py**
   - 數據庫查看工具
   - 建議: 移至 `scripts/utils/`

---

### 7️⃣ 部署相關（5個）

#### AWS 部署
1. **auto-deploy-v4.1.sh**
   - V4.1 自動部署
   - 建議: 移至 `deploy/aws/`

2. **deploy-v4.1-to-aws.sh**
   - V4.1 AWS 部署
   - 建議: 移至 `deploy/aws/`

3. **deploy-v4.1-no-proxy.sh**
   - 無代理部署
   - 建議: 移至 `deploy/aws/`

4. **MANUAL_DEPLOY_V4.1.sh**
   - 手動部署指南
   - 建議: 移至 `deploy/aws/`

#### EC2 部署
5. **ec2/setup.sh**
   - EC2 設置腳本
   - 建議: 保留在 `ec2/`

---

### 8️⃣ 分析工具（2個）Python

1. **gpt4_domain_analyzer.py**
   - GPT4 域名分析
   - 建議: 移至 `scripts/analysis/`

2. **analyze_domain_results.py**
   - 結果分析工具
   - 建議: 移至 `scripts/analysis/`

---

## 🗂️ 建議的目錄結構

```
GlobalpingChecker/
├── scripts/
│   ├── detection/              # 檢測腳本
│   │   ├── smart-zone-check.sh           ⭐ 最新
│   │   ├── id_globalping_multi_v3.3_Telegram.sh  ⭐ 當前
│   │   ├── id_globalping_multi_v3.2_Slack.sh
│   │   ├── id_globalping_auto_retry.sh
│   │   ├── id_globalping_cli.sh
│   │   ├── legacy/             # 舊版本
│   │   │   ├── id_globalping_multi_v3.1_Token.sh
│   │   │   ├── id_globalping_multi_v3.0.sh
│   │   │   └── id_globalping_multi_v2.0.sh
│   │   └── experimental/       # 實驗版本
│   │       └── id_globalping_multi_v4.0.sh
│   │
│   ├── management/             # 管理工具
│   │   └── domain-status-manager.sh      ⭐ 狀態管理
│   │
│   ├── quota/                  # 額度管理
│   │   ├── smart-check.sh
│   │   ├── auto-quota-check.sh
│   │   └── check-api-quota.sh
│   │
│   ├── notification/           # 通知系統
│   │   ├── telegram-notify.sh
│   │   └── slack-notify.sh
│   │
│   ├── setup/                  # 配置設置
│   │   ├── setup-telegram.sh
│   │   ├── setup-slack.sh
│   │   └── verify_setup.sh
│   │
│   ├── utils/                  # 工具腳本
│   │   ├── show_globalping_nodes.sh
│   │   ├── cleanup_scripts.sh
│   │   ├── verify_scripts.sh
│   │   ├── dns_test_indonesia.sh
│   │   └── view_db.py
│   │
│   └── analysis/               # 分析工具
│       ├── gpt4_domain_analyzer.py
│       └── analyze_domain_results.py
│
├── deploy/                     # 部署相關
│   └── aws/
│       ├── auto-deploy-v4.1.sh
│       ├── deploy-v4.1-to-aws.sh
│       ├── deploy-v4.1-no-proxy.sh
│       └── MANUAL_DEPLOY_V4.1.sh
│
├── ec2/                        # EC2 相關
│   ├── setup.sh
│   └── ...
│
├── v4/                         # V4 版本
├── v4.1/                       # V4.1 版本
├── aws/                        # AWS 配置
│
├── config/                     # 配置文件
│   ├── telegram-config.env
│   └── ...
│
├── data/                       # 數據文件
│   ├── domains.txt
│   ├── domain_status.db
│   └── ...
│
└── docs/                       # 文檔
    ├── guides/
    ├── deployment/
    └── reference/
```

---

## 📊 優先級分類

### 🔥 核心使用（保留在主目錄或 scripts/）
1. smart-zone-check.sh ⭐
2. domain-status-manager.sh ⭐
3. id_globalping_multi_v3.3_Telegram.sh ⭐
4. telegram-notify.sh
5. smart-check.sh

### 📦 常用工具（移至 scripts/）
1. check-api-quota.sh
2. setup-telegram.sh
3. show_globalping_nodes.sh
4. view_db.py

### 🗄️ 歸檔（移至 legacy/）
1. id_globalping_multi_v2.0.sh
2. id_globalping_multi_v3.0.sh
3. id_globalping_multi_v3.1_Token.sh

### 🧪 實驗性（移至 experimental/）
1. id_globalping_multi_v4.0.sh

---

## 🚀 執行整理

### 自動整理腳本

創建 `organize-globalping-scripts.sh` 來自動整理這些腳本。

### 手動整理步驟

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 1. 創建目錄結構
mkdir -p scripts/{detection/{legacy,experimental},management,quota,notification,setup,utils,analysis}
mkdir -p deploy/aws
mkdir -p config
mkdir -p data

# 2. 移動檢測腳本
mv smart-zone-check.sh scripts/detection/
mv id_globalping_multi_v3.3_Telegram.sh scripts/detection/
mv id_globalping_multi_v3.2_Slack.sh scripts/detection/
mv id_globalping_auto_retry.sh scripts/detection/
mv id_globalping_cli.sh scripts/detection/

# 3. 移動舊版本
mv id_globalping_multi_v3.1_Token.sh scripts/detection/legacy/
mv id_globalping_multi_v3.0.sh scripts/detection/legacy/
mv id_globalping_multi_v2.0.sh scripts/detection/legacy/

# 4. 移動實驗版本
mv id_globalping_multi_v4.0.sh scripts/detection/experimental/

# 5. 移動管理工具
mv domain-status-manager.sh scripts/management/

# 6. 移動額度管理
mv smart-check.sh scripts/quota/
mv auto-quota-check.sh scripts/quota/
mv check-api-quota.sh scripts/quota/

# 7. 移動通知系統
mv telegram-notify.sh scripts/notification/
mv slack-notify.sh scripts/notification/

# 8. 移動設置腳本
mv setup-telegram.sh scripts/setup/
mv setup-slack.sh scripts/setup/
mv verify_setup.sh scripts/setup/

# 9. 移動工具腳本
mv show_globalping_nodes.sh scripts/utils/
mv cleanup_scripts.sh scripts/utils/
mv verify_scripts.sh scripts/utils/
mv dns_test_indonesia.sh scripts/utils/
mv view_db.py scripts/utils/

# 10. 移動分析工具
mv gpt4_domain_analyzer.py scripts/analysis/
mv analyze_domain_results.py scripts/analysis/

# 11. 移動部署腳本
mv auto-deploy-v4.1.sh deploy/aws/
mv deploy-v4.1-to-aws.sh deploy/aws/
mv deploy-v4.1-no-proxy.sh deploy/aws/
mv MANUAL_DEPLOY_V4.1.sh deploy/aws/

# 12. 移動配置文件
mv telegram-config.env config/ 2>/dev/null || true

# 13. 移動數據文件
mv domains.txt data/ 2>/dev/null || true
mv *.db data/ 2>/dev/null || true
mv test_*.txt data/ 2>/dev/null || true
```

---

## 💡 建議

1. **立即整理**: 讓項目結構更清晰
2. **保留核心**: 最常用的腳本保持易訪問
3. **歸檔舊版**: 舊版本移至 legacy/
4. **文檔更新**: 更新所有文檔中的路徑引用

需要我創建自動整理腳本嗎？
