# 台指期監控系統 — 開發狀態記錄

> 這是台指期盤中監控系統的進度存檔點。
> 每次開發前先讀此檔案，了解上次停在哪裡。

## 專案基本資訊

- **路徑**: `03-Data-Analytics/Stock_Analize/`
- **開始日期**: 2026-03-19
- **開發者**: CK
- **目標**: 台指期當沖輔助監控系統（Tick 級警示 + Telegram 推播）

## 架構決策（已確定，勿更改）

### 雙機分工

| 機器 | 角色 | 資料來源 | 說明 |
|------|------|---------|------|
| **Windows 電腦** | 主監控（白盤+夜盤，人在時） | 群益 Capital API (SKCOM COM) | Tick 級即時報價，Windows only |
| **AWS EC2 Linux** | 常駐服務（盤後籌碼 + 夜盤備援） | TAIFEX 爬蟲 + HiStock | Docker 部署，24 小時運行 |
| **Telegram Bot** | 統一通知入口 | — | 所有警示與摘要推播到此 |

### 資料流

```
【Windows】
群益 Capital API
  → Tick 接收（futures_subscriber.py）
  → Tick 聚合成分鐘K（tick_processor.py）
  → 技術指標計算：MACD / RSI / KD / 布林通道（pandas-ta）
  → 警示規則檢查（alert_engine.py）
  → Telegram 推播（notifier.py）

【AWS EC2】
盤後爬蟲（每日 15:30）
  → HiStock / TAIFEX → 三大法人、未平倉、融資融券、PC Ratio
  → 存入 PostgreSQL
  → 每日籌碼摘要 → Telegram 推播

夜盤備援爬蟲（15:00–05:00，每分鐘）
  → TAIFEX 網頁 → 台指期分鐘K
  → 警示規則檢查 → Telegram 推播
```

### 技術棧

| 層級 | 技術 | 說明 |
|------|------|------|
| Windows 即時 | Python + comtypes + SKCOM | 群益 COM 介面 |
| 指標計算 | pandas-ta | MACD/RSI/KD/布林通道 |
| 警示引擎 | 純 Python | 可設定條件組合 |
| Telegram | python-telegram-bot | 推播通知 |
| AWS 後端 | FastAPI + APScheduler | 現有架構 |
| 資料庫 | SQLite（Windows 本機）+ PostgreSQL（AWS）| |
| 前端 | Vue 3（選配，後期再做）| |

## 現有程式碼盤點

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `capital_api/client.py` | 骨架完成 | 連線/登入邏輯已寫，待測試 |
| `capital_api/futures_subscriber.py` | 骨架完成，**關鍵缺口** | `_register_quote_handler()` 是空的，COM 事件未接 |
| `capital_api/example.py` | 可用 | 示範主程式架構 |
| `crawler/futures_data_fetcher.py` | 可用 | 盤後資料抓取（HiStock + TAIFEX）已完成 |
| `crawler/taifex_scraper.py` | 骨架完成，解析邏輯待補 | HTML 解析是空的 |
| `database/models_futures.py` | 可用 | 需新增 FuturesMinuteData、AlertRule 表 |
| `scheduler/futures_tasks.py` | 可用 | 需加入夜盤分鐘K任務 |
| `api/futures.py` | 可用 | 需新增即時報價 + 警示端點 |
| `frontend/FuturesDashboard.vue` | 骨架存在 | Phase C 才做 |

## 前置條件（開始寫程式前必須確認）

- [ ] 群益帳號已開通**期貨帳戶**
- [ ] 群益官網已申請 **API 使用權限**（審核 1–3 工作天）
- [ ] Windows 電腦已安裝 **SKCOM**（群益 COM 元件）
- [ ] Telegram Bot 已建立，取得 **BOT_TOKEN** 和 **CHAT_ID**
- [ ] AWS EC2 已有環境（現有 GlobalpingChecker 的 EC2 可複用）

## 當前進度

**Phase**: TC — TradingClaw LITE 程式交易版規劃
**Status**: In progress — TC-01 功能盤點 / 規格拆解中
**Last activity**: 2026-04-06 — 依照使用者貼文與截圖，規劃 AI 盯盤 + 程式交易 MVP

---

## 開發日誌

### [2026-04-06 23:05] — TradingClaw LITE 規格文件完成
- **Phase**: TC — TradingClaw LITE 程式交易版規劃
- **Status**: Complete
- **Done**:
  - 建立 `CONTEXT.md`，記錄功能需求、user story、acceptance criteria、技術邊界、風險與 forbidden zones
  - 更新 `ROADMAP.md`，將 TC 規格拆成可驗證步驟，並標記規格作業已完成
  - 完成正式規格草案：產品定位、MVP 範圍、模組分層、事件流程、風控原則、建議 Phase
- **Next**:
  - 等待使用者確認規格是否要進入下一步
  - 若確認，先從 Phase 1「分析 MVP」開始拆實作
- **Blocker**: 尚未確認實際要先落地的 broker adapter 與 TradingView 控制方式

---

## 開發日誌

### [2026-04-06 22:50] — TradingClaw LITE 程式交易規劃啟動
- **Phase**: TC — TradingClaw LITE 程式交易版規劃
- **Status**: In progress
- **Done**:
  - 讀取子專案 STATE / ROADMAP，確認目前可重用的核心能力集中在 `backend/capital_api/`
  - 盤點現有模組：`windows_monitor.py`、`tick_processor.py`、`alert_engine.py`、`notifier.py`、`price_target.py`
  - 從使用者貼文與附件截圖整理核心需求：單商品、TradingView 截圖分析、定時報告、Telegram 指令、AI 自動評估、可選自動下單、低 token 成本
  - 確認這次先做 Spec / 架構規劃，不直接動手實作
- **Next**:
  - 產出功能摘要、MVP 邊界、模組分層與事件流程
  - 補齊 user story / acceptance criteria / 風控規格
- **Blocker**: 尚未確認實際下單 API 範圍（僅 Capital.com? 還是多交易所抽象層）

---

## 開發日誌

**Phase**: A — Windows Capital API
**Status**: In progress — A-01 執行中
**Last activity**: 2026-03-19 — 開始改寫 capital_api/ 核心模組（基於 CapitalAPI_2 官方範例）

---

## 開發日誌

### [2026-03-19] — 專案規格確認完成
- **Phase**: 規格 (Phase 0)
- **Status**: Complete
- **Done**:
  - 確認目標：台指期當沖監控，日盤+夜盤，Tick 精度
  - 確認架構：雙機分工（Windows Capital API + AWS Linux 備援）
  - 確認不使用下單功能（純監控）
  - 確認通知方式：Telegram
  - 盤點現有程式碼，找出關鍵缺口：`_register_quote_handler()` 未實作
  - 建立 ROADMAP.md 與此 STATE.md
- **Next**:
  - 確認前置條件（群益 API 申請狀態 + SKCOM 安裝）
  - 確認後開始 A-01：補完 COM 事件處理器
- **Blocker**: 尚未確認群益 API 申請狀態與 SKCOM 安裝狀態

---

## 開發日誌

### [2026-03-19] — A-01 ~ A-05 完成（Capital API 核心模組全部改寫）
- **Phase**: A — Windows Capital API
- **Status**: A-01~A-05 Complete，待 A-06 Windows 實機測試
- **Done**:
  - `client.py` — 修正 DLL 路徑、改用 `EnterMonitorLONG`、補完錯誤訊息取得
  - `futures_subscriber.py` — 補完 COM 事件處理器（`OnNotifyTicksLONG`、`OnNotifyBest5LONG`）、修正台指期代碼為 `TX00`、正確使用 `comtypes.client.GetEvents`
  - `tick_processor.py` — 新建，Tick 聚合成分鐘K + pandas-ta 計算 MACD/RSI/KD/布林通道
  - `alert_engine.py` — 新建，支援：價格突破、量異常、MACD交叉、RSI超買賣、KD交叉、布林突破、自訂條件
  - `notifier.py` — 新建，Telegram Bot 推播（警示格式化 + 每日籌碼摘要）
  - `windows_monitor.py` — 新建，主程式整合（一鍵啟動，含 Ctrl+C 優雅關閉）
  - `requirements.txt` — 更新加入 pandas、pandas-ta、requests
  - `.env.example` — 更新加入 TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID
- **Key findings from CapitalAPI_2**:
  - 台指期正確代碼：`TX00`（近月通用），非 `TXF202603`
  - 連線報價需用 `SKQuoteLib_EnterMonitorLONG`（非 `EnterMonitor`）
  - 事件註冊：`comtypes.client.GetEvents(skQ, event_obj)`，必須保留引用否則 GC 釋放
  - 價格需除以 100.0（API 回傳整數 × 100）
- **Next**: A-06 — 在 Windows 電腦上實機測試
  1. 複製 `capital_api/` 到 Windows
  2. 複製 `CapitalAPI_2/元件/x64/SKCOM.dll` 到同目錄（或執行 install.bat）
  3. `pip install -r requirements.txt`
  4. 複製 `.env.example` 為 `.env`，填入帳號密碼和 Telegram 設定
  5. `python windows_monitor.py`
- **Blocker**: 需要在 Windows 實機上測試才能驗證 COM 事件是否正常觸發

---

### [2026-03-24] — Mac Mock 測試完成（A-06a）
- **Phase**: A — Windows Capital API
- **Status**: In progress（A-06b Windows 實機待執行）
- **Done**:
  - 建立 pyenv 3.11.9 venv：`backend/capital_api/.venv/`
  - 安裝依賴：`pandas` / `ta` / `python-dotenv` / `requests`（`pandas-ta` 不支援 3.11，改用 `ta`）
  - 修復 `__init__.py`：Mac/Linux 平台不載入 `CapitalClient` / `FuturesSubscriber`（避免 comtypes 爆炸）
  - 修復 `futures_subscriber.py`：`import comtypes.client` 加 try/except 保護
  - Mock 測試結果：TEST 1~5 全部通過
    - Tick 聚合：29 根分鐘K ✅
    - 技術指標：MACD=24.17 / RSI=65.33 / K=66.89 D=59.59 / 布林通道 ✅
    - 警示引擎：觸發 4 個（KD 黃金交叉、向上突破、向下跌破、自訂 RSI>40）✅
  - 執行指令：`echo 'n' | .venv/bin/python3 capital_api/test_mock.py`
- **Next**: A-06b — 在 Windows 實機測試（COM 事件 + SKCOM）
- **Blocker**: 需要 Windows 電腦 + SKCOM 安裝

---

### [2026-03-24] — Mac Mock 測試強化完成（A-06a v2）
- **Phase**: A — Windows Capital API
- **Status**: Complete ✅
- **Done**:
  - 修復 `test_mock.py`：加入 `--ci` 旗標，跳過 TEST 6 互動式 input()，可在 CI/腳本環境執行
  - 修復 `tick_processor.py`：MACD Signal 需要 35 根 K 棒，門檻從 26 改為 35
  - 修復 `tick_processor.py`：`ta` 套件加入 `_safe()` 過濾 NaN，並清除 None 值
  - 修復 `test_mock.py`：TEST 2 模擬根數從 30 改為 40（確保超過 35 根門檻）
  - 最終測試結果（`python test_mock.py --ci`）：
    - TEST 1 ✅ imports（pandas/ta/requests 全過，pandas-ta Mac 預期缺失）
    - TEST 2 ✅ 39 根分鐘K 聚合正常
    - TEST 3 ✅ MACD=31.04 / Signal=30.50 / Hist=0.54 / RSI=64.72 / K=71.00 D=72.98 / 布林通道 ✅
    - TEST 4 ✅ 4 個警示觸發（MACD 黃金交叉、向上突破、向下跌破、自訂 RSI>40）
    - TEST 5 ⚠️ Telegram 未設定（預期跳過）
    - TEST 6 ⏭️ CI 模式跳過
  - 執行指令：`.venv/bin/python3 capital_api/test_mock.py --ci`
- **Next**: A-06b — 在 Windows 實機測試（COM 事件 + SKCOM）
  - 將 `capital_api/` 目錄複製到 Windows
  - 安裝 SKCOM、設定 `.env`、執行 `windows_monitor.py`
- **Blocker**: 需要 Windows 電腦 + SKCOM 安裝

---

### [2026-03-24] — Telegram 推播端對端驗證完成（A-06a v3）
- **Phase**: A — Windows Capital API
- **Status**: Complete ✅
- **Done**:
  - 建立 `test_telegram_direct.sh` — 繞過 Cursor proxy，在系統終端機（iTerm/Terminal.app）直接用 curl 驗證 Telegram API
  - 執行結果：全部 4 則訊息成功推播到 Telegram Bot（@DNS_Checker 頻道）
    1. ✅ Bot Token 有效驗證
    2. ✅ 基本測試訊息（時間戳記）
    3. ✅ 警示格式訊息（MACD 黃金交叉，收盤 21201，指標欄位完整顯示）
    4. ✅ Python `TelegramNotifier.send_message()` 直接呼叫成功
    5. ✅ Python `TelegramNotifier.send_alert()` 完整警示格式（KD 黃金交叉，K=71.0 D=72.9）
  - Bot Token: `8771241397:AAESXT-...`，Chat ID: `229891358`，頻道名稱: `DNS_Checker`
  - 警示格式確認正確：emoji + 分隔線 + 指標欄位（RSI/MACD/KD）全部正常
- **Next**: A-06b — 在 Windows 實機測試（COM 事件 + SKCOM）
  - 將 `capital_api/` 目錄複製到 Windows
  - 安裝 SKCOM、設定 `.env`（填入已驗證的 BOT_TOKEN + CHAT_ID）
  - 執行 `windows_monitor.py`，確認 Tick 接收 + Telegram 推播串通
- **Blocker**: 需要 Windows 電腦 + SKCOM 安裝

---

### [2026-03-26] — GEM 框型偵測整合完成，Mac Mock 全測試通過（A-06a v4）
- **Phase**: A — Windows Capital API
- **Status**: Complete ✅
- **Done**:
  - `test_mock.py` Mock 根數從 40 升至 75（確保 `RectangleDetector` lookback=60 門檻可滿足）
  - TEST 4c 方法1：`get_indicators()['gem']` 正常回傳 GEM 區間資訊
    - status: `in_range`（區間內）
    - 阻力位：21181，支撐位：20992，區間高度：189 點，框型中線：21087
  - TEST 4c 方法2：直接呼叫 `calc_rectangle` / `calc_adam` / `calc_full_plan` / `format_plan_message` 全部正常
    - 區間：21003 ~ 21212（高度 209 點）
    - TP1（框型一倍）：21420，TP2（翻亞當）：21402，SL：20983
  - `tick_processor.py` GEM 整合路徑確認正確：detect() → plan 攤平 → indicators['gem']
  - 全測試結果：TEST 1 ✅ / TEST 2（74 根分鐘K）✅ / TEST 3（MACD/RSI/KD/布林全過）✅ / TEST 4（5 個警示）✅ / TEST 4b（趨勢線+圖表 80715 bytes）✅ / TEST 4c ✅
  - 執行指令：`MPLCONFIGDIR=/tmp/mpl_cache capital_api/.venv/bin/python3 capital_api/test_mock.py --ci`
- **Next**: A-06b — Windows 實機測試（COM 事件 + SKCOM）
- **Blocker**: 需要 Windows 電腦 + SKCOM 安裝

---

## Phase A 任務清單（Windows — Capital API）

- [x] **A-01**: 補完 `futures_subscriber.py` COM 事件處理器
- [x] **A-02**: 新建 `tick_processor.py` — Tick 聚合 + pandas-ta 指標
- [x] **A-03**: 新建 `alert_engine.py` — 警示規則引擎
- [x] **A-04**: 新建 `notifier.py` — Telegram Bot 推播
- [x] **A-05**: 新建 `windows_monitor.py` — 主程式整合
- [x] **A-06a**: Mac Mock 測試通過（2026-03-24）
  - 環境：pyenv 3.11.9 venv，`ta` 套件取代 `pandas-ta`（不支援 3.11）
  - TEST 1~5 全過：Tick 聚合 29 根分鐘K ✅、MACD/RSI/KD/布林通道 ✅、警示引擎觸發 4 個 ✅
  - 修復：`__init__.py` 改為 platform-aware lazy import（Mac 不載入 comtypes）
  - 修復：`futures_subscriber.py` comtypes import 加上 try/except 保護
- [x] **A-06a v3**: Telegram 端對端推播驗證通過（2026-03-24）
  - `test_telegram_direct.sh` 在 iTerm 執行，curl + Python TelegramNotifier 全部成功
  - 基本訊息 ✅、MACD 警示格式 ✅、KD 警示格式 ✅、Python send_alert() ✅
  - BOT_TOKEN / CHAT_ID 已確認有效，頻道：@DNS_Checker (ID: 229891358)
- [x] **A-06a v4**: GEM 框型偵測整合驗證通過（2026-03-26）
  - `test_mock.py` Mock 根數升至 75 根（確保超過 `RectangleDetector` lookback=60 門檻）
  - TEST 4c 方法1 正常：`indicators['gem']` 回傳區間資訊（status=in_range, R:21181, S:20992, H:189點）✅
  - TEST 4c 方法2 正常：`calc_full_plan()` / `format_plan_message()` 輸出完整 GEM 計畫 ✅
  - `tick_processor.py` GEM 整合邏輯確認正確（detect → 攤平 plan 欄位到 indicators['gem']）✅
  - 全部 TEST 1~4c 全過（TEST 5 Telegram 因環境變數未設定預期跳過，TEST 6 CI 跳過）
  - 執行指令：`MPLCONFIGDIR=/tmp/mpl_cache capital_api/.venv/bin/python3 capital_api/test_mock.py --ci`
- [ ] **A-06b**: Windows 實機測試（COM 事件驗證）
  - 安裝 SKCOM、設定 `.env`（填入已驗證的 BOT_TOKEN + CHAT_ID）
  - 執行 `windows_monitor.py`，確認 Tick 接收 + Telegram 推播串通

## Phase B 任務清單（AWS — 盤後 + 夜盤備援）

- [ ] **B-01**: 修復 `taifex_scraper.py` 解析邏輯
- [ ] **B-02**: 新增 `FuturesMinuteData` 資料庫模型
- [ ] **B-03**: 排程器加入夜盤分鐘K任務（15:00–05:00）
- [ ] **B-04**: 每日 15:30 盤後籌碼摘要自動推播
- [ ] **B-05**: Docker Compose + AWS 部署

## Phase C 任務清單（Dashboard — 選配）

- [ ] **C-01**: FuturesDashboard.vue 整合即時圖表
- [ ] **C-02**: 警示規則管理介面
- [ ] **C-03**: 籌碼面板
