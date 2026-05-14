# CK 多專案工作區 (Multi-Project Workspace)

## What This Is

這是一個個人技術工作區，涵蓋多個獨立子專案：DNS 監控系統、雲端部署工具、資料分析、遊戲開發、個人服務，以及開發工具腳本。所有專案由同一位工程師（CK）開發與維護，面向不同的技術與業務場景。

## Core Value

**讓 AI Agent 按規格執行，而不是按直覺亂跑。** 每個任務必須先有計畫，再有執行，最後有驗證。

## Requirements

### Validated

- ✓ GSD 框架已安裝 (`.cursor/get-shit-done/`) — 提供完整工作流程指令
- ✓ GSD 指令集已就緒 (`.cursor/commands/gsd/`) — 所有 slash commands 可用
- ✓ 專案目錄結構已組織 (01~07 分類) — existing

### Active

- [ ] Cursor Rules (`gsd-workflow`, `spec-before-code`, `state-tracking`) 整合 GSD 框架
- [ ] `.planning/` 目錄初始化，作為 Agent 的規格驅動開發根目錄
- [ ] 建立統一的 ROADMAP.md 與 STATE.md，支援跨 session 恢復

### Out of Scope

- 自動化 CI/CD 整合 — 各子專案獨立管理
- 統一 monorepo 打包 — 各專案技術棧差異太大
- 多人協作功能 — 單人工作區

## Context

### 技術環境

- **Shell**: zsh on macOS (darwin 24.6.0)
- **Editor**: Cursor IDE with Claude Opus
- **Version Control**: Git (monorepo 風格，單一根目錄)
- **子專案技術棧**: Node.js / Python / Shell / HTML+JS (視專案而定)

### 現有 GSD 安裝

`.cursor/get-shit-done/` 已有完整框架：
- `workflows/` — 15 個工作流程（execute-phase, plan-phase, resume-task 等）
- `commands/gsd/` — 30+ 個 slash commands
- `templates/` — state, roadmap, project, phase-prompt 等模板
- `references/` — principles, checkpoints, tdd, git-integration 等參考文件

### Cursor Rules 位置

`.cursor/rules/` — `.mdc` 格式，alwaysApply 規則會在每次 session 自動載入。

## Constraints

- **Tech Stack**: 各子專案獨立，不強制統一框架
- **Agent Scope**: 每次 session 只處理一個子專案的任務
- **Context Limit**: 超過 15 輪對話必須開新 session 並從 STATE.md 恢復
- **File Safety**: 修改任何子專案前必須先確認 ROADMAP.md 中該任務存在

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|----------|
| 使用 `.cursor/rules/*.mdc` 而非 `.cursorrules` | Cursor 新版推薦格式，支援 alwaysApply 與 glob | — Pending |
| GSD 框架放在 `.cursor/get-shit-done/` | 已有完整安裝，不重複建立 | ✓ Good |
| `.planning/` 作為 spec 文件根目錄 | 與 GSD 框架慣例一致 | — Pending |
| STATE.md 作為跨 session 存檔點 | 解決 Agent Context Rot 問題的核心機制 | — Pending |

---
*Last updated: 2026-03-12 after workspace initialization*
