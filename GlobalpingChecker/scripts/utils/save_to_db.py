#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Globalping 測試結果數據庫存儲工具
將 v3.0 測試結果解析並存入 SQLite 數據庫
"""

import sqlite3
import re
import sys
from datetime import datetime

class GlobalpingDB:
    def __init__(self, db_path='globalping_results.db'):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """初始化數據庫表結構"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # 測試批次表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_batches (
                batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_domains INTEGER,
                clean_count INTEGER DEFAULT 0,
                blocked_count INTEGER DEFAULT 0,
                timeout_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                partial_count INTEGER DEFAULT 0,
                api_error_count INTEGER DEFAULT 0,
                log_file TEXT,
                notes TEXT
            )
        ''')
        
        # 域名測試結果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER,
                domain TEXT NOT NULL,
                overall_status TEXT,
                test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES test_batches(batch_id)
            )
        ''')
        
        # 節點測試詳情表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_details (
                detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER,
                node_isp TEXT,
                node_asn TEXT,
                node_city TEXT,
                node_ip TEXT,
                target_ip TEXT,
                status TEXT,
                http_code TEXT,
                FOREIGN KEY (result_id) REFERENCES domain_results(result_id)
            )
        ''')
        
        self.conn.commit()
        print("✅ 數據庫初始化完成")
    
    def parse_log_file(self, log_file):
        """解析 v3.0 日誌文件"""
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析摘要信息
        summary = {}
        summary_match = re.search(r'✅ 正常連通 \(CLEAN\):\s+(\d+)', content)
        if summary_match:
            summary['clean'] = int(summary_match.group(1))
        
        blocked_match = re.search(r'🚨 DNS 污染 \(BLOCKED\):\s+(\d+)', content)
        if blocked_match:
            summary['blocked'] = int(blocked_match.group(1))
        
        timeout_match = re.search(r'⚠️\s+完全超時 \(TIMEOUT\):\s+(\d+)', content)
        if timeout_match:
            summary['timeout'] = int(timeout_match.group(1))
        
        warning_match = re.search(r'⚠️\s+服務異常 \(WARNING\):\s+(\d+)', content)
        if warning_match:
            summary['warning'] = int(warning_match.group(1))
        
        partial_match = re.search(r'🔄 部分異常 \(PARTIAL\):\s+(\d+)', content)
        if partial_match:
            summary['partial'] = int(partial_match.group(1))
        
        api_error_match = re.search(r'❌ 檢測失敗 \(API_ERROR\):\s+(\d+)', content)
        if api_error_match:
            summary['api_error'] = int(api_error_match.group(1))
        
        # 解析域名測試結果
        domains = []
        domain_pattern = r'🔍 檢測域名 \[\d+/\d+\]: (.+?) \.\.\.(.*?)(?=🔍 檢測域名|檢測完成|========|$)'
        
        for match in re.finditer(domain_pattern, content, re.DOTALL):
            domain_name = match.group(1).strip()
            domain_content = match.group(2)
            
            # 解析節點信息 - 更新正則以匹配 v3.1 格式
            nodes = []
            # 匹配格式: 📍 ISP (ASN) [City] ... 🔌 節點IP: xxx | 🎯 目標IP: xxx | [STATUS] ... (HTTP code)
            node_pattern = r'📍\s+(.+?)\s+\(AS(\d+)\)\s+\[(.+?)\].*?🔌\s+節點IP:\s+(\S+)\s+\|\s+🎯\s+目標IP:\s+(\S+)\s+\|\s+\[(\w+)\].*?(?:\(HTTP\s+(\d+)\))?'
            
            for node_match in re.finditer(node_pattern, domain_content, re.DOTALL):
                node = {
                    'isp': node_match.group(1).strip(),
                    'asn': node_match.group(2).strip(),
                    'city': node_match.group(3).strip(),
                    'node_ip': node_match.group(4).strip(),
                    'target_ip': node_match.group(5).strip(),
                    'status': node_match.group(6).strip()
                }
                
                # HTTP 狀態碼已在正則中捕獲
                if node_match.group(7):
                    node['http_code'] = node_match.group(7)
                else:
                    node['http_code'] = ''
                
                nodes.append(node)
            
            # 解析整體狀態
            overall_match = re.search(r'-> 整體狀態: (\w+)', domain_content)
            overall_status = overall_match.group(1) if overall_match else 'UNKNOWN'
            
            domains.append({
                'domain': domain_name,
                'overall_status': overall_status,
                'nodes': nodes
            })
        
        return summary, domains
    
    def save_test_results(self, log_file, notes=''):
        """保存測試結果到數據庫"""
        print(f"📖 解析日誌文件: {log_file}")
        summary, domains = self.parse_log_file(log_file)
        
        cursor = self.conn.cursor()
        
        # 插入測試批次
        cursor.execute('''
            INSERT INTO test_batches 
            (total_domains, clean_count, blocked_count, timeout_count, 
             warning_count, partial_count, api_error_count, log_file, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            len(domains),
            summary.get('clean', 0),
            summary.get('blocked', 0),
            summary.get('timeout', 0),
            summary.get('warning', 0),
            summary.get('partial', 0),
            summary.get('api_error', 0),
            log_file,
            notes
        ))
        
        batch_id = cursor.lastrowid
        print(f"✅ 創建測試批次 ID: {batch_id}")
        
        # 插入域名結果
        for domain_data in domains:
            cursor.execute('''
                INSERT INTO domain_results (batch_id, domain, overall_status)
                VALUES (?, ?, ?)
            ''', (batch_id, domain_data['domain'], domain_data['overall_status']))
            
            result_id = cursor.lastrowid
            
            # 插入節點詳情
            for node in domain_data['nodes']:
                cursor.execute('''
                    INSERT INTO node_details 
                    (result_id, node_isp, node_asn, node_city, node_ip, target_ip, status, http_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result_id,
                    node['isp'],
                    node['asn'],
                    node['city'],
                    node['node_ip'],
                    node['target_ip'],
                    node['status'],
                    node['http_code']
                ))
        
        self.conn.commit()
        print(f"✅ 保存完成：{len(domains)} 個域名")
        
        return batch_id
    
    def show_test_summary(self, batch_id):
        """顯示測試摘要"""
        cursor = self.conn.cursor()
        
        # 獲取批次信息
        cursor.execute('''
            SELECT test_date, total_domains, clean_count, blocked_count, 
                   timeout_count, warning_count, partial_count, api_error_count
            FROM test_batches WHERE batch_id = ?
        ''', (batch_id,))
        
        batch = cursor.fetchone()
        
        if not batch:
            print("❌ 找不到測試批次")
            return
        
        print("\n" + "="*60)
        print("📊 測試結果摘要")
        print("="*60)
        print(f"測試時間: {batch[0]}")
        print(f"總域名數: {batch[1]}")
        print(f"✅ 正常連通 (CLEAN):   {batch[2]}")
        print(f"🚨 DNS 污染 (BLOCKED): {batch[3]}")
        print(f"⚠️  完全超時 (TIMEOUT): {batch[4]}")
        print(f"⚠️  服務異常 (WARNING): {batch[5]}")
        print(f"🔄 部分異常 (PARTIAL): {batch[6]}")
        print(f"❌ 檢測失敗 (API_ERROR): {batch[7]}")
        print("="*60)
        
        # 顯示 BLOCKED 域名
        if batch[3] > 0:
            print("\n🚨 DNS 污染域名列表：")
            cursor.execute('''
                SELECT domain FROM domain_results 
                WHERE batch_id = ? AND overall_status = 'BLOCKED'
            ''', (batch_id,))
            for row in cursor.fetchall():
                print(f"  - {row[0]}")
        
        # 顯示 TIMEOUT 域名
        if batch[4] > 0:
            print("\n⚠️  完全超時域名列表：")
            cursor.execute('''
                SELECT domain FROM domain_results 
                WHERE batch_id = ? AND overall_status = 'TIMEOUT'
            ''', (batch_id,))
            for row in cursor.fetchall():
                print(f"  - {row[0]}")
        
        # 顯示 PARTIAL 域名
        if batch[6] > 0:
            print("\n🔄 部分異常域名列表：")
            cursor.execute('''
                SELECT domain FROM domain_results 
                WHERE batch_id = ? AND overall_status = 'PARTIAL'
            ''', (batch_id,))
            for row in cursor.fetchall():
                print(f"  - {row[0]}")
    
    def export_to_csv(self, batch_id, output_file):
        """導出測試結果為 CSV"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                dr.domain,
                dr.overall_status,
                nd.node_isp,
                nd.node_asn,
                nd.node_city,
                nd.node_ip,
                nd.target_ip,
                nd.status,
                nd.http_code
            FROM domain_results dr
            JOIN node_details nd ON dr.result_id = nd.result_id
            WHERE dr.batch_id = ?
            ORDER BY dr.domain, nd.detail_id
        ''', (batch_id,))
        
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '域名', '整體狀態', 'ISP', 'ASN', '城市', 
                '節點IP', '目標IP', '節點狀態', 'HTTP狀態碼'
            ])
            writer.writerows(cursor.fetchall())
        
        print(f"✅ CSV 導出完成: {output_file}")
    
    def close(self):
        """關閉數據庫連接"""
        if self.conn:
            self.conn.close()

def main():
    if len(sys.argv) < 2:
        print("用法: python3 save_to_db.py <日誌文件> [備註]")
        print("範例: python3 save_to_db.py ~/globalping_0305_1800.log '第一次完整測試'")
        sys.exit(1)
    
    log_file = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else ''
    
    # 初始化數據庫
    db = GlobalpingDB()
    
    # 保存測試結果
    batch_id = db.save_test_results(log_file, notes)
    
    # 顯示摘要
    db.show_test_summary(batch_id)
    
    # 導出 CSV
    csv_file = f'test_results_batch_{batch_id}.csv'
    db.export_to_csv(batch_id, csv_file)
    
    db.close()
    
    print(f"\n✅ 完成！批次 ID: {batch_id}")
    print(f"📊 數據庫: globalping_results.db")
    print(f"📄 CSV 文件: {csv_file}")

if __name__ == '__main__':
    main()
