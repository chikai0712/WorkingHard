# DNS 域名解析檢查工具

## 📋 專案概述

這是一個 DNS 域名解析檢查工具，**使用多個 ISP 的 Name Server (NS) 檢測域名解析是否異常**。主要功能包括：

- **DNS 劫持檢測**：檢測域名是否被解析到非預期的 IP 地址
- **DNS 污染檢測**：檢測部分 NS 是否無法正常解析（可能被污染）
- **解析一致性檢測**：比較不同 NS 的解析結果，發現異常差異
- **IP 白名單驗證**：驗證解析出的 IP 是否在允許的 IP 範圍內

支援 Nagios/Icinga 風格的退出碼，適合整合到監控系統中。

## 🎯 功能特性

### 核心功能
- **DNS 解析檢查**：檢查指定域名在特定 DNS 伺服器上的解析結果
- **多 NS 異常檢測**：使用多個 ISP 的 NS 檢測域名是否異常（DNS 劫持、污染）
- **IP 白名單驗證**：驗證解析出的 IP 是否在允許的 IP 範圍內
- **解析一致性檢測**：比較不同 NS 的解析結果，發現異常差異
- **多 IP 支援**：支援一個域名解析到多個 IP 的情況
- **Nagios 兼容**：使用標準的退出碼（0=OK, 2=CRITICAL, 3=UNKNOWN）
- **白名單管理**：支援 IP 範圍（CIDR）格式的白名單

### 異常檢測能力
- **DNS 劫持檢測**：檢測域名是否被解析到非預期的 IP
- **DNS 污染檢測**：檢測部分 NS 是否無法正常解析
- **解析不一致檢測**：發現不同 NS 解析結果的差異

## 🔍 程式碼分析

### 原始程式碼問題

1. **IP 處理邏輯錯誤**：`is_ip_in_whitelist` 函數中，將單個 IP 地址當作 IP 網絡處理
2. **錯誤處理不完善**：缺少對 DNS 解析失敗的詳細錯誤處理
3. **白名單格式驗證**：缺少對白名單文件格式的驗證
4. **日誌記錄不足**：缺少詳細的日誌記錄
5. **測試覆蓋不足**：缺少單元測試和整合測試

## 🚀 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 基本使用

#### 單 NS 檢查（原始版本）
```bash
# 檢查域名解析
python src/dns_checker.py -R example.com -S 8.8.8.8 -W whitelist.txt

# 改進版本
python src/dns_checker_v2.py -R example.com -S 8.8.8.8 -W whitelist.txt
```

#### 多 NS 異常檢測（推薦）
```bash
# 使用默認的多個公共 DNS 檢測
python src/dns_checker_multi_ns.py -R example.com -W whitelist.txt

# 指定多個 ISP 的 NS
python src/dns_checker_multi_ns.py \
  -R example.com \
  -S 8.8.8.8,1.1.1.1,9.9.9.9,208.67.222.222 \
  -W whitelist.txt

# JSON 格式輸出（便於自動化處理）
python src/dns_checker_multi_ns.py -R example.com -W whitelist.txt --format json
```

## 📁 專案結構

```
DNS-Checker/
├── src/                           # 源代碼
│   ├── dns_checker.py            # 原始版本（單 NS）
│   ├── dns_checker_v2.py         # 改進版本（單 NS，修復問題）
│   └── dns_checker_multi_ns.py   # 多 NS 異常檢測版本（推薦）
├── tests/                         # 測試
│   ├── test_dns_checker.py
│   └── test_utils.py
├── docs/                          # 文檔
│   ├── 程式碼分析.md              # 原始程式碼問題分析
│   ├── 改進建議.md                 # 改進方案
│   ├── API文檔.md                  # API 使用文檔
│   └── 多NS檢測說明.md             # 多 NS 檢測功能說明
├── configs/                        # 配置文件
│   └── whitelist.txt             # 白名單範例
├── scripts/                        # 腳本
│   └── setup.sh                  # 安裝腳本
└── requirements.txt               # 依賴
```

## 🔧 改進計劃

1. **修復 IP 處理邏輯**
2. **增強錯誤處理**
3. **添加日誌記錄**
4. **完善測試覆蓋**
5. **添加配置文件支援**
6. **支援多種輸出格式**

---

**最後更新**：2025-01-XX

