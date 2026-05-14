#!/bin/bash

# 完全繞過 .env 檔案的初始化腳本

echo "🚀 初始化 Domain Monitoring System"
echo "===================================="

# 直接使用 docker exec (不透過 docker-compose)
API_CONTAINER=$(docker ps --filter "name=dms-api" --format "{{.Names}}" | head -1)
POSTGRES_CONTAINER=$(docker ps --filter "name=dms-postgres" --format "{{.Names}}" | head -1)

if [ -z "$API_CONTAINER" ]; then
    echo "❌ API 容器未運行,請先執行: docker-compose up -d"
    exit 1
fi

echo "✅ 找到容器: $API_CONTAINER"
echo ""

# 1. 建立資料庫表結構
echo "📊 建立資料庫表結構..."
docker exec -i $API_CONTAINER python << 'PYEOF'
import os
os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'

from app.database import init_db
from app.models import Domain, Nameserver
from sqlalchemy.orm import Session
from app.database import SessionLocal

try:
    print("  建立表結構...")
    init_db()
    print("  ✅ 表結構建立完成")
    
    # 新增 DNS 伺服器
    db = SessionLocal()
    
    if db.query(Nameserver).count() == 0:
        print("  新增 DNS 伺服器...")
        nameservers = [
            Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.1.1"),
            Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.192.1"),
            Nameserver(country_code="US", isp_name="Google", dns_server="8.8.8.8"),
            Nameserver(country_code="US", isp_name="Cloudflare", dns_server="1.1.1.1"),
        ]
        for ns in nameservers:
            db.add(ns)
        db.commit()
        print(f"  ✅ 新增 {len(nameservers)} 個 DNS 伺服器")
    else:
        print("  ⚠️  DNS 伺服器已存在")
    
    db.close()
    
except Exception as e:
    print(f"  ❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "===================================="
echo "✅ 初始化完成!"
echo ""
echo "📍 測試 API:"
echo "   curl http://localhost:8000"
echo ""
echo "📍 查看域名列表:"
echo "   curl http://localhost:8000/api/domains"
echo ""
echo "📍 匯入 Cloudflare 清單:"
echo "   docker exec -i $API_CONTAINER python import_cloudflare.py /app/cloudflare_backup.csv"

