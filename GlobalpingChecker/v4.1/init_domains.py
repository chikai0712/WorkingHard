#!/usr/bin/env python3
"""
初始化数据库并加载所有域名
"""
import sqlite3
import os
from pathlib import Path

db_path = Path("/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/data/globalping_results.db")
domains_file = Path("/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/domains.txt")

# 确保数据目录存在
db_path.parent.mkdir(parents=True, exist_ok=True)

# 连接数据库
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 创建 domains 表（简化版）
cursor.execute("""
    CREATE TABLE IF NOT EXISTS domains (
        domain_id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE NOT NULL,
        zone TEXT DEFAULT 'PENDING',
        current_status TEXT,
        last_check_time TEXT,
        consecutive_normal INTEGER DEFAULT 0,
        consecutive_abnormal INTEGER DEFAULT 0,
        total_checks INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")

# 读取域名文件
with open(domains_file, 'r', encoding='utf-8') as f:
    domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"📝 加载 {len(domains)} 个域名...")

# 插入域名
for domain in domains:
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO domains (domain, zone) VALUES (?, 'PENDING')",
            (domain,)
        )
    except Exception as e:
        print(f"⚠️  插入 {domain} 失败: {e}")

conn.commit()

# 验证
cursor.execute("SELECT COUNT(*) FROM domains")
count = cursor.fetchone()[0]
print(f"✅ 数据库已初始化，共 {count} 个域名")

conn.close()
