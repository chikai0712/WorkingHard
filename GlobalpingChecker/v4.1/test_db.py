#!/usr/bin/env python3
"""
測試 V4.1 應用啟動
"""
import sys
import os

# 添加路徑
sys.path.insert(0, '/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1')

from app.config import get_settings
from app.database import get_db, SessionLocal
from app.models import Domain, TestBatch

def test_database():
    """測試數據庫連接"""
    print("🔍 測試數據庫連接...")
    
    settings = get_settings()
    print(f"📊 數據庫 URL: {settings.database_url}")
    
    db = SessionLocal()
    try:
        # 測試查詢
        domain_count = db.query(Domain).count()
        batch_count = db.query(TestBatch).count()
        
        print(f"✅ 數據庫連接成功！")
        print(f"   - 域名數量: {domain_count}")
        print(f"   - 批次數量: {batch_count}")
        
        # 測試寫入
        from app.models import SystemLog
        log = SystemLog(
            log_type="TEST",
            message="測試寫入",
            details="驗證數據庫可寫"
        )
        db.add(log)
        db.commit()
        print(f"✅ 數據庫寫入測試成功！")
        
        return True
    except Exception as e:
        print(f"❌ 數據庫測試失敗: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
