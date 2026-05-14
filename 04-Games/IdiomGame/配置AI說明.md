# 🤖 AI 圖片生成配置說明

## 快速配置

### 方法 1：在瀏覽器控制台配置（推薦）

打開瀏覽器開發者工具（F12），在 Console 中輸入：

```javascript
// 配置 OpenAI DALL-E 3
pictureGenerator.configureAI(
    'your-openai-api-key',
    'https://api.openai.com/v1/images/generations'
);
```

### 方法 2：修改 script.js

在 `script.js` 文件中找到這一行：

```javascript
const pictureGenerator = new IdiomPictureGenerator();
```

在下面添加：

```javascript
// 配置 AI 圖片生成（取消註釋並填入你的 API Key）
pictureGenerator.configureAI(
    'your-openai-api-key',
    'https://api.openai.com/v1/images/generations'
);
```

## 獲取 API Key

### OpenAI DALL-E 3

1. 訪問 https://platform.openai.com/
2. 註冊/登入帳號
3. 前往 API Keys 頁面
4. 創建新的 API Key
5. 複製 API Key

**注意**：DALL-E 3 需要付費，按圖片數量計費。

### Stable Diffusion (Stability AI)

1. 訪問 https://platform.stability.ai/
2. 註冊帳號
3. 獲取 API Key
4. 使用端點：`https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image`

## 確保生成卡通/漫畫風格

### 提示詞已優化

系統已經自動在提示詞中添加了以下關鍵詞：
- ✅ **卡通漫畫風格**
- ✅ **簡筆畫**
- ✅ **可愛風格**
- ✅ **兒童繪本插圖**

### DALL-E 3 設置

系統已自動設置：
- Model: `dall-e-3`
- Style: `vivid` (更適合卡通)
- Size: `1024x1024`

### 如果生成的圖片仍然不是卡通風格

1. **檢查提示詞**：在瀏覽器控制台查看實際發送的提示詞
   ```javascript
   console.log(pictureGenerator.createPicturePrompt('一石二鳥'));
   ```

2. **手動調整提示詞**：修改 `picture-generator.js` 中的 `createPicturePrompt` 方法

3. **使用負面提示詞**（如果 API 支援）：
   ```
   不要：realistic, photograph, 3D render, hyperrealistic
   ```

## 測試配置

配置完成後，測試是否正常工作：

```javascript
// 測試生成圖片
pictureGenerator.generatePicture('一石二鳥').then(url => {
    console.log('生成的圖片:', url);
    // 應該看到一個圖片 URL 或 base64 數據
});
```

## 常見問題

### Q: 提示詞已經包含卡通風格，為什麼還是生成寫實圖片？

A: 可能的原因：
1. API 沒有正確配置（檢查 `useAIGeneration` 是否為 `true`）
2. API Key 無效或過期
3. API 端點錯誤
4. 某些 AI 模型對中文提示詞理解不佳

**解決方案**：
- 使用英文提示詞（可以修改 `createPicturePrompt` 方法）
- 嘗試不同的 AI 服務
- 檢查 API 響應中的錯誤訊息

### Q: 如何查看實際發送的提示詞？

A: 打開瀏覽器開發者工具（F12），查看 Console，系統會自動輸出：
- `🎨 AI 生成提示詞: ...`
- `📤 發送 AI 請求: ...`
- `✅ AI 生成成功: ...` 或 `❌ AI 圖片生成失敗: ...`

### Q: 可以使用免費的 AI 圖片生成服務嗎？

A: 目前沒有完全免費的商業 AI 圖片生成服務。可以考慮：
1. 使用本地 Stable Diffusion（需要較強的 GPU）
2. 使用免費額度（如 OpenAI 新用戶贈送額度）
3. 繼續使用 Canvas 簡單繪圖（無需 API）

## 提示詞範例

查看 `prompt-examples.md` 獲取更多提示詞範例和優化建議。

