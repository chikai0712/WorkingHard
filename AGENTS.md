# AGENTS.md — GSD 工作區快速參考

> 這個檔案是給 AI Agent（Cursor、Claude Code 等）的頂層指引。
> 每次 session 開始時，Agent 應先讀取此文件。

## 你是誰，你在做什麼

你正在協助工程師 CK 開發與維護一個多專案技術工作區。
本工作區採用 **GSD（Get Shit Done）規格驅動開發框架**。

## 強制執行的規則

1. **先讀，再動**：每次 session 開始必須先讀 `.planning/STATE.md` 與 `.planning/ROADMAP.md`
2. **先規格，再程式**：任何超過 2 個檔案的修改，必須先確認 ROADMAP.md 中有對應任務
3. **一次一步**：執行完一個步驟後，更新 STATE.md，再繼續下一步
4. **不要亂跑**：如果發現需要修改範圍超出預期，立即停下來告訴使用者

## GSD 框架位置

```
.cursor/
  get-shit-done/          ← GSD 核心框架
    workflows/            ← 工作流程（execute-phase, plan-phase 等）
    commands/gsd/         ← Slash commands 定義
    templates/            ← PROJECT, STATE, ROADMAP 等模板
    references/           ← principles, checkpoints, tdd 等
  rules/
    gsd-workflow.mdc      ← 全局 GSD 規則（alwaysApply: true）
    spec-before-code.mdc  ← 規格優先閘門
    state-tracking.mdc    ← STATE.md 強制更新（alwaysApply: true）
.planning/
  PROJECT.md              ← 專案定義與需求
  ROADMAP.md              ← 執行路線圖
  STATE.md                ← 當前進度存檔點（最重要！）
  config.json             ← GSD 設定（mode, depth, parallelization）
  phases/                 ← 各 Phase 的 PLAN.md 與 SUMMARY.md
```

## 可用的 GSD 指令

| 指令 | 用途 |
|------|------|
| `/gsd/new-project` | 初始化新子專案 |
| `/gsd/create-roadmap` | 建立 ROADMAP.md |
| `/gsd/plan-phase [N]` | 規劃第 N 個 Phase |
| `/gsd/execute-phase [N]` | 執行第 N 個 Phase |
| `/gsd/execute-plan [path]` | 執行單一 PLAN.md |
| `/gsd/resume-task` | 從中斷點恢復 |
| `/gsd/verify-work [N]` | 驗收第 N 個 Phase |
| `/gsd/status` | 顯示當前進度 |
| `/gsd/map-codebase` | 掃描並文件化現有程式碼 |
| `/gsd/debug` | 系統化 debug 流程 |

完整指令列表：`.cursor/commands/gsd/help.md`

## 子專案目錄

```
01-DNS-Monitoring/    ← DNS 監控系統
02-Cloud-Deploy/      ← 雲端部署工具
03-Data-Analytics/    ← 資料分析（股票、匯率等）
04-Games/             ← 遊戲開發
05-Services/          ← 後端服務（Sentinel, BettingService）
06-DevTools/          ← 開發工具與腳本
07-Personal/          ← 個人項目（履歷、其他）
```

## 黃金規則

> **「Read ROADMAP.md, tell me which phase we are at, and only do that phase.」**

每次 session 都從這句話開始。
