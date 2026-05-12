# Telegram Bot 配置快速指南

## 📱 你的 Bot Token

從 URL 可以看到你的 Bot Token：
```
8771241397:AAEsXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo
```

## 🆔 獲取 Chat ID

### 方法 1：使用 @userinfobot（最簡單）

1. 在 Telegram 搜尋 **@userinfobot**
2. 點擊開始或發送任意消息
3. Bot 會回覆你的 User ID（這就是 Chat ID）

### 方法 2：向你的 Bot 發送消息

1. 在 Telegram 搜尋你的 Bot（Bot 名稱）
2. 點擊 **START** 或發送任意消息（例如：`/start` 或 `hello`）
3. 再次訪問：
   ```
   https://api.telegram.org/bot8771241397:AAEsXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo/getUpdates
   ```
4. 你會看到類似這樣的回應：
   ```json
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456789,
         "message": {
           "message_id": 1,
           "from": {
             "id": 123456789,  ← 這就是你的 Chat ID
             "is_bot": false,
             "first_name": "Your Name"
           },
           "chat": {
             "id": 123456789,  ← 這也是 Chat ID
             "first_name": "Your Name",
             "type": "private"
           },
           "text": "/start"
         }
       }
     ]
   }
   ```

## 🚀 配置步驟

### 在系統終端執行：

```bash
cd ~/Desktop/Project/GlobalpingChecker
bash setup-telegram.sh
```

### 輸入資訊：

1. **Bot Token**:
   ```
   8771241397:AAEsXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo
   ```

2. **Chat ID**:
   - 先向你的 Bot 發送消息
   - 然後從 getUpdates 獲取
   - 或使用 @userinfobot 獲取

3. **Bot 名稱**（可選）:
   ```
   Globalping Checker
   ```

## 🧪 測試通知

配置完成後，執行：

```bash
bash id_globalping_multi_v3.3_Telegram.sh test_2_domains.txt
```

你會在 Telegram 收到檢測報告！

## 💡 提示

目前 `getUpdates` 返回空結果 `[]`，表示：
- ✅ Bot Token 有效
- ⚠️ 還沒有向 Bot 發送過消息

**下一步**：
1. 在 Telegram 找到你的 Bot
2. 發送 `/start` 或任意消息
3. 重新訪問 getUpdates URL 獲取 Chat ID

---

**Bot Token**: `8771241397:AAEsXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo`  
**狀態**: ✅ 有效，等待獲取 Chat ID
