# 🎀 三麗鷗爆米花大遊行 - 完整遊戲規劃

**遊戲名稱**：《三麗鷗爆米花大遊行》  
**遊戲類型**：多階段連鎖反應 + 節奏操作  
**開發技術**：HTML5 + CSS3 + JavaScript（網頁遊戲）  
**目標平台**：桌面瀏覽器 + 手機瀏覽器  
**規劃日期**：2026-02-08

---

## 🎯 遊戲核心概念

玩家扮演「三麗鷗爆米花工廠」的總指揮，需要同時管理四個生產階段，確保爆米花生產線順暢運作。每個階段由不同的三麗鷗角色負責，玩家需要快速切換操作，創造完美的連鎖反應。

**核心玩法**：多任務管理 + 節奏操作 + 連鎖反應

---

## 🌟 四大生產階段

### 階段 1：大耳狗（Cinnamoroll）- 原料接取
**位置**：畫面最上方  
**角色動作**：左右移動接玉米

#### 操作方式
- **桌面版**：滑鼠左右移動 / 鍵盤 ← → 鍵
- **手機版**：手指左右滑動

#### 遊戲機制
```javascript
// 玉米掉落系統
{
  goodCorn: {
    probability: 70%,    // 好玉米機率
    points: +10,         // 得分
    effect: "正常"
  },
  goldenCorn: {
    probability: 20%,    // 金色玉米（加分）
    points: +30,
    effect: "下一階段速度加快"
  },
  badCorn: {
    probability: 8%,     // 壞玉米
    points: -5,
    effect: "大耳狗暈眩 2 秒"
  },
  rock: {
    probability: 2%,     // 石頭
    points: -10,
    effect: "大耳狗暈眩 3 秒 + 籃子破裂"
  }
}
```

#### 難度設計
| 關卡 | 掉落速度 | 同時掉落數 | 壞物品機率 |
|------|---------|-----------|-----------|
| 1-5  | 1.5秒/個 | 1個 | 5% |
| 6-10 | 1.0秒/個 | 1-2個 | 10% |
| 11-15| 0.8秒/個 | 2個 | 15% |
| 16+  | 0.5秒/個 | 2-3個 | 20% |

#### 視覺效果
- 大耳狗：可愛的飛行動畫，籃子會隨著玉米數量變重
- 好玉米：金黃色，閃閃發光
- 金色玉米：帶星星特效
- 壞玉米：黑色，冒煙
- 石頭：灰色，有裂紋

---

### 階段 2：庫洛米（Kuromi）- 魔法加熱
**位置**：畫面中上方  
**角色動作**：攪拌大鍋，施展魔法

#### 操作方式
- **桌面版**：快速點擊滑鼠 / 空白鍵連打
- **手機版**：快速點擊螢幕

#### 遊戲機制
```javascript
// 溫度控制系統
{
  temperature: {
    min: 0,
    max: 100,
    perfect: 60-80,      // 黃金區間
    clickIncrease: +5,   // 每次點擊增加
    autoDecrease: -2/s   // 自動降溫
  },
  results: {
    tooLow: "爆不開（< 50）",
    perfect: "完美爆米花（60-80）",
    tooHigh: "燒焦（> 90）"
  }
}
```

#### 溫度計 UI 設計
```
[冷] ====|====|====|====|==== [熱]
  0    25   50   75   100
         [黃金區間: 60-80]
```

#### 特殊機制
- **連擊系統**：連續 10 次點擊在黃金區間 → 觸發「完美爆發」
- **完美爆發效果**：
  - 一次產出 2倍 爆米花
  - 畫面出現紫色魔法特效
  - 庫洛米會說「Perfect!」

#### 難度設計
| 關卡 | 黃金區間寬度 | 降溫速度 | 需要點擊數 |
|------|------------|---------|-----------|
| 1-5  | 30 (50-80) | -1/s | 15次 |
| 6-10 | 20 (60-80) | -2/s | 20次 |
| 11-15| 15 (62-77) | -3/s | 25次 |
| 16+  | 10 (65-75) | -4/s | 30次 |

---

### 階段 3：布丁狗（Pompompurin）- 精準包裝
**位置**：畫面中下方  
**角色動作**：接住爆米花並包裝

#### 操作方式
- **桌面版**：看準時機按空白鍵 / 點擊
- **手機版**：點擊螢幕

#### 遊戲機制（節奏遊戲）
```javascript
// 節奏判定系統
{
  timing: {
    perfect: "±50ms",    // 完美：+20分
    great: "±100ms",     // 很好：+15分
    good: "±150ms",      // 好：+10分
    miss: "> 150ms"      // 失誤：0分，爆米花掉地
  },
  combo: {
    multiplier: "每5連擊 +10%分數",
    maxCombo: "50連擊"
  }
}
```

#### 爆米花飛行模式
```javascript
// 三種飛行模式（隨機）
{
  straight: {
    speed: "固定速度直線飛來",
    difficulty: "簡單"
  },
  wave: {
    speed: "波浪形飛來",
    difficulty: "中等"
  },
  random: {
    speed: "忽快忽慢 + 曲線",
    difficulty: "困難"
  }
}
```

#### 視覺效果
- **判定特效**：
  - Perfect：金色光圈 + "Perfect!" 文字
  - Great：銀色光圈 + "Great!" 文字
  - Good：銅色光圈 + "Good!" 文字
  - Miss：紅色 X + 爆米花掉地動畫

#### 連擊顯示
```
Combo: 15
Score Multiplier: x1.3
```

---

### 階段 4：美樂蒂（My Melody）- 裝箱送餐
**位置**：畫面最下方  
**角色動作**：將爆米花裝箱並送給客人

#### 操作方式
- **桌面版**：拖曳爆米花到紙箱
- **手機版**：拖曳爆米花到紙箱

#### 遊戲機制
```javascript
// 客人系統
{
  customers: [
    {
      name: "Hello Kitty",
      patience: 30秒,
      order: 6個爆米花,
      tip: 100分
    },
    {
      name: "Keroppi",
      patience: 20秒,
      order: 4個爆米花,
      tip: 80分
    },
    {
      name: "Bad Badtz-Maru",
      patience: 15秒,
      order: 3個爆米花,
      tip: 60分
    }
  ]
}
```

#### 耐心條系統
```
[客人頭像] [████████░░] 80% (24秒剩餘)
           訂單：6個爆米花
```

- **綠色（100-60%）**：客人開心
- **黃色（60-30%）**：客人不耐煩
- **紅色（30-0%）**：客人生氣，即將離開

#### 特殊機制
- **快速服務獎勵**：在耐心條 > 80% 完成 → 獎勵 2倍 分數
- **完美服務**：連續服務 5 位客人不失誤 → 觸發「VIP 客人」
- **VIP 客人**：
  - 雙子星（Little Twin Stars）出現
  - 訂單量大（10個）
  - 獎勵超高（500分）

---

## 🔥 Fever Time（夢幻合作模式）

### 觸發條件
連續成功完成 **10 組爆米花**（從接玉米到送給客人）

### 持續時間
**15 秒**

### 特殊效果

#### 視覺效果
- 背景變成閃亮的舞台燈光（粉紅 + 紫色漸變）
- 所有角色周圍出現星星特效
- 畫面邊緣出現彩虹光暈
- BGM 切換為快節奏版本

#### 遊戲效果
```javascript
{
  stage1: "大耳狗飛行速度 +50%，自動吸引玉米",
  stage2: "庫洛米自動維持完美溫度，產出 2倍 爆米花",
  stage3: "所有爆米花自動完美包裝（Perfect判定）",
  stage4: "客人耐心條凍結，不會減少",
  score: "所有分數 x3"
}
```

#### Fever Time 計量表
```
Fever Meter: [████████░░] 80%
還需 2 組完美爆米花觸發 Fever Time!
```

---

## 🎮 操作控制總覽

### 桌面版（鍵盤 + 滑鼠）
```
階段切換：
- Tab 鍵：切換到下一個階段
- 1/2/3/4 鍵：直接跳到對應階段

階段 1（大耳狗）：
- ← → 方向鍵：移動
- 滑鼠移動：移動

階段 2（庫洛米）：
- 空白鍵連打：加熱
- 滑鼠連點：加熱

階段 3（布丁狗）：
- 空白鍵：包裝
- 滑鼠點擊：包裝

階段 4（美樂蒂）：
- 滑鼠拖曳：裝箱
```

### 手機版（觸控）
```
階段切換：
- 點擊角色頭像：切換階段

階段 1：左右滑動
階段 2：快速點擊
階段 3：點擊螢幕
階段 4：拖曳爆米花
```

---

## 📊 遊戲數值設計

### 關卡難度曲線

| 關卡 | 玉米速度 | 加熱難度 | 飛行模式 | 客人耐心 | 目標分數 |
|------|---------|---------|---------|---------|---------|
| 1    | 慢 | 寬容 | 直線 | 30秒 | 500 |
| 5    | 中慢 | 寬容 | 直線 | 25秒 | 1,000 |
| 10   | 中 | 普通 | 直線+波浪 | 20秒 | 2,000 |
| 15   | 中快 | 困難 | 波浪+隨機 | 15秒 | 3,500 |
| 20   | 快 | 很難 | 隨機 | 12秒 | 5,000 |
| 25+  | 極快 | 極難 | 隨機+多重 | 10秒 | 7,000+ |

### 分數系統
```javascript
{
  // 階段 1
  goodCorn: +10,
  goldenCorn: +30,
  
  // 階段 2
  perfectHeat: +50,
  goodHeat: +20,
  
  // 階段 3
  perfect: +20,
  great: +15,
  good: +10,
  combo: "每5連擊 +10%",
  
  // 階段 4
  normalService: +100,
  fastService: +200,
  vipService: +500,
  
  // Fever Time
  feverMultiplier: "x3"
}
```

### 星級評價
```
★☆☆ (1星)：完成關卡
★★☆ (2星)：達到目標分數
★★★ (3星)：達到目標分數 + 零失誤
```

---

## 🎨 視覺設計規範

### 色彩方案
```css
/* 主色調 - 三麗鷗粉嫩風格 */
--primary-pink: #FFB7D5;
--primary-blue: #A8D8EA;
--primary-yellow: #FFF4A3;
--primary-purple: #D4A5D4;

/* 角色專屬色 */
--cinnamoroll: #A8D8EA;  /* 大耳狗 - 天藍色 */
--kuromi: #8B5A8E;       /* 庫洛米 - 深紫色 */
--pompompurin: #F9C74F;  /* 布丁狗 - 金黃色 */
--mymelody: #FFB7D5;     /* 美樂蒂 - 粉紅色 */

/* 功能色 */
--success: #90EE90;      /* 成功 - 淺綠 */
--warning: #FFD700;      /* 警告 - 金色 */
--danger: #FF6B6B;       /* 危險 - 紅色 */
--perfect: #FFD700;      /* 完美 - 金色 */
```

### UI 元素設計

#### 遊戲畫面布局
```
┌─────────────────────────────────────┐
│  分數: 1,250  關卡: 5  Fever: 80%  │ ← 頂部狀態欄
├─────────────────────────────────────┤
│  [大耳狗區域] 🐶 ← 玉米掉落        │ ← 階段1 (25%)
├─────────────────────────────────────┤
│  [庫洛米區域] 😈 ← 溫度計          │ ← 階段2 (25%)
├─────────────────────────────────────┤
│  [布丁狗區域] 🐶 ← 爆米花飛來      │ ← 階段3 (25%)
├─────────────────────────────────────┤
│  [美樂蒂區域] 🐰 ← 客人排隊        │ ← 階段4 (25%)
└─────────────────────────────────────┘
```

#### 角色動畫狀態
```javascript
{
  idle: "待機動畫（呼吸、眨眼）",
  working: "工作動畫（移動、攪拌、包裝）",
  success: "成功動畫（跳躍、比讚）",
  fail: "失敗動畫（暈眩、哭泣）",
  fever: "Fever動畫（閃光、特效）"
}
```

---

## 🎵 音效與音樂設計

### 背景音樂（BGM）
```javascript
{
  mainMenu: "輕快的三麗鷗主題曲",
  gameplay: "節奏感強的工廠音樂",
  feverTime: "快節奏電子音樂",
  victory: "勝利慶祝音樂",
  gameOver: "溫柔的安慰音樂"
}
```

### 音效（SFX）
```javascript
{
  // 階段 1
  cornDrop: "滴答聲",
  cornCatch: "叮！",
  badCornHit: "咚！+ 暈眩音效",
  
  // 階段 2
  click: "噗滋",
  perfectHeat: "叮叮叮！",
  burnSound: "嘶嘶嘶...",
  
  // 階段 3
  perfect: "Perfect! + 鈴聲",
  great: "Great! + 鼓聲",
  good: "Good! + 拍手",
  miss: "啊！+ 掉落聲",
  
  // 階段 4
  boxFull: "咔嚓！",
  customerHappy: "Happy! + 笑聲",
  customerAngry: "哼！+ 生氣聲",
  
  // 特殊
  feverStart: "Fever Time! + 歡呼",
  comboSound: "連擊音效（越高越激昂）"
}
```

### 語音（Voice）
```javascript
{
  cinnamoroll: "Yay!",
  kuromi: "Perfect!",
  pompompurin: "Nice!",
  mymelody: "Thank you!"
}
```

---

## 🏆 成就系統

### 基礎成就
```javascript
[
  {
    id: "first_popcorn",
    name: "第一份爆米花",
    description: "完成第一組爆米花",
    reward: "解鎖大耳狗貼紙"
  },
  {
    id: "perfect_10",
    name: "完美十連",
    description: "連續10次Perfect判定",
    reward: "解鎖布丁狗貼紙"
  },
  {
    id: "fever_master",
    name: "Fever達人",
    description: "觸發10次Fever Time",
    reward: "解鎖庫洛米貼紙"
  },
  {
    id: "speed_demon",
    name: "閃電服務",
    description: "5秒內完成一組爆米花",
    reward: "解鎖美樂蒂貼紙"
  }
]
```

### 進階成就
```javascript
[
  {
    id: "no_miss",
    name: "零失誤大師",
    description: "完成一個關卡零失誤",
    reward: "解鎖Hello Kitty特別造型"
  },
  {
    id: "combo_50",
    name: "連擊之王",
    description: "達成50連擊",
    reward: "解鎖彩虹爆米花特效"
  },
  {
    id: "stage_20",
    name: "工廠老闆",
    description: "通過第20關",
    reward: "解鎖無限模式"
  }
]
```

---

## 📱 技術實現方案

### 技術棧
```javascript
{
  frontend: "HTML5 + CSS3 + JavaScript (ES6+)",
  canvas: "HTML5 Canvas API（遊戲渲染）",
  audio: "Web Audio API（音效管理）",
  storage: "LocalStorage（進度保存）",
  framework: "原生 JavaScript（無框架，輕量化）"
}
```

### 檔案結構
```
Sanrio-Popcorn-Game/
├── index.html              # 主頁面
├── css/
│   ├── styles.css          # 主樣式
│   ├── animations.css      # 動畫效果
│   └── responsive.css      # 響應式設計
├── js/
│   ├── main.js             # 主程序
│   ├── game.js             # 遊戲邏輯
│   ├── stage1.js           # 階段1（大耳狗）
│   ├── stage2.js           # 階段2（庫洛米）
│   ├── stage3.js           # 階段3（布丁狗）
│   ├── stage4.js           # 階段4（美樂蒂）
│   ├── fever.js            # Fever Time
│   ├── audio.js            # 音效管理
│   ├── score.js            # 分數系統
│   └── achievement.js      # 成就系統
├── assets/
│   ├── images/
│   │   ├── characters/     # 角色圖片
│   │   ├── items/          # 道具圖片
│   │   └── ui/             # UI元素
│   ├── audio/
│   │   ├── bgm/            # 背景音樂
│   │   └── sfx/            # 音效
│   └── fonts/              # 字體
└── README.md               # 說明文檔
```

### 核心類別設計
```javascript
// 遊戲主類別
class PopcornGame {
  constructor() {
    this.score = 0;
    this.level = 1;
    this.feverMeter = 0;
    this.stages = [];
  }
  
  init() { /* 初始化遊戲 */ }
  update() { /* 更新遊戲狀態 */ }
  render() { /* 渲染畫面 */ }
  switchStage(stageId) { /* 切換階段 */ }
}

// 階段基類
class Stage {
  constructor(character) {
    this.character = character;
    this.isActive = false;
  }
  
  activate() { /* 啟動階段 */ }
  deactivate() { /* 停用階段 */ }
  update() { /* 更新邏輯 */ }
  render() { /* 渲染畫面 */ }
}

// 階段1：大耳狗
class CinnamorollStage extends Stage {
  constructor() {
    super('Cinnamoroll');
    this.basket = { x: 400, y: 100 };
    this.corns = [];
  }
  
  moveBas ket(direction) { /* 移動籃子 */ }
  spawnCorn() { /* 生成玉米 */ }
  checkCollision() { /* 碰撞檢測 */ }
}

// 階段2：庫洛米
class KuromiStage extends Stage {
  constructor() {
    super('Kuromi');
    this.temperature = 0;
    this.targetZone = { min: 60, max: 80 };
  }
  
  heat() { /* 加熱 */ }
  checkTemperature() { /* 檢查溫度 */ }
  explode() { /* 爆米花 */ }
}

// 階段3：布丁狗
class PompompurinStage extends Stage {
  constructor() {
    super('Pompompurin');
    this.popcorns = [];
    this.combo = 0;
  }
  
  spawnPopcorn() { /* 生成爆米花 */ }
  checkTiming(clickTime) { /* 檢查時機 */ }
  updateCombo() { /* 更新連擊 */ }
}

// 階段4：美樂蒂
class MyMelodyStage extends Stage {
  constructor() {
    super('MyMelody');
    this.customers = [];
    this.boxes = [];
  }
  
  spawnCustomer() { /* 生成客人 */ }
  packPopcorn() { /* 裝箱 */ }
  serveCustomer() { /* 服務客人 */ }
}

// Fever Time 管理
class FeverManager {
  constructor() {
    this.meter = 0;
    this.isActive = false;
    this.duration = 15000; // 15秒
  }
  
  addMeter(amount) { /* 增加計量 */ }
  activate() { /* 啟動Fever */ }
  deactivate() { /* 結束Fever */ }
}
```

---

## 🎯 開發優先級

### Phase 1：核心功能（第1週）
- [x] 建立專案結構
- [ ] 實現階段1（大耳狗）基本功能
- [ ] 實現階段2（庫洛米）基本功能
- [ ] 實現階段3（布丁狗）基本功能
- [ ] 實現階段4（美樂蒂）基本功能
- [ ] 基本分數系統

### Phase 2：遊戲體驗（第2週）
- [ ] 階段切換系統
- [ ] Fever Time 功能
- [ ] 連擊系統
- [ ] 難度曲線調整
- [ ] 音效整合

### Phase 3：視覺優化（第3週）
- [ ] 角色動畫
- [ ] 特效系統
- [ ] UI 美化
- [ ] 響應式設計
- [ ] 背景音樂

### Phase 4：進階功能（第4週）
- [ ] 成就系統
- [ ] 進度保存
- [ ] 排行榜
- [ ] 教學模式
- [ ] 無限模式

---

## 🚀 下一步行動

### 立即開始
1. **創建專案資料夾**
2. **建立基本 HTML 結構**
3. **實現階段1（大耳狗）原型**
4. **測試基本操作**

### 需要的資源
- [ ] 三麗鷗角色圖片（7張）
- [ ] 爆米花相關圖片（玉米、爆米花、包裝）
- [ ] UI 元素圖片
- [ ] 背景音樂（3-4首）
- [ ] 音效（15-20個）

---

**準備好開始開發了嗎？** 🎮✨

我可以幫您：
1. **立即開始編寫程式碼**（從階段1開始）
2. **先準備圖片資源**（找免費素材）
3. **創建簡化版原型**（先做基本功能）
4. **其他建議**

請告訴我您想從哪裡開始！🚀

