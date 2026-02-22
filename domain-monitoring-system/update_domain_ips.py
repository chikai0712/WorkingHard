"""批量更新域名的 IP 白名單"""
import asyncio
import aiodns
import os

# 設定正確的資料庫連接
os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Domain


async def resolve_domain_ips(domain: str) -> list:
    """解析域名的當前 IP"""
    resolver = aiodns.DNSResolver(nameservers=["8.8.8.8"], timeout=5)
    try:
        result = await resolver.query(domain, 'A')
        return [r.host for r in result]
    except Exception as e:
        print(f"  ⚠️  無法解析 {domain}: {e}")
        return []


async def update_domain_ips():
    """自動解析並更新所有域名的 IP"""
    db = SessionLocal()
    
    try:
        # 取得所有域名
        domains = db.query(Domain).all()
        
        # 過濾出 IP 為預設值的域名
        domains = [d for d in domains if "0.0.0.0" in d.expected_ips]
        
        print(f"找到 {len(domains)} 個需要更新 IP 的域名")
        print("="*50)
        
        updated_count = 0
        failed_count = 0
        
        for domain in domains:
            print(f"正在解析: {domain.domain}...", end=" ")
            
            # 解析當前 IP
            ips = await resolve_domain_ips(domain.domain)
            
            if ips:
                domain.expected_ips = ips
                updated_count += 1
                print(f"✅ {', '.join(ips)}")
            else:
                failed_count += 1
                print(f"❌ 解析失敗")
            
            # 每 10 個提交一次
            if updated_count % 10 == 0:
                db.commit()
        
        db.commit()
        
        print("="*50)
        print(f"更新完成!")
        print(f"  ✅ 成功: {updated_count} 個")
        print(f"  ❌ 失敗: {failed_count} 個")
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("開始自動解析域名 IP...")
    asyncio.run(update_domain_ips())

