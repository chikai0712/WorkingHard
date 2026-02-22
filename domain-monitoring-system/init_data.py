"""Sample data initialization script"""
import asyncio
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import Domain, Nameserver

# Override DATABASE_URL for Docker environment
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'


def init_sample_data():
    """初始化範例資料"""
    print("初始化資料庫...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # 檢查是否已有資料
        if db.query(Domain).count() > 0:
            print("資料庫已有資料,跳過初始化")
            return
        
        print("新增範例網域...")
        
        # 新增範例網域
        domains = [
            Domain(
                domain="example.com",
                expected_ips=["93.184.216.34"],
                expected_ns=["a.iana-servers.net", "b.iana-servers.net"],
                keyword="Example Domain",
                check_interval=300
            ),
            Domain(
                domain="google.com",
                expected_ips=["142.250.185.46"],
                expected_ns=["ns1.google.com", "ns2.google.com"],
                keyword="Google",
                check_interval=300
            )
        ]
        
        for domain in domains:
            db.add(domain)
        
        print("新增 ISP DNS 伺服器...")
        
        # 新增常用 DNS 伺服器
        nameservers = [
            # 台灣
            Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.1.1"),
            Nameserver(country_code="TW", isp_name="中華電信", dns_server="168.95.192.1"),
            Nameserver(country_code="TW", isp_name="台灣固網", dns_server="61.31.233.1"),
            
            # 美國
            Nameserver(country_code="US", isp_name="Google", dns_server="8.8.8.8"),
            Nameserver(country_code="US", isp_name="Google", dns_server="8.8.4.4"),
            Nameserver(country_code="US", isp_name="Cloudflare", dns_server="1.1.1.1"),
            Nameserver(country_code="US", isp_name="Cloudflare", dns_server="1.0.0.1"),
            
            # 中國
            Nameserver(country_code="CN", isp_name="中國電信", dns_server="202.96.128.86"),
            Nameserver(country_code="CN", isp_name="中國聯通", dns_server="123.125.81.6"),
            
            # 日本
            Nameserver(country_code="JP", isp_name="NTT", dns_server="210.141.112.163"),
        ]
        
        for ns in nameservers:
            db.add(ns)
        
        db.commit()
        
        print("✅ 範例資料初始化完成!")
        print(f"   - 新增 {len(domains)} 個網域")
        print(f"   - 新增 {len(nameservers)} 個 DNS 伺服器")
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_sample_data()

