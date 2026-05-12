#!/usr/bin/env python3
# ============================================
# Simple DNS Server for HA Simulation
# Supports dynamic record updates via file
# ============================================

import socket
import struct
import os
import time
import threading
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# DNS 配置
DNS_PORT = 53
ZONE_FILE = "/zones/app.example.com.zone"
DOMAIN = "app.example.com"
DEFAULT_IP = "172.20.0.10"  # 初始指向 Main Service

# 記錄快取
dns_records = {}
last_modified = 0

class DNSHandler:
    def __init__(self):
        # 初始化時強制載入
        global dns_records, last_modified
        dns_records[DOMAIN] = DEFAULT_IP
        last_modified = 0  # 強制重新載入
        print(f"[DNS] Initializing DNS handler...")
        self.load_zone_file()
        print(f"[DNS] Initialized with IP: {dns_records.get(DOMAIN, DEFAULT_IP)}")
    
    def load_zone_file(self):
        """從 zone 文件載入 DNS 記錄"""
        global dns_records, last_modified
        
        try:
            if os.path.exists(ZONE_FILE):
                mtime = os.path.getmtime(ZONE_FILE)
                if mtime > last_modified:
                    with open(ZONE_FILE, 'r') as f:
                        content = f.read()
                        # 解析 A 記錄 - 使用正則表達式直接匹配整個文件
                        # 這樣可以避免逐行解析時的問題
                        print(f"[DNS] Parsing zone file, content length: {len(content)}")
                        pattern = r'^app\.example\.com\.\s+IN\s+A\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*$'
                        match = re.search(pattern, content, re.MULTILINE)
                        
                        found_a_record = False
                        if match:
                            ip = match.group(1)
                            print(f"[DNS] Regex matched IP: {ip}")
                            # 驗證 IP 格式
                            ip_parts = ip.split('.')
                            if len(ip_parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in ip_parts):
                                dns_records[DOMAIN] = ip
                                print(f"[DNS] Loaded record: {DOMAIN} -> {ip}")
                                last_modified = mtime
                                found_a_record = True
                            else:
                                print(f"[DNS] Invalid IP format: {ip}, using default")
                        
                        if not found_a_record:
                            # 如果正則匹配失敗，嘗試逐行查找
                            print(f"[DNS] Regex match failed, trying line-by-line parsing...")
                            for line_num, line in enumerate(content.split('\n'), 1):
                                original_line = line
                                line = line.strip()
                                
                                # 跳過註釋、空行
                                if not line or line.startswith(';') or line.startswith('$'):
                                    continue
                                
                                # 跳過 SOA、NS 記錄和包含括號的行
                                if line.startswith('@') or '(' in line or 'SOA' in line or 'NS' in line:
                                    continue
                                
                                # 查找 A 記錄行：必須包含 app.example.com、IN 和 A，且 A 後面直接跟 IP
                                if 'app.example.com' in line and 'IN' in line and 'A' in line:
                                    # 使用正則表達式提取 IP
                                    match = re.search(r'A\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                                    if match:
                                        ip = match.group(1)
                                        ip_parts = ip.split('.')
                                        if len(ip_parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in ip_parts):
                                            dns_records[DOMAIN] = ip
                                            print(f"[DNS] Loaded record: {DOMAIN} -> {ip} from line {line_num}: {line}")
                                            last_modified = mtime
                                            found_a_record = True
                                            break
                            
                            if not found_a_record:
                                print(f"[DNS] Warning: No A record found, using default: {DEFAULT_IP}")
                                dns_records[DOMAIN] = DEFAULT_IP
            else:
                # 如果文件不存在，使用預設值
                dns_records[DOMAIN] = DEFAULT_IP
                print(f"[DNS] Using default record: {DOMAIN} -> {DEFAULT_IP}")
        except Exception as e:
            print(f"[DNS] Error loading zone file: {e}")
            dns_records[DOMAIN] = DEFAULT_IP
    
    def get_ip(self, domain):
        """獲取域名的 IP 地址"""
        # 重新載入 zone 文件（檢查是否有更新）
        self.load_zone_file()
        ip = dns_records.get(domain, DEFAULT_IP)
        
        # 調試輸出
        print(f"[DNS] get_ip called for {domain}, got: {repr(ip)}")
        
        # 確保返回的是有效的 IP 地址
        if ip and isinstance(ip, str):
            # 移除任何非 IP 字符
            ip = ip.strip()
            # 如果包含非數字字符（除了點），使用預設值
            if any(c not in '0123456789.' for c in ip):
                print(f"[DNS] IP contains invalid characters: {repr(ip)}, using default")
                return DEFAULT_IP
            # 驗證 IP 格式
            ip_parts = ip.split('.')
            if len(ip_parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in ip_parts):
                return ip
            else:
                print(f"[DNS] Invalid IP format: {repr(ip)}, using default")
        else:
            print(f"[DNS] IP is not a valid string: {repr(ip)}, using default")
        return DEFAULT_IP
    
    def parse_dns_query(self, data):
        """解析 DNS 查詢"""
        try:
            # 跳過 DNS 標頭（12 bytes）
            pos = 12
            domain_parts = []
            
            # 解析域名
            while pos < len(data):
                length = data[pos]
                if length == 0:
                    pos += 1
                    break
                pos += 1
                domain_parts.append(data[pos:pos+length].decode('utf-8'))
                pos += length
            
            # 跳過查詢類型（2 bytes）和查詢類別（2 bytes）
            pos += 4
            
            domain = '.'.join(domain_parts)
            return domain
        except Exception as e:
            print(f"[DNS] Error parsing query: {e}")
            return None
    
    def build_dns_response(self, query_data, domain, ip):
        """構建 DNS 回應"""
        try:
            # 複製查詢標頭
            response = bytearray(query_data[:12])
            
            # 修改標誌：標準回應，無錯誤
            response[2] = 0x81  # QR=1, Opcode=0, AA=1, TC=0, RD=1
            response[3] = 0x80  # RA=1, Z=0, RCODE=0
            
            # 設置回應計數
            response[6] = 0x00
            response[7] = 0x01  # 1 個回答
            
            # 添加查詢部分（原樣返回）
            response.extend(query_data[12:])
            
            # 添加回答部分
            # 域名指針（指向查詢中的域名）
            response.append(0xc0)
            response.append(0x0c)
            
            # 類型：A 記錄
            response.extend(struct.pack('!H', 1))
            
            # 類別：IN
            response.extend(struct.pack('!H', 1))
            
            # TTL：300 秒
            response.extend(struct.pack('!I', 300))
            
            # 數據長度：4 bytes (IPv4)
            response.extend(struct.pack('!H', 4))
            
            # IP 地址
            ip_parts = ip.split('.')
            for part in ip_parts:
                response.append(int(part))
            
            return bytes(response)
        except Exception as e:
            print(f"[DNS] Error building response: {e}")
            return None
    
    def handle_query(self, data, addr):
        """處理 DNS 查詢"""
        domain = self.parse_dns_query(data)
        
        if domain and domain == DOMAIN:
            ip = self.get_ip(domain)
            print(f"[DNS] Query: {domain} -> {ip} (type: {type(ip)}) from {addr[0]}")
            if not ip or ip == '(' or not isinstance(ip, str):
                print(f"[DNS] Invalid IP, using default: {DEFAULT_IP}")
                ip = DEFAULT_IP
            response = self.build_dns_response(data, domain, ip)
            return response
        else:
            print(f"[DNS] Query for unknown domain: {domain}")
            return None

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP 健康檢查端點"""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 禁用日誌

def run_dns_server():
    """運行 DNS 服務器"""
    handler = DNSHandler()
    
    # UDP socket for DNS
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', DNS_PORT))
    
    print(f"[DNS] DNS Server started on port {DNS_PORT}")
    print(f"[DNS] Serving domain: {DOMAIN}")
    
    # 定期重新載入 zone 文件
    def reload_zone():
        while True:
            time.sleep(2)
            handler.load_zone_file()
    
    reload_thread = threading.Thread(target=reload_zone, daemon=True)
    reload_thread.start()
    
    # 主循環
    while True:
        try:
            data, addr = sock.recvfrom(512)
            response = handler.handle_query(data, addr)
            if response:
                sock.sendto(response, addr)
        except Exception as e:
            print(f"[DNS] Error: {e}")

def run_health_server():
    """運行 HTTP 健康檢查服務器"""
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    print(f"[DNS] Health check server started on port 8080")
    server.serve_forever()

if __name__ == '__main__':
    # 啟動健康檢查服務器（在背景執行）
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # 啟動 DNS 服務器（主線程）
    run_dns_server()

