# Ennoconn Interview Guide - Simple English Version
# 樺漢面試指南 - 簡化英文版

## Opening Introduction (開場自我介紹)

**English:**
"Good morning. My name is CK Chiu.
I am an IT Director with 23 years of experience in digital change and global IT management.
I have a special connection with Ennoconn. In 2009, when I worked at Foxconn, I managed the IT work for Ennoconn. So I know the company culture and the IPC industry very well.

I am good at three things:
1. Digital Change: I led projects that grew revenue by 200% and built a data platform with 50TB of data. This fits well with Ennoconn's ESaaS plan.
2. Cost Saving: I have a business mindset. I cut IT costs by 40% using cloud cost control and better design.
3. Global Management: I managed teams across Asia and the US. I set up ISO 27001 and security systems to keep everything safe.

I know both technical work (SAP/Oracle) and business needs. I can help Ennoconn with 'Cloud-to-Edge' work right away. Thank you."

---

## Interview Q&A (面試問答)

### 1. Challenges & Problem Solving (挑戰與解決問題)

**Q: What was your biggest challenge at Foxconn/Ennoconn? How did you solve it?**
**Q: 你在鴻海/樺漢遇過最大的困難是什麼？如何解決？**

**Answer:**
"At that time, the subsidiary did not like headquarters' standard rules. I did not force them. Instead, I used 'Data to Convince' them.

I made an IT cost report. It showed that using standard processes would save $120,000 every year. I also showed them 'Quick Wins' like better monitoring. This built trust. Finally, I raised the IT standard rate to 90%."

---

### 2. Cost Reduction (成本控制)

**Q: How do you save money for the company?**
**Q: 如何幫公司省錢？**

**Answer:**
"I use FinOps to control IT spending better.

For example, I used Cloud Spot Instances for batch work. I also improved the Hybrid Cloud design. This cut yearly IT costs by 35% (over $350,000) while keeping good performance."

---

### 3. Digital Transformation & Results (技術轉型與成效)

**Q: What did you achieve with SAP/Oracle cloud migration?**
**Q: 針對 SAP/Oracle 轉型上雲，你有什麼具體成效？**

**Answer:**
"I led the move from old architecture to Microservices. I used CDC (Change Data Capture) to sync Oracle data to a Data Lake in real-time.

This made data work 70% faster. Business reports changed from 'next day' to 'real-time' for better decisions."

---

## Foxconn/Ennoconn Experience Story (鴻海/樺漢經驗故事)

### Core Challenge: Resistance to Standards
### 核心挑戰：子公司對標準化的抗拒

**Context:**
Ennoconn was growing. They did not like Hon Hai HQ's strict IT rules. They wanted freedom and worried about extra costs.

I could not just give orders. I had to build trust first.

---

### Solution: Data + Flexible Management
### 解決方案：數據 + 彈性管理

#### A. Use Data to Convince (數據驅動說服)

**What I Did:**
- Made a cost report showing $120,000 yearly savings from standard processes
- Showed security risks with numbers to explain why we needed standard firewall rules

**Result:**
Management agreed to firewall standards. Security response time dropped from 2 hours to under 30 minutes.

---

#### B. "Core Control, Edge Flexibility" (核心統一、邊緣彈性)

**What I Did:**
- **Core Control (Must Follow):** ERP/SAP, HR systems, and main security rules (like passwords) controlled by HQ
- **Edge Flexibility (Can Choose):** Business systems can be different if they meet basic requirements. For example, they can pick Cisco or Fortinet, not just one brand.

**Why This Works:**
This shows I understand business needs, not just rules.

---

#### C. Step-by-Step Integration (漸進式整合)

**Phase 1 (Low Risk, High Value):**
Started with "Monitoring and Logs." This was easy and showed quick benefits.

**Phase 2:**
Unified security rules and firewall settings.

**Phase 3:**
Finally changed network design and integrated Active Directory (AD).

---

### Final Results (最終成果)

- Cut integration time by 40%
- Raised IT standard rate to over 90%
- Helped move plants from China to Taiwan (Taoyuan)
- Set up production automation

---

## Management Philosophy (核心管理心法)

### 1. Speak with Data (TCO/ROI)
### 用數據說話

**What I Do:**
Turn "opinions" into "benefits" using numbers.

**Example:**
- Made an IT Cost Dashboard showing $120,000 yearly savings
- Showed security risks with numbers (potential downtime costs)

**Result:**
Convinced management to accept standards. Security response time went from 2 hours to 30 minutes.

---

### 2. Balance Control and Flexibility
### 在控制與彈性間取得平衡

**Governance Model:**
- **Core (Red Lines):** ERP, HR, and main security must be controlled by HQ
- **Edge (Freedom):** Business systems can be different if they meet basic standards

**Provide Options:**
Don't force one brand. Give choices (like Cisco or Fortinet) as long as they meet security needs.

**Local Adjustment:**
Let subsidiaries adjust for local laws (like China Cybersecurity Law, GDPR).

---

### 3. Step-by-Step Approach
### 漸進式整合

**Start Small:**
Begin with "Low Risk, High Value" items like monitoring or backup. These don't disturb daily work but solve problems fast.

**Build Trust:**
After quick wins, move to Phase 2 (security) and then network changes.

**Use Influence:**
Create an IT community where successful teams share results. This makes others want to join, not forced by orders.

---

## Interview Answer Summary (面試回答範例)

**English Version:**
"When managing subsidiaries, my approach is 'Core Control, Edge Flexibility.'

First, I 'Speak with Data.' At Foxconn managing Ennoconn, I made an IT Cost Dashboard. It showed $120,000 yearly savings from standard processes. I also showed security risks with numbers. This made compliance a good business choice for them.

Second, I use 'Step-by-Step Integration.' I don't change core systems right away. I start with 'Quick Wins' like monitoring to solve their problems and build trust.

Finally, I keep flexibility. Core ERP and security are controlled by HQ. But subsidiaries can choose solutions (like hardware brands) that fit local needs, as long as they meet basic standards.

This way, I raised the IT standard rate from 30% to 90% while keeping good working relationships."

---

## Strategic Questions for Ennoconn ESaaS
## 針對樺漢 ESaaS 的策略性提問

### 1. Architecture & Edge Computing (架構與邊緣運算)

**Question:**
"About the ESaaS strategy with Cloud-to-Edge integration. Have we added Edge Caching or Local Survivability at the Edge level (IPC/Gateway)?

For SAP S/4HANA Cloud integration, do we only use Cloud Connector for real-time connection? Or are we planning to put lightweight middleware (like SAP Edge Services) at the factory? This would keep production data running with Zero Downtime even when the network is unstable."

---

### 2. Data Platform & Value Services (數據中台與加值服務)

**Question:**
"ESaaS's main value is turning hardware data into business insights. When planning the Data Middle Platform, how do we combine device data (OT Data) with ERP data (IT Data)?

I used CDC technology with Data Lakehouse to sync data in seconds. Is Ennoconn facing challenges moving from 'next day reports' to 'real-time analysis' on the ESaaS platform? This is where I can help a lot."

---

### 3. Security & Compliance (資安與合規)

**Question:**
"As ESaaS grows, we manage not just internal IT but also client cloud operations (MSP role). For 'Cloud Security,' have we extended DevSecOps to manage firmware updates (OTA) for edge devices?

I'm asking about SBOM (Software Bill of Materials) compliance, which is required in Western markets. I want to know the current automation level and how my experience in global compliance can help the team."

---

## Closing Vision Statement (總結願景)

**English:**
"I see ESaaS not just as a change in how we sell products. It's a rebuild of IT from 'Monolithic' to 'Microservices and Edge Computing.' This is exactly what I did at Foxconn and in the gaming industry—building a flexible, scalable, and secure Cloud-to-Edge platform."

---

## Interview Tips (面試小提醒)

### Key Points:
1. **Use Numbers:** Foxconn managers love numbers. When you say "$120,000" or "35%," say it with confidence.
2. **Show Results:** Always connect your actions to business results (cost savings, time reduction, revenue growth).
3. **Be Specific:** Don't just say "I improved things." Say "I cut costs by 40%" or "I reduced response time from 2 hours to 30 minutes."
4. **Know the Industry:** Show you understand IPC, manufacturing, and Ennoconn's ESaaS strategy.

### Language Tips:
- Speak clearly and slowly
- Use simple words when possible
- Emphasize key terms: Data-Driven, FinOps, Real-time, Zero Downtime
- Practice numbers in English: "$120,000" = "one hundred twenty thousand dollars"

---

## Vocabulary Reference (詞彙參考)

| English | Chinese | Simple Explanation |
|---------|---------|-------------------|
| Digital Transformation | 數位轉型 | Using technology to change business |
| Cost Reduction | 成本控制 | Saving money |
| FinOps | 雲端財務管理 | Managing cloud costs |
| Microservices | 微服務 | Breaking big systems into small parts |
| CDC | 異動資料擷取 | Copying data changes in real-time |
| Data Lake | 數據湖 | Storage for all types of data |
| Edge Computing | 邊緣運算 | Processing data near the source |
| Zero Downtime | 零中斷 | System never stops working |
| DevSecOps | 開發安全維運 | Security in development process |
| SBOM | 軟體物料清單 | List of software components |
| MSP | 託管服務供應商 | Company that manages IT for others |
| Quick Wins | 快速勝利 | Fast, easy improvements |
| Baseline | 基線標準 | Minimum requirements |
| Governance | 治理 | Rules and management structure |

---

**Document Created:** 2026-02-12
**For:** CK Chiu - IT Director Interview Preparation
**Target Company:** Ennoconn Corporation (樺漢科技)

