# Project 根目錄文件分類報告

## 📊 文件分類

### 🗂️ 配置文件（1個）
**保留在根目錄**

1. **.gitignore**
   - Git 忽略規則
   - 必須保留在根目錄

---

### 📖 文檔類（10個）
**建議移至 `docs/` 目錄**

#### 部署相關
1. **AWS部署檔案整理說明.md**
   - AWS 部署說明
   - 移至: `docs/deployment/`

#### 指南類
2. **AUTO_RETRY_GUIDE.md**
   - 自動重試指南
   - 移至: `docs/guides/`

3. **DOMAIN_CHECKER_GUIDE.md**
   - 域名檢測指南
   - 移至: `docs/guides/`

4. **EXECUTION_GUIDE.md**
   - 執行指南
   - 移至: `docs/guides/`

5. **GIT更新指南.md**
   - Git 更新說明
   - 移至: `docs/guides/`

6. **GPT4_測試說明.md**
   - GPT4 測試文檔
   - 移至: `docs/guides/`

#### 參考文檔
7. **domain-status-classification.md**
   - 域名狀態分類說明
   - 移至: `docs/reference/`

8. **VERSION_3.0_README.md**
   - V3.0 版本說明
   - 移至: `docs/versions/`

9. **VERSION_COMPARISON.md**
   - 版本比較
   - 移至: `docs/versions/`

#### 項目管理
10. **PROJECT_ORGANIZATION_REPORT.md**
    - 項目整理報告
    - 移至: `docs/project/`

---

### 🔧 腳本類（7個）
**建議移至 `scripts/` 目錄**

#### 檢測腳本
1. **id_globalping_auto_retry.sh**
   - 自動重試檢測
   - 移至: `scripts/detection/`

2. **id_globalping_cli.sh**
   - CLI 檢測工具
   - 移至: `scripts/detection/`

3. **id_globalping_v1.1.sh**
   - V1.1 檢測腳本
   - 移至: `scripts/detection/legacy/`

4. **show_globalping_nodes.sh**
   - 顯示節點信息
   - 移至: `scripts/utils/`

#### 管理腳本
5. **cleanup_scripts.sh**
   - 清理腳本
   - 移至: `scripts/maintenance/`

6. **verify_scripts.sh**
   - 驗證腳本
   - 移至: `scripts/maintenance/`

7. **organize-projects.sh**
   - 項目整理腳本
   - 移至: `scripts/maintenance/`

---

### 🐍 Python 腳本（3個）
**建議移至 `scripts/python/` 目錄**

1. **analyze_domain_results.py**
   - 域名結果分析
   - 移至: `scripts/python/analysis/`

2. **gpt4_domain_analyzer.py**
   - GPT4 域名分析器
   - 移至: `scripts/python/analysis/`

3. **quick_analysis.py**
   - 快速分析工具
   - 移至: `scripts/python/analysis/`

---

### 📋 新增文件（1個）
**保留在根目錄**

1. **00-README.md**
   - 項目結構說明
   - 保留在根目錄作為導航

---

## 🎯 建議的整理方案

### 目錄結構
```
Project/
├── .gitignore                    ✅ 保留
├── 00-README.md                  ✅ 保留
│
├── docs/                         📖 新建
│   ├── deployment/
│   │   └── AWS部署檔案整理說明.md
│   ├── guides/
│   │   ├── AUTO_RETRY_GUIDE.md
│   │   ├── DOMAIN_CHECKER_GUIDE.md
│   │   ├── EXECUTION_GUIDE.md
│   │   ├── GIT更新指南.md
│   │   └── GPT4_測試說明.md
│   ├── reference/
│   │   └── domain-status-classification.md
│   ├── versions/
│   │   ├── VERSION_3.0_README.md
│   │   └── VERSION_COMPARISON.md
│   └── project/
│       └── PROJECT_ORGANIZATION_REPORT.md
│
└── scripts/                      🔧 新建
    ├── detection/
    │   ├── id_globalping_auto_retry.sh
    │   ├── id_globalping_cli.sh
    │   └── legacy/
    │       └── id_globalping_v1.1.sh
    ├── utils/
    │   └── show_globalping_nodes.sh
    ├── maintenance/
    │   ├── cleanup_scripts.sh
    │   ├── verify_scripts.sh
    │   └── organize-projects.sh
    └── python/
        └── analysis/
            ├── analyze_domain_results.py
            ├── gpt4_domain_analyzer.py
            └── quick_analysis.py
```

---

## 📊 統計

| 類型 | 數量 | 處理方式 |
|------|------|---------|
| 配置文件 | 1 | 保留根目錄 |
| 文檔 | 10 | 移至 docs/ |
| Shell 腳本 | 7 | 移至 scripts/ |
| Python 腳本 | 3 | 移至 scripts/python/ |
| 新增文件 | 1 | 保留根目錄 |
| **總計** | **22** | - |

---

## 🚀 執行整理

### 自動整理腳本
創建 `organize-root-files.sh` 來自動整理這些文件。

### 手動整理步驟
```bash
cd ~/Desktop/Project

# 1. 創建目錄結構
mkdir -p docs/{deployment,guides,reference,versions,project}
mkdir -p scripts/{detection/legacy,utils,maintenance,python/analysis}

# 2. 移動文檔
mv AWS部署檔案整理說明.md docs/deployment/
mv *_GUIDE.md docs/guides/
mv *指南.md docs/guides/
mv domain-status-classification.md docs/reference/
mv VERSION*.md docs/versions/
mv PROJECT_ORGANIZATION_REPORT.md docs/project/

# 3. 移動腳本
mv id_globalping_auto_retry.sh scripts/detection/
mv id_globalping_cli.sh scripts/detection/
mv id_globalping_v1.1.sh scripts/detection/legacy/
mv show_globalping_nodes.sh scripts/utils/
mv cleanup_scripts.sh scripts/maintenance/
mv verify_scripts.sh scripts/maintenance/
mv organize-projects.sh scripts/maintenance/

# 4. 移動 Python 腳本
mv *_domain_*.py scripts/python/analysis/
mv quick_analysis.py scripts/python/analysis/
```

---

## 💡 建議

1. **立即整理**: 這些文件會讓根目錄更清爽
2. **保留**: .gitignore 和 00-README.md
3. **歸檔**: 舊版本腳本移至 legacy/

需要我創建自動整理腳本嗎？
