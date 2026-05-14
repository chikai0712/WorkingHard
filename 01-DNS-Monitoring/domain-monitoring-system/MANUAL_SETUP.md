# 🔧 手動初始化指南

由於遇到 `.env` 檔案權限問題,請按照以下步驟手動完成設定。

## 步驟 1: 確認服務運行

```bash
docker ps | grep dms
```

應該看到 5 個容器在運行:
- dms-postgres
- dms-redis  
- dms-api
- dms-celery-worker
- dms-celery-beat

## 步驟 2: 初始化資料庫

### 方法 A: 使用 Python 腳本 (推薦)

```bash
docker exec -i dms-api python << 'EOF'
import os
os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'

from app.database import init_db
from app.models import Nameserver
from app.database import SessionLocal

# 建立表結構
print("建立資料庫表結構...")
init_db()
print("✅ 完成")

# 新增 DNS 伺服器
db = SessionLocal()
if db.query(Nameserver).count() == 0:
    nameservers = [
        Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.1.1"),
        Nameserver(country_code="US", isp_name="Google", dns_server="8.8.8.8"),
        Nameserver(country_code="US", isp_name="Cloudflare", dns_server="1.1.1.1"),
    ]
    for ns in nameservers:
        db.add(ns)
    db.commit()
    print(f"✅ 新增 {len(nameservers)} 個 DNS 伺服器")
db.close()
EOF
```

### 方法 B: 使用 SQL 直接建立

```bash
docker exec -i dms-postgres psql -U dms_user -d domain_monitoring << 'SQL'
-- 建立 domains 表
CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    expected_ips INET[] NOT NULL,
    expected_ns VARCHAR(255)[] NOT NULL,
    keyword VARCHAR(500),
    check_interval INTEGER DEFAULT 300,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 建立 nameservers 表
CREATE TABLE IF NOT EXISTS nameservers (
    id SERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL,
    isp_name VARCHAR(100) NOT NULL,
    dns_server INET UNIQUE NOT NULL,
    is_healthy BOOLEAN DEFAULT true,
    last_check TIMESTAMP,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 建立 monitoring_events 表
CREATE TABLE IF NOT EXISTS monitoring_events (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER REFERENCES domains(id),
    event_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- 建立 alerts 表
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER REFERENCES domains(id),
    alert_level VARCHAR(10) NOT NULL,
    root_cause VARCHAR(100) NOT NULL,
    evidence JSONB,
    is_resolved BOOLEAN DEFAULT false,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    notified_at TIMESTAMP,
    resolved_at TIMESTAMP
);

-- 新增 DNS 伺服器
INSERT INTO nameservers (country_code, isp_name, dns_server) VALUES
('TW', '中華電信', '168.95.1.1'),
('TW', '中華電信', '168.95.192.1'),
('US', 'Google', '8.8.8.8'),
('US', 'Google', '8.8.4.4'),
('US', 'Cloudflare', '1.1.1.1'),
('US', 'Cloudflare', '1.0.0.1')
ON CONFLICT (dns_server) DO NOTHING;

SELECT 'Database initialized successfully!' as status;
SQL
```

## 步驟 3: 驗證初始化

```bash
# 檢查表是否建立
docker exec dms-postgres psql -U dms_user -d domain_monitoring -c "\dt"

# 檢查 DNS 伺服器
docker exec dms-postgres psql -U dms_user -d domain_monitoring -c "SELECT * FROM nameservers;"

# 測試 API
curl http://localhost:8000
```

## 步驟 4: 匯入 Cloudflare 域名清單

### 4.1 準備 CSV 檔案

從 Google Sheets 匯出 CSV:
1. 開啟「CF DNS backup Plan」
2. 檔案 → 下載 → 逗號分隔值 (.csv)
3. 儲存為 `cloudflare_backup.csv`

### 4.2 複製到專案目錄

```bash
cp ~/Downloads/cloudflare_backup.csv /Users/ckchiu/Desktop/Project/domain-monitoring-system/
```

### 4.3 執行匯入

```bash
docker exec -i dms-api python import_cloudflare.py /app/cloudflare_backup.csv
```

### 4.4 自動解析 IP (可選)

```bash
docker exec -i dms-api python update_domain_ips.py
```

## 步驟 5: 查看結果

```bash
# 查看域名數量
curl http://localhost:8000/api/domains | jq 'length'

# 查看前 10 個域名
curl http://localhost:8000/api/domains?limit=10 | jq '.[].domain'

# 查看 API 文件
open http://localhost:8000/docs
```

## 常見問題

### Q: 如何確認容器正在運行?

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Q: 如何查看 API 日誌?

```bash
docker logs dms-api -f
```

### Q: 如何重新啟動服務?

```bash
docker restart dms-api dms-celery-worker dms-celery-beat
```

### Q: 資料庫連接失敗?

```bash
# 檢查 PostgreSQL
docker exec dms-postgres pg_isready -U dms_user

# 重啟 PostgreSQL
docker restart dms-postgres

# 等待 10 秒後重試
sleep 10
```

## 完整重置 (如果需要)

```bash
# 停止並刪除所有容器和資料
docker-compose down -v

# 重新啟動
docker-compose up -d

# 等待服務啟動
sleep 15

# 重新初始化 (使用上面的方法 A 或 B)
```

## 成功標誌

當你看到以下輸出時,表示系統已準備就緒:

```bash
$ curl http://localhost:8000
{"status":"healthy","service":"Domain Monitoring System","version":"1.0.0"}
```

現在你可以開始匯入 Cloudflare 域名清單了! 🎉

