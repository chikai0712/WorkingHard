#!/usr/bin/env python3
"""
完整的数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加 app 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def init_database():
    """初始化数据库"""
    try:
        # 导入必要的模块
        from app.database import init_db, SessionLocal
        from app.models import Domain, DomainZone
        from app.config import get_settings
        
        settings = get_settings()
        
        print("🔄 初始化数据库...")
        
        # 创建所有表
        init_db()
        
        # 加载域名
        db = SessionLocal()
        try:
            domains_file = settings.domains_file
            with open(domains_file, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            print(f"📝 加载 {len(domains)} 个域名...")
            
            for domain in domains:
                existing = db.query(Domain).filter(Domain.domain == domain).first()
                if not existing:
                    d = Domain(domain=domain, zone=DomainZone.PENDING)
                    db.add(d)
            
            db.commit()
            print(f"✅ 数据库初始化完成")
            
            # 显示统计
            from sqlalchemy import func
            total = db.query(func.count(Domain.domain_id)).scalar()
            print(f"📊 数据库统计: {total} 个域名")
            
        finally:
            db.close()
        
        print("\n✅ 数据库已准备好")
        print("📝 下一步: 重启应用以拉取节点清单")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()
