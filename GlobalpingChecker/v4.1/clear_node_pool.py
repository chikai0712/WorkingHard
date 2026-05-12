#!/usr/bin/env python3
"""
清空节点池并准备重新拉取
"""
import sqlite3
from pathlib import Path

db_path = Path("/Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1/data/globalping_results.db")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 清空节点池
print("🗑️  清空现有节点池...")
cursor.execute("DELETE FROM node_pool")
conn.commit()

# 验证
cursor.execute("SELECT COUNT(*) FROM node_pool")
count = cursor.fetchone()[0]
print(f"✅ 节点池已清空，当前节点数: {count}")

conn.close()

print("\n📝 下一步:")
print("1. 重启应用: pkill -f 'uvicorn app.main' && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8766")
print("2. 应用启动时会自动重新拉取节点清单")
print("3. 检查 http://127.0.0.1:8766/api/nodes/pool 查看节点池状态")
