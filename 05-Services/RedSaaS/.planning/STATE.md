# RedSaaS — 當前進度狀態

## 專案概覽

- **目標**：博弈產業資安自動化平台，先內部使用再對外銷售
- **當前 Phase**：Phase 1 — 內部工具化
- **啟動日期**：2026-07-09

---

### [2026-07-09 00:00] — 專案初始化

- **Phase**: Phase 1 — 內部工具化
- **Status**: In progress
- **Done**: 建立專案目錄結構、ROADMAP.md、STATE.md、初版博弈漏洞 Nuclei templates（IDOR/BOLA、Rate Limit、金額邊界值）、Docker Compose 本地靶場環境設定（crAPI + DVWA + DefectDojo + Nuclei）
- **Next**: 執行 `docker compose up` 啟動靶場環境，對 crAPI 跑第一次 Nuclei 掃描，驗證 templates 有無命中
- **Blocker**: 尚未有實際客戶授權的測試目標；目前只針對本地靶場環境進行驗證

---

---

### [2026-07-11 19:00] — Phase 1-04 Web UI 完成，secureCodeBox 整合計畫開始

- **Phase**: Phase 1 — 內部工具化
- **Status**: In progress
- **Done**:
  - `app.py` Web UI 完成：Flask + 即時 log + 停止按鈕 + 報告預覽
  - 掃描 pipeline 端對端驗證通過（Nuclei → DefectDojo → Word 報告）
  - 修正 Flask GIL 阻塞問題：ThreadPoolExecutor + readline() 非阻塞讀取
  - URL 欄位預設 https://，停止按鈕功能完整
  - Web UI 對外部目標（568win.com）掃描成功啟動
- **Next**: 整合 secureCodeBox（kind 本機 k8s）
  - 待整合工具清單：Nmap、gowitness、OWASP Nettacker、PentAGI
- **Blocker**: 無

- **Phase**: Phase 1 — 內部工具化
- **Status**: In progress
- **Done**:
  - `report-generator/generate_report.py` 完成，288 行
  - DefectDojo API 串接：自動抓 findings、engagement、product 資訊
  - Ollama llama3.2:3b 本地生成繁體中文段落（漏洞描述、風險影響、修補建議）
  - Word 報告輸出：封面、執行摘要統計、漏洞詳情、附錄
  - 端對端測試：10 個 findings → Word 報告，約 3 分鐘完成
  - 修正：DefectDojo null 欄位用 `or ""` 處理
- **Next**: Phase 1-04 — 基礎掃描排程（CLI 或最小化 Web UI）
- **Blocker**: 無

- **Phase**: Phase 1 — 內部工具化
- **Status**: In progress
- **Done**:
  - DefectDojo `development_environment` fixture 載入完成
  - Nuclei 掃描結果（10 findings）成功匯入 DefectDojo，Test ID: 1
  - 完整管線驗證：crAPI 靶場 → Nuclei 掃描 → DefectDojo 匯入
  - Phase 1-01 所有驗收條件達成
  - 關鍵修正記錄：
    - DefectDojo image port 從 8080 改為 8081
    - DD_INITIALIZE=true 在新版 image 無效，需手動執行 migrate + createsuperuser + loaddata
- **Next**: Phase 1-02 — 補寫兩個 gambling template（Token 洩漏偵測、後台管理介面預設路徑暴露），並找到適合驗證的博弈平台靶場
- **Blocker**: 無

- **Phase**: Phase 1 — 內部工具化
- **Status**: In progress
- **Done**:
  - DefectDojo migration 手動執行完成（253 個 migration 全部 OK）
  - Superuser `admin` 建立完成（密碼 Admin1234!）
  - API Token 取得：`8d6ba6cb...`
  - Product Type / Product / Engagement 建立完成（ID 各為 1）
  - import-scan API 串接驗證：端點可達，但空白結果檔導致 parser 500（預期行為）
  - compose 修正：DefectDojo port mapping 從 `8001:8080` 改為 `8001:8081`
- **Next**: 用官方 nuclei-templates 對 crAPI 跑掃描取得有效結果，匯入 DefectDojo 完成 Phase 1-01 驗證
- **Blocker**: gambling templates 針對博弈平台路徑設計，crAPI 無對應端點，需用官方 templates 或實際授權目標驗證 TP/FP

- **Phase**: Phase 1 — 內部工具化
- **Status**: In progress
- **Done**:
  - 靶場環境全部 Healthy（crAPI、DVWA、DefectDojo、Redis、Worker）
  - 修復三個 gambling template 的載入錯誤：
    - `agent-panel-no-ratelimit.yaml`：extractor type `header` → `regex`
    - `withdrawal-amount-boundary.yaml`：移除 http block 層的 `tags`、修正 `{{token}}` 變數
    - `idor-player-balance.yaml`：`{{token}}`、`{{uid}}` 改為靜態測試值
  - Nuclei v3.11.0 對 crAPI 掃描成功執行，Templates loaded: 3，無載入錯誤
  - Docker Compose profiles 架構完整：`scan` / `reporting` / `redteam` / `adrecon` / `platform`
- **Next**: 把掃描結果匯入 DefectDojo，驗證 API 串接；接著補寫 Token 洩漏與後台路徑暴露兩個 template
- **Blocker**: gambling templates 針對真實博弈平台路徑設計，crAPI 靶場無法觸發命中（預期行為）；需要找到對應路徑的靶場或實際授權目標才能驗證 TP/FP

---

---

### [2026-07-13 09:30] — 架構升維：加入 AI 行為防禦層 + BAS 閉環設計

- **Phase**: Phase 1.5 紅隊攻擊平台整合 / Phase 1.8（新增）
- **Status**: In progress
- **Done**:
  - ROADMAP.md 架構升維完成，加入三個新核心模組：
    1. **Phase 1.5-02 BAS 閉環**：Caldera + Atomic Red Team，博弈商業邏輯攻擊劇本，24 小時內自動轉防禦規則
    2. **Phase 1.8 AI 行為防禦層**（全新 Phase）：
       - 第一層前線哨兵（1B/8B，<50ms）— 每日吞吐交易日誌建立 UI 操作基線
       - 第二層後台推理大腦（地端 70B，LoRA + RAG）— 跨系統商業邏輯串聯分析
       - UI 行為基準定義：「跳步驟」攻擊偵測（直接呼叫後端 API 繞過前端流程）
    3. Phase 2-03 AI 防禦層客戶版打包
  - 整體系統架構圖更新至 ROADMAP.md（攻擊面 + 閉環 + 防禦面三層結構）
  - secureCodeBox DefectDojo hook 根因確認：孤兒 endpoint_status ID 8–57，Docker Desktop 需重啟後修復
  - DefectDojo 靜態檔（CSS/JS）已修復，介面正常
- **Next**:
  1. 重啟 Docker Desktop → 修復 DefectDojo 孤兒 endpoint → 驗證 nuclei-crapi Done
  2. Phase 1.5-02：部署 MITRE Caldera，設計第一個博弈 BAS 劇本
  3. Phase 1.8-01：定義交易日誌收集格式與 UI 行為基準欄位
- **Blocker**: Docker Desktop 停止運行（需手動重啟），孤兒 endpoint 修復依賴此步驟

### [2026-07-13 13:00] — secureCodeBox K8s Pipeline 端對端驗證完成

- **Phase**: Phase 1.5 — 紅隊攻擊平台整合
- **Status**: In progress
- **Done**:
  - k3d cluster `securecodebox`（1 server + 2 agents）確認正常運行
  - nuclei ScanType 安裝完成（`docker.io/projectdiscovery/nuclei:v3.11.0`）
  - 修復 PVC 問題：`local-path` StorageClass 不支援 `ReadWriteMany`，改用 `--set 'nucleiTemplateCache.enabled=false'` 繞過
  - 網路問題診斷：k3d pod 無法存取 `host.k3d.internal`，改用 Mac 實際 IP `192.168.1.106`
  - crAPI 靶機（`0.0.0.0:888->80/tcp`）掃描成功
  - `crapi-exposure-v2` scan：`Scanning → Parsing → HookProcessing → Done`，共 12 筆 findings
    - [HIGH] Codeigniter - .env File Discovery
    - [HIGH] Laravel - Sensitive Information Disclosure
    - [INFORMATIONAL] HTTP Missing Security Headers（x10）
  - findings.json 從 MinIO 讀取驗證成功（透過 port-forward 9000 + mc CLI）
- **Next**: 把 findings 匯入 DefectDojo，完成完整閉環
- **Blocker**: 無

### [2026-07-13 13:30] — K8s Pipeline 閉環完成

- **Phase**: Phase 1.5 — 紅隊攻擊平台整合
- **Status**: Complete
- **Done**:
  - `scan.py --target http://192.168.1.106:8888 --name "crAPI K8s Pipeline" --templates exposure --no-report` 執行成功
  - DefectDojo Product ID: 8, Engagement ID: 10, Test ID: 21
  - 12 筆 findings 匯入確認：2 High + 10 Info
  - K8s pipeline 端對端完整閉環：Nuclei → MinIO → securecodebox → DefectDojo
- **Next**: 靶機部署進 k3d cluster，解決硬編碼 IP 問題
- **Blocker**: 無

## 待處理技術債

### [TODO] scan YAML 硬編碼 Mac IP 問題
- **檔案**：`lab/scans/crapi-nuclei-scan.yaml`
- **現況**：target URL 寫死 `http://192.168.1.106:888`，換網路環境會失效
- **三個解法**（選一個實作）：
  1. **選項 1 — k3d gateway IP**：在 cluster pod 內跑 `ip route | grep default` 取得固定 gateway IP（通常 `172.x.0.1`），換掉 Mac IP
  2. **選項 2 — 靶機部署進 k3d**（最乾淨）：把 crAPI 改成 K8s manifest 部署到 cluster，用 cluster 內部 DNS `http://crapi-web.crapi.svc.cluster.local`
  3. **選項 3 — scan.py 動態取 IP**（最快）：在 `scan.py` 觸發 K8s scan 前自動執行 `ipconfig getifaddr en0` 取得當下 IP

### [2026-07-15 22:00] — Image 倉庫管理 UI 完成

- **Phase**: Phase 2 — 服務串接
- **Status**: In progress
- **Done**:
  - SQLMap image 從不存在的 `paoloo/sqlmap` 換成 `cytopia/sqlmap`
  - `docker-compose.yml` 新增 `tools` profile，6 個掃描工具版本集中管理
  - 所有掃描工具 image tag 釘死（nmap:7.95 / nuclei:v3.11.0 / zap-stable:2.17.0）
  - `web-pentest.yaml` image tag 同步釘死
  - compose 頂部加升級流程說明文件
  - 後端新增 3 個 API：`/api/images`（查狀態）、`/api/images/<id>/pull`（單一更新）、`/api/images/pull-all`（全部更新）
  - 前端新增「Image 倉庫」tab（sidebar 工具分類下）：
    - 3 欄 grid 顯示每個 image 的下載狀態、版本 tag、大小、建立日期、digest
    - 已下載顯示綠點 + 「更新」按鈕；未下載顯示紅點 + 「下載」按鈕
    - 「全部更新」一鍵下載所有工具 image，即時 log 顯示進度
    - 版本釘定規則說明卡
- **Next**:
  - 重啟 app.py 驗證 Image 倉庫 UI 正常顯示
  - `docker compose --profile tools pull` 補完工具 image（SQLMap 換 image 後應可 pull）
  - 重跑 web-pentest 驗證 8 步驟全部通過
- **Blocker**: 無

### [2026-07-15 20:30] — web-pentest 套組補齊 + ZAP timeout 修正

- **Phase**: Phase 2 — 服務串接
- **Status**: In progress
- **Done**:
  - `web-pentest.yaml` 補上 SQLMap / Gobuster / Nikto 三個 step（共 8 步驟）
  - SQLMap: `--forms --crawl 2 --level 2 --risk 1`（非破壞性）
  - Gobuster: `dirb/common.txt`，20 threads
  - Nikto: `--maxtime 120`
  - ZAP polling timeout: `ascan/view/status` 10s → 30s，xmlreport 30s → 60s
  - Nuclei CVE 路徑修正：`cves/` → `http/cves/`（v10 結構變更）
- **Next**:
  - 重跑 web-pentest 驗證 8 個 step 全部執行
  - 確認 ZAP Active Scan 能跑完（上次 35% 時 timeout）
  - 確認 SQLMap / Gobuster / Nikto image 可以自動 pull
- **Blocker**: 無

### [2026-07-15 19:30] — ZAP engine 修復 + 報告亂碼修正

- **Phase**: Phase 2 — 服務串接
- **Status**: In progress
- **Done**:
  - 診斷 ZAP 結果檔從未產生的根因：`docker run --rm --network host` 在 macOS Docker Desktop 無法連到 `lab-network` 裡的靶機
  - `app.py` ZAP engine 從臨時 container 改為呼叫 ZAP daemon REST API（`localhost:8090`），利用 daemon 已在 `lab-network` 內的優勢
  - 新增 `import time`（原本缺少，ZAP polling loop 需要）
  - ZAP daemon 確認正常：`{"version":"2.17.0"}`，unhealthy 只是 healthcheck 設定問題，不影響功能
  - `generate_report.py` 亂碼修正：
    - 新增 `sanitize_text()`：過濾輸入欄位中的泰文/阿拉伯文等非 CJK/ASCII 字元
    - 新增 `sanitize_ai_output()`：過濾 LM 輸出中混入雜訊語言的行（非 CJK/ASCII 比例 > 30% 的行）
    - Prompt 強化：明確禁止模型使用繁中/英以外語言
  - `import re` 補加至 generate_report.py
- **Next**:
  - 重跑 `web-pentest` preset 驗證 ZAP step 是否正常產生 `/tmp/zap-{job_id}.xml`
  - 確認 DefectDojo ZAP Scan 匯入成功
  - 生成一份新報告驗證亂碼問題已消除
- **Blocker**: 無

### [2026-07-15 20:36] — Web 滲透套組 8/8 步驟全通過

- **Phase**: Phase 2 — 服務串接
- **Status**: In progress
- **Done**:
  - `redsaas-pentest-tools:latest` Docker image build 成功（kali-rolling + sqlmap 1.10.6 + gobuster 3.8.2 + ffuf 2.1.0）
  - 修正 Dockerfile 兩個 bug：`gobuster version` → `gobuster --version`；補裝 `unzip` + `dirb` 讓 wordlist 正常解壓
  - `/usr/share/wordlists/dirb/common.txt` symlink 建立，Gobuster 能正常讀取
  - `web-pentest.yaml` SQLMap / Gobuster 改用 `redsaas-pentest-tools:latest`（不依賴任何第三方 Hub image）
  - `data/image_catalog.py` 建立為唯一 image 版本來源，`routes/images.py` 改 import 它
  - `core/config.py` 自動設定 `DOCKER_HOST` 環境變數（macOS Docker Desktop socket 路徑）
  - `start.sh` 一鍵啟動：kill 舊 process + 等 port 釋放 + 設 DOCKER_HOST + 啟動 Flask + 自動開瀏覽器
  - 架構重構完成：`app.py` 31 行主幹 + 5 個 Blueprint（scan / tools / reports / images / infra）
  - 修正 `scb_client` 頂層 import 造成 Flask 啟動時 block 的問題（改為延遲 import）
  - `ThreadPoolExecutor(max_workers=4)` 取代無上限 `threading.Thread`
  - Web 滲透套組 8 步驟全部執行：
    - Nmap ✓ → Nuclei ✓ → ZAP ✓（19 alerts）→ SQLMap ✓（no injectable params）→ Gobuster ✓ → Nikto ✓ → DefectDojo 匯入 ✓ → AI 報告 ✓
- **Next**:
  - 確認 Gobuster 實際路徑枚舉輸出（有沒有找到 endpoint）
  - Nikto DTD 錯誤根因調查（`+ ERROR: reading DTD`）
  - AI 報告生成完成後確認 Word 報告品質
- **Blocker**: 無



1. **立即**：把 `crapi-exposure-v2` findings 匯入 DefectDojo，完成 K8s pipeline 閉環
2. **技術債（已決定）**：把靶機部署進 k3d cluster
   - crAPI + DVWA 的 Docker Compose 轉成 K8s manifest
   - 部署到獨立 `crapi` namespace
   - nuclei target 改用 cluster 內部 DNS：`http://crapi-web.crapi.svc.cluster.local`
   - 完成後刪除 `lab/scans/crapi-nuclei-scan.yaml` 裡的硬編碼 IP
3. **Phase 1.5-02 啟動**：`docker run -d securecodebox/caldera` 部署中控台
4. **Phase 1.8 設計**：定義博弈平台「正常 UI 操作時序」基準（存款流程、登入流程、代理商後台操作）

### [2026-07-15 17:15] — Web 滲透套組端對端驗證完成

- **Phase**: Phase 2 — 服務串接
- **Status**: In progress
- **Done**:
  - ZAP 輸出格式從 JSON 改為 XML（-J → -x），DefectDojo ZAP Scan parser 相容
  - ZAP target 自動補 https:// scheme（568win.com → https://568win.com）
  - ZAP 路徑 bug 修正（-J /zap/wrk/... → -x 只傳檔名）
  - 0 findings 時仍產出報告（不再 sys.exit(0)）
  - report generator 新增「重現步驟」「修復驗證」兩個區塊
  - Nmap 改用 --top-ports 1000 取代固定 8 個 port
  - web-pentest.yaml 移除 auth block（外部目標不需要登入）
  - target 沒有 scheme 時自動補 https://（源頭標準化）
  - DefectDojo 匯入加入去重（deduplication_on_engagement + close_old_findings）
  - /tmp 結果檔匯入成功後自動清除
  - 報表中心加入 checkbox 多選 + 批次歸檔/還原/刪除
  - log 區塊加入「複製 log」和「清除」按鈕
  - 報告加入「一、測試範圍與環境」表格（目標、工具、測試方法論）
  - 568win.com Web 滲透套組端對端通過：17 個 ZAP findings 匯入 DefectDojo
- **Next**:
  - 等 engagement #21 AI 報告生成完成，確認內容品質
  - DefectDojo Engagements 列表加「查看」連結（直接跳到 DD）
  - 考慮加入掃描歷史頁面顯示每次掃描的目標和 findings 數
- **Blocker**: 無

- **Phase**: Phase 2 — 服務串接
- **Status**: In progress
- **Done**:
  - crAPI 自動登入取 JWT，注入 Nuclei `-H "Authorization: Bearer xxx"`
  - `shlex.split()` 修正 cmd 解析 bug（引號內空格不再被錯誤拆開）
  - `NUCLEI_ALLOWED_UNSIGNED=true` 環境變數讓自訂模板不被跳過
  - Nuclei 官方模板快取到 `lab/nuclei-templates/`，不再每次重新下載
  - 完整掃描：Templates loaded 2163（官方 2155 + 自訂 8），18 matches found
  - DefectDojo 匯入加入 `deduplication_on_engagement + close_old_findings`
  - `generate_report.py` 分頁 bug 修正（`next` URL port 80 問題）
  - report generator 去重邏輯（相同 title+severity 只保留一筆）
  - 報表中心新增：歸檔 / 還原 / 刪除功能
  - ZAP daemon 模式啟動（docker compose --profile redteam）
  - web-pentest.yaml 整合 ZAP baseline scan
  - 自訂模板（`api-security/` + `gambling/`）全部重寫為基於實際 API 測試的路徑
  - gambling 5 個模板全面升級（路徑、攻擊向量、移除假 token）
  - api-security 4 個模板（BFLA mechanic、BFLA orders、PII、coupon injection）
- **Next**:
  - 等 AI 報告背景生成完成（engagement #16）
  - 執行 web-pentest 套組（含 ZAP）端對端驗證
  - 修正 Nuclei 掃描只剩 8 templates 的 runtime error（官方模板路徑問題）
- **Blocker**: 無

- **Phase**: Phase 1.5-05 中控看板整合
- **Status**: In progress
- **Done**:
  - `app.py` HTML 全面改版（v2）
  - Pipeline 進度條：Nmap → Nuclei → DefectDojo → 報告生成，各階段即時變色
  - 掃描歷史頁面：統計卡（總掃描/High+Critical/Medium/完成數）+ K8s scans 表格
  - Findings 嚴重度統計列（Critical/High/Medium/Low/Info 分色）
  - `scb_client.py` 修正：MinIO port 9001→9000，namespace default→securecodebox-system
  - Python AST 語法驗證通過
- **Next**: 靶機 K8s 化（crAPI + DVWA 部署進 k3d cluster，移除硬編碼 IP 192.168.1.106）
- **Blocker**: 無
