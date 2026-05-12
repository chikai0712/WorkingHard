# 地區封鎖檢測系統 - 架構設計與資源需求

## 目標
真正且準確地檢測域名在越南和印尼是否被封鎖或無法訪問

---

## 架構方案

### 方案 A：分散式檢測節點（推薦）

```
┌─────────────────────────────────────────────────────────────┐
│                    中央控制系統（台灣）                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Domain Monitoring System (現有系統)                  │   │
│  │  - 任務調度                                           │   │
│  │  - 數據匯總                                           │   │
│  │  - 告警決策                                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API 調用
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  越南節點     │    │  印尼節點     │    │  其他地區     │
│  (Hanoi)     │    │  (Jakarta)   │    │  (可擴展)     │
├──────────────┤    ├──────────────┤    ├──────────────┤
│ DNS Agent    │    │ DNS Agent    │    │ DNS Agent    │
│ - 本地DNS檢測 │    │ - 本地DNS檢測 │    │ - 本地DNS檢測 │
│ - HTTP檢測   │    │ - HTTP檢測   │    │ - HTTP檢測   │
│ - 回報結果   │    │ - 回報結果   │    │ - 回報結果   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 資源需求詳細分析

### 1. 雲端伺服器（VPS）

#### 越南節點
- **提供商選項**：
  - ✅ **DigitalOcean** - Singapore datacenter (最近越南)
  - ✅ **Vultr** - Singapore datacenter
  - ✅ **Linode** - Singapore datacenter
  - ✅ **AWS EC2** - ap-southeast-1 (Singapore)
  - ⚠️ **越南本地 VPS**（如 BKNS, Viettel IDC）- 需要當地支付方式

- **規格需求**：
  - CPU: 1 vCPU
  - RAM: 1GB
  - 儲存: 25GB SSD
  - 頻寬: 1TB/月
  - **月費**: $5-10 USD

#### 印尼節點
- **提供商選項**：
  - ✅ **DigitalOcean** - Singapore datacenter
  - ✅ **Vultr** - Singapore datacenter
  - ✅ **AWS EC2** - ap-southeast-3 (Jakarta) ⭐ 最佳選擇
  - ✅ **Google Cloud** - asia-southeast2 (Jakarta)
  - ⚠️ **印尼本地 VPS**（如 Biznet, Telkom）

- **規格需求**：同越南節點
- **月費**: $5-10 USD

#### 總成本（VPS）
- 2 個節點 × $10 = **$20 USD/月**
- 年費: **$240 USD/年**

---

### 2. 檢測代理程式（Agent）

#### 技術架構
```python
# 輕量級 Python Agent
├── dns_agent.py          # DNS 檢測模組
├── http_agent.py         # HTTP/HTTPS 檢測模組
├── reporter.py           # 結果回報模組
├── config.yaml           # 配置文件
└── requirements.txt      # 依賴套件
```

#### 功能需求
1. **DNS 檢測**
   - 使用本地 ISP DNS 伺服器
   - 檢測 A 記錄、CNAME、NS 記錄
   - 記錄解析時間和結果

2. **HTTP/HTTPS 檢測**
   - 檢測網站可訪問性
   - 檢測關鍵字內容
   - 記錄 HTTP 狀態碼和響應時間

3. **結果回報**
   - 定期回報到中央系統
   - 使用 HTTPS API
   - 包含時間戳和地理位置

#### 開發成本
- 開發時間: 2-3 天
- 維護成本: 低（自動化運行）

---

### 3. 網路架構

#### 中央系統 API 擴展
```python
# 新增 API 端點
POST /api/agent/report          # 接收 Agent 回報
GET  /api/agent/tasks           # 分發檢測任務
GET  /api/agent/status          # Agent 狀態監控
POST /api/agent/register        # Agent 註冊
```

#### 安全性
- **API 認證**: JWT Token 或 API Key
- **加密傳輸**: HTTPS/TLS
- **防火牆**: 只允許已註冊的 Agent IP

---

### 4. DNS 伺服器列表（當地 ISP）

#### 越南 ISP DNS
```yaml
vietnam:
  - name: VNPT
    dns_servers:
      - 203.162.4.191
      - 203.162.4.190
    note: "需要從越南網路內訪問"
  
  - name: Viettel
    dns_servers:
      - 203.113.131.1
      - 203.113.131.2
    note: "越南最大電信商"
  
  - name: FPT
    dns_servers:
      - 210.245.24.20
      - 210.245.24.21
    note: "越南第二大 ISP"
```

#### 印尼 ISP DNS
```yaml
indonesia:
  - name: Telkom
    dns_servers:
      - 202.134.0.155
      - 202.134.2.5
    note: "印尼最大電信商"
  
  - name: Indosat
    dns_servers:
      - 202.155.0.15
      - 202.155.0.19
    note: "印尼第二大電信商"
  
  - name: XL Axiata
    dns_servers:
      - 202.152.0.2
      - 202.152.2.2
    note: "印尼第三大電信商"
```

---

### 5. 部署方案

#### 方案 A：Docker 容器化（推薦）
```dockerfile
# Agent Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "agent.py"]
```

**優點**：
- ✅ 易於部署和更新
- ✅ 環境一致性
- ✅ 資源隔離

#### 方案 B：Systemd 服務
```ini
[Unit]
Description=DNS Monitoring Agent
After=network.target

[Service]
Type=simple
User=dnsagent
WorkingDirectory=/opt/dns-agent
ExecStart=/usr/bin/python3 /opt/dns-agent/agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### 6. 監控與維護

#### Agent 健康監控
- **心跳檢測**: 每 5 分鐘回報狀態
- **自動重啟**: 失敗時自動重啟
- **日誌收集**: 集中式日誌管理

#### 告警機制
- Agent 離線超過 10 分鐘 → 發送告警
- 檢測失敗率超過 50% → 發送告警
- VPS 資源使用率超過 80% → 發送告警

---

## 成本總結

### 一次性成本
| 項目 | 成本 | 說明 |
|------|------|------|
| Agent 開發 | $0 | 自行開發（2-3天） |
| 系統整合 | $0 | 擴展現有系統 |
| 測試部署 | $0 | 使用試用額度 |
| **總計** | **$0** | |

### 月度成本
| 項目 | 成本 | 說明 |
|------|------|------|
| 越南 VPS | $10 | DigitalOcean/Vultr |
| 印尼 VPS | $10 | AWS Jakarta 或 Singapore |
| 流量費用 | $2 | API 回報流量 |
| **總計** | **$22/月** | |

### 年度成本
- **$264 USD/年** (~NT$ 8,000/年)

---

## 替代方案：第三方服務

### 方案 B：使用現成的監控服務

#### 1. Pingdom (推薦)
- **功能**: 多地區 HTTP/DNS 監控
- **地區**: 包含亞太地區節點
- **價格**: $10-72/月
- **優點**: 免維護、即開即用
- **缺點**: 無法使用當地 ISP DNS

#### 2. UptimeRobot
- **功能**: 基礎 HTTP 監控
- **地區**: 有限的亞太節點
- **價格**: $7-26/月
- **優點**: 便宜、易用
- **缺點**: DNS 檢測功能有限

#### 3. Catchpoint
- **功能**: 企業級監控
- **地區**: 全球 700+ 節點
- **價格**: $500+/月
- **優點**: 功能完整、專業
- **缺點**: 昂貴

---

## 實施建議

### 階段 1：概念驗證（1 週）
1. 在 Singapore VPS 部署測試 Agent
2. 驗證能否訪問越南/印尼 ISP DNS
3. 測試 API 回報機制

### 階段 2：正式部署（1 週）
1. 部署越南和印尼節點
2. 配置自動化監控
3. 整合到現有系統

### 階段 3：優化運營（持續）
1. 監控 Agent 健康狀態
2. 優化檢測頻率
3. 擴展更多地區

---

## 技術風險與對策

### 風險 1：VPS 被封鎖
- **對策**: 準備備用 IP，使用多個提供商

### 風險 2：ISP DNS 不可訪問
- **對策**: 使用公開 DNS + 本地網路測試

### 風險 3：Agent 離線
- **對策**: 自動重啟 + 告警通知

### 風險 4：成本超支
- **對策**: 設定流量上限，使用預付費

---

## 結論

### 推薦方案：**方案 A（分散式檢測節點）**

**理由**：
1. ✅ 成本可控（$22/月）
2. ✅ 完全自主控制
3. ✅ 可擴展性強
4. ✅ 真正的地區檢測

**下一步**：
1. 選擇 VPS 提供商（建議 DigitalOcean + AWS Jakarta）
2. 開發輕量級 Agent
3. 部署測試環境
4. 整合到現有系統

**預計時間**：2-3 週完成
**預計成本**：$264/年

