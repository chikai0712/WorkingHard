# GlobalpingChecker - 智能域名檢測系統

## 🎯 項目概述

智能域名檢測系統，支持分區檢測、自動狀態管理和多種通知方式。

## 📁 項目結構

```
GlobalpingChecker/
├── scripts/              # 所有腳本
│   ├── detection/       # 檢測腳本
│   ├── management/      # 管理工具
│   ├── quota/          # 額度管理
│   ├── notification/   # 通知系統
│   ├── setup/          # 配置設置
│   └── utils/          # 工具腳本
├── deploy/             # 部署相關
├── config/             # 配置文件
├── data/               # 數據文件
├── v4/                 # V4 版本
├── v4.1/               # V4.1 Web版本
├── ec2/                # EC2 相關
└── aws/                # AWS 配置
```

## 🚀 快速開始

### 1. 執行智能分區檢測
```bash
./run-smart-check.sh
```

### 2. 查看域名狀態
```bash
./manage-domains.sh stats
```

### 3. 配置 Telegram 通知
```bash
cd scripts/setup/
bash setup-telegram.sh
```

## 📊 核心功能

### 智能分區檢測 ⭐
- 異常區：頻繁檢測有問題的域名
- 正常區：抽樣檢測正常的域名
- 自動轉換：連續 3 次正常自動移至正常區
- 節省額度：比全量檢測節省 75% API 額度

### 狀態管理
- 完整的歷史記錄（SQLite）
- 實時統計查詢
- 手動狀態調整
- 導出報告

### 通知系統
- Telegram 通知
- Slack 通知
- 自定義通知級別

## 🔧 常用命令

### 檢測相關
```bash
# 智能分區檢測
./run-smart-check.sh

# V3.3 Telegram 版本
cd scripts/detection/
bash id_globalping_multi_v3.3_Telegram.sh ../data/domains.txt
```

### 管理相關
```bash
# 查看統計
./manage-domains.sh stats

# 查看異常域名
./manage-domains.sh abnormal

# 查看正常域名
./manage-domains.sh normal

# 查看狀態變化
./manage-domains.sh changes
```

### 額度管理
```bash
# 檢查 API 額度
cd scripts/quota/
bash check-api-quota.sh
```

## 📖 文檔

- [腳本說明](scripts/README.md)
- [部署指南](docs/deployment/)
- [使用指南](docs/guides/)
- [版本比較](docs/versions/)

## 🎯 版本說明

- **智能分區系統** ⭐ 最新推薦
- **V3.3** - Telegram 通知版本
- **V3.2** - Slack 通知版本
- **V4.1** - Web 界面版本（Docker + PostgreSQL）

## 💡 最佳實踐

1. 使用智能分區檢測節省 API 額度
2. 配置 Telegram 接收實時通知
3. 定期查看域名狀態統計
4. 備份數據庫文件

---

**最後更新**: $(date +%Y-%m-%d)
