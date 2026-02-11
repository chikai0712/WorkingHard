# 寶可夢對戰遊戲 - 完整開發計劃

## 📋 專案概述

**專案名稱**：小智 vs 電腦：寶可夢對戰遊戲  
**開發語言**：Python 3.x  
**主要框架**：Pygame  
**遊戲類型**：回合制對戰遊戲  
**開發時間**：預計 2-3 天

---

## 🎯 遊戲核心功能

### 1. 基礎對戰系統
- ✅ 3 vs 3 隊伍對戰（小智 vs 電腦）
- ✅ 回合制攻擊機制
- ✅ 血量顯示與扣血動畫
- ✅ 勝負判定系統

### 2. 寶可夢管理
- ✅ 隨時手動換人
- ✅ 強制換人（當前寶可夢倒下時）
- ✅ 寶可夢狀態顯示（HP、名稱）
- ✅ 換人按鈕 UI

### 3. 視覺與音效
- ✅ 背景圖片（競技場）
- ✅ 寶可夢圖片顯示
- ✅ 背景音樂循環播放
- ✅ 血條動態顯示

---

## 📁 專案結構

```
Pokemon-Battle-Game/
│
├── main.py                 # 主程式
├── pokemon.py              # 寶可夢類別定義
├── battle.py               # 戰鬥邏輯
├── ui.py                   # UI 繪製
├── requirements.txt        # 依賴套件
├── README.md              # 說明文檔
│
├── assets/                # 資源文件夾
│   ├── images/           # 圖片資源
│   │   ├── background.png
│   │   ├── charizard.png
│   │   ├── blastoise.png
│   │   ├── venusaur.png
│   │   ├── garchomp.png
│   │   ├── kingdra.png
│   │   └── persian.png
│   │
│   └── audio/            # 音效資源
│       └── bgm.mp3
│
└── docs/                 # 文檔
    ├── game_design.md    # 遊戲設計文檔
    └── api_reference.md  # API 參考
```

---

## 🔧 技術架構分析

### 核心類別設計

#### 1. Pokemon 類別
```python
class Pokemon:
    - name: str           # 寶可夢名稱
    - max_hp: int        # 最大血量
    - hp: int            # 當前血量
    - atk: int           # 攻擊力
    - image: Surface     # 圖片物件
    
    方法：
    - __init__()         # 初始化
    - is_alive()         # 是否存活
    - take_damage()      # 受到傷害
    - get_hp_ratio()     # 血量百分比
```

#### 2. Battle 類別
```python
class Battle:
    - ash_team: List[Pokemon]    # 小智隊伍
    - comp_team: List[Pokemon]   # 電腦隊伍
    - ash_idx: int               # 當前出戰索引
    - comp_idx: int              # 電腦出戰索引
    - game_state: str            # 遊戲狀態
    
    方法：
    - attack()                   # 執行攻擊
    - switch_pokemon()           # 換人
    - check_winner()             # 檢查勝負
    - auto_switch_comp()         # 電腦自動換人
```

#### 3. UI 類別
```python
class GameUI:
    - screen: Surface            # 遊戲視窗
    - font: Font                 # 字體
    
    方法：
    - draw_background()          # 繪製背景
    - draw_pokemon()             # 繪製寶可夢
    - draw_hp_bar()              # 繪製血條
    - draw_switch_buttons()      # 繪製換人按鈕
    - draw_message()             # 繪製訊息
```

---

## 🎮 遊戲流程圖

```
開始遊戲
    ↓
載入資源（圖片、音樂）
    ↓
初始化雙方隊伍
    ↓
進入主遊戲循環
    ↓
┌─────────────────────┐
│   繪製遊戲畫面      │
│   - 背景            │
│   - 寶可夢          │
│   - 血條            │
│   - 按鈕            │
└─────────────────────┘
    ↓
┌─────────────────────┐
│   處理玩家輸入      │
│   - 點擊攻擊        │
│   - 點擊換人        │
└─────────────────────┘
    ↓
執行戰鬥邏輯
    ↓
┌─────────────────────┐
│   玩家攻擊          │
│   ↓                 │
│   電腦寶可夢扣血    │
│   ↓                 │
│   檢查是否倒下      │
│   ↓                 │
│   電腦自動換人      │
└─────────────────────┘
    ↓
┌─────────────────────┐
│   電腦反擊          │
│   ↓                 │
│   玩家寶可夢扣血    │
│   ↓                 │
│   檢查是否倒下      │
│   ↓                 │
│   進入強制換人模式  │
└─────────────────────┘
    ↓
檢查勝負
    ↓
是否結束？
    ├─ 否 → 回到主循環
    └─ 是 → 顯示結果 → 結束
```

---

## 📊 寶可夢數據表

### 小智隊伍

| 寶可夢 | HP  | 攻擊力 | 圖片檔案 |
|--------|-----|--------|----------|
| 噴火龍 | 186 | 45     | charizard.png |
| 水箭龜 | 188 | 38     | blastoise.png |
| 妙蛙花 | 190 | 42     | venusaur.png |

### 電腦隊伍

| 寶可夢 | HP  | 攻擊力 | 圖片檔案 |
|--------|-----|--------|----------|
| 烈咬陸鯊 | 239 | 42   | garchomp.png |
| 刺龍王 | 181 | 40     | kingdra.png |
| 貓老大 | 163 | 35     | persian.png |

---

## 🚀 開發步驟

### Phase 1: 環境準備（30分鐘）
1. ✅ 安裝 Python 3.x
2. ✅ 安裝 Pygame：`pip install pygame`
3. ✅ 創建專案目錄結構
4. ✅ 準備資源文件（圖片、音樂）

### Phase 2: 核心功能開發（2小時）
1. ✅ 實作 Pokemon 類別
2. ✅ 實作 Battle 類別
3. ✅ 實作基礎攻擊邏輯
4. ✅ 實作換人機制

### Phase 3: UI 開發（1.5小時）
1. ✅ 繪製背景與寶可夢
2. ✅ 繪製血條
3. ✅ 繪製換人按鈕
4. ✅ 繪製訊息提示

### Phase 4: 整合與測試（1小時）
1. ✅ 整合所有模組
2. ✅ 測試戰鬥流程
3. ✅ 測試換人機制
4. ✅ 測試勝負判定

### Phase 5: 優化與打磨（1小時）
1. ✅ 加入音樂
2. ✅ 優化 UI 顯示
3. ✅ 修復 Bug
4. ✅ 撰寫文檔

---

## 💻 核心代碼實作

### 1. requirements.txt
```
pygame==2.5.2
```

### 2. pokemon.py
```python
import pygame

class Pokemon:
    """寶可夢類別"""
    
    def __init__(self, name, hp, atk, img_path):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        
        # 載入圖片
        try:
            self.image = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (250, 250))
        except:
            # 如果圖片載入失敗，使用灰色方塊代替
            self.image = pygame.Surface((250, 250))
            self.image.fill((150, 150, 150))
    
    def is_alive(self):
        """檢查是否存活"""
        return self.hp > 0
    
    def take_damage(self, damage):
        """受到傷害"""
        self.hp = max(0, self.hp - damage)
    
    def get_hp_ratio(self):
        """取得血量百分比"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0
```

### 3. battle.py
```python
class Battle:
    """戰鬥管理類別"""
    
    def __init__(self, ash_team, comp_team):
        self.ash_team = ash_team
        self.comp_team = comp_team
        self.ash_idx = 0
        self.comp_idx = 0
        self.game_state = "BATTLE"  # BATTLE, FORCE_SWITCH, WIN, LOSE
    
    def attack(self):
        """執行攻擊"""
        if self.game_state != "BATTLE":
            return
        
        # 玩家攻擊
        player_pkmn = self.ash_team[self.ash_idx]
        comp_pkmn = self.comp_team[self.comp_idx]
        
        comp_pkmn.take_damage(player_pkmn.atk)
        
        # 檢查電腦寶可夢是否倒下
        if not comp_pkmn.is_alive():
            self.auto_switch_comp()
            if self.check_winner():
                return
        
        # 電腦反擊
        player_pkmn.take_damage(comp_pkmn.atk)
        
        # 檢查玩家寶可夢是否倒下
        if not player_pkmn.is_alive():
            if any(p.is_alive() for p in self.ash_team):
                self.game_state = "FORCE_SWITCH"
            else:
                self.game_state = "LOSE"
    
    def switch_pokemon(self, new_idx):
        """換人"""
        if 0 <= new_idx < len(self.ash_team):
            if self.ash_team[new_idx].is_alive():
                self.ash_idx = new_idx
                self.game_state = "BATTLE"
                return True
        return False
    
    def auto_switch_comp(self):
        """電腦自動換人"""
        for i in range(len(self.comp_team)):
            if self.comp_team[i].is_alive() and i != self.comp_idx:
                self.comp_idx = i
                return
        # 沒有活著的寶可夢了
        self.game_state = "WIN"
    
    def check_winner(self):
        """檢查勝負"""
        ash_alive = any(p.is_alive() for p in self.ash_team)
        comp_alive = any(p.is_alive() for p in self.comp_team)
        
        if not comp_alive:
            self.game_state = "WIN"
            return True
        elif not ash_alive:
            self.game_state = "LOSE"
            return True
        return False
```

### 4. ui.py
```python
import pygame

class GameUI:
    """遊戲 UI 管理"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 48)
        
        # 載入背景
        try:
            self.background = pygame.image.load("assets/images/background.png")
            self.background = pygame.transform.scale(self.background, (800, 600))
        except:
            self.background = None
    
    def draw_background(self):
        """繪製背景"""
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((50, 50, 50))
    
    def draw_pokemon(self, pokemon, x, y):
        """繪製寶可夢"""
        self.screen.blit(pokemon.image, (x, y))
    
    def draw_hp_bar(self, pokemon, x, y):
        """繪製血條"""
        # 背景槽
        pygame.draw.rect(self.screen, (100, 0, 0), (x, y, 200, 20))
        # 當前血量
        hp_width = int(200 * pokemon.get_hp_ratio())
        pygame.draw.rect(self.screen, (0, 255, 0), (x, y, hp_width, 20))
        # 邊框
        pygame.draw.rect(self.screen, (0, 0, 0), (x, y, 200, 20), 2)
        
        # 顯示名稱和血量
        text = self.font.render(f"{pokemon.name} HP: {int(pokemon.hp)}/{pokemon.max_hp}", True, (255, 255, 255))
        self.screen.blit(text, (x, y - 30))
    
    def draw_switch_buttons(self, team, current_idx):
        """繪製換人按鈕"""
        for i, pokemon in enumerate(team):
            x = 50 + i * 150
            y = 500
            
            # 按鈕顏色
            if i == current_idx:
                color = (255, 255, 0)  # 當前出戰：黃色
            elif pokemon.is_alive():
                color = (200, 200, 200)  # 可用：灰色
            else:
                color = (100, 100, 100)  # 倒下：深灰色
            
            # 繪製按鈕
            pygame.draw.rect(self.screen, color, (x, y, 130, 50))
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, 130, 50), 2)
            
            # 按鈕文字
            text = self.font.render(f"{pokemon.name}", True, (0, 0, 0))
            hp_text = self.font.render(f"HP:{int(pokemon.hp)}", True, (0, 0, 0))
            self.screen.blit(text, (x + 10, y + 5))
            self.screen.blit(hp_text, (x + 10, y + 25))
    
    def draw_message(self, message, color=(255, 0, 0)):
        """繪製訊息"""
        text = self.title_font.render(message, True, color)
        text_rect = text.get_rect(center=(400, 300))
        self.screen.blit(text, text_rect)
```

### 5. main.py
```python
import pygame
import sys
from pokemon import Pokemon
from battle import Battle
from ui import GameUI

# 初始化
pygame.init()
pygame.mixer.init()

# 視窗設定
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("小智 vs 電腦：寶可夢對戰")
clock = pygame.time.Clock()

# 載入音樂
try:
    pygame.mixer.music.load("assets/audio/bgm.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except:
    print("音樂載入失敗")

# 創建隊伍
ash_team = [
    Pokemon("噴火龍", 186, 45, "assets/images/charizard.png"),
    Pokemon("水箭龜", 188, 38, "assets/images/blastoise.png"),
    Pokemon("妙蛙花", 190, 42, "assets/images/venusaur.png")
]

comp_team = [
    Pokemon("烈咬陸鯊", 239, 42, "assets/images/garchomp.png"),
    Pokemon("刺龍王", 181, 40, "assets/images/kingdra.png"),
    Pokemon("貓老大", 163, 35, "assets/images/persian.png")
]

# 創建戰鬥和 UI
battle = Battle(ash_team, comp_team)
ui = GameUI(screen)

# 主遊戲循環
running = True
while running:
    # 繪製畫面
    ui.draw_background()
    
    # 繪製寶可夢
    player_pkmn = ash_team[battle.ash_idx]
    comp_pkmn = comp_team[battle.comp_idx]
    
    ui.draw_pokemon(player_pkmn, 50, 250)
    ui.draw_pokemon(comp_pkmn, 500, 50)
    
    # 繪製血條
    ui.draw_hp_bar(player_pkmn, 50, 220)
    ui.draw_hp_bar(comp_pkmn, 500, 310)
    
    # 繪製換人按鈕
    ui.draw_switch_buttons(ash_team, battle.ash_idx)
    
    # 顯示訊息
    if battle.game_state == "FORCE_SWITCH":
        ui.draw_message("請選擇下一隻寶可夢！", (255, 0, 0))
    elif battle.game_state == "WIN":
        ui.draw_message("小智獲勝！", (0, 255, 0))
    elif battle.game_state == "LOSE":
        ui.draw_message("電腦獲勝！", (255, 0, 0))
    
    # 事件處理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            
            # 檢查是否點擊換人按鈕
            if 500 <= my <= 550:
                for i in range(len(ash_team)):
                    if 50 + i * 150 <= mx <= 180 + i * 150:
                        battle.switch_pokemon(i)
                        break
            # 點擊其他地方進行攻擊
            elif battle.game_state == "BATTLE":
                battle.attack()
    
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
```

---

## 📝 執行步驟

### 1. 創建專案目錄
```bash
mkdir Pokemon-Battle-Game
cd Pokemon-Battle-Game
mkdir -p assets/images assets/audio
```

### 2. 安裝依賴
```bash
pip install pygame
```

### 3. 準備資源文件
- 將 6 張寶可夢圖片放入 `assets/images/`
- 將背景圖片放入 `assets/images/background.png`
- 將音樂文件放入 `assets/audio/bgm.mp3`

### 4. 創建程式文件
- 創建 `pokemon.py`
- 創建 `battle.py`
- 創建 `ui.py`
- 創建 `main.py`

### 5. 執行遊戲
```bash
python main.py
```

---

## 🎮 遊戲操作說明

### 基本操作
- **攻擊**：點擊畫面任意位置（非按鈕區域）
- **換人**：點擊下方的寶可夢按鈕

### 遊戲規則
1. 雙方各有 3 隻寶可夢
2. 點擊攻擊後，玩家先攻擊，電腦自動反擊
3. 當寶可夢 HP 歸零時：
   - 電腦會自動換下一隻
   - 玩家必須手動選擇下一隻
4. 當一方所有寶可夢都倒下時，遊戲結束

---

## 🐛 常見問題與解決方案

### 問題 1：圖片無法載入
**解決方案**：
- 確認圖片路徑正確
- 確認圖片格式為 PNG
- 檢查檔案名稱是否正確（區分大小寫）

### 問題 2：音樂無法播放
**解決方案**：
- 嘗試將 MP3 轉換為 WAV 格式
- 檢查音樂文件路徑
- 確認 pygame.mixer 已正確初始化

### 問題 3：中文顯示亂碼
**解決方案**：
- 使用支援中文的字體（如 SimHei、Microsoft YaHei）
- 或使用英文顯示

### 問題 4：遊戲運行緩慢
**解決方案**：
- 降低圖片解析度
- 調整 FPS（clock.tick 的參數）
- 優化繪製邏輯

---

## 🚀 未來擴展功能

### 短期擴展（1-2天）
- [ ] 招式選單（多種攻擊方式）
- [ ] 傷害隨機波動
- [ ] 攻擊動畫效果
- [ ] 音效（攻擊音效、換人音效）

### 中期擴展（1週）
- [ ] 屬性相剋系統
- [ ] 更多寶可夢選擇
- [ ] 道具系統（藥水、精靈球）
- [ ] 存檔功能

### 長期擴展（1個月）
- [ ] 多人對戰模式
- [ ] 線上對戰
- [ ] 寶可夢升級系統
- [ ] 劇情模式

---

## 📚 參考資源

### Pygame 官方文檔
- https://www.pygame.org/docs/

### 寶可夢數據參考
- https://pokemondb.net/

### 音樂資源
- Charizard's Black Sky: https://youtube.com/watch?v=OC_ES7__Xwc

---

## ✅ 檢查清單

### 開發前
- [ ] Python 3.x 已安裝
- [ ] Pygame 已安裝
- [ ] 專案目錄已創建
- [ ] 資源文件已準備

### 開發中
- [ ] Pokemon 類別完成
- [ ] Battle 類別完成
- [ ] UI 類別完成
- [ ] 主程式完成
- [ ] 基本測試通過

### 開發後
- [ ] 完整測試通過
- [ ] 文檔撰寫完成
- [ ] 代碼註解完整
- [ ] README 撰寫完成

---

## 📞 聯絡資訊

**開發者**：邱棋凱  
**Email**：Chikai0712@gmail.com  
**專案日期**：2026-02-07

---

**祝您開發順利！🎮✨**

