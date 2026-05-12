# 資源文件說明

本遊戲需要以下資源文件才能完整運行。請將對應的圖片和音樂文件放入指定目錄。

## 📁 目錄結構

```
assets/
├── images/          # 圖片資源
│   ├── background.png
│   ├── charizard.png
│   ├── blastoise.png
│   ├── venusaur.png
│   ├── garchomp.png
│   ├── kingdra.png
│   └── persian.png
└── audio/           # 音效資源
    └── bgm.mp3
```

## 🖼️ 圖片資源需求

### 背景圖片
- **檔案名稱**：`background.png`
- **建議尺寸**：800x600 像素
- **說明**：競技場背景圖

### 寶可夢圖片（小智隊伍）
1. **噴火龍** - `charizard.png`
2. **水箭龜** - `blastoise.png`
3. **妙蛙花** - `venusaur.png`

### 寶可夢圖片（電腦隊伍）
1. **烈咬陸鯊** - `garchomp.png`
2. **刺龍王** - `kingdra.png`
3. **貓老大** - `persian.png`

**圖片要求**：
- 格式：PNG（建議使用透明背景）
- 建議尺寸：至少 250x250 像素
- 程式會自動縮放到 250x250

## 🎵 音樂資源需求

### 背景音樂
- **檔案名稱**：`bgm.mp3`
- **建議來源**：Charizard's Black Sky
- **連結**：https://youtube.com/watch?v=OC_ES7__Xwc
- **格式**：MP3 或 WAV

## 📝 如何準備資源

### 方法 1：手動創建目錄
```bash
cd Pokemon-Battle-Game
mkdir -p assets/images
mkdir -p assets/audio
```

然後將圖片和音樂文件複製到對應目錄。

### 方法 2：使用命令創建（macOS/Linux）
```bash
cd Pokemon-Battle-Game
mkdir -p assets/{images,audio}
```

## ⚠️ 重要提示

1. **沒有資源文件也能運行**
   - 如果缺少圖片，遊戲會使用灰色方塊代替
   - 如果缺少音樂，遊戲會靜音運行
   - 遊戲邏輯不受影響

2. **檔案名稱必須完全一致**
   - 注意大小寫（例如：`charizard.png` 不等於 `Charizard.png`）
   - 注意副檔名（必須是 `.png` 或 `.mp3`）

3. **圖片格式建議**
   - 使用 PNG 格式以支援透明背景
   - 避免使用 JPG（會有白色背景）

## 🔍 資源來源建議

### 寶可夢圖片
- 官方寶可夢圖鑑
- Bulbapedia
- Pokémon Database
- 自行繪製或使用 AI 生成

### 背景圖片
- 使用 AI 圖片生成工具（如 DALL-E、Midjourney）
- 自行繪製
- 使用免費素材網站（注意版權）

### 音樂
- YouTube 下載（注意版權）
- 免費音樂素材網站
- 自行創作

## ✅ 檢查清單

在執行遊戲前，請確認：

- [ ] `assets/images/` 目錄已創建
- [ ] `assets/audio/` 目錄已創建
- [ ] 7 張圖片已放入 `assets/images/`
- [ ] 背景音樂已放入 `assets/audio/`
- [ ] 所有檔案名稱正確無誤

---

**準備好資源後，執行 `python main.py` 即可開始遊戲！**

