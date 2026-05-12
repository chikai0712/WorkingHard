# GlobalpingChecker 腳本目錄

## 📁 目錄結構

### detection/ - 檢測腳本
**當前使用**:
- **smart-zone-check.sh** ⭐ 智能分區檢測（最新）
- **id_globalping_multi_v3.3_Telegram.sh** ⭐ V3.3 Telegram版

**其他版本**:
- id_globalping_multi_v3.2_Slack.sh - V3.2 Slack版

**legacy/** - 舊版本:
- id_globalping_multi_v3.1_Token.sh - V3.1
- id_globalping_multi_v3.0.sh - V3.0
- id_globalping_multi_v2.0.sh - V2.0

**experimental/** - 實驗版本:
- id_globalping_multi_v4.0.sh - V4.0

### management/ - 管理工具
- **domain-status-manager.sh** ⭐ 域名狀態管理

### quota/ - 額度管理
- smart-check.sh - 智能額度檢查
- auto-quota-check.sh - 自動額度檢查
- check-api-quota.sh - API 額度查詢

### notification/ - 通知系統
- telegram-notify.sh - Telegram 通知函數庫
- slack-notify.sh - Slack 通知函數庫

### setup/ - 配置設置
- setup-telegram.sh - Telegram 配置向導
- setup-slack.sh - Slack 配置向導
- verify_setup.sh - 驗證配置

### utils/ - 工具腳本
- view_db.py - 數據庫查看工具
- verify_scripts.sh - 驗證腳本
- test-api-token.sh - 測試 API Token
- test-telegram-bot.sh - 測試 Telegram Bot

---

## 🚀 快速使用

### 執行智能分區檢測
```bash
cd detection/
bash smart-zone-check.sh ../data/domains.txt
```

### 查看域名狀態
```bash
cd management/
bash domain-status-manager.sh stats
```

### 檢查 API 額度
```bash
cd quota/
bash check-api-quota.sh
```

### 配置 Telegram
```bash
cd setup/
bash setup-telegram.sh
```

---

## 📊 版本說明

- **V3.3** ⭐ 當前推薦版本（Telegram 通知）
- **V3.2** - Slack 通知版本
- **V3.1** - Token 支持版本
- **V3.0** - 基礎版本
- **V2.0** - 舊版本（已歸檔）
- **V4.0** - 實驗版本

---

## 🎯 智能分區系統

智能分區檢測系統是最新的檢測方案：
- 異常區：頻繁檢測有問題的域名
- 正常區：抽樣檢測正常的域名
- 自動轉換：根據檢測結果自動調整分區
- 節省額度：比全量檢測節省 75% API 額度

使用方法：
```bash
cd detection/
bash smart-zone-check.sh ../data/domains.txt
```
