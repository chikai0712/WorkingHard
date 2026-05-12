# CK 多專案工作區 — 完整專案索引

> 最後更新：2026-05-05
> 管理框架：GSD（Get Shit Done）規格驅動開發

---

## 目錄總覽

| # | 目錄 | 用途 | 子專案數 |
|---|------|------|---------|
| 01 | `01-DNS-Monitoring/` | DNS 監控與檢測 | 6 |
| 02 | `02-Cloud-Deploy/` | 雲端部署與 IaC | 3 |
| 03 | `03-Data-Analytics/` | 資料分析與爬蟲 | 4 |
| 04 | `04-Games/` | 遊戲開發 | 4 大類 / 11 款 |
| 05 | `05-Services/` | 後端服務 | 3 |
| 06 | `06-DevTools/` | 開發工具與腳本 | 5 |
| 07 | `07-Personal/` | 個人項目與履歷 | 4 |
| 08 | `08-Database/` | 資料庫學習 | 1 |
| — | 根目錄獨立專案 | 見下方 | 6 |

---

## 01-DNS-Monitoring/ — DNS 監控系統

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `bind-dns-local/` | Docker + BIND9 | 本地 DNS Server，Docker Compose 部署，含 failover / monitor 腳本 |
| `DNS/` | Python | DNS BCP 災難復原計畫、SSL 憑證管理器、Google Cloud DNS API 整合 |
| `DNS-Checker/` | Python | 多 NS 域名檢測工具，含白名單、自動測試、API 文檔 |
| `DNS-HA-Simulator/` | Docker Compose | DNS 高可用模擬器，主/備站切換測試環境 |
| `domain-monitoring-system/` | Python + Celery + Docker | 完整域名監控系統，含 DB、Cloudflare 整合、Uptime 監控 |
| `Host DNS/` | K8s + Shell | 雲端 DNS 託管方案評估（AWS/GCP 費用估算、Mlytics vs Cloudflare 比較） |
| `Multi-NS/` | — | 多 NS 相關（空目錄或早期實驗） |

---

## 02-Cloud-Deploy/ — 雲端部署工具

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `terraform-cdn-setup/` | Terraform | AWS CloudFront + Route53 + GCP CDN 的 IaC 設定 |
| `Website/` | Shell + Terraform | AWS EC2 部署自動化、DNS failover 測試、Wireshark 封包分析 |
| `websites/` | HTML | 測試用靜態網站（site1-test, site2-gaming），分 AWS / Google 版本 |

---

## 03-Data-Analytics/ — 資料分析

| 子專案 | 技術棧 | 狀態 | 說明 |
|--------|--------|------|------|
| `Stock_Analize/` | Python + Vue.js + 群益 API | 🔄 In progress | 台指期貨監控系統，三大法人資料、前後端分離 |
| `Cloudflare-DNS-data/` | Python | 🔲 Pending | Cloudflare DNS Analytics + Mlytics API 數據報表 |
| `XE-Rate-Scraper/` | Python + Selenium | ✅ Stable | XE 匯率爬蟲，含登入 / 2FA / Cookie 處理 |
| `CDN/DNS Management/` | FastAPI + Next.js | — | 多 DNS Provider 管理平台（GoDaddy / Namecheap），前後端分離 |

---

## 04-Games/ — 遊戲開發

### BrawlStars 風格遊戲

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `BrawlStars/` | JS + Phaser | 荒野亂鬥風格遊戲，含 AI 角色生成器 |

### HTML5 小遊戲集（`Game/`）

| 子專案 | 說明 |
|--------|------|
| `Cat-Pizza/` | 貓咪披薩遊戲 |
| `Cat-Pizza-Kids/` | 兒童版貓咪披薩 |
| `Paint/` | 塗色本，含圖片下載工具 |
| `Popcorn-Kingdom/` | 爆米花王國經營遊戲，含角色 / 建築 / 資源系統 |
| `Sanrio-Pizza-Shop/` | 三麗鷗披薩店 |
| `Sanrio-Popcorn-Game/` | 三麗鷗爆米花遊戲，支援 iPad 連線 |
| `Shiba-Bubble-Tea/` | 柴犬珍珠奶茶遊戲 |

### 其他遊戲

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `IdiomGame/` | JS | 成語遊戲，含 AI 圖片生成整合 |
| `Pokemon-Battle-Game/` | Python + Pygame | 寶可夢對戰遊戲，自訂圖片資源 |

---

## 05-Services/ — 後端服務

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `BettingService/` | Go | 投注服務微服務（Gateway + Order Service），K8s 部署、GitLab CI/CD、Canary 發布、Prometheus 監控 |
| `sentinel.backend/` | C# (.NET) | 訪客指紋 / 風控系統後端，Auth、Proxy、異常登入偵測、Distil 整合 |
| `sentinel.frontend/` | Vue.js + Tailwind | Sentinel 前端 Dashboard，異常登入告警、訪客圖表、CDN 測試 |

---

## 06-DevTools/ — 開發工具

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `腳本區/` | Shell / txt | 歷年運維腳本收藏（主機監控、MySQL 備份、LAMP/LNMP 安裝、Jenkins 等） |
| `har-tools/` | Python | HAR 檔分析與轉 CSV 工具 |
| `load-testing/` | Node.js | 漸進式負載測試腳本（`creep-load-test.mjs`） |
| `scripts/` | Shell | 部署腳本集（gaming site、SSM、EC2） |
| `simulator/` | Node.js | 瀏覽器指紋模擬器，含 fuzzy hash |

---

## 07-Personal/ — 個人項目

| 子專案 | 說明 |
|--------|------|
| `Resume/` | CK 履歷集：IT Director / SRE / Platform Engineering Manager / Solution Architect，中英文多版本 |
| `Ollie/` | 給小朋友的寶可夢遊戲 |
| `login-demo/` | 登入功能 Demo + 負載測試 |
| `每日三件事/` | 每日待辦記錄 |

---

## 08-Database/ — 資料庫學習

| 子專案 | 技術棧 | 說明 |
|--------|--------|------|
| `mssql-learning/` | Docker + MSSQL | MSSQL 學習環境，含 Docker Compose 與學習路線圖 |

---

## 根目錄獨立專案

| 專案 | 技術棧 | 狀態 | 說明 |
|------|--------|------|------|
| `GlobalpingChecker/` | Python + Flask | ⏸️ Paused (Phase 2) | 智能域名檢測系統 v4.1 / v5，Globalping API 多區域 DNS 檢測，Telegram / Slack 通知，AWS Lambda / EC2 部署 |
| `AWS-deploy/` | Shell + Terraform + Python | — | AWS 部署工具集，CLI 腳本、Terraform IaC、EC2 管理 |
| `my-game/` | CCGS 框架 | — | Claude Code Game Studios 遊戲開發框架，48 個 AI Agent，多引擎支援（Godot / Unity / Unreal） |
| `Claude-Code-Game-Studios/` | CCGS 框架 | — | CCGS 框架 Template / Reference |
| `scripts/` | Shell + Python | — | 全局工具腳本（Globalping 檢測、GPT4 分析、維護腳本） |
| `docs/` | Markdown | — | 全局文件（部署指南、FW2 HA 換機 Runbook、版本說明） |
| `tg_commander.py` | Python | — | Telegram 指令機器人 |

---

## GSD 進度追蹤（有獨立 `.planning/` 的專案）

| 專案 | Planning 路徑 | 狀態 | 當前 Phase |
|------|--------------|------|-----------|
| GlobalpingChecker V5 | `GlobalpingChecker/.planning/` | ⏸️ Paused | Phase 2 — 部署驗證 |
| 台指期監控系統 | `03-Data-Analytics/Stock_Analize/.planning/` | 🔄 In progress | Phase A — Windows 實機測試 |
| Cloudflare DNS data | `03-Data-Analytics/Cloudflare-DNS-data/.planning/` | 🔲 Pending | Phase 0 — 需求確認 |
| XE-Rate-Scraper | `03-Data-Analytics/XE-Rate-Scraper/.planning/` | ✅ Stable | Phase 1 完成 |

恢復進度指令：

```
Read [子專案路徑]/.planning/STATE.md and ROADMAP.md, then tell me current progress.
```

---

## 技術棧統計

| 技術 | 使用位置 |
|------|---------|
| **Python** | DNS-Checker, domain-monitoring, Stock_Analize, XE-Rate-Scraper, Cloudflare-DNS-data, GlobalpingChecker, HAR tools, Pokemon-Battle-Game |
| **JavaScript / Node.js** | 多款 HTML5 遊戲, load-testing, simulator, IdiomGame |
| **Vue.js** | Stock_Analize frontend, sentinel.frontend |
| **Go** | BettingService |
| **C# (.NET)** | sentinel.backend |
| **Terraform** | terraform-cdn-setup, Website, AWS-deploy |
| **Docker** | bind-dns-local, DNS-HA-Simulator, domain-monitoring, GlobalpingChecker, mssql-learning |
| **Shell** | 大量部署 / 監控 / 維護腳本 |
| **FastAPI** | CDN DNS Management backend |
| **Next.js** | CDN DNS Management frontend |

---

## 快速導航

```bash
# 主要專案
cd GlobalpingChecker        # 智能域名檢測
cd AWS-deploy               # AWS 部署工具
cd 05-Services/BettingService  # Go 投注服務

# 資料分析
cd 03-Data-Analytics/Stock_Analize       # 台指期
cd 03-Data-Analytics/XE-Rate-Scraper     # 匯率爬蟲

# 遊戲
cd 04-Games/Pokemon-Battle-Game   # 寶可夢對戰
cd 04-Games/Game/                 # HTML5 小遊戲集

# 文件
cd docs/firewall-cutover-jkopay/  # FW2 HA Runbook
cd 07-Personal/Resume/            # 履歷
```
