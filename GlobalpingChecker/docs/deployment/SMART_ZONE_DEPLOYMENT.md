# 智能分區檢測系統部署指南

## 🎯 系統概述

智能分區檢測系統將域名分為兩個區域：
- **異常區（ABNORMAL_ZONE）**: 有問題的域名，頻繁檢測
- **正常區（NORMAL_ZONE）**: 正常的域名，抽樣檢測

## 📊 優勢

### 當前系統 vs 智能分區系統

| 特性 | 當前系統 | 智能分區系統 |
|------|---------|-------------|
| 檢測對象 | 100個全部 | 88異常+3抽樣 |
| 額度消耗 | 300次/檢測 | 273次/檢測 |
| 異常域名檢測頻率 | 1-2次/小時 | 6次/小時 |
| 正常域名檢測頻率 | 1-2次/小時 | 抽樣檢測 |
| 狀態追蹤 | 無 | 完整追蹤 |
| 自動轉換 | 無 | 自動轉換 |

## 🚀 部署步驟

### 步驟 1：上傳文件到 EC2

在本地終端執行：

```bash
cd ~/Desktop/Project/GlobalpingChecker

# 上傳智能分區檢測腳本
scp -i ~/.ssh/globalping-checker-key.pem smart-zone-check.sh ec2-user@54.238.247.106:~/globalping-checker/

# 上傳狀態管理工具
scp -i ~/.ssh/globalping-checker-key.pem domain-status-manager.sh ec2-user@54.238.247.106:~/globalping-checker/

# 設置權限
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106 'chmod +x ~/globalping-checker/*.sh'
```

### 步驟 2：初始化系統

SSH 到 EC2：

```bash
ssh -i ~/.ssh/globalping-checker-key.pem ec2-user@54.238.247.106
cd ~/globalping-checker

# 首次運行，初始化數據庫
bash smart-zone-check.sh domains.txt
```

### 步驟 3：更新 Crontab

```bash
crontab -e
```

替換為：
```bash
# 智能分區檢測（每 10 分鐘）
*/10 * * * * cd ~/globalping-checker && bash smart-zone-check.sh domains.txt >> ~/smart-check.log 2>&1
```

## 📊 工作流程

### 初始狀態
```
100 個域名 → 全部放入異常區（PENDING）
第一次檢測 → 分類狀態
```

### 檢測循環
```
每 10 分鐘：
  1. 檢查額度 >= 300
  2. 獲取異常區域名（88個）
  3. 抽樣正常區域名（3個）
  4. 執行檢測
  5. 更新狀態
  6. 自動轉換區域
```

### 狀態轉換

#### 異常 → 正常
```
條件：連續 3 次檢測為 CLEAN
動作：移至正常區
通知：發送 Telegram "域名已恢復"
```

#### 正常 → 異常
```
條件：檢測到任何異常狀態
動作：立即移至異常區
通知：發送 Telegram "域名出現異常"
```

## 🔧 管理命令

### 查看統計信息
```bash
bash domain-status-manager.sh stats
```

輸出：
```
📊 域名狀態統計
========================================
總域名數: 100
異常區: 88 個
正常區: 12 個

狀態分布：
BLOCKED    45  ABNORMAL_ZONE
TIMEOUT    30  ABNORMAL_ZONE
WARNING    13  ABNORMAL_ZONE
CLEAN      12  NORMAL_ZONE
```

### 查看異常區域名
```bash
bash domain-status-manager.sh abnormal
```

### 查看正常區域名
```bash
bash domain-status-manager.sh normal
```

### 查看最近狀態變化
```bash
bash domain-status-manager.sh changes
```

### 手動移動域名
```bash
# 將域名移至正常區
bash domain-status-manager.sh move example.com NORMAL_ZONE

# 將域名移至異常區
bash domain-status-manager.sh move example.com ABNORMAL_ZONE
```

### 導出報告
```bash
bash domain-status-manager.sh export report.csv
```

## 📱 Telegram 通知增強

系統會發送以下通知：

### 1. 域名恢復通知
```
✅ 域名已恢復正常

域名: example.com
狀態: BLOCKED → CLEAN
連續正常: 3 次
時間: 2026-03-07 10:30:00
```

### 2. 域名異常通知
```
⚠️ 域名出現異常

域名: example.com
狀態: CLEAN → BLOCKED
位置: 正常區 → 異常區
時間: 2026-03-07 10:30:00
```

### 3. 定期摘要報告
```
📊 智能分區檢測報告

檢測時間: 2026-03-07 10:30:00

異常區: 88 個
  🚨 BLOCKED: 45
  ⚠️ TIMEOUT: 30
  ⚠️ WARNING: 13

正常區: 12 個
  ✅ CLEAN: 12

本次檢測:
  異常區: 88 個
  正常區抽樣: 3 個
  額度消耗: 273 次
  剩餘額度: 227 / 500
```

## 📊 預期效果

### 檢測頻率提升
```
異常域名（88個）：
  當前: 1-2 次/小時
  優化後: 6 次/小時
  提升: 3-6 倍

正常域名（12個）：
  當前: 1-2 次/小時（浪費）
  優化後: 抽樣檢測
  節省: 75% 額度
```

### 額度利用率
```
當前系統:
  100 域名 × 3 = 300 次
  每小時 1-2 次檢測
  總計: 300-600 次/小時

智能系統:
  91 域名 × 3 = 273 次
  每小時 6 次檢測（額度允許）
  總計: 最多 1638 次/小時
  實際: 約 1000 次/小時（受額度限制）
```

### 問題發現速度
```
域名恢復檢測:
  當前: 30-60 分鐘
  優化後: 10-30 分鐘
  提升: 2-6 倍

域名異常檢測:
  當前: 30-60 分鐘
  優化後: 立即（抽樣到時）
  平均: 20 分鐘
```

## 🎯 實施時間線

### 立即（今天）
```
1. 上傳腳本到 EC2
2. 初始化數據庫
3. 更新 crontab
4. 開始運行
```

### 第一天
```
- 所有域名完成首次分類
- 異常域名開始頻繁檢測
- 正常域名開始抽樣檢測
```

### 第一週
```
- 部分異常域名恢復正常
- 系統自動調整分區
- 檢測效率提升明顯
```

## 💡 注意事項

### 1. 數據庫位置
```
位置: ~/globalping-checker/domain_status.db
備份: 定期備份數據庫
```

### 2. 日誌查看
```bash
# 查看運行日誌
tail -f ~/smart-check.log

# 查看最近的狀態變化
bash domain-status-manager.sh changes
```

### 3. 手動干預
```bash
# 如果某個域名誤判，可以手動調整
bash domain-status-manager.sh move example.com NORMAL_ZONE
```

## 🔄 回滾方案

如果需要回到原系統：

```bash
# 恢復原 crontab
crontab -e

# 改回：
*/10 * * * * cd ~/globalping-checker && bash smart-check.sh domains.txt >> ~/smart-check.log 2>&1
```

---

**準備好部署了嗎？執行步驟 1 開始上傳文件！** 🚀
