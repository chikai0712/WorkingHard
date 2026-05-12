# 腳本版本對比分析

## 📊 詳細對比表

| 特性 | v2.0 | v2.1 | v3.0 | v4.0 |
|------|------|------|------|------|
| **文件路徑** | ~/id_globalping_multi_v2.sh | ~/id_globalping_multi_v2.1.sh | ~/Desktop/Project/id_globalping_auto_retry.sh | ~/Desktop/Project/id_globalping_cli.sh |
| **延遲時間** | 4 秒 | 5 秒 | 8 秒 | 5 秒 |
| **批次大小** | 50 個 | 40 個 | 30 個 | 30 個 |
| **批次休息** | 30 秒 | 45 秒 | 60 秒 | 45 秒 |
| **API 等待** | 8 秒 | 10 秒 | 8 秒 | N/A (CLI) |
| **自動重試** | ✅ | ✅ | ✅ | ✅ |
| **重試輪數** | 未知 | 2 輪 | 2 輪 | 2 輪 |
| **禁用代理** | ❌ | ❌ | ✅ | ❌ |
| **PARTIAL 二次檢測** | ❌ | ❌ | ✅ | ✅ |
| **節點詳細信息** | ❌ | ❌ | ✅ (ASN/城市/節點IP) | ✅ (ASN/城市) |
| **CSV 導出** | ✅ | ✅ | ❌ | ❌ |
| **使用方式** | API 直接調用 | API 直接調用 | API 直接調用 | Globalping CLI |
| **腳本行數** | ~500 行 | 640 行 | ~350 行 | ~200 行 |

---

## 🎯 版本評分

### v2.0 - 改進版
**評分**: ⭐⭐⭐⭐ (4/5)

**優點**:
- ✅ 完整的狀態分類
- ✅ CSV 導出功能
- ✅ 自動重試機制
- ✅ 已驗證可用

**缺點**:
- ❌ 延遲較短（4秒，容易觸發限制）
- ❌ 無代理處理
- ❌ 無節點詳細信息

**適用場景**: 需要 CSV 導出，API 配額充足

---

### v2.1 - 自動重試版
**評分**: ⭐⭐⭐⭐ (4/5)

**優點**:
- ✅ 延遲增加到 5 秒
- ✅ API 等待時間增加到 10 秒
- ✅ 批次控制更保守（40個/批，45秒休息）
- ✅ 自動重試 2 輪
- ✅ CSV 導出功能
- ✅ 更完善的錯誤處理

**缺點**:
- ❌ 無代理處理（可能遇到 403 錯誤）
- ❌ 無 PARTIAL 二次檢測
- ❌ 無節點詳細信息

**適用場景**: 需要 CSV 導出，比 v2.0 更穩定

---

### v3.0 - 穩定版 ⭐ 推薦
**評分**: ⭐⭐⭐⭐⭐ (5/5)

**優點**:
- ✅ 延遲最長（8秒，最穩定）
- ✅ 批次控制最保守（30個/批，60秒休息）
- ✅ **自動禁用代理**（避免 403 錯誤）
- ✅ **PARTIAL 二次檢測**（提高準確性）
- ✅ **節點詳細信息**（ASN、城市、節點IP、目標IP）
- ✅ 自動重試 2 輪
- ✅ 代碼更簡潔（350行）

**缺點**:
- ❌ 無 CSV 導出（但日誌更詳細）
- ⚠️ 速度較慢（因為延遲長）

**適用場景**: **大批量檢測、長期使用、最穩定可靠**

---

### v4.0 - CLI 版本
**評分**: ⭐⭐⭐ (3/5)

**優點**:
- ✅ 使用官方 CLI（理論上更穩定）
- ✅ 代碼最簡潔（200行）
- ✅ 節點詳細信息

**缺點**:
- ❌ **需要 API 配額**（免費配額很快用完）
- ❌ 需要註冊帳號才能長期使用
- ❌ 無 CSV 導出

**適用場景**: 已註冊帳號，有充足配額

---

## 🏆 推薦排名

### 1. v3.0 - 穩定版 ⭐⭐⭐⭐⭐
**最推薦！**

```bash
~/Desktop/Project/id_globalping_auto_retry.sh ~/Documents/domains.txt
```

**為什麼選 v3.0？**
- 最穩定（延遲 8 秒 + 禁用代理）
- 功能最完整（PARTIAL 二次檢測 + 節點詳細信息）
- 最不容易觸發 API 限制
- 適合大批量檢測（498 個域名）

---

### 2. v2.1 - 自動重試版 ⭐⭐⭐⭐
**次選！**

```bash
~/id_globalping_multi_v2.1.sh ~/Documents/domains.txt
```

**為什麼選 v2.1？**
- 比 v2.0 更穩定（延遲 5 秒，API 等待 10 秒）
- 有 CSV 導出（方便後續分析）
- 自動重試 2 輪
- 批次控制更保守

**注意**: 可能遇到代理問題，需要手動禁用代理：
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
~/id_globalping_multi_v2.1.sh ~/Documents/domains.txt
```

---

### 3. v2.0 - 改進版 ⭐⭐⭐⭐
**備選！**

```bash
~/id_globalping_multi_v2.sh ~/Documents/domains.txt
```

**為什麼選 v2.0？**
- 已驗證可用
- 有 CSV 導出
- 速度較快（延遲 4 秒）

**注意**: 延遲較短，更容易觸發 API 限制

---

### 4. v4.0 - CLI 版本 ⭐⭐⭐
**需要配額！**

```bash
~/Desktop/Project/id_globalping_cli.sh ~/Documents/domains.txt
```

**為什麼選 v4.0？**
- 官方 CLI，理論上更穩定
- 代碼簡潔

**限制**: 需要註冊帳號或等待配額重置

---

## 💡 使用建議

### 場景 1: 大批量檢測（498 個域名）
**推薦**: v3.0
```bash
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/Documents/domains.txt > ~/check.out 2>&1 &
```

### 場景 2: 需要 CSV 導出
**推薦**: v2.1
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
~/id_globalping_multi_v2.1.sh ~/Documents/domains.txt
```

### 場景 3: 快速測試（10-20 個域名）
**推薦**: v2.0 或 v2.1
```bash
~/id_globalping_multi_v2.sh ~/test_20.txt
```

### 場景 4: 已註冊帳號
**推薦**: v4.0
```bash
globalping auth --token YOUR_TOKEN
~/Desktop/Project/id_globalping_cli.sh ~/Documents/domains.txt
```

---

## 📊 速度對比（498 個域名）

| 版本 | 預計時間 | 說明 |
|------|---------|------|
| v2.0 | 40-50 分鐘 | 最快，但容易觸發限制 |
| v2.1 | 50-60 分鐘 | 較快，較穩定 |
| v3.0 | 70-90 分鐘 | 較慢，最穩定 |
| v4.0 | 45-55 分鐘 | 中等，需要配額 |

---

## 🎯 最終建議

**如果你要檢測 498 個域名**：

1. ✅ **首選 v3.0**（最穩定、功能最完整）
2. ✅ **次選 v2.1**（如果需要 CSV 導出）
3. ⚠️ **等待 20 分鐘**（讓 API 配額重置）

**執行命令**：
```bash
# 20 分鐘後自動執行 v3.0
nohup bash -c 'sleep 1200 && ~/Desktop/Project/id_globalping_auto_retry.sh ~/Documents/domains.txt' > ~/check.out 2>&1 &

# 或立即執行 v2.1（需要手動禁用代理）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
nohup ~/id_globalping_multi_v2.1.sh ~/Documents/domains.txt > ~/check_v21.out 2>&1 &
```

---

**總結**: v3.0 > v2.1 > v2.0 > v4.0（當前情況）
