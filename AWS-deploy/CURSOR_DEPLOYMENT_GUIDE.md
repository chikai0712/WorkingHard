# 🎯 在 Cursor 中執行 AWS 部署

## ✅ 是的，現在可以了！

雖然不能直接在 Cursor 終端執行，但我創建了**自動化腳本**，讓你在 Cursor 中一鍵觸發，自動在系統終端執行。

## 🚀 快速開始

### 在 Cursor 終端執行以下命令：

```bash
cd ~/Desktop/Project/AWS-deploy
```

然後選擇你需要的操作：

---

## 📋 可用命令

### 1. 檢查 AWS 狀態

```bash
./status-from-cursor.sh
```

**功能**：
- 自動開啟系統終端
- 顯示所有 EC2 實例
- 顯示運行狀態
- 顯示成本估算

---

### 2. 部署 Globalping Checker

```bash
./deploy-from-cursor.sh
```

**功能**：
- 自動開啟系統終端
- 檢測是否有現有實例
- 選擇更新或重建
- 完成部署

---

### 3. 更新代碼

```bash
./update-from-cursor.sh
```

**功能**：
- 自動開啟系統終端
- 上傳最新代碼
- 保留配置和域名
- 快速更新

---

### 4. 管理界面

```bash
./manager-from-cursor.sh
```

**功能**：
- 自動開啟系統終端
- 顯示完整管理菜單
- 可執行所有操作

---

## 🎬 工作流程

### 典型使用場景

```bash
# 1. 在 Cursor 中編輯代碼
# （正常使用 Cursor IDE 編輯 GlobalpingChecker 代碼）

# 2. 在 Cursor 終端檢查狀態
cd ~/Desktop/Project/AWS-deploy
./status-from-cursor.sh
# → 自動開啟系統終端顯示狀態

# 3. 在 Cursor 終端執行更新
./update-from-cursor.sh
# → 自動開啟系統終端執行更新

# 4. 完成！
# 新視窗會顯示更新結果
```

---

## 📊 命令對比

| 操作 | Cursor 中執行 | 效果 |
|------|--------------|------|
| **檢查狀態** | `./status-from-cursor.sh` | 開啟終端顯示狀態 |
| **部署服務** | `./deploy-from-cursor.sh` | 開啟終端執行部署 |
| **更新代碼** | `./update-from-cursor.sh` | 開啟終端更新代碼 |
| **管理界面** | `./manager-from-cursor.sh` | 開啟終端管理菜單 |

---

## 💡 優勢

### ✅ 在 Cursor 中操作
- 不需要手動切換到系統終端
- 一行命令自動執行
- 保持在 Cursor 工作流程中

### ✅ 自動處理代理
- 腳本自動禁用代理
- 在系統終端執行，避免 Cursor 代理
- 100% 可靠

### ✅ 視覺化反饋
- 自動開啟新終端視窗
- 實時顯示執行進度
- 完成後可查看結果

---

## 🔧 進階使用

### 批量操作

```bash
# 檢查狀態 → 更新代碼 → 再次檢查
cd ~/Desktop/Project/AWS-deploy
./status-from-cursor.sh && sleep 2 && ./update-from-cursor.sh && sleep 2 && ./status-from-cursor.sh
```

### 自定義操作

如果需要執行其他 AWS 命令，使用管理界面：

```bash
./manager-from-cursor.sh
```

然後在開啟的終端中選擇操作。

---

## 📝 示例：完整部署流程

### 場景：首次部署 Globalping Checker

```bash
# 步驟 1：在 Cursor 終端執行
cd ~/Desktop/Project/AWS-deploy
./deploy-from-cursor.sh
```

**會發生什麼**：
1. Cursor 顯示：「✅ 已在系統終端開啟部署程序」
2. 自動開啟新的終端視窗
3. 在新視窗中執行部署
4. 你可以看到實時進度

**在新視窗中**：
```
🚀 開始部署 Globalping Checker 到 AWS EC2...
✅ 找到現有實例: i-xxxxx
   狀態: stopped
   IP: 18.182.6.127

請選擇操作：
  1) 更新現有實例（推薦）
  2) 刪除並重新部署
  3) 取消

選擇 (1-3): 1

🔄 更新現有實例...
⏳ 啟動實例...
✅ 實例已啟動: 18.182.6.127
📤 上傳最新代碼...
🎉 更新完成！
```

---

## 🎯 最佳實踐

### 日常開發

1. **在 Cursor 中編輯代碼**
   - 修改 `GlobalpingChecker/*.sh`
   - 編輯配置文件

2. **在 Cursor 終端執行更新**
   ```bash
   ./update-from-cursor.sh
   ```

3. **查看結果**
   - 在自動開啟的終端查看更新進度
   - 完成後可以關閉終端

### 定期檢查

```bash
# 每天檢查一次狀態
./status-from-cursor.sh
```

### 成本控制

```bash
# 使用管理界面停止不用的實例
./manager-from-cursor.sh
# 選擇選項 11（停止所有服務）
```

---

## ❓ 常見問題

### Q: 為什麼不能直接在 Cursor 終端執行？

A: Cursor 會自動設置代理，阻止 AWS CLI 連線。這些腳本會自動在系統終端執行，繞過代理。

### Q: 會開啟很多終端視窗嗎？

A: 每次執行會開啟一個新視窗，完成後可以關閉。或者使用 `./manager-from-cursor.sh` 只開啟一個視窗執行所有操作。

### Q: 可以看到執行進度嗎？

A: 可以！所有操作都會在新開啟的終端視窗中實時顯示進度。

### Q: 如果出錯怎麼辦？

A: 錯誤信息會顯示在終端視窗中，可以查看詳細錯誤並根據提示解決。

---

## 🎉 總結

**是的，你現在可以在 Cursor 中執行 AWS 部署了！**

只需要在 Cursor 終端執行：

```bash
cd ~/Desktop/Project/AWS-deploy

# 檢查狀態
./status-from-cursor.sh

# 部署服務
./deploy-from-cursor.sh

# 更新代碼
./update-from-cursor.sh

# 管理界面
./manager-from-cursor.sh
```

所有操作都會自動在系統終端執行，你只需要在 Cursor 中輸入命令即可！🚀

---

**創建時間**: 2026-03-07  
**適用於**: Cursor IDE + macOS
