#!/usr/bin/env python3
"""
GlobalpingChecker V4.1 - 模擬數據生成器
基於實際數據庫結構，生成完整的測試數據
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, init_db
from app.models import (
    Domain, DomainZone, DomainStatus, TestBatch, DomainResult, 
    NodeDetail, CheckCycle, CycleType
)
from datetime import datetime, timedelta
import random

def main():
    init_db()
    db = SessionLocal()
    
    try:
        print("🚀 開始生成模擬數據...\n")
        
        # 1. 創建檢測循環
        print("📋 創建檢測循環...")
        cycle = CheckCycle(
            cycle_type=CycleType.ABNORMAL_CHECK,
            cycle_number=1,
            iteration=1,
            max_iterations=10,
            started_at=datetime.utcnow() - timedelta(hours=2),
            is_active=False,
            total_domains=100
        )
        db.add(cycle)
        db.flush()
        cycle_id = cycle.cycle_id
        print(f"  ✅ 循環 #{cycle_id} 已建立\n")
        
        # 2. 創建測試批次
        print("📝 創建測試批次...")
        batch = TestBatch(
            cycle_id=cycle_id,
            cycle_type=CycleType.ABNORMAL_CHECK,
            iteration=1,
            test_date=datetime.utcnow() - timedelta(hours=1, minutes=30),
            total_domains=100,
            clean_count=45,
            blocked_count=35,
            timeout_count=10,
            warning_count=5,
            partial_count=3,
            api_error_count=2,
            moved_to_normal=8,
            moved_to_abnormal=12,
            duration_seconds=1234,
            notes="模擬檢測批次 - 演示數據"
        )
        db.add(batch)
        db.flush()
        batch_id = batch.batch_id
        print(f"  ✅ 批次 #{batch_id} 已建立\n")
        
        # 3. 更新域名狀態並創建檢測結果
        print("🔍 更新域名狀態和檢測結果...")
        
        domains = db.query(Domain).filter(Domain.zone == DomainZone.PENDING).limit(100).all()
        
        stats = {"clean": 0, "blocked": 0, "timeout": 0, "warning": 0, "partial": 0, "error": 0}
        
        for i, domain in enumerate(domains):
            rand = random.random()
            
            if rand < 0.45:
                status = DomainStatus.CLEAN
                zone = DomainZone.NORMAL
                stats["clean"] += 1
            elif rand < 0.80:
                status = DomainStatus.BLOCKED
                zone = DomainZone.ABNORMAL
                stats["blocked"] += 1
            elif rand < 0.90:
                status = DomainStatus.TIMEOUT
                zone = DomainZone.ABNORMAL
                stats["timeout"] += 1
            elif rand < 0.95:
                status = DomainStatus.WARNING
                zone = DomainZone.ABNORMAL
                stats["warning"] += 1
            elif rand < 0.98:
                status = DomainStatus.PARTIAL
                zone = DomainZone.ABNORMAL
                stats["partial"] += 1
            else:
                status = DomainStatus.API_ERROR
                zone = DomainZone.PENDING
                stats["error"] += 1
            
            # 更新域名
            domain.zone = zone
            domain.current_status = status
            domain.last_check_time = datetime.utcnow() - timedelta(hours=1, minutes=30)
            domain.total_checks = random.randint(1, 50)
            domain.consecutive_normal = random.randint(0, 20) if zone == DomainZone.NORMAL else 0
            domain.consecutive_abnormal = random.randint(0, 20) if zone == DomainZone.ABNORMAL else 0
            
            # 創建檢測結果
            result = DomainResult(
                batch_id=batch_id,
                domain_id=domain.domain_id,
                domain=domain.domain,
                overall_status=status,
                previous_zone=DomainZone.PENDING,
                new_zone=zone,
                zone_changed=True,
                test_date=datetime.utcnow() - timedelta(hours=1, minutes=30),
                error_message="模擬 API 錯誤" if status == DomainStatus.API_ERROR else None
            )
            db.add(result)
            db.flush()
            
            # 創建節點詳情
            for j in range(random.randint(1, 3)):
                node = NodeDetail(
                    result_id=result.result_id,
                    node_isp=random.choice(["XL Axiata", "INDOSAT", "Telkomsel", "Colt"]),
                    node_asn=random.randint(130000, 150000),
                    node_city=random.choice(["Jakarta", "Bandung", "Surabaya", "Medan"]),
                    node_ip=f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                    target_ip=random.choice(["1.2.3.4", "5.6.7.8", "9.10.11.12", "13.14.15.16"]) if status == DomainStatus.CLEAN else "36.86.63.185",
                    status=status,
                    http_code=200 if status == DomainStatus.CLEAN else (0 if status == DomainStatus.TIMEOUT else 403),
                    response_time_ms=random.randint(50, 500) if status != DomainStatus.TIMEOUT else 0
                )
                db.add(node)
            
            if (i + 1) % 20 == 0:
                print(f"  已處理 {i + 1}/{len(domains)} 個域名...")
        
        db.commit()
        print(f"  ✅ 已處理 {len(domains)} 個域名\n")
        
        # 4. 統計結果
        print("📊 模擬數據統計:")
        print(f"  清潔: {stats['clean']}")
        print(f"  被封鎖: {stats['blocked']}")
        print(f"  超時: {stats['timeout']}")
        print(f"  警告: {stats['warning']}")
        print(f"  部分: {stats['partial']}")
        print(f"  API 錯誤: {stats['error']}")
        print()
        
        # 5. 驗證數據
        print("✅ 驗證數據...")
        normal_count = db.query(Domain).filter(Domain.zone == DomainZone.NORMAL).count()
        abnormal_count = db.query(Domain).filter(Domain.zone == DomainZone.ABNORMAL).count()
        pending_count = db.query(Domain).filter(Domain.zone == DomainZone.PENDING).count()
        
        print(f"  正常區: {normal_count}")
        print(f"  異常區: {abnormal_count}")
        print(f"  待分類: {pending_count}")
        print()
        
        print("=" * 60)
        print("✅ 模擬數據生成完成！")
        print("=" * 60)
        print("\n現在訪問監控頁面查看數據:")
        print("  http://127.0.0.1:8000")
        print()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
