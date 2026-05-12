# 快速測試指南

## 🎯 測試 2 個域名

### 1. 創建測試文件

```bash
cd ~/Desktop/Project/GlobalpingChecker
cat > test_2_domains.txt << 'EOF'
7plusmm.com
diamonds9bet.com
EOF
```

---

## 🧪 測試各版本腳本

### 測試 v3.0（推薦）✅

```bash
cd ~/Desktop/Project/GlobalpingChecker
./id_globalping_auto_retry.sh test_2_domains.txt
```

**預計時間**: 30 秒  
**消耗配額**: 6 credits (2域名 × 3節點)

---

### 測試 v2.0

```bash
cd ~/Desktop/Project/GlobalpingChecker
./id_globalping_multi_v2.sh test_2_domains.txt
```

**預計時間**: 20 秒  
**消耗配額**: 6 credits

---

### 測試 v2.1（有 Bug）⚠️

```bash
cd ~/Desktop/Project/GlobalpingChecker
./id_globalping_multi_v2.1.sh test_2_domains.txt
```

**已知問題**:
- macOS Bash 3.2 不支持 `declare -A`
- 域名解析錯誤

**建議**: 跳過此版本，使用 v3.0 或 v2.0

---

## 📊 查看結果

### 實時輸出

測試時會顯示：
```
🔍 檢測域名 [1/2]: 7plusmm.com ...
  📍 BIZNET NETWORKS (AS17451) [Jakarta]
     🎯 目標IP: xxx.xxx.xxx.xxx  | [CLEAN] ✅ 正常連通
  ...
```

### 查看日誌

```bash
# v3.0 日誌
tail -50 ~/globalping_*.log

# v2.0 日誌
tail -50 ~/globalping_multi_*.log

# 查看 CSV（v2.0）
open ~/globalping_multi_*.csv
```

---

## ⚡ 一鍵測試命令

### 測試 v3.0（最推薦）

```bash
cd ~/Desktop/Project/GlobalpingChecker && \
echo -e "7plusmm.com\ndiamonds9bet.com" > test_2_domains.txt && \
./id_globalping_auto_retry.sh test_2_domains.txt
```

### 測試 v2.0

```bash
cd ~/Desktop/Project/GlobalpingChecker && \
echo -e "7plusmm.com\ndiamonds9bet.com" > test_2_domains.txt && \
./id_globalping_multi_v2.sh test_2_domains.txt
```

---

## 🔍 版本對比

| 版本 | 狀態 | 延遲 | 特點 | 推薦度 |
|------|------|------|------|--------|
| **v3.0** | ✅ 可用 | 8秒 | 最穩定、節點詳細信息 | ⭐⭐⭐⭐⭐ |
| **v2.0** | ✅ 可用 | 4秒 | 速度快、有CSV | ⭐⭐⭐⭐ |
| **v2.1** | ❌ 有Bug | 5秒 | Bash版本問題 | ⭐ |
| **v4.0** | ⚠️ 需配額 | 5秒 | CLI版本 | ⭐⭐⭐ |

---

## 💡 建議

**優先使用 v3.0**：
- 最穩定
- 功能最完整
- 自動禁用代理
- 節點詳細信息

**如需 CSV 導出，使用 v2.0**

---

**現在請在終端執行測試命令！** 🚀
