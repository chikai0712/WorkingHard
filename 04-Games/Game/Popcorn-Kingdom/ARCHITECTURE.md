# 🏰 爆米花王國 - 遊戲架構文檔

## 📋 專案概述

**遊戲名稱**：爆米花王國 (Popcorn Kingdom)  
**遊戲類型**：自動化經營模擬遊戲  
**目標玩家**：小學二年級（7-8歲）  
**技術棧**：HTML5 + CSS3 + 原生 JavaScript  
**開發狀態**：✅ 完成

---

## 🗂️ 檔案結構

```
Popcorn-Kingdom/
├── index.html          # 主頁面（遊戲UI結構）
├── styles.css          # 樣式表（視覺設計）
├── game.js             # 遊戲主邏輯（遊戲循環、訂單系統）
├── resources.js        # 資源管理（金幣、玉米、爆米花、滿意度）
├── buildings.js        # 建築系統（玉米田、市場、烤爐、外送站）
├── ui.js               # UI控制（彈窗、通知、事件處理）
├── animations.js       # 動畫效果（粒子、飛行動畫）
├── audio.js            # 音效系統（Web Audio API）
└── README.md           # 遊戲設計文檔
```

---

## 🏗️ 系統架構

### 1. 遊戲主類別 (game.js)

```javascript
class PopcornKingdomGame {
    - resourceManager      // 資源管理器
    - buildingManager      // 建築管理器
    - animationManager     // 動畫管理器
    - audioManager         // 音效管理器
    - uiManager           // UI管理器
    
    + start()             // 啟動遊戲
    + gameLoop()          // 遊戲循環（60 FPS）
    + update(deltaTime)   // 更新遊戲狀態
    + save()              // 儲存進度
    + load()              // 載入進度
    + reset()             // 重置遊戲
}
```

**核心功能**：
- 遊戲循環（使用 requestAnimationFrame）
- 事件處理和分發
- 訂單系統管理
- 自動儲存（每30秒）

---

### 2. 資源管理系統 (resources.js)

```javascript
class ResourceManager {
    resources: {
        gold: 100,           // 金幣
        corn: 0,             // 玉米數量
        cornMax: 10,         // 玉米最大儲存
        popcorn: 0,          // 爆米花數量
        popcornMax: 10,      // 爆米花最大儲存
        satisfaction: 100    // 客戶滿意度
    }
    
    + addGold(amount)           // 增加金幣
    + spendGold(amount)         // 扣除金幣
    + addCorn()                 // 增加玉米
    + useCorn()                 // 消耗玉米
    + addPopcorn()              // 增加爆米花
    + usePopcorn()              // 消耗爆米花
    + adjustSatisfaction()      // 調整滿意度
    + update(deltaTime)         // 更新（被動收入）
}
```

**核心功能**：
- 資源增減管理
- 品質系統（好玉米 70%，壞玉米 30%）
- 滿意度影響價格（100-80%: ×1.0, 79-50%: ×0.8, 49-0%: ×0.5）
- 被動收入計算
- 加成系統（品質、收益）

---

### 3. 建築系統 (buildings.js)

#### 建築基類
```javascript
class Building {
    + id                // 建築ID
    + name              // 建築名稱
    + icon              // 建築圖示
    + level             // 當前等級
    + unlocked          // 是否解鎖
    + progress          // 工作進度
    
    + work(deltaTime)   // 工作邏輯
    + upgrade()         // 升級
}
```

#### 四個建築類別

**1. CornField（玉米田）**
- 功能：自動生產玉米
- 等級：1-4（5秒 → 3秒 → 2秒 → 1秒）
- 升級成本：50, 150, 500 金幣
- 初始解鎖

**2. Market（市場）**
- 功能：自動販售玉米
- 等級：1-4（3秒 → 2秒 → 1秒 → 0.5秒）
- 升級成本：100, 300, 1000 金幣
- 收益：好玉米 +10，壞玉米 -5
- 初始解鎖

**3. Oven（烤爐）**
- 功能：將玉米烤成爆米花
- 等級：1-4（5秒 → 3秒 → 2秒 → 1秒）
- 解鎖成本：100 金幣
- 升級成本：200, 500, 1500 金幣
- 轉換：好玉米 → 爆米花，壞玉米 → 燒焦

**4. Delivery（外送站）**
- 功能：外送爆米花
- 等級：1-4（3秒 → 2秒 → 1秒 → 0.5秒）
- 解鎖成本：200 金幣
- 升級成本：400, 1000, 3000 金幣
- 收益：爆米花 +50（Lv4: +75）

#### 建設系統

**房子（被動收入）**：
- 🏠 小屋：100金幣 → +1金幣/秒
- 🏡 房子：500金幣 → +5金幣/秒
- 🏰 豪宅：2000金幣 → +20金幣/秒

**花園（提升效果）**：
- 🌸 小花：50金幣 → 滿意度+5%
- 🌺 大花：200金幣 → 滿意度+10%
- 🌳 大樹：1000金幣 → 品質+10%
- ⛲ 噴泉：5000金幣 → 收益+20%

---

### 4. UI 控制系統 (ui.js)

```javascript
class UIManager {
    + setupEventListeners()      // 設定事件監聽
    + handleBuildingClick()      // 處理建築點擊
    + showUpgradeModal()         // 顯示升級彈窗
    + showBuildModal()           // 顯示建設彈窗
    + showNotification()         // 顯示通知
    + updateProgress()           // 更新進度條
}
```

**核心功能**：
- 建築點擊事件處理
- 彈窗管理（升級、建設）
- 通知系統
- 進度條更新

---

### 5. 動畫系統 (animations.js)

```javascript
class AnimationManager {
    + createParticles()          // 創建粒子效果
    + createFloatingText()       // 創建浮動文字
    + animateCornFly()           // 玉米飛行動畫
    + animatePopcornFly()        // 爆米花飛行動畫
    + animateGoldGain()          // 金幣獲得動畫
    + flashBuilding()            // 建築閃光
    + glowBuilding()             // 建築發光
    + update(deltaTime)          // 更新動畫
}
```

**動畫效果**：
- 資源飛行動畫（玉米、爆米花、金幣）
- 粒子系統（Canvas）
- 浮動文字
- 建築特效（閃光、發光、震動）

---

### 6. 音效系統 (audio.js)

```javascript
class AudioManager {
    + playSound(type)            // 播放音效
    + playTone(freq, duration)   // 播放音調
    + playSuccess()              // 播放成功音效
    + playFailure()              // 播放失敗音效
    + toggleMute()               // 切換靜音
}
```

**音效類型**：
- produce: 生產玉米（440Hz）
- sell: 賣出（523Hz）
- cook: 烤製（659Hz）
- deliver: 外送（784Hz）
- coin: 金幣（880Hz）
- unlock: 解鎖（1047Hz）
- upgrade: 升級（1175Hz）
- build: 建造（698Hz）
- error: 錯誤（220Hz）
- bad: 壞玉米（196Hz）

---

## 🎮 遊戲流程

### 初始狀態
```
金幣：100
玉米田：Lv.1（已解鎖）
市場：Lv.1（已解鎖）
烤爐：未解鎖（需要100金幣）
外送站：未解鎖（需要200金幣）
```

### 遊戲循環
```
1. 玉米田自動生產玉米（5秒/個）
2. 市場自動販售玉米（3秒/個）
   - 好玉米：+10金幣，滿意度+1%
   - 壞玉米：-5金幣，滿意度-10%
3. 賺到100金幣 → 解鎖烤爐
4. 烤爐將玉米烤成爆米花（5秒/個）
5. 賺到200金幣 → 解鎖外送站
6. 外送站送爆米花（3秒/個，+50金幣）
7. 用賺來的錢升級建築和建設
```

### 訂單系統
```
- 每60秒出現一個訂單
- 小訂單：3個爆米花 → +30金幣
- 中訂單：5個爆米花 → +60金幣
- 大訂單：10個爆米花 → +150金幣
- 限時90-120秒完成
```

---

## 💾 儲存系統

### LocalStorage 結構
```javascript
// 資源數據
popcornKingdom_resources: {
    resources: {...},
    bonuses: {...},
    passiveIncome: 0,
    cornQuality: {...}
}

// 建築數據
popcornKingdom_buildings: {
    buildings: {...},
    constructionSlots: [...]
}

// 遊戲數據
popcornKingdom_game: {
    orderTimer: 0,
    currentOrder: null
}
```

### 自動儲存
- 每30秒自動儲存
- 頁面關閉前儲存
- 手動儲存按鈕

---

## 🎨 視覺設計

### 色彩方案
```css
背景：漸層紫色（#667eea → #764ba2）
遊戲區：天空藍到草綠（#87CEEB → #98D8C8）
資源欄：金色漸層（#FFD700 → #FFA500）
建築：白色漸層（#fff → #f0f0f0）
```

### 響應式設計
- 桌面版：1200px 最大寬度
- 平板版：768px 以下單欄布局
- 手機版：優化觸控操作

---

## 🚀 如何使用

### 1. 直接打開
```bash
# 雙擊 index.html 即可在瀏覽器中遊玩
```

### 2. 本地伺服器（推薦）
```bash
cd Popcorn-Kingdom
python3 -m http.server 8000
# 訪問 http://localhost:8000
```

### 3. 部署到網頁
- 上傳所有檔案到網頁伺服器
- 支援任何靜態網頁託管服務（GitHub Pages, Netlify, Vercel）

---

## 🎯 遊戲平衡

### 收益對比
| 路線 | 時間 | 收益 | 效率 |
|------|------|------|------|
| 直接賣玉米 | 8秒 | 10金幣 | 1.25金幣/秒 |
| 烤爆米花 | 10秒 | 50金幣 | 5金幣/秒 |
| 外送服務 | 10秒 | 50金幣 + 訂單 | 5+金幣/秒 |

### 升級投資回報
| 建築 | 升級成本 | 效率提升 | 回本時間 |
|------|---------|---------|---------|
| 玉米田 Lv.2 | 50金幣 | +67% | ~40秒 |
| 市場 Lv.2 | 100金幣 | +50% | ~80秒 |
| 烤爐 Lv.2 | 200金幣 | +67% | ~40秒 |
| 外送站 Lv.2 | 400金幣 | +50% | ~80秒 |

---

## 🐛 已知限制

1. **瀏覽器相容性**：需要支援 ES6 和 Web Audio API
2. **效能**：大量動畫可能影響低階設備
3. **儲存**：依賴 LocalStorage，清除瀏覽器數據會遺失進度

---

## 🔧 擴展建議

### 短期
- [ ] 添加更多音效
- [ ] 增加成就系統
- [ ] 添加教學模式

### 中期
- [ ] 多語言支援
- [ ] 更多建築類型
- [ ] 季節活動

### 長期
- [ ] 雲端儲存
- [ ] 排行榜系統
- [ ] 多人模式

---

## 📝 開發筆記

### 設計理念
1. **簡單易懂**：適合小學二年級，操作簡單
2. **自動化**：減少重複點擊，專注策略
3. **視覺回饋**：每個動作都有動畫和音效
4. **教育意義**：學習資源管理和因果關係

### 技術亮點
1. **模組化設計**：每個系統獨立，易於維護
2. **無框架**：純原生 JavaScript，輕量化
3. **Web Audio API**：動態生成音效，無需音檔
4. **Canvas 動畫**：流暢的粒子效果

---

**開發完成！準備開始遊玩！** 🎮✨

