# TradingClaw LITE — CONTEXT

## 任務名稱
TradingClaw LITE 程式交易版規格（Spec First）

## 任務目標
將使用者提供的貼文敘述與介面截圖整理為一份可實作的 MVP 規格，聚焦在「單商品、低 token、AI 盯盤 + 報告 + 半自動/自動交易」的產品方案。

## 需求確認

### 功能需求（自然語言）
- 系統需支援單一商品監控與分析。
- 系統需整合圖表觀測、新聞/宏觀摘要、AI 分析、Telegram 指令與可選交易執行。
- 系統需支援定時報告與手動觸發分析。
- 系統需提供不同自動化層級：AI 建議、AI 確認、直接下單。
- 系統需以低 token 成本運作，優先使用圖像與本地預處理減少上下文負擔。

### User Story
身為一個有自己交易邏輯的散戶交易者，我希望系統能持續監控單一商品的圖表、快訊與消息面，並在符合我定義的邏輯時自動生成報告、給出交易方向，必要時在風控通過後自動下單，以便我不用長時間盯盤也能快速反應市場。

### Acceptance Criteria
1. 使用者可輸入單一商品並手動觸發分析。
2. 系統可設定每 5 分鐘 / 15 分鐘 / 30 分鐘 / 1 小時 / 每日定時報告。
3. AI 分析必須輸出結構化結果：方向、信心、理由、建議動作、失效條件。
4. 低於信心閾值時只能產出監控/報告，不可直接下單。
5. 系統至少支援 `AI建議`、`AI確認`、`直接下單` 三種模式。
6. Telegram 至少支援：查報告、查持倉、觸發分析、全平。
7. 下單前必須經過獨立風控檢查（倉位、冷卻時間、時段、連線、格式驗證）。
8. MVP 先以單商品為主，不處理多商品投組協調。

## 技術規格

### 現有可重用模組
- `backend/capital_api/windows_monitor.py`：監控主流程
- `backend/capital_api/tick_processor.py`：Tick 聚合、技術指標、趨勢線、GEM 框型
- `backend/capital_api/alert_engine.py`：規則引擎
- `backend/capital_api/notifier.py`：Telegram 訊息 / 圖片推播
- `backend/capital_api/price_target.py`：GEM / 框型 /目標價推算

### 預計新增模組（規格層）
- `backend/trading_runtime/trading_orchestrator.py`
- `backend/trading_runtime/risk_guard.py`
- `backend/trading_runtime/strategy_policy.py`
- `backend/trading_runtime/decision_schema.py`
- `backend/capture/tradingview_controller.py`
- `backend/feeds/news_watcher.py`
- `backend/feeds/macro_digest.py`
- `backend/llm/prompt_builder.py`
- `backend/brokers/*.py`

### API / I/O 定義（規格草案）
- 輸入：商品代碼、時間框架、圖表截圖、新聞摘要、宏觀摘要、持倉狀態、交易模式設定
- AI 輸出：`symbol`, `direction`, `confidence`, `action`, `reasons`, `risk`, `invalid_if`
- Risk Guard 輸出：`allow`, `mode`, `checks`, `blocked_reasons`
- Execution 輸出：`submitted`, `rejected`, `position_closed`, `error`

### 資料結構變更
目前僅做規格，不先改資料庫。未來若落地實作，可能新增：
- 決策紀錄表
- 下單審核紀錄表
- 報告快取表
- 事件佇列 / 任務排程狀態

## 風險評估

### 下游影響功能
- 現有 `capital_api` 監控主流程可能被抽象成 trading runtime 底盤
- Telegram 指令邏輯可能從 notifier 擴展成 command handler
- 若加入 broker adapter，會影響現有券商串接邊界

### 需要的測試類型
- Unit：decision schema、risk guard、strategy policy
- Integration：TradingView 擷取 → AI 分析 → Telegram 報告
- Integration：AI 決策 → risk guard → broker adapter
- Manual / paper trading：模擬訊號與人工測試
- E2E（後期）：完整自動下單鏈路

### 預估影響範圍
中～大（因為會新增一條交易 runtime 軸線）

## 核心限制 / 設計原則
1. 單商品 MVP 優先。
2. 低 token 成本優先於模型堆料。
3. 本地可做的預處理不要全部丟給 LLM。
4. AI 負責判斷，不直接繞過 deterministic 風控。
5. 所有自動下單都必須可回溯。
6. 先做規格，不在本輪直接實作。

## Forbidden Zones
- 不修改既有 Capital API 底層登入與 COM 事件核心邏輯（除非後續明確進入實作 Phase）
- 不在本輪直接接實盤自動下單
- 不擴大到多商品投組協調
- 不先做複雜資料庫重構
- 不先做大型前端重寫

## 開發策略
先完成規格 → 拆 MVP Phase → 再逐步進入實作：
1. 分析與報告 MVP
2. 定時任務與 Telegram 指令
3. AI 決策結構化
4. 風控層
5. 半自動 / 自動交易執行器
