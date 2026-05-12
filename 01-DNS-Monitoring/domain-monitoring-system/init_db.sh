#!/bin/bash

# 在容器內直接初始化資料庫

echo "🔧 初始化資料庫..."

# 使用 Python 直接建立表結構
docker-compose exec -T api python << 'EOF'
import os
os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'

from app.database import init_db
from app.models import Domain, Nameserver
from sqlalchemy.orm import Session
from app.database import SessionLocal

print("建立資料庫表結構...")
init_db()

print("新增範例 DNS 伺服器...")
db = SessionLocal()

try:
    # 檢查是否已有資料
    if db.query(Nameserver).count() > 0:
        print("DNS 伺服器已存在,跳過初始化")
    else:
        nameservers = [
            Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.1.1"),
            Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.192.1"),
            Nameserver(country_code="US", isp_name="Google", dns_server="8.8.8.8"),
            Nameserver(country_code="US", isp_name="Google", dns_server="8.8.4.4"),
            Nameserver(country_code="US", isp_name="Cloudflare", dns_server="1.1.1.1"),
            Nameserver(country_code="US", isp_name="Cloudflare", dns_server="1.0.0.1"),
        ]
        
        for ns in nameservers:
            db.add(ns)
        
        db.commit()
        print(f"✅ 新增 {len(nameservers)} 個 DNS 伺服器")

except Exception as e:
    print(f"❌ 錯誤: {e}")
    db.rollback()
finally:
    db.close()

print("✅ 資料庫初始化完成!")
EOF

echo ""
echo "✅ 初始化完成!"
echo "現在可以匯入 Cloudflare 域名清單了"

