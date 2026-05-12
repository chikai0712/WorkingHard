# AI 圖片生成提示詞範例

## 確保生成卡通/漫畫風格的提示詞模板

### 基本模板

```
{成語場景描述}，卡通漫畫風格，簡筆畫，可愛幽默風格，線條清晰，黑白或彩色，適合兒童教育，類似兒童繪本插圖
```

### 具體成語範例

#### 一石二鳥
```
一隻鳥扔石頭打中兩隻鳥，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育，類似兒童繪本插圖
```

#### 畫蛇添足
```
一條蛇被畫上多餘的腳，卡通漫畫風格，簡筆畫，幽默風格，線條清晰，適合兒童教育，類似兒童繪本插圖
```

#### 守株待兔
```
一個人在樹樁旁邊等待兔子，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育，類似兒童繪本插圖
```

## 不同 AI 服務的優化提示詞

### OpenAI DALL-E 3

**推薦設置：**
- Model: `dall-e-3`
- Style: `vivid` (更適合卡通)
- Quality: `standard`

**提示詞格式：**
```
{場景描述}，卡通風格，簡筆畫，可愛，線條清晰，兒童繪本風格，vivid colors
```

### Stable Diffusion

**推薦設置：**
- Style Preset: `comic-book` 或 `anime`
- Negative Prompt: `realistic, photograph, 3D render`

**提示詞格式：**
```
{場景描述}, cartoon style, simple line drawing, cute, clear lines, children's book illustration, comic book style
```

### Midjourney

**推薦設置：**
- Style: `--style cute` 或 `--style expressive`
- Quality: `--q 1`

**提示詞格式：**
```
{場景描述}, cartoon style, simple line art, cute illustration, children's book style --style cute --v 6
```

## 負面提示詞（Negative Prompt）

使用負面提示詞可以避免生成寫實風格：

```
realistic, photograph, 3D render, hyperrealistic, photorealistic, detailed shading, complex lighting
```

## 測試建議

1. **先測試簡單提示詞**：確認 API 連接正常
2. **逐步添加風格關鍵詞**：觀察效果變化
3. **調整風格強度**：根據結果微調
4. **保存成功的提示詞**：建立提示詞庫

## 常見問題

### Q: 生成的圖片太寫實？
A: 添加更多風格關鍵詞，如「卡通風格」、「簡筆畫」、「兒童繪本」

### Q: 生成的圖片太複雜？
A: 強調「簡筆畫」、「線條清晰」、「簡單風格」

### Q: 顏色太單調？
A: 添加「vivid colors」、「鮮豔色彩」、「彩色插圖」

