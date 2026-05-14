# 🌐 DNS 伺服器來源分析報告

## 📊 三個網站對比分析

### 1️⃣ public-dns.info

#### 特點
- **全球公共 DNS 伺服器資料庫**
- 收錄超過 30,000+ 公共 DNS 伺服器
- 按國家/地區分類
- 提供延遲測試數據
- 定期更新

#### 優勢
✅ 覆蓋範圍廣（全球各地）
✅ 數據量大
✅ 有地理位置信息
✅ 可按國家篩選
✅ 提供性能指標（延遲、可用性）

#### 劣勢
❌ 沒有官方 API
❌ 需要爬蟲抓取
❌ 包含很多小型/不穩定的 DNS
❌ 需要自己過濾品質

#### 適用場景
- 檢測**全球範圍**的 DNS 污染
- 需要**大量樣本**進行統計分析
- 檢測特定**國家/地區**的封鎖情況

---

### 2️⃣ dnschecker.org

#### 特點
- **精選的全球 DNS 伺服器**
- 約 30-50 個主流 DNS
- 按地區分類（美國、歐洲、亞洲等）
- 包含知名 DNS 提供商（Google、Cloudflare、OpenDNS 等）

#### 優勢
✅ 精選高品質 DNS
✅ 穩定可靠
✅ 地理分布均勻
✅ 易於維護
✅ 響應速度快

#### 劣勢
❌ 數量較少（~50 個）
❌ 主要是國際 DNS，缺少中國本地 ISP DNS
❌ 沒有 API
❌ 需要手動維護列表

#### 適用場景
- 檢測**國際範圍**的可訪問性
- 快速驗證全球 DNS 解析
- 作為**基準對照組**

---

### 3️⃣ ipshu.com (zh-hant.ipshu.com)

#### 特點
- **中國大陸 ISP DNS 列表**
- 包含中國電信、聯通、移動等主要運營商
- 按省份/城市分類
- 繁體中文界面

#### 優勢
✅ **專注中國大陸 ISP DNS**
✅ 覆蓋主要運營商
✅ 按地區細分
✅ 對檢測中國封鎖非常有用

#### 劣勢
❌ 只有中國 DNS
❌ 數據更新頻率不明
❌ 沒有 API
❌ 需要爬蟲抓取

#### 適用場景
- 檢測**中國大陸 ISP 封鎖**
- 驗證域名在中國的可訪問性
- 分析不同省份/運營商的封鎖差異

---

## 🎯 推薦策略：三層 DNS 檢測架構

### 架構設計

```
┌─────────────────────────────────────────────────┐
│           DNS 檢測三層架構                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  第一層：國際基準 DNS (dnschecker.org)           │
│  ├─ Google DNS (8.8.8.8, 8.8.4.4)              │
│  ├─ Cloudflare (1.1.1.1, 1.0.0.1)              │
│  ├─ OpenDNS (208.67.222.222, 208.67.220.220)   │
│  ├─ Quad9 (9.9.9.9, 149.112.112.112)           │
│  └─ 其他國際 DNS (~20 個)                        │
│                                                 │
│  用途：作為「真實值」基準，判斷域名是否真的存在    │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  第二層：中國 ISP DNS (ipshu.com)                │
│  ├─ 中國電信 DNS (各省)                          │
│  ├─ 中國聯通 DNS (各省)                          │
│  ├─ 中國移動 DNS (各省)                          │
│  └─ 其他運營商 DNS                               │
│                                                 │
│  用途：檢測中國大陸的 DNS 污染/封鎖              │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  第三層：全球採樣 DNS (public-dns.info)          │
│  ├─ 亞洲各國 DNS (日本、韓國、新加坡等)           │
│  ├─ 歐洲各國 DNS                                 │
│  ├─ 美洲各國 DNS                                 │
│  └─ 其他地區 DNS                                 │
│                                                 │
│  用途：檢測其他國家/地區的封鎖情況                │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔍 檢測邏輯設計

### 判斷流程

```python
def detect_dns_blocking(domain):
    """
    三層 DNS 檢測邏輯
    """
    
    # 第一層：國際基準檢測
    international_result = check_international_dns(domain)
    
    if international_result['success_rate'] < 0.5:
        return {
            'status': 'domain_invalid',
            'reason': '域名本身無效或未配置 DNS'
        }
    
    # 第二層：中國 ISP 檢測
    china_result = check_china_isp_dns(domain)
    
    if china_result['success_rate'] < 0.3:
        return {
            'status': 'china_blocked',
            'reason': '中國大陸 ISP 封鎖',
            'blocked_isps': china_result['failed_isps'],
            'evidence': {
                'international_ok': True,
                'china_blocked': True
            }
        }
    
    # 第三層：全球採樣檢測
    global_result = check_global_dns(domain)
    
    if global_result['success_rate'] < 0.7:
        return {
            'status': 'regional_blocked',
            'reason': '部分地區封鎖',
            'blocked_regions': global_result['failed_regions']
        }
    
    return {
        'status': 'ok',
        'reason': '全球可正常訪問'
    }
```

---

## 📋 實施建議

### 階段 1：基礎實施（立即可用）

**使用 dnschecker.org 的精選 DNS**

```python
# 手動維護的高品質 DNS 列表
INTERNATIONAL_DNS = [
    # Google
    '8.8.8.8', '8.8.4.4',
    # Cloudflare
    '1.1.1.1', '1.0.0.1',
    # OpenDNS
    '208.67.222.222', '208.67.220.220',
    # Quad9
    '9.9.9.9', '149.112.112.112',
    # 其他國際 DNS...
]
```

**優點**：
- ✅ 立即可用
- ✅ 穩定可靠
- ✅ 無需爬蟲
- ✅ 易於維護

---

### 階段 2：增強檢測（中期目標）

**增加中國 ISP DNS（從 ipshu.com 獲取）**

```python
CHINA_ISP_DNS = {
    '中國電信': [
        '202.96.128.86',  # 上海電信
        '202.96.134.133', # 廣東電信
        '202.96.209.133', # 北京電信
        # ...
    ],
    '中國聯通': [
        '202.106.0.20',   # 北京聯通
        '221.5.88.88',    # 廣東聯通
        # ...
    ],
    '中國移動': [
        '221.179.38.38',  # 遼寧移動
        '120.196.165.24', # 江蘇移動
        # ...
    ]
}
```

**實施方式**：
1. 手動從 ipshu.com 複製主要 ISP DNS
2. 定期（每月）更新一次
3. 重點選擇一線城市的 DNS

**優點**：
- ✅ 精確檢測中國封鎖
- ✅ 可分析不同運營商的差異
- ✅ 數據量可控

---

### 階段 3：全球覆蓋（長期目標）

**從 public-dns.info 獲取全球 DNS**

```python
# 爬蟲腳本範例
import requests
from bs4 import BeautifulSoup

def fetch_public_dns_by_country(country_code):
    """
    從 public-dns.info 獲取特定國家的 DNS
    """
    url = f"https://public-dns.info/nameserver/{country_code}.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    dns_list = []
    # 解析 HTML 表格...
    
    return dns_list

# 重點國家
TARGET_COUNTRIES = ['jp', 'kr', 'sg', 'us', 'de', 'uk']
```

**優點**：
- ✅ 全球覆蓋
- ✅ 可檢測多國封鎖
- ✅ 數據豐富

**缺點**：
- ❌ 需要維護爬蟲
- ❌ 數據量大
- ❌ 需要過濾品質

---

## 🎯 推薦方案

### 方案 A：快速實施（推薦）

**DNS 來源**：
- 第一層：dnschecker.org（手動維護 20-30 個國際 DNS）
- 第二層：ipshu.com（手動維護 30-50 個中國 ISP DNS）

**優點**：
- ✅ 快速上線
- ✅ 穩定可靠
- ✅ 維護成本低
- ✅ 足夠檢測 99% 的封鎖情況

**實施步驟**：
1. 從 dnschecker.org 複製國際 DNS 列表
2. 從 ipshu.com 複製中國主要 ISP DNS
3. 寫入資料庫 `nameservers` 表
4. 增加 `region` 和 `isp` 欄位分類

---

### 方案 B：完整方案（進階）

**DNS 來源**：
- 第一層：dnschecker.org（20-30 個）
- 第二層：ipshu.com（50-100 個）
- 第三層：public-dns.info（100-200 個，按國家採樣）

**優點**：
- ✅ 全球覆蓋
- ✅ 數據豐富
- ✅ 可做深度分析

**缺點**：
- ❌ 需要爬蟲
- ❌ 維護成本高
- ❌ 檢測時間長

---

## 💡 資料庫設計建議

### 擴展 nameservers 表

```sql
ALTER TABLE nameservers ADD COLUMN region VARCHAR(50);
ALTER TABLE nameservers ADD COLUMN country_code VARCHAR(10);
ALTER TABLE nameservers ADD COLUMN isp VARCHAR(100);
ALTER TABLE nameservers ADD COLUMN dns_type VARCHAR(20);

-- dns_type: 'international', 'china_isp', 'regional'
```

### 範例數據

```sql
-- 國際 DNS
INSERT INTO nameservers (dns_server, region, country_code, isp, dns_type) VALUES
('8.8.8.8', 'Global', 'US', 'Google', 'international'),
('1.1.1.1', 'Global', 'US', 'Cloudflare', 'international');

-- 中國 ISP DNS
INSERT INTO nameservers (dns_server, region, country_code, isp, dns_type) VALUES
('202.96.128.86', 'Shanghai', 'CN', '中國電信', 'china_isp'),
('202.106.0.20', 'Beijing', 'CN', '中國聯通', 'china_isp');

-- 其他地區 DNS
INSERT INTO nameservers (dns_server, region, country_code, isp, dns_type) VALUES
('168.95.1.1', 'Taiwan', 'TW', 'HiNet', 'regional'),
('203.80.96.10', 'Japan', 'JP', 'IIJ', 'regional');
```

---

## 🔧 檢測邏輯優化

### 分層檢測

```python
@celery_app.task(name='check_single_domain_multilayer')
def check_single_domain_multilayer(domain_id: int):
    """多層 DNS 檢測"""
    db = SessionLocal()
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    
    # 第一層：國際 DNS
    international_ns = db.query(Nameserver).filter(
        Nameserver.dns_type == 'international',
        Nameserver.is_healthy == True
    ).all()
    
    international_result = check_dns_layer(domain, international_ns)
    
    # 第二層：中國 ISP DNS
    china_ns = db.query(Nameserver).filter(
        Nameserver.dns_type == 'china_isp',
        Nameserver.is_healthy == True
    ).all()
    
    china_result = check_dns_layer(domain, china_ns)
    
    # 分析結果
    analysis = analyze_multilayer_result(
        international_result,
        china_result
    )
    
    # 記錄事件
    event = MonitoringEvent(
        domain_id=domain.id,
        event_type='multilayer_dns_check',
        status=analysis['status'],
        details={
            'international': international_result,
            'china': china_result,
            'analysis': analysis
        }
    )
    db.add(event)
    db.commit()
```

---

## 📊 總結與建議

### 立即行動（推薦）

1. **使用 dnschecker.org**
   - 手動複製 20-30 個國際 DNS
   - 作為基準對照組

2. **使用 ipshu.com**
   - 手動複製 30-50 個中國 ISP DNS
   - 重點：電信、聯通、移動的主要城市 DNS

3. **資料庫分類**
   - 增加 `dns_type` 欄位
   - 分層檢測和分析

### 效果預期

✅ 可精確檢測中國大陸的 DNS 污染
✅ 可區分「域名無效」vs「被封鎖」
✅ 可分析不同 ISP 的封鎖情況
✅ 維護成本低，穩定可靠

### 後續擴展

- 增加更多國家/地區的 DNS
- 開發爬蟲自動更新 DNS 列表
- 增加 DNS 性能監控
- 生成封鎖分析報告

---

## 🎯 結論

**最佳方案**：結合使用三個網站

- **dnschecker.org** → 國際基準 DNS（必須）
- **ipshu.com** → 中國 ISP DNS（必須，針對你的需求）
- **public-dns.info** → 全球採樣 DNS（可選，進階功能）

這樣的組合可以：
1. ✅ 準確判斷域名是否被中國封鎖
2. ✅ 區分不同運營商的封鎖情況
3. ✅ 提供全球可訪問性視圖
4. ✅ 維護成本可控

需要我幫你實施這個方案嗎？

