# 域名檢測腳本 v3.0 - 執行方式指南

## 🚀 兩種執行方式

---

## 方式 1：前台執行（非背景）

### 特點
- ✅ 可以直接看到實時輸出
- ✅ 可以隨時按 `Ctrl+C` 中斷
- ✅ 適合小批量測試或需要監控的情況
- ⚠️ 終端關閉會中斷執行
- ⚠️ 需要保持終端開啟

### 執行命令

```bash
# 基本執行
~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt
```

### 實時輸出示例

```
========================================
域名檢測腳本 v3.0 - 穩定版
========================================
域名文件: /Users/ckchiu/domains.txt
總域名數: 498
延遲設置: 8秒/域名
自動重試: 啟用（最多 2 輪）
========================================

=== 第一輪檢測 ===
進度: [1/498] 
🔍 檢測域名 [1/498]: example.com ...
  📍 BIZNET NETWORKS          | IP: 1.2.3.4         | [CLEAN] ✅ 正常連通 (HTTP 301)
  📍 Media Sarana Data        | IP: 1.2.3.4         | [CLEAN] ✅ 正常連通 (HTTP 301)
  📍 XL Axiata                | IP: 1.2.3.4         | [CLEAN] ✅ 正常連通 (HTTP 301)
  -> 整體狀態: CLEAN
------------------------------------------------
進度: [2/498] 
🔍 檢測域名 [2/498]: example2.com ...
...
```

### 如何中斷

```bash
# 按 Ctrl+C 中斷
# 已檢測的結果會保存在日誌文件中
```

### 適用場景

- ✅ 測試 10-50 個域名
- ✅ 需要實時監控進度
- ✅ 調試和測試腳本
- ✅ 短時間內完成的檢測

---

## 方式 2：後台執行（推薦長時間檢測）

### 特點
- ✅ 可以關閉終端，不影響執行
- ✅ 適合大批量檢測（100+ 域名）
- ✅ 可以登出系統，腳本繼續運行
- ✅ 輸出保存到文件，隨時查看
- ⚠️ 需要手動查看進度

### 執行命令

```bash
# 後台執行（推薦）
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt > ~/check.out 2>&1 &
```

### 命令解析

```bash
nohup                                              # 忽略掛斷信號
~/Desktop/Project/id_globalping_auto_retry.sh     # 腳本路徑
~/domains.txt                                      # 域名文件
> ~/check.out                                      # 標準輸出重定向到文件
2>&1                                               # 錯誤輸出也重定向到同一文件
&                                                  # 在後台執行
```

### 執行後的輸出

```bash
[1] 12345
nohup: ignoring input and appending output to 'nohup.out'
```

- `[1]`：作業編號
- `12345`：進程 ID (PID)

### 查看進度的方法

#### 1. 實時查看詳細日誌（推薦）

```bash
tail -f ~/globalping_*.log
```

輸出：
```
🔍 檢測域名 [15/498]: example.com ...
  📍 BIZNET NETWORKS          | IP: 1.2.3.4         | [CLEAN] ✅
...
```

按 `Ctrl+C` 退出查看（不會停止腳本）

#### 2. 查看標準輸出

```bash
tail -f ~/check.out
```

#### 3. 統計已處理域名數

```bash
grep "🔍 檢測域名" ~/globalping_*.log | wc -l
```

輸出：`15`（已處理 15 個域名）

#### 4. 查看最新進度

```bash
tail -20 ~/globalping_*.log
```

#### 5. 自動刷新進度（每 30 秒）

```bash
watch -n 30 'grep "🔍 檢測域名" ~/globalping_*.log | wc -l'
```

### 檢查腳本是否在運行

```bash
# 方法 1：查看進程
ps aux | grep globalping

# 方法 2：查看作業
jobs

# 方法 3：查看 PID
ps aux | grep id_globalping_auto_retry
```

### 停止後台執行

```bash
# 方法 1：使用 PID
kill 12345

# 方法 2：查找並停止
kill $(ps aux | grep "id_globalping_auto_retry" | grep -v grep | awk '{print $2}')

# 方法 3：強制停止
kill -9 $(ps aux | grep "id_globalping_auto_retry" | grep -v grep | awk '{print $2}')
```

### 適用場景

- ✅ 檢測 100+ 個域名
- ✅ 預計執行時間超過 30 分鐘
- ✅ 需要關閉終端或登出
- ✅ 定時任務（cron）
- ✅ 無人值守執行

---

## 📊 兩種方式對比

| 特性 | 前台執行 | 後台執行 |
|------|---------|---------|
| 實時輸出 | ✅ 直接顯示 | ❌ 需要查看文件 |
| 關閉終端 | ❌ 會中斷 | ✅ 繼續執行 |
| 適合域名數 | 10-50 個 | 100+ 個 |
| 監控方式 | 直接看終端 | 查看日誌文件 |
| 中斷方式 | Ctrl+C | kill 命令 |
| 輸出保存 | 僅日誌文件 | 日誌 + check.out |
| 推薦場景 | 測試/調試 | 生產環境 |

---

## 🎯 實際使用建議

### 小批量測試（10-20 個域名）

```bash
# 前台執行，直接觀察
head -20 ~/domains.txt > ~/test.txt
~/Desktop/Project/id_globalping_auto_retry.sh ~/test.txt
```

### 中批量檢測（50-100 個域名）

```bash
# 前台執行，但可以開另一個終端做其他事
~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt
```

### 大批量檢測（100+ 個域名）

```bash
# 後台執行，定期查看進度
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt > ~/check.out 2>&1 &

# 查看進度
tail -f ~/globalping_*.log
```

### 定時任務（每天自動檢測）

```bash
# 編輯 crontab
crontab -e

# 添加定時任務（每天凌晨 2 點執行）
0 2 * * * /Users/ckchiu/Desktop/Project/id_globalping_auto_retry.sh /Users/ckchiu/domains.txt > /Users/ckchiu/cron_check.log 2>&1
```

---

## 💡 進階技巧

### 1. 後台執行 + 實時監控

```bash
# 終端 1：後台執行
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt > ~/check.out 2>&1 &

# 終端 2：實時監控
tail -f ~/globalping_*.log
```

### 2. 記錄 PID 方便管理

```bash
# 執行並記錄 PID
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt > ~/check.out 2>&1 &
echo $! > ~/globalping.pid

# 稍後停止
kill $(cat ~/globalping.pid)
```

### 3. 自動通知完成

```bash
# 執行完成後發送通知（macOS）
nohup bash -c '~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt && osascript -e "display notification \"域名檢測完成\" with title \"Globalping\""' > ~/check.out 2>&1 &
```

### 4. 分批執行

```bash
# 分成 5 批，每批 100 個
split -l 100 ~/domains.txt ~/batch_

# 依次執行
for file in ~/batch_*; do
    nohup ~/Desktop/Project/id_globalping_auto_retry.sh "$file" > "${file}.out" 2>&1 &
    sleep 3600  # 每批間隔 1 小時
done
```

---

## 🔍 故障排除

### 問題 1：後台執行後找不到進程

```bash
# 檢查是否真的在運行
ps aux | grep globalping

# 檢查日誌是否有更新
ls -lt ~/globalping_*.log

# 查看錯誤輸出
cat ~/check.out
```

### 問題 2：前台執行時終端卡住

```bash
# 可能是網絡問題或 API 超時
# 按 Ctrl+C 中斷
# 查看日誌了解卡在哪裡
tail -50 ~/globalping_*.log
```

### 問題 3：後台執行但沒有輸出

```bash
# 檢查輸出文件
ls -lh ~/check.out
cat ~/check.out

# 檢查日誌文件
ls -lh ~/globalping_*.log
tail ~/globalping_*.log
```

---

## 📋 快速參考

### 前台執行

```bash
~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt
```

### 後台執行

```bash
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt > ~/check.out 2>&1 &
```

### 查看進度

```bash
tail -f ~/globalping_*.log
```

### 停止執行

```bash
# 前台：Ctrl+C
# 後台：kill $(ps aux | grep "id_globalping_auto_retry" | grep -v grep | awk '{print $2}')
```

---

## ✅ 推薦配置

**498 個域名（預計 70-90 分鐘）**：

```bash
# 使用後台執行
nohup ~/Desktop/Project/id_globalping_auto_retry.sh ~/domains.txt > ~/check.out 2>&1 &

# 開另一個終端監控
tail -f ~/globalping_*.log

# 或定期檢查進度
watch -n 60 'echo "已處理: $(grep "🔍 檢測域名" ~/globalping_*.log | wc -l)/498"'
```

這樣你可以：
- ✅ 關閉監控終端
- ✅ 做其他工作
- ✅ 隨時查看進度
- ✅ 腳本穩定運行

---

**祝檢測順利！** 🚀
