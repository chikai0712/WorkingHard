"""
數據庫遷移腳本 - 從舊版本遷移到 V4.1
"""
import sqlite3
from datetime import datetime
from pathlib import Path

def migrate_database(db_path: str):
    """遷移數據庫到 V4.1 結構"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 開始數據庫遷移...")
    
    # 檢查現有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    print(f"📋 現有表: {existing_tables}")
    
    # 1. 創建 domains 表
    if 'domains' not in existing_tables:
        print("📝 創建 domains 表...")
        cursor.execute("""
            CREATE TABLE domains (
                domain_id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain VARCHAR(255) UNIQUE NOT NULL,
                zone VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                current_status VARCHAR(20),
                last_check_time DATETIME,
                consecutive_normal INTEGER DEFAULT 0,
                consecutive_abnormal INTEGER DEFAULT 0,
                total_checks INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX idx_domain_zone ON domains(zone)")
        cursor.execute("CREATE INDEX idx_domain_status ON domains(current_status)")
        
        # 從 domain_results 提取唯一域名
        cursor.execute("SELECT DISTINCT domain FROM domain_results")
        domains = cursor.fetchall()
        for (domain,) in domains:
            cursor.execute("""
                INSERT INTO domains (domain, zone, total_checks, created_at, updated_at)
                VALUES (?, 'PENDING', 0, ?, ?)
            """, (domain, datetime.utcnow(), datetime.utcnow()))
        print(f"✅ 已導入 {len(domains)} 個域名")
    
    # 2. 創建 domain_zone_history 表
    if 'domain_zone_history' not in existing_tables:
        print("📝 創建 domain_zone_history 表...")
        cursor.execute("""
            CREATE TABLE domain_zone_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_id INTEGER NOT NULL,
                previous_zone VARCHAR(20),
                new_zone VARCHAR(20) NOT NULL,
                reason VARCHAR(500),
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                batch_id INTEGER,
                FOREIGN KEY (domain_id) REFERENCES domains(domain_id),
                FOREIGN KEY (batch_id) REFERENCES test_batches(batch_id)
            )
        """)
    
    # 3. 創建 check_cycles 表
    if 'check_cycles' not in existing_tables:
        print("📝 創建 check_cycles 表...")
        cursor.execute("""
            CREATE TABLE check_cycles (
                cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_type VARCHAR(20) NOT NULL,
                cycle_number INTEGER DEFAULT 1,
                iteration INTEGER DEFAULT 1,
                max_iterations INTEGER DEFAULT 10,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                total_domains INTEGER DEFAULT 0,
                normal_count INTEGER DEFAULT 0,
                abnormal_count INTEGER DEFAULT 0
            )
        """)
    
    # 4. 創建 cycle_schedules 表
    if 'cycle_schedules' not in existing_tables:
        print("📝 創建 cycle_schedules 表...")
        cursor.execute("""
            CREATE TABLE cycle_schedules (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_type VARCHAR(20) NOT NULL,
                start_hour INTEGER NOT NULL,
                start_minute INTEGER DEFAULT 0,
                check_interval_minutes INTEGER DEFAULT 90,
                is_enabled BOOLEAN DEFAULT 1,
                description VARCHAR(255)
            )
        """)
        
        # 插入默認排程
        cursor.execute("""
            INSERT INTO cycle_schedules (cycle_type, start_hour, start_minute, check_interval_minutes, description)
            VALUES 
                ('ABNORMAL_CHECK', 1, 0, 90, '異常區檢測循環 (AM 1:00 - AM 9:00)'),
                ('NORMAL_CHECK', 9, 0, 90, '正常區檢測循環 (AM 9:00 - AM 1:00)')
        """)
    
    # 5. 創建 system_logs 表
    if 'system_logs' not in existing_tables:
        print("📝 創建 system_logs 表...")
        cursor.execute("""
            CREATE TABLE system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                log_type VARCHAR(50),
                message TEXT,
                details TEXT
            )
        """)
    
    # 6. 更新 test_batches 表（添加新欄位）
    cursor.execute("PRAGMA table_info(test_batches)")
    test_batches_columns = {row[1] for row in cursor.fetchall()}
    
    if 'cycle_id' not in test_batches_columns:
        print("📝 更新 test_batches 表...")
        cursor.execute("ALTER TABLE test_batches ADD COLUMN cycle_id INTEGER")
    if 'cycle_type' not in test_batches_columns:
        cursor.execute("ALTER TABLE test_batches ADD COLUMN cycle_type VARCHAR(20)")
    if 'iteration' not in test_batches_columns:
        cursor.execute("ALTER TABLE test_batches ADD COLUMN iteration INTEGER")
    if 'moved_to_normal' not in test_batches_columns:
        cursor.execute("ALTER TABLE test_batches ADD COLUMN moved_to_normal INTEGER DEFAULT 0")
    if 'moved_to_abnormal' not in test_batches_columns:
        cursor.execute("ALTER TABLE test_batches ADD COLUMN moved_to_abnormal INTEGER DEFAULT 0")
    
    # 7. 更新 domain_results 表（添加新欄位）
    cursor.execute("PRAGMA table_info(domain_results)")
    domain_results_columns = {row[1] for row in cursor.fetchall()}
    
    if 'domain_id' not in domain_results_columns:
        print("📝 更新 domain_results 表...")
        cursor.execute("ALTER TABLE domain_results ADD COLUMN domain_id INTEGER")
        
        # 更新 domain_id
        cursor.execute("SELECT result_id, domain FROM domain_results")
        for result_id, domain in cursor.fetchall():
            cursor.execute("SELECT domain_id FROM domains WHERE domain = ?", (domain,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE domain_results SET domain_id = ? WHERE result_id = ?", 
                             (row[0], result_id))
    
    if 'previous_zone' not in domain_results_columns:
        cursor.execute("ALTER TABLE domain_results ADD COLUMN previous_zone VARCHAR(20)")
    if 'new_zone' not in domain_results_columns:
        cursor.execute("ALTER TABLE domain_results ADD COLUMN new_zone VARCHAR(20)")
    if 'zone_changed' not in domain_results_columns:
        cursor.execute("ALTER TABLE domain_results ADD COLUMN zone_changed BOOLEAN DEFAULT 0")
    
    # 8. 更新 node_details 表（添加新欄位）
    cursor.execute("PRAGMA table_info(node_details)")
    node_details_columns = {row[1] for row in cursor.fetchall()}
    
    if 'node_country' not in node_details_columns:
        print("📝 更新 node_details 表...")
        cursor.execute("ALTER TABLE node_details ADD COLUMN node_country VARCHAR(10) DEFAULT 'ID'")
    
    conn.commit()
    conn.close()
    
    print("✅ 數據庫遷移完成！")
    print("\n📊 遷移摘要:")
    print("  - domains 表: 域名管理")
    print("  - domain_zone_history 表: 區域變更歷史")
    print("  - check_cycles 表: 循環管理")
    print("  - cycle_schedules 表: 排程配置")
    print("  - system_logs 表: 系統日誌")
    print("  - test_batches 表: 已更新")
    print("  - domain_results 表: 已更新")
    print("  - node_details 表: 已更新")


if __name__ == "__main__":
    db_path = "../data/globalping_results.db"
    
    # 備份數據庫
    import shutil
    backup_path = f"../data/globalping_results.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"💾 備份數據庫到: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    # 執行遷移
    migrate_database(db_path)
    
    print("\n🎉 遷移完成！現在可以啟動 V4.1 應用了。")
    print("💡 啟動命令: cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1 && python -m uvicorn app.main:app --reload")
