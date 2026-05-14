# 群益 API - 台指期即時報價

使用群益證券 API 訂閱台指期 (TXF) 即時報價。

## 前置需求

1. **群益證券帳戶**  
   需要有群益證券的帳號密碼

2. **安裝群益 API 元件**  
   - 下載並安裝群益 API 元件 (SKCOM)
   - 官方下載：https://www.capital.com.tw/Service2/download/api.asp

3. **Python 套件**
   ```bash
   pip install -r requirements.txt
   ```

## 快速開始

### 1. 設定環境變數

複製 `.env.example` 為 `.env`：

```bash
cp .env.example .env
```

編輯 `.env`，填入你的群益帳號密碼：

```env
CAPITAL_ACCOUNT=你的群益帳號
CAPITAL_PASSWORD=你的群益密碼
```

### 2. 執行範例

```bash
python example.py
```

程式會：
1. 自動登入群益 API
2. 訂閱台指期近月合約即時報價
3. 持續顯示收到的報價資料
4. 按 `Ctrl+C` 停止

## 使用方式

### 基本用法

```python
from capital_api import CapitalClient, FuturesSubscriber

# 定義報價處理函式
def on_quote(quote_data):
    print(f"成交價: {quote_data['price']}")

# 使用 with 語法 (自動連線/斷線)
with CapitalClient() as client:
    subscriber = FuturesSubscriber(client)
    subscriber.subscribe_txf(callback=on_quote)
    
    # 持續接收報價
    while True:
        time.sleep(1)
```

### 進階用法

```python
# 手動控制連線
client = CapitalClient(account='帳號', password='密碼')

if client.connect():
    if client.login_quote():
        subscriber = FuturesSubscriber(client)
        subscriber.subscribe_txf(callback=on_quote)
        
        # ... 你的邏輯 ...
        
        subscriber.unsubscribe_all()
    
    client.disconnect()
```

## 報價資料格式

`on_quote` 回調函式會收到以下格式的字典：

```python
{
    'timestamp': '2026-03-06T14:30:00.123456',  # 時間戳記
    'product': 'TXF202603',                      # 商品代碼
    'price': 18500,                              # 成交價
    'volume': 10,                                # 成交量
    'bid': 18499,                                # 買價
    'ask': 18501,                                # 賣價
    'bid_volume': 50,                            # 買量
    'ask_volume': 30                             # 賣量
}
```

## 注意事項

1. **Windows 限定**  
   群益 API 使用 COM 介面，僅支援 Windows 系統

2. **交易時段**  
   台指期交易時段：
   - 一般交易：08:45 - 13:45
   - 盤後交易：15:00 - 次日 05:00

3. **API 限制**  
   - 需要先在群益官網申請 API 使用權限
   - 注意 API 呼叫頻率限制

4. **合約代碼**  
   程式會自動選擇近月合約，如需指定特定月份，請修改 `_get_current_txf_code()` 函式

## 整合到現有系統

如果要整合到你的 `Stock_Analize` 系統：

```python
# 在 backend/main.py 或其他地方
from capital_api import CapitalClient, FuturesSubscriber
from database.session import get_db
from database.models_futures import FuturesTick

def save_quote_to_db(quote_data):
    """將報價存入資料庫"""
    db = next(get_db())
    tick = FuturesTick(
        timestamp=quote_data['timestamp'],
        product=quote_data['product'],
        price=quote_data['price'],
        volume=quote_data['volume']
    )
    db.add(tick)
    db.commit()

# 啟動訂閱
with CapitalClient() as client:
    subscriber = FuturesSubscriber(client)
    subscriber.subscribe_txf(callback=save_quote_to_db)
    # ...
```

## 警示規則引擎（AlertEngine）

`AlertEngine` 預設已載入以下規則：

| 規則 | 說明 | 等級 |
|------|------|------|
| MACD 交叉 | 黃金交叉 / 死亡交叉 | high |
| RSI | 超買 > 80 / 超賣 < 20 | medium |
| KD 交叉 | 黃金交叉 / 死亡交叉 | high |
| 布林通道突破 | 突破上軌 / 跌破下軌 | medium |
| 成交量異常 | 單分鐘 > 1000 口 | medium |
| 趨勢線突破 | 跌破上升支撐線 / 突破下降壓力線 | high |

自訂規則：

```python
from capital_api.alert_engine import AlertEngine

engine = AlertEngine()

# 價格突破警示（一次性，回破後可再觸發）
engine.add_price_breakout(level=21000, direction='above')

# 自訂條件
engine.add_custom(
    name='價量背離',
    condition=lambda bar, ind, prev: (
        bar['volume'] > 800 and
        ind.get('rsi', 50) < 45
    ),
    message_fn=lambda bar, ind: f"價量背離，量 {bar['volume']} RSI {ind['rsi']:.1f}",
)
```

---

## GEM 框型價位計算

`TickProcessor` 內建 `RectangleDetector`，每根分鐘K完成後自動偵測：

- 近 N 根（預設 60）K棒的震盪區間（高低點）
- 判斷是否向上突破 / 向下跌破
- 計算框型目標（TP1）和翻亞當目標（TP2）

結果掛在 `indicators['gem']`，格式：

```python
gem = {
    'status':     'breakout_up',   # 'breakout_up' / 'breakout_down' / 'in_range'
    'resistance': 21300.0,
    'support':    21000.0,
    'height':     300.0,
    'mid':        21150.0,
    # 突破時額外有以下欄位：
    'direction':      'up',
    'breakout_price': 21310.0,
    'origin_price':   21050.0,
    'tp1':            21600.0,     # 框型一倍目標
    'tp2':            21570.0,     # 翻亞當目標
    'sl':             20980.0,     # 初始停損
    'adam_distance':  260.0,
    'plan':           {...},       # calc_full_plan() 完整結果
}
```

環境變數控制 GEM 參數：

```env
GEM_LOOKBACK_BARS=60       # 回溯K棒數（預設 60）
GEM_BREAKOUT_BUFFER=0.002  # 突破確認緩衝（預設 0.2%）
GEM_SL_OFFSET=20           # 停損緩衝點數（預設 20）
GEM_COOLDOWN_MINUTES=15    # 同方向推播冷卻時間（預設 15 分鐘）
```

手動使用 GEM 計算：

```python
from capital_api.price_target import calc_full_plan, format_plan_message

plan = calc_full_plan(
    resistance=21300,
    support=21000,
    breakout_price=21320,
    origin_price=21050,
    sl_offset=20,
)
print(format_plan_message(plan))
```

---



- 確認群益 API 元件已正確安裝
- 檢查帳號密碼是否正確
- 確認網路連線正常

### 收不到報價

- 確認在交易時段內
- 檢查是否已申請 API 使用權限
- 查看 log 確認訂閱是否成功

## Telegram 推播設定

### 環境變數

在 `.env` 加入：

```env
TELEGRAM_BOT_TOKEN=你的BotToken   # 從 @BotFather 取得
TELEGRAM_CHAT_ID=你的ChatID       # 從 @userinfobot 取得
```

### 推播模組使用方式

```python
from capital_api.notifier import TelegramNotifier

n = TelegramNotifier(
    bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
    chat_id=os.getenv('TELEGRAM_CHAT_ID'),
)

# 傳送文字訊息
n.send_message('<b>測試訊息</b>', parse_mode='HTML')

# 傳送警示（含完整 OHLCV + 技術指標 + GEM 高低點）
n.send_alert(
    alert={
        'name': 'MACD 黃金交叉',
        'message': 'MACD 黃金交叉，收盤 21201',
        'level': 'high',   # high / medium / low
        'close': 21201,
        'volume': 202,
        'datetime': '09:38',
    },
    bar={                  # 分鐘K OHLCV（選填，補完整四價）
        'open': 21185, 'high': 21210,
        'low': 21180, 'close': 21201, 'volume': 202,
    },
    indicators={           # get_indicators() 完整 dict（選填）
        'rsi': 63.0, 'macd': 32.46, 'macd_signal': 30.1, 'macd_hist': 2.36,
        'k': 71.0, 'd': 72.9,
        'bb_upper': 21300, 'bb_mid': 21100, 'bb_lower': 20900,
        'trend_direction': 'up',
    },
    gem=indicators.get('gem'),  # 高低點預測（來自 TickProcessor）
)

# 傳送趨勢線圖（PNG bytes）
n.send_photo(png_bytes, caption='TXF Trendline Chart')

# 每日籌碼摘要
n.send_daily_summary({
    'date': '2026-03-25',
    'foreign_net': 3500,
    'trust_net': -200,
    'dealer_net': 100,
    'foreign_oi': 45000,
    'pc_ratio': 0.85,
    'margin_balance': 1234.5,
    'close': 21000,
    'volume': 85000,
})
```

---

## ⚠️  Cursor 開發環境限制：Telegram 無法在 Cursor terminal 發送

### 問題原因

Cursor IDE 的 terminal 運行在沙盒（sandbox）環境中，會透過內部 proxy 轉發網路請求。
這個 proxy 封鎖了對 `api.telegram.org` 的連線，導致：

```
NameResolutionError: Failed to resolve 'api.telegram.org'
```

即使在 `notifier.py` 中清除了所有 proxy 環境變數（`unset HTTP_PROXY` 等），
Cursor sandbox 仍在底層攔截 DNS 查詢，無法繞過。

### 解法：改用系統終端機（iTerm）執行

所有需要對外發送 Telegram 的腳本，必須在 **iTerm / Terminal.app** 執行，不能在 Cursor terminal。

**A-06b 驗證腳本（含 5 個測試）：**

```bash
# 在 iTerm 執行
cd /Users/ckchiu/Desktop/Project/03-Data-Analytics/Stock_Analize/backend/capital_api
bash run_a06b.sh
```

測試內容：

| 測試 | 內容 | 預期 Telegram 收到 |
|------|------|-------------------|
| TEST 1 | curl 確認 Bot Token 有效 | — |
| TEST 2 | curl 基本文字訊息 | 1 則 |
| TEST 3 | curl 警示格式訊息 | 1 則 |
| TEST 4 | Python `TelegramNotifier` send_message + send_alert | 2 則 |
| TEST 5 | `send_mock_report.py` 完整流程（含趨勢線圖） | 2~3 則 |

**手動執行 send_mock_report.py（單獨）：**

```bash
# 在 iTerm 執行
cd /Users/ckchiu/Desktop/Project/03-Data-Analytics/Stock_Analize/backend/capital_api
MPLCONFIGDIR=/tmp/mpl_cache \
TELEGRAM_BOT_TOKEN=8771241397:AAESXT-Cn5EQ6sRBiHar1AKKwiQPKxJ_dJo \
TELEGRAM_CHAT_ID=229891358 \
.venv/bin/python3 send_mock_report.py
```

### venv 位置

```
backend/capital_api/.venv/   ← 正確路徑（Python 3.13）
```

```bash
# 啟動 venv
source backend/capital_api/.venv/bin/activate

# 或直接指定 python
backend/capital_api/.venv/bin/python3 your_script.py
```

---

## 參考資源

- [群益 API 官方文件](https://www.capital.com.tw/Service2/download/api.asp)
- [skcom 非官方範例](https://github.com/tacosync/skcom)
- [Python COM 介面文件](https://pythonhosted.org/comtypes/)
