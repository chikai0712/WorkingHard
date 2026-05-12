# 多專案工作區 — 主狀態索引

> 這是工作區層級的索引檔案。
> **每個子專案有自己的 STATE.md**，請直接讀對應子專案的 planning 目錄。

## 恢復指令（按專案貼入）

```
# GlobalpingChecker
Read GlobalpingChecker/.planning/STATE.md and ROADMAP.md, then tell me current progress.

# Cloud Deploy
Read 02-Cloud-Deploy/.planning/STATE.md and ROADMAP.md, then tell me current progress.

# 台指期監控（Stock_Analize）
Read 03-Data-Analytics/Stock_Analize/.planning/STATE.md and ROADMAP.md, then tell me current progress.

# Cloudflare DNS data
Read 03-Data-Analytics/Cloudflare-DNS-data/.planning/STATE.md and ROADMAP.md, then tell me current progress.

# XE-Rate-Scraper
Read 03-Data-Analytics/XE-Rate-Scraper/.planning/STATE.md and ROADMAP.md, then tell me current progress.
```

## 子專案索引

| 專案 | 路徑 | 狀態 | 當前 Phase | 上次活動 |
|------|------|------|-----------|----------|
| **GlobalpingChecker V5** | `GlobalpingChecker/.planning/` | ⏸️ Paused | Phase 2 — 部署驗證 | 2026-03-19 |
| **Cloud Deploy** | `02-Cloud-Deploy/.planning/` | 🔄 In progress | Phase 4 — EC2 實機部署驗證 | 2026-05-07 |
| **Personal / Resume** | `07-Personal/Resume/` | ✅ Updated | 履歷分析與 MD 優化版 | 2026-05-08 |
| **台指期監控系統** | `03-Data-Analytics/Stock_Analize/.planning/` | 🔄 In progress | Phase A — A-06b Windows 實機測試 | 2026-03-26 |
| **Cloudflare DNS data** | `03-Data-Analytics/Cloudflare-DNS-data/.planning/` | 🔲 Pending | Phase 0 — 需求確認 | 2026-03-25 |
| **XE-Rate-Scraper** | `03-Data-Analytics/XE-Rate-Scraper/.planning/` | ✅ Stable | Phase 1 完成，Phase 2 選配 | 2026-03 |

## 工作區層級進度

- [x] **Phase 1**: GSD 框架整合（Cursor Rules + `.planning/` 初始化）
- [x] **Phase 2**: 子專案各自建立獨立 STATE.md + ROADMAP.md
- [ ] **Phase 3**: 驗證與調整（根據實際使用回饋優化規則）

---

### [2026-05-12 12:02] — 產出 SRE 履歷完整英文版
- **Phase**: Personal / Resume — 履歷整理
- **Status**: Complete
- **Done**: 依 `07-Personal/Resume/CK-SRE-Resume-2026.md` 內容擴寫英文完整版，輸出至 `07-Personal/Resume/CK-SRE-Resume-2026-EN-Full.md`，保留較多原始中文細節、段落結構與量化成果。
- **Next**: 可再依投遞需求裁切成 2-page ATS 版、SRE 版或 DevOps Manager 版。
- **Blocker**: LinkedIn/GitHub 仍待補；若投遞外商高階職缺，建議再做語氣與篇幅精修。

- **Phase**: Personal / Resume — 履歷整理
- **Status**: Complete
- **Done**: 讀取 `07-Personal/Resume/CK-SRE-Resume-2026.md`，整理成自然英文、可投遞的精簡版，輸出至 `07-Personal/Resume/CK-SRE-Resume-2026-EN.md`。
- **Next**: 若要投遞外商，可再細分為 Full SRE 版、DevOps Manager 版與 2-page ATS 版。
- **Blocker**: 目前為精簡英文版，尚未逐段完整保留所有原始中文細節；LinkedIn/GitHub 仍待補。

- **Phase**: Personal / Resume — 履歷整理
- **Status**: Complete
- **Done**: 分析 `202601 IT Director _ Solution Architect .pdf`，參考既有履歷 Markdown 版本，產出 `07-Personal/Resume/202601-IT-Director-Solution-Architect-履歷優化版.md`，包含履歷分析、定位建議、ATS 友善版內容與後續補強建議。
- **Next**: 視投遞職缺再拆分成 IT Director 版、Solution Architect 版或英文 ATS 版。
- **Blocker**: PDF 文字層抽取有限，已用 OCR 與既有 Markdown 交叉整理；LinkedIn/GitHub URL 尚待補。

- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 更新 `02-Cloud-Deploy/ec2-simple-website/user_data.sh.tftpl`，新增 Browser 版 dig 面板，可查 CNAME/A/AAAA 並推測目前是否經過常見 CDN。
- **Next**: 部署新 EC2 後以 `http://<Elastic-IP>` 驗證 Direct / EC2-Nginx，再接 DNS 後驗證 CDN/DNS 路徑。
- **Blocker**: 尚未實際 apply；DNS 管理位置未確認。

- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 為 `02-Cloud-Deploy` 建立 `.planning/STATE.md`、`ROADMAP.md`、`CONTEXT.md`，並新增 `ec2-simple-website/` Terraform 模組，可使用新 AWS profile `new-website` 在東京區域建立 EC2 + Nginx + Elastic IP。
- **Next**: 在 `02-Cloud-Deploy/ec2-simple-website/` 執行 `./deploy.sh` 進行新 AWS 帳號實機部署驗證。
- **Blocker**: 尚未確認 `clouddeployment168.site` DNS 管理位置；尚未實際 apply。

### [2026-03-26] — 各子專案建立獨立 planning 目錄
- **Phase**: 工作區架構優化
- **Status**: Complete
- **Done**:
  - `GlobalpingChecker/.planning/STATE.md` + `ROADMAP.md` 建立
  - `03-Data-Analytics/Cloudflare-DNS-data/.planning/STATE.md` + `ROADMAP.md` 建立
  - `03-Data-Analytics/XE-Rate-Scraper/.planning/STATE.md` + `ROADMAP.md` 建立
  - `Cloudflare DNS data` 目錄更名為 `Cloudflare-DNS-data`（移除空格）
  - 根目錄 STATE.md / ROADMAP.md 改為索引模式
  - `state-tracking.mdc` 更新，加入子專案 planning 規則
- **Next**: 各子專案依需求繼續開發
- **Blocker**: 無

### [2026-04-11 16:38] — 新增 FortiGate FW2 HA 換機 Runbook
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 建立 `docs/firewall-cutover-jkopay/FW2_HA_Replacement_Runbook.md`，內容包含 HA 建置、路由/NAT 驗證、Smoke Test、回滾條件與拓樸示意。
- **Next**: 依現場型號與實際介面名稱（port/VLAN）替換模板中的參數，進行切換窗預演。
- **Blocker**: 待補現場設備型號、FortiOS 版本與實際 DB Port/白名單來源 IP 清單。

### [2026-04-11 16:40] — Runbook 補充名詞與設計理由
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 更新 `docs/firewall-cutover-jkopay/FW2_HA_Replacement_Runbook.md`，新增 Glossary（HA、SNAT、next-hop、BPDU Guard 等）與每個步驟「為什麼要這樣做」說明。
- **Next**: 依現場設備型號補齊指令差異（Cisco/FortiSwitch）與正式 IP/白名單參數。
- **Blocker**: 尚未取得現場交換器型號與 DB 埠清單。

### [2026-04-11 16:42] — 補充常見錯誤與排障章節
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 在 `docs/firewall-cutover-jkopay/FW2_HA_Replacement_Runbook.md` 新增「常見錯誤與對應症狀」章節，涵蓋 SNAT 漂移、DB ACL、HA flap、STP 誤設、非對稱路由與現場排障順序。
- **Next**: 依實際設備命令語法補上 switch 品牌別檢查指令（Cisco/FortiSwitch）。
- **Blocker**: 仍需現場交換器型號資訊以完成品牌別指令稿。

### [2026-04-11 16:44] — 新增 On-call 快速決策表
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 在 Runbook 新增「故障 -> 指令 -> 判斷標準 -> 回復動作」表格與回滾/觀察決策門檻，方便現場 on-call 快速處置。
- **Next**: 依現場交換器品牌補上對應 show/debug 指令（Cisco/FortiSwitch）。
- **Blocker**: 缺少交換器品牌與型號資訊。

### [2026-04-11 17:25] — 補充 AP/DB 跨平台影響章節
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 在 Runbook 新增「影響 AP 與 DB 的規劃重點（跨平台）」章節，涵蓋共同檢查項與實體機/VMware/Kubernetes 各自風險與檢查指令。
- **Next**: 依現場系統清單補上實際 namespace、DB port、vSwitch/Port Group 名稱。
- **Blocker**: 待取得現場 AP/DB 資訊清單（平台分布與網段）。

### [2026-04-11 17:29] — 新增三階段 AP/DB 可打勾檢查清單
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 在 Runbook 新增「切換前/切換中/切換後」三階段檢查清單，並按實體機/VMware/K8s 細分檢查項與回滾觸發條件。
- **Next**: 依現場實際 DB 類型與命名補上具體參數（DB_PORT、namespace、Port Group）。
- **Blocker**: 尚缺現場資產清單與實際參數。

### [2026-04-13 15:40] — 升級 SOP（最短停機導向）
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 在 Runbook 新增第 14 章「SOP 升級版（最短停機導向）」，補強切換前/中/後與回滾流程，納入 DNS/hosts 快取、連線池重試風暴、K8s probe 與平台差異處置。
- **Next**: 依現場實際應用框架（Java/.NET/Node）補上具體 connection pool 參數建議值。
- **Blocker**: 尚未取得應用框架版本與現行連線池設定。

### [2026-04-13 15:46] — 新增權限管控與 Break-Glass 章節
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 在 Runbook 新增第 15 章「權限與資安管控（Automation Governance）」，包含 RBAC/SoD、Secrets 管理、最小權限、微切分、審計追溯與 Break-Glass SOP。
- **Next**: 與資安/網管確認現場 PAM、CI/CD 與 Runner 網段實際控制策略並填入實參。
- **Blocker**: 尚缺 PAM/CI 權限模型與網路 ACL 現況資料。

### [2026-05-05] — 更新 00-README.md 為完整專案分類索引
- **Phase**: Phase 3 — 驗證與調整
- **Status**: Complete
- **Done**: 重寫 `00-README.md`，包含 8 大分類目錄詳解、根目錄獨立專案、GSD 進度追蹤、技術棧統計與快速導航。
- **Next**: 無特定後續，視需求繼續開發各子專案。
- **Blocker**: 無

### [2026-04-13 19:06] — 產出 FW2 技術規劃摘要版
- **Phase**: Phase 3 — 驗證與調整
- **Status**: In progress
- **Done**: 新增 `docs/firewall-cutover-jkopay/FW2_Technical_Summary.md`，彙整 FW2 架構規劃、最短停機策略、AP/DB 連動風險、回滾門檻與治理要求。
- **Next**: 將摘要版中的 KPI/門檻值改為現場正式值（交易成功率、觀察窗口、回滾 SLA）。
- **Blocker**: 仍待業務與值班團隊確認正式 KPI 門檻與告警策略。
