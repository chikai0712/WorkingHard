# 邱棋凱 (CK Chiu)
**Platform Engineering Manager | Head of Platform & SRE**

---

## 📋 聯絡資訊
- **Email**: Chikai0712@gmail.com
- **Mobile**: 0921-893-712
- **Location**: 台北市大安區
- **LinkedIn**: [可補充]
- **GitHub**: [可補充]

---

## 💼 專業摘要

擁有 **23 年平台與基礎架構領導經驗**的技術專家，過去 10 年專注於**平台工程、SRE 及內部開發者平台（IDP）建設**。曾在大型遊戲、雲端服務與製造業帶領跨國團隊交付高度自動化的雲端與混合環境。

### 核心價值主張
- ✅ **平台產品化思維**: 設計 IDP 服務 200+ 開發者，自助服務採用率 85%+，IT 服務請求處理時間減少 70%
- ✅ **開發者體驗優化**: 建立 Golden Paths，微服務上線時間從 2 週縮短至 2 天（93% 改善）
- ✅ **SRE 實踐**: 定義 SLO/Error Budget，MTTR 從 45 分鐘降至 8 分鐘，系統可用性 99.95%+
- ✅ **雲原生架構**: K8s 平台支援 17 萬+ CCU，資源利用率提升 40%
- ✅ **FinOps 意識**: 年度雲端成本節省 USD $500k+，TCO 降低 25-30%

---

## 🎯 核心技術能力

### 平台工程與 IDP
- **IDP 框架**: Backstage, 自助式服務平台, Service Catalog, Plugin Development
- **Golden Paths**: 標準化微服務架構, Cookiecutter, Paved Roads
- **容器編排**: Kubernetes (EKS/GKE), Helm Charts, Operators, CRDs, Multi-tenant K8s
- **GitOps**: ArgoCD, Flux, Progressive Delivery, Canary Deployments

### 基礎設施即代碼
- **IaC 工具**: Terraform (模組化設計), Pulumi, Crossplane
- **配置管理**: Ansible, SaltStack
- **Drift Detection**: 配置漂移偵測與自動修復

### SRE 與可觀測性
- **可靠性工程**: SLO/SLI/SLA 定義, Error Budgets, Chaos Engineering
- **監控平台**: Prometheus, Grafana, Alertmanager, PagerDuty
- **可觀測性**: OpenTelemetry, Distributed Tracing, MELT (Metrics, Events, Logs, Traces)
- **事故管理**: Incident Response, Post-mortems, Runbook Automation

### 雲端與網路
- **多雲架構**: AWS, GCP, Azure, 混合雲設計
- **網路**: VPC, Direct Connect, Transit Gateway, SD-WAN, Zero Trust
- **安全**: Security Groups, Firewall Rules, WAF, IPS/IDS

### 自動化與 AI
- **自動化運維**: Python, Go, Shell, Toil Reduction, Auto-remediation
- **AI 整合**: LLM (ChatGPT/Claude API), RAG 架構, 向量資料庫
- **AIOps**: 異常檢測, 自動化根因分析, 智能告警

### 數據平台
- **流處理**: Kafka, KSQL, Flink
- **數據庫**: MySQL, PostgreSQL, Redis, MongoDB
- **監控數據**: ClickHouse, TimescaleDB

---

## 💼 工作經歷

### 🏢 Senior Technical Consultant | 保密公司
**2025.03 - 現在 | 台北 | 團隊: 12 人（平台工程、SRE、基礎架構）**

#### 平台工程與開發者體驗

**Internal Developer Platform (IDP) 建設**
- 擔任平台產品的 **Product Owner**，透過開發者訪談識別痛點，規劃並交付面向 **300+ 開發者**的自助式平台
- 整合 **20+ 服務**（CI/CD、監控、日誌、資安掃描、成本分析、資料庫配置、環境申請）至統一入口
- **成果**: 自助服務採用率 **85%+**，IT 服務請求處理時間減少 **70%**，開發者滿意度 NPS **+45**

**Golden Paths 與標準化**
- 設計應用部署的 "Golden Paths"，使用 Helm Charts 標準化微服務架構
- 建立服務樣板（Cookiecutter），涵蓋 CI/CD、監控、日誌、資安掃描的最佳實踐
- **成果**: 微服務上線時間從 **2 週縮短至 2 天**，部署失敗率降低 **60%**

**基礎設施自助服務**
- 使用 Terraform 和 Ansible 實現自動化資料庫部署，開發者可透過平台自助申請
- 將資料庫配置時間從 **3 天縮短至 5 分鐘**（**99.7% 改善**），消除 **90% 手動配置錯誤**
- **成果**: 年度人力成本節省 **USD $150k+**

#### 雲原生平台架構

**混合雲平台設計**
- 設計並落實整合地端 IDC 與 AWS/GCP 的混合雲架構
- 使用 Terraform/Ansible 實現完整 IaC，所有基礎設施納入版本控制
- **成果**: 支援 **24 小時內於跨雲/跨區域間切換**，降低供應商鎖定風險 **90%**

**Kubernetes 平台管理**
- 建構 EKS/GKE 叢集，使用 HPA、Cluster Autoscaler 實現自動擴縮
- 導入 Helm 統一部署流程，建立 Helm Chart Repository
- **成果**: 資源利用率提升 **40%**，部署成功率 **98%+**

**GitOps 實踐**
- 導入 ArgoCD 實現 GitOps，所有變更均有版本控制與審計紀錄
- 建立 Progressive Delivery 機制（Canary、Blue-Green）
- **成果**: 配置錯誤率降低 **80%**，變更回滾時間從 **30 分鐘降至 2 分鐘**

#### SRE 與可靠性工程

**SLO/Error Budget 機制**
- 為關鍵服務制定 **99.9-99.95% 可用性目標**，建立 SLO 儀表板
- 實施 Error Budget 管理，平衡功能開發與系統穩定性
- **成果**: 關鍵服務可用性達 **99.95%+**，計劃外停機時間減少 **85%**

**可觀測性平台**
- 建立跨雲監控平台（Prometheus/Grafana/Alertmanager）
- 整合 ELK Stack 進行日誌分析，實現分散式追蹤（Jaeger）
- **成果**: MTTD 降至 **2 分鐘內**，MTTR 降至 **30 分鐘以內**

**事故管理流程**
- 建立 24/7 On-call 機制，整合 PagerDuty 實現智能告警路由
- 導入 Blameless Postmortem 文化，建立 Runbook 自動化
- **成果**: 誤報率降低 **50%**，重複事故減少 **70%**

#### FinOps 與成本優化

**成本治理機制**
- 建立 FinOps 治理框架，以標籤與成本儀表板掌握多雲支出
- 實施預算告警與成本歸屬（Chargeback/Showback）
- **成果**: 年度 IT 成本節省 **USD $350k+**，TCO 降低 **35%**

**供應商管理**
- 主導雲端供應商談判，與 AWS/GCP/Cloudflare 簽訂 Enterprise Agreement
- **成果**: 取得 **20%+ 折扣優惠**，年度節省 **USD $80k+**

---

### 🏢 DevOps Manager | AXIOM
**2024.04 - 2024.12 | 台北 | 團隊: 6 人（DevOps/SRE）**

#### 平台工程實踐

**IDP 首版交付**
- 從零設計並交付 Internal Developer Platform，整合 Jenkins、GitLab CI、K8s、監控系統
- 服務 **150+ 開發者**，提供環境配置、CI/CD、監控、日誌的自助服務能力
- **成果**: 環境建立時間從 **2 天降至 15 分鐘**（**98% 改善**），消除 **85% 手動配置錯誤**

**團隊職能建設**
- 建立 DevOps/SRE 團隊職能矩陣，明確界定 Senior/Junior 分級標準
- 製作職能量化表，建立透明的晉升機制
- **成果**: 團隊交付速度提升 **35%**，Sprint 準時交付率 **92%+**

#### SRE 與數據驅動運維

**SLO 機制建立**
- 定義關鍵業務服務的 SLO，針對核心服務設定 **99.9% 可用性目標**
- 使用 Prometheus/Grafana 建立 SLO Dashboard，追蹤 Error Budget
- **成果**: 服務可用性穩定在 **99.9-99.95%** 區間

**數據中心架構**
- 架構設計數據中心基礎設施，使用 Kafka 收集監控資料（Prometheus、Zabbix Metrics）
- 透過 KSQL 進行即時數據轉換與告警規則評估，整合 Slack 實現即時通知
- **成果**: MTTD 從 **15 分鐘縮短至 2 分鐘**（**87% 改善**），MTTR 從 **30 分鐘縮短至 8 分鐘**（**73% 改善**）

#### 網路自動化

**Software-Defined Networking (SDN)**
- 主導從 CLI 基礎防火牆管理遷移至 SDN
- 使用 Terraform 和 Python API 自動化防火牆規則配置，涵蓋 **30+ 據點**
- **成果**: 配置錯誤率降低 **75%**，網路變更部署時間從 **1.5 小時縮短至 8 分鐘**（**91% 改善**）

#### AI 整合

**LLM 驅動的 DevOps**
- 整合 LLM（ChatGPT API）至 DevOps 流程，開發自動化 Code Review 工具
- 運用 LLM 自動生成測試案例，整合至 Jenkins Pipeline
- **成果**: Code Review 時間減少 **55%**，測試覆蓋率提升 **35%**

---

### 🏢 Security Operation Center Manager | Mlytics
**2022.07 - 2023.06 | 台北 | 團隊: 12 人**

#### 團隊與流程優化

**教育訓練體系重建**
- 重新規劃教育訓練流程，減少不必要的訓練項目
- **成果**: 上線時間從 **6 個月縮短至 1 個月**

**流程文件化與自動化準備**
- 重新列舉日常工作與常見工作，製作 SOP 並加入 KB
- **成果**: 流程文件化率從 **20% 提升至 90%**，為自動化奠定基礎

**職級制度建立**
- 重新定義部門職級 JD，將 Promo 流程從主管認定改為制度化
- 列舉 Promo 的具備條件，讓同仁更有規範遵循
- **成果**: 團隊透明度提升，內部晉升率 **60%+**

#### 技術與成本優化

**監控系統完善**
- 利用 Shell 與 Zabbix 完善監控系統，找出閒置機器，分析流量使用
- **成果**: 降低營運成本 **25%**

**自動化工具開發**
- 自行撰寫多樣檢測工具，檢測域名可用與屏蔽
- 內部作業流程自動化，串接 Slack 訊息及後端工具

#### 重大專案

**2022 世界盃**
- 協助跨部門溝通規劃機組及國際資源
- 世界杯開打前後，多次協助客戶抵禦大規模 DDoS 攻擊
- **成果**: 零停機時間，客戶滿意度 **95%+**

**ISO 27001 稽核**
- 擔任資安代表，協助公司完成 ISO 27001:2013 稽核
- **成果**: 一次性通過認證

**自動切換機制**
- 規劃域名自動切換與偵測攻擊的自動切換機制
- 整合工單系統與業務系統至單一介面

---

### 🏢 IT Director | Astro Corp (泰偉電子)
**2016.06 - 2022.05 | 台北 | 團隊: 20-60 人**

#### 雲原生平台建設

**Kubernetes 平台**
- 導入 K8S，自動管理服務，全自動 Scale out and in
- 及時應對瞬間大量玩家連線需求（**17 萬+ 同時在線**）
- **成果**: 環境資源浪費降低 **40%**，年度節省 **USD $200k+**

**Golden Paths 定義**
- 定義應用部署的 "Golden Paths"，標準化 Helm charts
- 協助開發團隊適應 K8s 自動擴展架構
- **成果**: 部署失敗率降低 **60%**

**混合雲架構**
- 地端同步 AWS、GCP 至 K8S 平台
- **成果**: 平台在異常或其他狀況時，可於 **24 小時內快速移轉至雲端**

#### SRE 與 AIOps 實踐

**可觀測性平台**
- 搭建 ELK Log 問題排除與分析
- 轉換監控策略，部署 Observability stack（Prometheus/Grafana）
- **成果**: 問題識別時間減少 **70%**，MTTD 從 **15 分鐘縮短至 2 分鐘**

**AIOps 實踐**
- 從監控開始的完善到相關問題串接後續自動化處理流程
- 實現異常情況下的自動恢復機制
- **成果**: MTTR 減少 **60%**，系統可用性從 **99.5% 提升至 99.95%+**

#### 團隊建設

**24/7 運維團隊**
- 創建 24 小時值班團隊，建立值班流程 SOP、內部 KB 及教育訓練課程
- 規範內部稽核及績效制度

**DevOps 團隊**
- 建立 Devop 團隊，利用 Jenkins、Ansible、Shell 及 Python
- 將程式佈版、更新、偵錯全面自動化

---

### 🏢 Game Technology Department Manager | Gamania (遊戲橘子)
**2011.11 - 2013.06 | 台北 | 團隊: 20 人**

#### 平台與基礎設施

**大規模系統管理**
- 負責管理所有核心業務的系統網路，基礎設施（網絡和服務器）的操作
- 推動監控系統，監控上百個服務器的性能和網絡設備
- **成果**: 支援單遊戲 **17 萬玩家同時在線**

**自動化維護**
- 設計半自動維護流程，降低重複性高的更版工作
- **成果**: 重複性工作減少 **70%**

**可靠性提升**
- 設計金流平台，並且確保連線的同時保護交易的安全
- 超過 10TB 的玩家數據 DR 和 BCP 計劃
- **成果**: 成功減少服務停止時間（從 **4998 小時降至 952 小時**）

---

## 🏆 專業證照

### 管理與資安
- 🎓 **PMP** (Project Management Professional)
- 🎓 **CISM** (Certified Information Security Manager)
- 🎓 **ISO 27001 資安主管**認證

### 技術認證
- 🎓 **RHCE** (Red Hat Certified Engineer)
- 🎓 **MCSE** (Microsoft Certified Systems Engineer)
- 🎓 **CCNP Security** (Cisco Certified Network Professional - Security)

### 規劃中認證（2026）
- **CKA** (Certified Kubernetes Administrator)
- **CKS** (Certified Kubernetes Security Specialist)
- **AWS Certified DevOps Engineer – Professional**
- **FinOps Certified Practitioner**

---

## 🎓 學歷
**世新大學 | 平面傳播科技學系 學士**  
1998 - 2002 | 台北

---

## 🌐 語言能力
- **中文**: 母語
- **英文**: 技術溝通流利（全英文會議、技術文件閱讀、跨國團隊協作）

---

## 🎯 核心成就總覽

### 平台工程效率
- ⚡ 微服務上線時間：從 **2 週縮短至 2 天**（93% 改善）
- 🚀 環境配置時間：從 **2 天縮短至 15 分鐘**（98% 改善）
- 📊 自助服務採用率：**85%+**
- 🎯 部署成功率：**98%+**
- 📉 IT 服務請求處理時間：減少 **70%**

### SRE 與可靠性
- ⏱️ MTTD：縮短至 **2 分鐘內**（87% 改善）
- 🔧 MTTR：從 **45 分鐘降至 8-12 分鐘**（73% 改善）
- 📈 系統可用性：**99.95%+**
- 📉 誤報率：降低 **50%**
- 👥 支援規模：**17 萬+ 同時在線用戶**

### 成本與效率
- 💰 年度成本節省：**USD $500k+**
- 📊 資源利用率：提升 **40%**
- 🎯 TCO：降低 **25-35%**
- ⚡ 配置錯誤率：降低 **75-80%**

### 團隊與管理
- 👨‍💼 管理經驗：**6-60 人**技術團隊
- 🌏 跨國經驗：台灣、中國、菲律賓、柬埔寨、馬來西亞
- 📈 團隊保留率：**95%**
- 🎓 內部晉升率：**60%+**

---

## 📝 職涯願景

作為一位專注於**平台工程與開發者體驗**的技術領導者，我致力於：

1. **降低開發者認知負載**: 透過建立 IDP 與 Golden Paths，讓開發者專注於業務邏輯而非基礎設施
2. **提升組織交付速度**: 透過自動化與標準化，加速軟體交付週期
3. **建立可靠性文化**: 透過 SRE 實踐，在創新與穩定之間取得平衡
4. **實踐 FinOps**: 將成本意識融入架構設計，實現技術與商業的雙贏

我期待加入一個重視**開發者體驗、技術卓越與持續改進**的團隊，將平台工程的最佳實踐帶給組織。

---

**邱棋凱 CK Chiu**  
Email: Chikai0712@gmail.com | Mobile: 0921-893-712  
最後更新：2026-02-11

