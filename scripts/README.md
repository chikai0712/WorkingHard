# 腳本目錄

## 📁 目錄結構

### detection/ - 檢測腳本
- id_globalping_auto_retry.sh - 自動重試檢測
- id_globalping_cli.sh - CLI 檢測工具
- legacy/ - 舊版本腳本
  - id_globalping_v1.1.sh - V1.1 檢測腳本

### utils/ - 工具腳本
- show_globalping_nodes.sh - 顯示節點信息

### maintenance/ - 維護腳本
- cleanup_scripts.sh - 清理腳本
- verify_scripts.sh - 驗證腳本
- organize-projects.sh - 項目整理腳本

### python/analysis/ - Python 分析工具
- analyze_domain_results.py - 域名結果分析
- gpt4_domain_analyzer.py - GPT4 域名分析器
- quick_analysis.py - 快速分析工具

---

## 🚀 使用方法

### 執行檢測
```bash
cd detection/
bash id_globalping_auto_retry.sh domains.txt
```

### 查看節點
```bash
cd utils/
bash show_globalping_nodes.sh
```

### 分析結果
```bash
cd python/analysis/
python3 analyze_domain_results.py
```
