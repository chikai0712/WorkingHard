#!/usr/bin/env python3
"""
手動觸發檢測 - 用於測試和調試
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, init_db
from app.checker import run_cycle_check
from app.models import CycleType, CheckCycle, Domain, DomainZone
from datetime import datetime

async def main():
    print("🚀 手動觸發檢測...\n")
    
    init_db()
    db = SessionLocal()
    
    try:
        # 創建新循環
        cycle = CheckCycle(
            cycle_type=CycleType.ABNORMAL_CHECK,
            cycle_number=1,
            iteration=1,
            max_iterations=10,
            started_at=datetime.utcnow(),
            is_active=True,
            total_domains=10  # 先測試 10 個域名
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        
        print(f"📋 循環已建立: {cycle.cycle_id}")
        
        # 獲取待檢測的域名（先測試 10 個）
        domains_list = db.query(Domain).filter(
            Domain.zone == DomainZone.PENDING
        ).limit(10).all()
        
        domain_names = [d.domain for d in domains_list]
        print(f"📝 待檢測域名: {len(domain_names)} 個")
        for i, d in enumerate(domain_names[:5], 1):
            print(f"   {i}. {d}")
        if len(domain_names) > 5:
            print(f"   ... 還有 {len(domain_names) - 5} 個")
        
        # 執行檢測
        print(f"\n🔍 開始檢測...\n")
        result = await run_cycle_check(
            domains=domain_names,
            cycle_id=cycle.cycle_id,
            cycle_type=CycleType.ABNORMAL_CHECK,
            iteration=1
        )
        
        print("\n✅ 檢測完成")
        
        # 查詢結果
        from app.models import TestBatch
        batch = db.query(TestBatch).order_by(TestBatch.batch_id.desc()).first()
        if batch:
            print(f"\n📊 批次統計:")
            print(f"   批次 ID: {batch.batch_id}")
            print(f"   清潔: {batch.clean_count}")
            print(f"   被封鎖: {batch.blocked_count}")
            print(f"   超時: {batch.timeout_count}")
            print(f"   警告: {batch.warning_count}")
            print(f"   部分: {batch.partial_count}")
            print(f"   API 錯誤: {batch.api_error_count}")
        
    except Exception as e:
        print(f"\n❌ 檢測失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
