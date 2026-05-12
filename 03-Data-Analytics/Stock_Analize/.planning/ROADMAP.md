# ROADMAP — 台指期監控系統

## 專案目標

建立台指期當沖輔助監控系統，提供 Tick 級即時警示與每日盤後籌碼摘要，透過 Telegram 推播通知。

## 成功條件（Definition of Done）

1. Windows 電腦執行 `python windows_monitor.py` 後，能接收台指期 Tick 並計算技術指標
2. 技術指標觸發條件時（例如 MACD 黃金交叉），Telegram 收到推播訊息
3. 每日 15:30 後，Telegram 自動收到三大法人 + 未平倉籌碼摘要
4. 系統穩定運行一個完整交易日（白盤 + 夜盤）無崩潰

## 版本記錄

| 版本 | 日期 | 說明 |
|------|------|------|
| v0.1 | 2026-03-19 | 規格確認，建立 ROADMAP |
| v0.2 | 2026-04-06 | 新增 TradingClaw LITE 程式交易規劃 Phase |

## Phase TC：TradingClaw LITE 程式交易版規劃（Spec Only）

**目標**: 以現有 Capital API / TickProcessor / AlertEngine / Telegram 能力為基礎，規劃一版給散戶使用的輕量 AI 盯盤 + 半自動/自動交易工作流
**預估工期**: 先規格 0.5–1 天，實作依模組拆分 3–7 天
**前置條件**: 明確定義交易風控、可下單券商 API、提示詞 / AI 決策邊界、單商品 MVP 範圍

### 任務：TradingClaw LITE 程式交易規格
- **目標**: 將使用者提供的貼文內容與介面截圖整理成可實作的 MVP 規格
- **方法**: 盤點功能模組、拆出資料流、AI 分析流、交易執行流、風控流
- **驗證**: 產出單商品 MVP 架構圖、模組清單、事件流程與 Phase 拆解
- **影響範圍**: `backend/capital_api/`、未來可能新增 `trading_runtime/`、`prompt/`、`scheduler/` 與設定檔

| 任務 | 狀態 | 說明 | 驗證方式 |
|------|------|------|----------|
| TC-01 | ✅ 完成 | 盤點現有能力與 TradingClaw 截圖功能 | 完成功能矩陣與差距分析 |
| TC-02 | ✅ 完成 | 定義單商品 MVP 的資料流 / 分析流 / 下單流 | 完成事件流程圖與模組邊界 |
| TC-03 | ✅ 完成 | 定義 AI 決策層與風控層規則 | 完成 user story + acceptance criteria |
| TC-04 | ✅ 完成 | 拆解實作 Phase（監控 / 報告 / 訊號 / 下單） | ROADMAP 可逐步執行 |
|
### 規格拆解步驟
- [x] 讀取現有 `capital_api` 核心模組，確認可重用能力
  - 驗證：`windows_monitor.py` / `tick_processor.py` / `alert_engine.py` / `notifier.py` / `price_target.py` 已盤點完成
- [x] 整理使用者貼文與四張 UI 截圖，萃取功能需求與產品定位
  - 驗證：輸出功能摘要、產品定位、MVP 邊界
- [x] 定義 User Story 與至少 3 條以上 Acceptance Criteria
  - 驗證：規格文件內可直接作為後續實作依據
- [x] 定義技術分層：capture / feeds / analysis / strategy / risk / execution
  - 驗證：每層都有清楚責任與輸入輸出
- [x] 盤點風險與 Forbidden Zones，寫入 `CONTEXT.md`
  - 驗證：避免後續實作直接碰到底層交易與 COM 核心
- [ ] 等待使用者確認規格後，再進入下一個實作 Phase
  - 驗證：使用者確認要先做哪個 Phase（分析、報告、風控或下單）

## Phase A：Windows Capital API（第一優先）

**目標**: 在 Windows 電腦上接收台指期 Tick，計算技術指標，觸發 Telegram 警示
**預估工期**: 2–3 天（不含前置條件等待時間）
**前置條件**: 群益 API 申請通過 + SKCOM 安裝完成

**開發策略：Mac 開發驗證完畢後，一次部署到 Windows。**

| 任務 | 狀態 | 說明 | 驗證方式 |
|------|------|------|----------|
| A-01 | ✅ 完成 | 補完 COM 事件處理器 | futures_subscriber.py 事件處理完整 |
| A-02 | ✅ 完成 | Tick 聚合 + ta 指標 | Mock 測試 29 根分鐘K，指標計算正常 |
| A-03 | ✅ 完成 | 警示規則引擎 | Mock 測試觸發 4 個警示 |
| A-04 | ✅ 完成 | Telegram 推播 | notifier.py 完成，待 token 測試 |
| A-05 | ✅ 完成 | 主程式整合 | windows_monitor.py 完成 |
| A-06a | ✅ 完成 | Mac Mock 測試強化 | `python test_mock.py --ci` TEST 1~5 全過，MACD Signal 正常，無 NaN |
| A-06b | 🔲 待做 | Telegram token 實測 | Mac 上設定 token，實際收到推播 |
| A-06c | 🔲 待做 | FastAPI SSE 端點（選配）| 盤中可從 Web 看即時報價 |
| A-07 | 🔲 待做 | Windows 部署 | 全部 Mac 驗證完後一次部署 