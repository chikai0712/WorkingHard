"""批量管理無效域名的工具腳本"""
import os
os.environ['DATABASE_URL'] = 'postgresql://dms_user:dms_password@postgres:5432/domain_monitoring'

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Domain
from sqlalchemy import text


def list_failed_domains():
    """列出所有無法解析的域名"""
    db = SessionLocal()
    
    try:
        # 使用原生 SQL 查詢 ARRAY 欄位
        result = db.execute(text("""
            SELECT id, domain, expected_ips, is_active 
            FROM domains 
            WHERE '0.0.0.0' = ANY(expected_ips)
            ORDER BY domain
        """))
        
        failed_domains = result.fetchall()
        
        print(f"找到 {len(failed_domains)} 個無法解析的域名:")
        print("="*60)
        
        for i, row in enumerate(failed_domains[:20], 1):
            status = "啟用" if row.is_active else "停用"
            print(f"{i}. {row.domain} - {status}")
        
        if len(failed_domains) > 20:
            print(f"... 還有 {len(failed_domains) - 20} 個")
        
        return len(failed_domains)
        
    finally:
        db.close()


def disable_failed_domains():
    """停用所有無法解析的域名"""
    db = SessionLocal()
    
    try:
        # 使用原生 SQL 更新
        result = db.execute(text("""
            UPDATE domains 
            SET is_active = false 
            WHERE '0.0.0.0' = ANY(expected_ips) 
            AND is_active = true
            RETURNING domain
        """))
        
        disabled_domains = result.fetchall()
        count = len(disabled_domains)
        
        if count == 0:
            print("沒有需要停用的域名")
            return 0
        
        print(f"準備停用 {count} 個無法解析的域名...")
        
        for row in disabled_domains[:10]:
            print(f"  停用: {row.domain}")
        
        if count > 10:
            print(f"  ... 還有 {count - 10} 個")
        
        db.commit()
        
        print(f"\n✅ 成功停用 {count} 個域名")
        return count
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


def clean_old_alerts():
    """清理已解決的舊告警"""
    db = SessionLocal()
    
    try:
        from app.models import Alert
        from datetime import datetime, timedelta
        
        # 刪除 7 天前已解決的告警
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        deleted = db.query(Alert).filter(
            Alert.is_resolved == True,
            Alert.resolved_at < cutoff_date
        ).delete()
        
        db.commit()
        
        print(f"✅ 清理了 {deleted} 個舊告警")
        return deleted
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


def resolve_duplicate_alerts():
    """解決重複的告警(保留最新的)"""
    db = SessionLocal()
    
    try:
        from app.models import Alert
        from sqlalchemy import func
        
        # 找出重複的告警(同一個 domain_id + root_cause)
        duplicates = db.query(
            Alert.domain_id,
            Alert.root_cause,
            func.count(Alert.id).label('count')
        ).filter(
            Alert.is_resolved == False
        ).group_by(
            Alert.domain_id,
            Alert.root_cause
        ).having(
            func.count(Alert.id) > 1
        ).all()
        
        resolved_count = 0
        
        for domain_id, root_cause, count in duplicates:
            # 保留最新的,解決其他的
            alerts = db.query(Alert).filter(
                Alert.domain_id == domain_id,
                Alert.root_cause == root_cause,
                Alert.is_resolved == False
            ).order_by(Alert.last_seen.desc()).all()
            
            # 解決除了第一個以外的所有告警
            for alert in alerts[1:]:
                alert.is_resolved = True
                alert.resolved_at = datetime.utcnow()
                resolved_count += 1
        
        db.commit()
        
        print(f"✅ 解決了 {resolved_count} 個重複告警")
        return resolved_count
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python manage_domains.py list          - 列出無效域名")
        print("  python manage_domains.py disable       - 停用無效域名")
        print("  python manage_domains.py clean-alerts  - 清理舊告警")
        print("  python manage_domains.py resolve-dups  - 解決重複告警")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "list":
        list_failed_domains()
    elif action == "disable":
        list_failed_domains()
        print("\n確認要停用這些域名嗎? (y/N): ", end="")
        confirm = input().lower()
        if confirm == 'y':
            disable_failed_domains()
        else:
            print("已取消")
    elif action == "clean-alerts":
        clean_old_alerts()
    elif action == "resolve-dups":
        resolve_duplicate_alerts()
    else:
        print(f"未知的操作: {action}")

