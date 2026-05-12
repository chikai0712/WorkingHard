#!/usr/bin/env python3
"""
域名檢測結果分析工具
用於分析現有的檢測日誌，生成分類報告
"""

import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

class DomainAnalyzer:
    def __init__(self):
        self.domains = {}
        self.stats = {
            'total': 0,
            'clean': 0,
            'blocked': 0,
            'timeout': 0,
            'warning': 0,
            'partial': 0,
            'api_error': 0
        }
        
        # 分類存儲
        self.clean_domains = []
        self.blocked_domains = []
        self.timeout_domains = []
        self.warning_domains = []
        self.partial_domains = []
        self.api_error_domains = []
    
    def parse_log(self, log_text: str):
        """解析日誌文本"""
        lines = log_text.strip().split('\n')
        
        current_domain = None
        current_nodes = []
        
        for line in lines:
            # 檢測域名行
            domain_match = re.search(r'🔍 檢測域名[：:]\s*(\S+)', line)
            if domain_match:
                # 保存上一個域名的數據
                if current_domain:
                    self._process_domain(current_domain, current_nodes)
                
                # 開始新域名
                current_domain = domain_match.group(1)
                current_nodes = []
                continue
            
            # 檢測節點結果行
            node_match = re.search(r'📍\s+(.+?)\s+\|\s+IP:\s+(\S+)\s+\|\s+\[(\w+)\]', line)
            if node_match and current_domain:
                isp = node_match.group(1).strip()
                ip = node_match.group(2).strip()
                status = node_match.group(3).strip()
                
                # 提取 HTTP 狀態碼
                code_match = re.search(r'HTTP\s+(\d+)', line)
                http_code = code_match.group(1) if code_match else '0'
                
                current_nodes.append({
                    'isp': isp,
                    'ip': ip,
                    'status': status,
                    'http_code': http_code
                })
                continue
            
            # 檢測 API 錯誤
            if 'API 建立失敗' in line or 'API_ERROR' in line:
                if current_domain:
                    self._process_domain(current_domain, [], api_error=True)
                    current_domain = None
                    current_nodes = []
        
        # 處理最後一個域名
        if current_domain:
            self._process_domain(current_domain, current_nodes)
    
    def _process_domain(self, domain: str, nodes: List[Dict], api_error: bool = False):
        """處理單個域名的數據"""
        self.stats['total'] += 1
        
        if api_error:
            self.stats['api_error'] += 1
            self.api_error_domains.append(domain)
            self.domains[domain] = {
                'status': 'API_ERROR',
                'nodes': []
            }
            return
        
        if not nodes:
            return
        
        # 統計各節點狀態
        status_count = defaultdict(int)
        for node in nodes:
            status_count[node['status']] += 1
        
        # 判斷整體狀態
        total_nodes = len(nodes)
        
        if status_count['BLOCKED'] == total_nodes:
            overall_status = 'BLOCKED'
            self.stats['blocked'] += 1
            self.blocked_domains.append(domain)
        elif status_count['TIMEOUT'] == total_nodes:
            overall_status = 'TIMEOUT'
            self.stats['timeout'] += 1
            self.timeout_domains.append(domain)
        elif status_count['CLEAN'] == total_nodes:
            overall_status = 'CLEAN'
            self.stats['clean'] += 1
            self.clean_domains.append(domain)
        elif status_count['WARNING'] == total_nodes:
            overall_status = 'WARNING'
            self.stats['warning'] += 1
            self.warning_domains.append(domain)
        else:
            overall_status = 'PARTIAL'
            self.stats['partial'] += 1
            self.partial_domains.append(domain)
        
        self.domains[domain] = {
            'status': overall_status,
            'nodes': nodes
        }
    
    def generate_report(self) -> str:
        """生成分析報告"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("域名檢測結果分析報告")
        lines.append("=" * 80)
        lines.append("")
        
        # 統計摘要
        lines.append("📊 統計摘要")
        lines.append("-" * 80)
        lines.append(f"總域名數：{self.stats['total']}")
        
        if self.stats['total'] > 0:
            lines.append(f"✅ 正常連通 (CLEAN):     {self.stats['clean']:3d} ({self.stats['clean']*100//self.stats['total']:2d}%)")
            lines.append(f"🚨 DNS 污染 (BLOCKED):   {self.stats['blocked']:3d} ({self.stats['blocked']*100//self.stats['total']:2d}%)")
            lines.append(f"⚠️  完全超時 (TIMEOUT):   {self.stats['timeout']:3d} ({self.stats['timeout']*100//self.stats['total']:2d}%)")
            lines.append(f"⚠️  服務異常 (WARNING):   {self.stats['warning']:3d} ({self.stats['warning']*100//self.stats['total']:2d}%)")
            lines.append(f"🔄 部分異常 (PARTIAL):   {self.stats['partial']:3d} ({self.stats['partial']*100//self.stats['total']:2d}%)")
            lines.append(f"❌ 檢測失敗 (API_ERROR): {self.stats['api_error']:3d} ({self.stats['api_error']*100//self.stats['total']:2d}%)")
        
        lines.append("")
        
        # 需要關注的域名
        if self.blocked_domains:
            lines.append("=" * 80)
            lines.append(f"🚨 DNS 污染域名 ({len(self.blocked_domains)} 個)")
            lines.append("=" * 80)
            for domain in self.blocked_domains:
                nodes = self.domains[domain]['nodes']
                lines.append(f"  • {domain}")
                for node in nodes:
                    lines.append(f"    - {node['isp']}: {node['ip']}")
            lines.append("")
        
        if self.timeout_domains:
            lines.append("=" * 80)
            lines.append(f"⚠️  完全超時域名 ({len(self.timeout_domains)} 個)")
            lines.append("=" * 80)
            lines.append("這些域名在所有節點都無法解析或連接超時")
            lines.append("")
            for domain in self.timeout_domains:
                lines.append(f"  • {domain}")
            lines.append("")
        
        if self.partial_domains:
            lines.append("=" * 80)
            lines.append(f"🔄 部分異常域名 ({len(self.partial_domains)} 個)")
            lines.append("=" * 80)
            lines.append("這些域名在不同節點有不同的結果（區域性問題）")
            lines.append("")
            for domain in self.partial_domains:
                nodes = self.domains[domain]['nodes']
                lines.append(f"  • {domain}")
                for node in nodes:
                    status_icon = {
                        'CLEAN': '✅',
                        'BLOCKED': '🚨',
                        'TIMEOUT': '⚠️',
                        'WARNING': '⚠️'
                    }.get(node['status'], '❓')
                    lines.append(f"    {status_icon} {node['isp']}: {node['ip']} [{node['status']}]")
            lines.append("")
        
        if self.warning_domains:
            lines.append("=" * 80)
            lines.append(f"⚠️  服務異常域名 ({len(self.warning_domains)} 個)")
            lines.append("=" * 80)
            lines.append("這些域名 DNS 正常但服務器返回錯誤狀態碼")
            lines.append("")
            for domain in self.warning_domains:
                nodes = self.domains[domain]['nodes']
                lines.append(f"  • {domain}")
                for node in nodes:
                    lines.append(f"    - {node['isp']}: HTTP {node['http_code']}")
            lines.append("")
        
        if self.api_error_domains:
            lines.append("=" * 80)
            lines.append(f"❌ 檢測失敗域名 ({len(self.api_error_domains)} 個)")
            lines.append("=" * 80)
            lines.append("這些域名因 API 頻率限制未能完成檢測，需要重新檢測")
            lines.append("")
            for domain in self.api_error_domains:
                lines.append(f"  • {domain}")
            lines.append("")
        
        # 建議
        lines.append("=" * 80)
        lines.append("📋 建議動作")
        lines.append("=" * 80)
        
        if self.blocked_domains:
            lines.append("🚨 DNS 污染域名：")
            lines.append("  - 通知營運團隊")
            lines.append("  - 考慮更換域名或使用 CDN")
            lines.append("  - 記錄封鎖的 ISP 和地區")
            lines.append("")
        
        if self.timeout_domains:
            lines.append("⚠️  完全超時域名：")
            lines.append("  - 檢查域名 DNS 配置")
            lines.append("  - 確認服務器是否正常運行")
            lines.append("  - 檢查防火牆設置")
            lines.append("")
        
        if self.partial_domains:
            lines.append("🔄 部分異常域名：")
            lines.append("  - 記錄哪些 ISP/地區有問題")
            lines.append("  - 考慮使用多個 CDN 節點")
            lines.append("  - 監控特定地區的可用性")
            lines.append("")
        
        if self.warning_domains:
            lines.append("⚠️  服務異常域名：")
            lines.append("  - 通知技術團隊檢查服務器")
            lines.append("  - 檢查應用程式日誌")
            lines.append("  - 不是封鎖問題，是網站本身的問題")
            lines.append("")
        
        if self.api_error_domains:
            lines.append("❌ 檢測失敗域名：")
            lines.append("  - 使用改進版腳本重新檢測")
            lines.append("  - 或手動檢測這些域名")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def export_csv(self, filename: str):
        """導出 CSV 報告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("域名,整體狀態,節點1_ISP,節點1_IP,節點1_狀態,節點2_ISP,節點2_IP,節點2_狀態,節點3_ISP,節點3_IP,節點3_狀態\n")
            
            for domain, data in self.domains.items():
                status = data['status']
                nodes = data['nodes']
                
                row = [domain, status]
                
                for i in range(3):
                    if i < len(nodes):
                        node = nodes[i]
                        row.extend([node['isp'], node['ip'], node['status']])
                    else:
                        row.extend(['', '', ''])
                
                f.write(','.join(row) + '\n')
    
    def export_failed_domains(self, filename: str):
        """導出失敗域名清單（用於重新檢測）"""
        with open(filename, 'w', encoding='utf-8') as f:
            for domain in self.api_error_domains:
                f.write(domain + '\n')

def main():
    if len(sys.argv) < 2:
        print("用法: python3 analyze_results.py <日誌文件或直接貼上日誌內容>")
        print("範例: python3 analyze_results.py log.txt")
        print("或者: cat log.txt | python3 analyze_results.py")
        sys.exit(1)
    
    # 讀取輸入
    if sys.argv[1] == '-':
        # 從標準輸入讀取
        log_text = sys.stdin.read()
    else:
        # 從文件讀取
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                log_text = f.read()
        except FileNotFoundError:
            print(f"錯誤: 文件不存在: {sys.argv[1]}")
            sys.exit(1)
    
    # 分析
    analyzer = DomainAnalyzer()
    analyzer.parse_log(log_text)
    
    # 生成報告
    report = analyzer.generate_report()
    print(report)
    
    # 導出文件
    base_name = sys.argv[1].replace('.log', '').replace('.txt', '') if sys.argv[1] != '-' else 'analysis'
    
    csv_file = f"{base_name}_analysis.csv"
    analyzer.export_csv(csv_file)
    print(f"\n✅ CSV 報告已導出: {csv_file}")
    
    if analyzer.api_error_domains:
        failed_file = f"{base_name}_failed_domains.txt"
        analyzer.export_failed_domains(failed_file)
        print(f"✅ 失敗域名清單已導出: {failed_file}")
        print(f"\n💡 使用以下命令重新檢測失敗的域名：")
        print(f"   ./id_globalping_multi_v2.sh {failed_file}")

if __name__ == '__main__':
    main()
