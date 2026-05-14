# AI 圖片生成整合指南

## 概述

目前的圖片生成器使用簡單的 Canvas 繪圖來生成成語圖片。你可以輕鬆整合 AI 圖片生成 API 來生成更精美的圖片或漫畫。

## 支援的 AI 服務

### 1. OpenAI DALL-E

```javascript
// 在 script.js 中配置
pictureGenerator.configureAI(
    'your-openai-api-key',
    'https://api.openai.com/v1/images/generations'
);

// 在 picture-generator.js 中的 generateAIPicture 方法中實現：
const response = await fetch(this.apiEndpoint, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
    },
    body: JSON.stringify({
        prompt: prompt,
        n: 1,
        size: "512x512"
    })
});

const data = await response.json();
return data.data[0].url;
```

### 2. Stable Diffusion API

```javascript
pictureGenerator.configureAI(
    'your-stable-diffusion-api-key',
    'https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image'
);

const response = await fetch(this.apiEndpoint, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
    },
    body: JSON.stringify({
        text_prompts: [{ text: prompt }],
        cfg_scale: 7,
        height: 512,
        width: 512,
        steps: 30
    })
});
```

### 3. Midjourney (透過 API)

```javascript
// 根據 Midjourney API 文檔配置
pictureGenerator.configureAI(
    'your-midjourney-api-key',
    'your-midjourney-endpoint'
);
```

## 使用方式

### 方法 1：直接配置（推薦）

在 `script.js` 中添加：

```javascript
// 配置 AI 圖片生成（可選）
// pictureGenerator.configureAI('your-api-key', 'api-endpoint');

// 如果不配置，將使用簡單的 Canvas 繪圖
```

### 方法 2：動態配置

在遊戲中提供配置界面，讓用戶輸入 API Key。

## 提示詞優化（確保卡通/漫畫風格）

已優化的提示詞模板，確保生成卡通或漫畫風格：

```javascript
createPicturePrompt(idiom) {
    // 基礎提示詞
    let prompt = `${idiom}的場景`;
    
    // 強制性風格描述（確保卡通/漫畫風格）
    const style = '，卡通漫畫風格，簡筆畫，可愛幽默風格，線條清晰，黑白或彩色，適合兒童教育，類似兒童繪本插圖';
    
    return prompt + style;
}
```

### 關鍵風格關鍵詞

為了確保生成卡通/漫畫風格，提示詞中必須包含：

- **卡通漫畫風格** - 明確指定風格
- **簡筆畫** - 簡單線條
- **可愛風格** - 適合兒童
- **兒童繪本插圖** - 參考風格
- **線條清晰** - 視覺效果

### DALL-E 3 特定設置

```javascript
{
    model: "dall-e-3",  // 使用 DALL-E 3
    style: "vivid",      // vivid 風格更適合卡通
    quality: "standard"
}
```

### Stable Diffusion 特定設置

```javascript
{
    style_preset: "comic-book",  // 使用漫畫風格預設
    cfg_scale: 7,                // 控制風格強度
}
```

## 注意事項

1. **API 費用**：AI 圖片生成通常需要付費
2. **生成速度**：AI 生成可能需要幾秒到幾十秒
3. **緩存**：建議緩存生成的圖片，避免重複生成
4. **錯誤處理**：如果 AI 生成失敗，會自動回退到簡單繪圖

## 實現圖片緩存

```javascript
class IdiomPictureGenerator {
    constructor() {
        this.pictureCache = new Map();
    }

    async generatePicture(idiom) {
        // 檢查緩存
        if (this.pictureCache.has(idiom)) {
            return this.pictureCache.get(idiom);
        }

        let pictureData;
        if (this.useAIGeneration) {
            pictureData = await this.generateAIPicture(idiom);
        } else {
            pictureData = this.generateSimplePicture(idiom);
        }

        // 保存到緩存
        this.pictureCache.set(idiom, pictureData);
        return pictureData;
    }
}
```

## 本地圖片替代方案

如果不想使用 AI API，可以：

1. 手動準備成語圖片
2. 將圖片放在 `images/` 資料夾
3. 修改 `generatePicture` 方法：

```javascript
generatePicture(idiom) {
    // 優先使用本地圖片
    const localImage = `images/${idiom}.png`;
    // 如果存在，返回本地圖片路徑
    // 否則使用 Canvas 繪圖
    return this.generateSimplePicture(idiom);
}
```

