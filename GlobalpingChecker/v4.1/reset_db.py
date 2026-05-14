#!/usr/bin/env python3
"""
重置数据库脚本
"""
import os
import sys
from pathlib import Path

# 添加 app 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, SessionLocal
from app.models import Domain, DomainZone
from app.config import get_settings

def reset_database():
    """重置数据库"""
    settings = get_settings()
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    
    print(f"📋 数据库路径: {db_path}")
    
    # 备份现有数据库
    if db_path.exists():
        backup_path = db_path.with_suffix('.db.reset_backup')
        print(f"💾 备份现有数据库到: {backup_path}")
        os.rename(db_path, backup_path)
    
    # 创建新数据库
    print("🔄 初始化新数据库...")
    init_db()
    
    # 加载域名列表
    db = SessionLocal()
    try:
        domains_file = settings.domains_file
        if not os.path.exists(domains_file):
            print(f"⚠️  找不到域名文件: {domains_file}")
            return
        
        with open(domains_file, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"📝 加载 {len(domains)} 个域名...")
        
        for domain in domains:
            existing = db.query(Domain).filter(Domain.domain == domain).first()
            if not existing:
                d = Domain(domain=domain, zone=DomainZone.PENDING)
                db.add(d)
        
        db.commit()
        print(f"✅ 数据库重置完成，已加载 {len(domains)} 个域名")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
