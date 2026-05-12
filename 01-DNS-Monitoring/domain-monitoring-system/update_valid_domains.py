"""更新所有正常域名的 IP 白名單"""
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
        return []


async def update_valid_domains():
    """更新所有正常域名的 IP"""
    db = SessionLocal()
    
    try:
        # 取得所有啟用且 IP 不是 0.0.0.0 的域名
        domains = db.query(Domain).filter(Domain.is_active == True).all()
        
        # 過濾出 IP 不是 0.0.0.0 的域名
        valid_domains = [d for d in domains if "0.0.0.0" not in d.expected_ips]
        
        print(f"找到 {len(valid_domains)} 個正常域名需要更新 IP")
        print("="*60)
        
        updated_count = 0
        failed_count = 0
        changed_count = 0
        
        for i, domain in enumerate(valid_domains, 1):
            print(f"[{i}/{len(valid_domains)}] 正在解析: {domain.domain}...", end=" ")
            
            old_ips = set(domain.expected_ips)
            
            # 解析當前 IP
            ips = await resolve_domain_ips(domain.domain)
            
            if ips:
                new_ips = set(ips)
                
                # 檢查 IP 是否有變化
                if old_ips != new_ips:
                    domain.expected_ips = ips
                    changed_count += 1
                    print(f"🔄 IP 已變更: {', '.join(ips)}")
                else:
                    print(f"✅ IP 未變: {', '.join(ips)}")
                
                updated_count += 1
            else:
                failed_count += 1
                print(f"❌ 解析失敗")
            
            # 每 20 個提交一次
            if i % 20 == 0:
                db.commit()
                print(f"  → 已提交 {i} 個域名的更新")
        
        db.commit()
        
        print("="*60)
        print(f"更新完成!")
        print(f"  ✅ 成功解析: {updated_count} 個")
        print(f"  🔄 IP 已變更: {changed_count} 個")
        print(f"  ❌ 解析失敗: {failed_count} 個")
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("開始更新正常域名的 IP...")
    asyncio.run(update_valid_domains())

