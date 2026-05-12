#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Globalping 數據庫查詢工具
查看和分析測試結果
"""

import sqlite3
import sys
from datetime import datetime

class GlobalpingDBViewer:
    def __init__(self, db_path='globalping_results.db'):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"❌ 無法連接數據庫: {e}")
            sys.exit(1)
    
    def show_all_batches(self):
        """顯示所有測試批次"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM test_batches ORDER BY test_date DESC
        ''')
        
        batches = cursor.fetchall()
        
        if not batches:
            print("📭 數據庫中沒有測試記錄")
            return
        
        print("\n" + "="*80)
        print("📊 所有測試批次")
        print("="*80)
        
        for batch in batches:
            normal = batch['clean_count']
            abnormal = (batch['blocked_count'] + batch['timeout_count'] + batch['warning_count'] +
                       batch['partial_count'] + batch['api_error_count'])
            pct = batch['total_domains'] and (normal / batch['total_domains'] * 100) or 0
            ab_pct = batch['total_domains'] and (abnormal / batch['total_domains'] * 100) or 0
            print(f"\n批次 ID: {batch['batch_id']}")
            print(f"測試時間: {batch['test_date']}")
            print(f"總域名數: {batch['total_domains']}")
            print(f"  【正常】 ✅ {normal:3d} ({pct:.1f}%)  |  【異常】 ❌ {abnormal:3d} ({ab_pct:.1f}%)")
            print(f"  ✅ CLEAN:   {batch['clean_count']:3d}  🚨 BLOCKED: {batch['blocked_count']:3d}  ⚠️  TIMEOUT: {batch['timeout_count']:3d}  ⚠️  WARNING: {batch['warning_count']:3d}  🔄 PARTIAL: {batch['partial_count']:3d}  ❌ API_ERROR: {batch['api_error_count']:3d}")
            if batch['notes']:
                print(f"備註: {batch['notes']}")
            print(f"日誌: {batch['log_file']}")
            print("-" * 80)
    
    def show_batch_detail(self, batch_id):
        """顯示特定批次的詳細信息"""
        cursor = self.conn.cursor()
        
        # 獲取批次信息
        cursor.execute('SELECT * FROM test_batches WHERE batch_id = ?', (batch_id,))
        batch = cursor.fetchone()
        
        if not batch:
            print(f"❌ 找不到批次 ID: {batch_id}")
            return
        
        print("\n" + "="*80)
        print(f"📊 批次 {batch_id} 詳細信息")
        print("="*80)
        print(f"測試時間: {batch['test_date']}")
        print(f"總域名數: {batch['total_domains']}")
        normal = batch['clean_count']
        abnormal = (batch['blocked_count'] + batch['timeout_count'] + batch['warning_count'] +
                    batch['partial_count'] + batch['api_error_count'])
        print(f"【分類】 正常: {normal}  |  異常: {abnormal}")
        print(f"✅ CLEAN:   {batch['clean_count']}  🚨 BLOCKED: {batch['blocked_count']}  ⚠️  TIMEOUT: {batch['timeout_count']}  ⚠️  WARNING: {batch['warning_count']}  🔄 PARTIAL: {batch['partial_count']}  ❌ API_ERROR: {batch['api_error_count']}")
        
        # 正常域名 (CLEAN)
        cursor.execute('''
            SELECT domain FROM domain_results
            WHERE batch_id = ? AND overall_status = 'CLEAN'
            ORDER BY domain
        ''', (batch_id,))
        clean_domains = cursor.fetchall()
        print(f"\n【正常】 正常連通 (CLEAN) - {len(clean_domains)} 個:")
        if clean_domains:
            for i, row in enumerate(clean_domains, 1):
                print(f"  {i:3d}. {row['domain']}")
        else:
            print("  (無)")
        
        # 異常域名（按類型分組）
        statuses = [
            ('BLOCKED', '🚨 DNS 污染'),
            ('TIMEOUT', '⚠️  完全超時'),
            ('WARNING', '⚠️  服務異常'),
            ('PARTIAL', '🔄 部分異常'),
            ('API_ERROR', '❌ 檢測失敗')
        ]
        print(f"\n【異常】 各類型域名:")
        has_any_abnormal = False
        for status, title in statuses:
            cursor.execute('''
                SELECT domain FROM domain_results 
                WHERE batch_id = ? AND overall_status = ?
                ORDER BY domain
            ''', (batch_id, status))
            domains = cursor.fetchall()
            if domains:
                has_any_abnormal = True
                print(f"\n  {title} ({len(domains)} 個):")
                for i, row in enumerate(domains, 1):
                    print(f"    {i:3d}. {row['domain']}")
        if not has_any_abnormal:
            print("  (無異常記錄)")
    
    def show_domain_detail(self, domain, batch_id=None):
        """顯示特定域名的詳細信息"""
        cursor = self.conn.cursor()
        
        if batch_id:
            cursor.execute('''
                SELECT * FROM domain_results 
                WHERE domain = ? AND batch_id = ?
            ''', (domain, batch_id))
        else:
            cursor.execute('''
                SELECT * FROM domain_results 
                WHERE domain = ?
                ORDER BY test_date DESC
                LIMIT 1
            ''', (domain,))
        
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ 找不到域名: {domain}")
            return
        
        print("\n" + "="*80)
        print(f"🔍 域名詳細信息: {domain}")
        print("="*80)
        print(f"批次 ID: {result['batch_id']}")
        print(f"測試時間: {result['test_date']}")
        print(f"整體狀態: {result['overall_status']}")
        
        # 獲取節點詳情
        cursor.execute('''
            SELECT * FROM node_details WHERE result_id = ?
        ''', (result['result_id'],))
        
        nodes = cursor.fetchall()
        
        print(f"\n節點測試結果 ({len(nodes)} 個節點):")
        print("-" * 80)
        
        for i, node in enumerate(nodes, 1):
            print(f"\n節點 {i}:")
            print(f"  ISP: {node['node_isp']}")
            print(f"  ASN: AS{node['node_asn']}")
            print(f"  城市: {node['node_city']}")
            print(f"  節點IP: {node['node_ip']}")
            print(f"  目標IP: {node['target_ip']}")
            print(f"  狀態: {node['status']}")
            if node['http_code']:
                print(f"  HTTP: {node['http_code']}")
    
    def show_statistics(self, batch_id=None):
        """顯示統計信息"""
        cursor = self.conn.cursor()
        
        if batch_id:
            where_clause = f"WHERE dr.batch_id = {batch_id}"
            title = f"批次 {batch_id} 統計信息"
        else:
            where_clause = ""
            title = "所有測試統計信息"
        
        print("\n" + "="*80)
        print(f"📈 {title}")
        print("="*80)
        
        # 分類匯總：正常 vs 異常
        cursor.execute(f'''
            SELECT 
                SUM(CASE WHEN overall_status = 'CLEAN' THEN 1 ELSE 0 END) as normal,
                SUM(CASE WHEN overall_status != 'CLEAN' THEN 1 ELSE 0 END) as abnormal
            FROM domain_results dr
            {where_clause}
        ''')
        row = cursor.fetchone()
        normal = row['normal'] or 0
        abnormal = row['abnormal'] or 0
        total = normal + abnormal
        print("\n【分類匯總】")
        print(f"  正常 (CLEAN):     {normal:4d}" + (f" ({100*normal/total:.1f}%)" if total else ""))
        print(f"  異常 (其他狀態):  {abnormal:4d}" + (f" ({100*abnormal/total:.1f}%)" if total else ""))
        
        # 按狀態統計
        print("\n按狀態統計:")
        cursor.execute(f'''
            SELECT overall_status, COUNT(*) as count
            FROM domain_results dr
            {where_clause}
            GROUP BY overall_status
            ORDER BY count DESC
        ''')
        
        for row in cursor.fetchall():
            print(f"  {row['overall_status']:10s}: {row['count']:4d}")
        
        # 按 ISP 統計 BLOCKED
        print("\n按 ISP 統計 BLOCKED 數量:")
        cursor.execute(f'''
            SELECT nd.node_isp, COUNT(DISTINCT dr.domain) as blocked_count
            FROM domain_results dr
            JOIN node_details nd ON dr.result_id = nd.result_id
            {where_clause}
            {'AND' if where_clause else 'WHERE'} dr.overall_status = 'BLOCKED'
            GROUP BY nd.node_isp
            ORDER BY blocked_count DESC
            LIMIT 10
        ''')
        
        blocked_by_isp = cursor.fetchall()
        if blocked_by_isp:
            for row in blocked_by_isp:
                print(f"  {row['node_isp']:30s}: {row['blocked_count']:4d}")
        else:
            print("  (無 BLOCKED 記錄)")
        
        # 按城市統計 BLOCKED
        print("\n按城市統計 BLOCKED 數量:")
        cursor.execute(f'''
            SELECT nd.node_city, COUNT(DISTINCT dr.domain) as blocked_count
            FROM domain_results dr
            JOIN node_details nd ON dr.result_id = nd.result_id
            {where_clause}
            {'AND' if where_clause else 'WHERE'} dr.overall_status = 'BLOCKED'
            GROUP BY nd.node_city
            ORDER BY blocked_count DESC
            LIMIT 10
        ''')
        
        blocked_by_city = cursor.fetchall()
        if blocked_by_city:
            for row in blocked_by_city:
                print(f"  {row['node_city']:20s}: {row['blocked_count']:4d}")
        else:
            print("  (無 BLOCKED 記錄)")
    
    def compare_batches(self, batch_id1, batch_id2):
        """對比兩個批次"""
        cursor = self.conn.cursor()
        
        print("\n" + "="*80)
        print(f"🔄 對比批次 {batch_id1} vs {batch_id2}")
        print("="*80)
        
        # 獲取兩個批次的信息
        cursor.execute('SELECT * FROM test_batches WHERE batch_id IN (?, ?)', (batch_id1, batch_id2))
        batches = {row['batch_id']: row for row in cursor.fetchall()}
        
        if len(batches) != 2:
            print("❌ 找不到指定的批次")
            return
        
        batch1 = batches[batch_id1]
        batch2 = batches[batch_id2]
        
        print(f"\n批次 {batch_id1}: {batch1['test_date']}")
        print(f"批次 {batch_id2}: {batch2['test_date']}")
        
        print("\n狀態對比:")
        print(f"{'狀態':<12} {'批次 ' + str(batch_id1):>10} {'批次 ' + str(batch_id2):>10} {'變化':>10}")
        print("-" * 50)
        
        statuses = ['clean_count', 'blocked_count', 'timeout_count', 'warning_count', 'partial_count']
        status_names = ['CLEAN', 'BLOCKED', 'TIMEOUT', 'WARNING', 'PARTIAL']
        
        for status, name in zip(statuses, status_names):
            val1 = batch1[status]
            val2 = batch2[status]
            diff = val2 - val1
            diff_str = f"{diff:+d}" if diff != 0 else "0"
            print(f"{name:<12} {val1:>10d} {val2:>10d} {diff_str:>10}")
        
        # 新增的 BLOCKED 域名
        cursor.execute('''
            SELECT domain FROM domain_results 
            WHERE batch_id = ? AND overall_status = 'BLOCKED'
            AND domain NOT IN (
                SELECT domain FROM domain_results 
                WHERE batch_id = ? AND overall_status = 'BLOCKED'
            )
        ''', (batch_id2, batch_id1))
        
        new_blocked = cursor.fetchall()
        if new_blocked:
            print(f"\n新增 BLOCKED 域名 ({len(new_blocked)} 個):")
            for row in new_blocked:
                print(f"  - {row['domain']}")
        
        # 恢復的域名（從 BLOCKED 變為 CLEAN）
        cursor.execute('''
            SELECT dr2.domain 
            FROM domain_results dr1
            JOIN domain_results dr2 ON dr1.domain = dr2.domain
            WHERE dr1.batch_id = ? AND dr1.overall_status = 'BLOCKED'
            AND dr2.batch_id = ? AND dr2.overall_status = 'CLEAN'
        ''', (batch_id1, batch_id2))
        
        recovered = cursor.fetchall()
        if recovered:
            print(f"\n恢復的域名 ({len(recovered)} 個):")
            for row in recovered:
                print(f"  - {row['domain']}")
    
    def close(self):
        """關閉數據庫連接"""
        if self.conn:
            self.conn.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Globalping 數據庫查詢工具')
    parser.add_argument('--db', default='globalping_results.db', help='數據庫文件路徑')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有測試批次')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='顯示批次詳情')
    show_parser.add_argument('batch_id', type=int, help='批次 ID')
    
    # domain 命令
    domain_parser = subparsers.add_parser('domain', help='查詢域名')
    domain_parser.add_argument('domain', help='域名')
    domain_parser.add_argument('--batch', type=int, help='批次 ID')
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='顯示統計信息')
    stats_parser.add_argument('--batch', type=int, help='批次 ID')
    
    # compare 命令
    compare_parser = subparsers.add_parser('compare', help='對比兩個批次')
    compare_parser.add_argument('batch1', type=int, help='批次 1 ID')
    compare_parser.add_argument('batch2', type=int, help='批次 2 ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    db = GlobalpingDBViewer(args.db)
    
    try:
        if args.command == 'list':
            db.show_all_batches()
        elif args.command == 'show':
            db.show_batch_detail(args.batch_id)
        elif args.command == 'domain':
            db.show_domain_detail(args.domain, args.batch)
        elif args.command == 'stats':
            db.show_statistics(args.batch)
        elif args.command == 'compare':
            db.compare_batches(args.batch1, args.batch2)
    finally:
        db.close()

if __name__ == '__main__':
    main()
