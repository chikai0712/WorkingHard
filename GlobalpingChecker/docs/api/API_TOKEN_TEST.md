# 🔍 API Token 測試指南

## ⚠️ 重要：必須在系統終端執行

由於 Cursor 的代理問題，API 測試必須在系統終端執行。

## 🚀 快速測試

### 在系統終端執行：

```bash
cd ~/Desktop/Project/GlobalpingChecker
bash test-api-token.sh
```

## 📝 手動測試命令

### 測試 1：不含前綴

```bash
curl -s -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits | python3 -m json.tool
```

### 測試 2：含 gp_ 前綴

```bash
curl -s -H "Authorization: Bearer gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits | python3 -m json.tool
```

## ✅ 正確的輸出示例

```json
{
  "measurements": {
    "create": {
      "limit": 100,
      "remaining": 95,
      "reset": 1709769600
    }
  },
  "credits": {
    "remaining": 9500
  }
}
```

## 📊 額度說明

- **limit**: 每分鐘最多測量次數
- **remaining**: 剩餘次數
- **reset**: 重置時間（Unix 時間戳）
- **credits.remaining**: 本月剩餘額度

## 🔧 在 EC2 上測試

```bash
# SSH 到 EC2
ssh ec2-user@54.238.247.106

# 測試 API
curl -s -H "Authorization: Bearer uh5vlg4ttg3v5gwby5zgtqrciimahql5" \
  https://api.globalping.io/v1/limits
```

## 💡 Token 格式

根據測試結果，確定正確的格式：
- 如果測試 1 成功：使用 `uh5vlg4ttg3v5gwby5zgtqrciimahql5`
- 如果測試 2 成功：使用 `gp_uh5vlg4ttg3v5gwby5zgtqrciimahql5`

## 📝 更新腳本

確定正確格式後，更新以下文件中的 Token：
- `check-api-quota.sh`
- `id_globalping_multi_v3.3_Telegram.sh`
- `telegram-config.env`（如果需要）

---

**現在在系統終端執行 `bash test-api-token.sh` 測試 Token！**
