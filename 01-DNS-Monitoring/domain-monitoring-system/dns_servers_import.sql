-- =====================================================
-- DNS 伺服器列表 - 三層架構
-- 來源：dnschecker.org, ipshu.com, public-dns.info
-- 更新日期：2026-02-24
-- =====================================================

-- 先擴展資料庫結構
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS dns_type VARCHAR(20);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS isp VARCHAR(100);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS country_code VARCHAR(10);

-- =====================================================
-- 第一層：國際基準 DNS (dnschecker.org)
-- 用途：作為「真實值」基準，判斷域名是否真的存在
-- =====================================================

-- Google Public DNS (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('8.8.8.8', 'international', 'Google', 'Global', 'US', true),
('8.8.4.4', 'international', 'Google', 'Global', 'US', true);

-- Cloudflare DNS (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('1.1.1.1', 'international', 'Cloudflare', 'Global', 'US', true),
('1.0.0.1', 'international', 'Cloudflare', 'Global', 'US', true);

-- OpenDNS (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('208.67.222.222', 'international', 'OpenDNS', 'Global', 'US', true),
('208.67.220.220', 'international', 'OpenDNS', 'Global', 'US', true);

-- Quad9 (瑞士)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('9.9.9.9', 'international', 'Quad9', 'Global', 'CH', true),
('149.112.112.112', 'international', 'Quad9', 'Global', 'CH', true);

-- Level3 (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('209.244.0.3', 'international', 'Level3', 'Global', 'US', true),
('209.244.0.4', 'international', 'Level3', 'Global', 'US', true);

-- Verisign (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('64.6.64.6', 'international', 'Verisign', 'Global', 'US', true),
('64.6.65.6', 'international', 'Verisign', 'Global', 'US', true);

-- DNS.WATCH (德國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('84.200.69.80', 'international', 'DNS.WATCH', 'Europe', 'DE', true),
('84.200.70.40', 'international', 'DNS.WATCH', 'Europe', 'DE', true);

-- Comodo Secure DNS (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('8.26.56.26', 'international', 'Comodo', 'Global', 'US', true),
('8.20.247.20', 'international', 'Comodo', 'Global', 'US', true);

-- AdGuard DNS (塞浦路斯)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('94.140.14.14', 'international', 'AdGuard', 'Global', 'CY', true),
('94.140.15.15', 'international', 'AdGuard', 'Global', 'CY', true);

-- CleanBrowsing (美國)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('185.228.168.9', 'international', 'CleanBrowsing', 'Global', 'US', true),
('185.228.169.9', 'international', 'CleanBrowsing', 'Global', 'US', true);

-- =====================================================
-- 第二層：中國 ISP DNS (ipshu.com)
-- 用途：檢測中國大陸的 DNS 污染/封鎖
-- =====================================================

-- 中國電信 (China Telecom)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
-- 北京電信
('202.96.209.133', 'china_isp', '中國電信', 'Beijing', 'CN', true),
('202.96.209.5', 'china_isp', '中國電信', 'Beijing', 'CN', true),
-- 上海電信
('202.96.128.86', 'china_isp', '中國電信', 'Shanghai', 'CN', true),
('202.96.128.166', 'china_isp', '中國電信', 'Shanghai', 'CN', true),
-- 廣東電信
('202.96.134.133', 'china_isp', '中國電信', 'Guangdong', 'CN', true),
('202.96.128.143', 'china_isp', '中國電信', 'Guangdong', 'CN', true),
-- 江蘇電信
('218.2.2.2', 'china_isp', '中國電信', 'Jiangsu', 'CN', true),
('218.4.4.4', 'china_isp', '中國電信', 'Jiangsu', 'CN', true),
-- 浙江電信
('202.101.172.35', 'china_isp', '中國電信', 'Zhejiang', 'CN', true),
('202.101.172.47', 'china_isp', '中國電信', 'Zhejiang', 'CN', true),
-- 四川電信
('61.139.2.69', 'china_isp', '中國電信', 'Sichuan', 'CN', true),
('218.6.200.139', 'china_isp', '中國電信', 'Sichuan', 'CN', true),
-- 湖南電信
('222.246.129.80', 'china_isp', '中國電信', 'Hunan', 'CN', true),
('59.51.78.210', 'china_isp', '中國電信', 'Hunan', 'CN', true),
-- 福建電信
('218.85.152.99', 'china_isp', '中國電信', 'Fujian', 'CN', true),
('218.85.157.99', 'china_isp', '中國電信', 'Fujian', 'CN', true);

-- 中國聯通 (China Unicom)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
-- 北京聯通
('202.106.0.20', 'china_isp', '中國聯通', 'Beijing', 'CN', true),
('202.106.195.68', 'china_isp', '中國聯通', 'Beijing', 'CN', true),
-- 上海聯通
('210.22.70.3', 'china_isp', '中國聯通', 'Shanghai', 'CN', true),
('210.22.84.3', 'china_isp', '中國聯通', 'Shanghai', 'CN', true),
-- 廣東聯通
('221.5.88.88', 'china_isp', '中國聯通', 'Guangdong', 'CN', true),
('221.4.8.1', 'china_isp', '中國聯通', 'Guangdong', 'CN', true),
-- 江蘇聯通
('221.6.4.66', 'china_isp', '中國聯通', 'Jiangsu', 'CN', true),
('221.6.4.67', 'china_isp', '中國聯通', 'Jiangsu', 'CN', true),
-- 浙江聯通
('221.12.1.227', 'china_isp', '中國聯通', 'Zhejiang', 'CN', true),
('221.12.33.227', 'china_isp', '中國聯通', 'Zhejiang', 'CN', true),
-- 山東聯通
('202.102.134.68', 'china_isp', '中國聯通', 'Shandong', 'CN', true),
('202.102.152.3', 'china_isp', '中國聯通', 'Shandong', 'CN', true),
-- 河南聯通
('202.102.224.68', 'china_isp', '中國聯通', 'Henan', 'CN', true),
('202.102.227.68', 'china_isp', '中國聯通', 'Henan', 'CN', true);

-- 中國移動 (China Mobile)
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
-- 北京移動
('211.136.112.50', 'china_isp', '中國移動', 'Beijing', 'CN', true),
('221.130.33.52', 'china_isp', '中國移動', 'Beijing', 'CN', true),
-- 上海移動
('211.136.192.6', 'china_isp', '中國移動', 'Shanghai', 'CN', true),
('211.136.150.66', 'china_isp', '中國移動', 'Shanghai', 'CN', true),
-- 廣東移動
('211.136.17.107', 'china_isp', '中國移動', 'Guangdong', 'CN', true),
('120.196.165.7', 'china_isp', '中國移動', 'Guangdong', 'CN', true),
-- 江蘇移動
('221.131.143.69', 'china_isp', '中國移動', 'Jiangsu', 'CN', true),
('112.4.0.55', 'china_isp', '中國移動', 'Jiangsu', 'CN', true),
-- 浙江移動
('211.140.13.188', 'china_isp', '中國移動', 'Zhejiang', 'CN', true),
('211.140.188.188', 'china_isp', '中國移動', 'Zhejiang', 'CN', true),
-- 遼寧移動
('221.179.38.38', 'china_isp', '中國移動', 'Liaoning', 'CN', true),
('221.179.155.161', 'china_isp', '中國移動', 'Liaoning', 'CN', true);

-- =====================================================
-- 第三層：亞太地區 DNS (public-dns.info)
-- 用途：檢測亞太地區的可訪問性
-- =====================================================

-- 台灣 HiNet
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('168.95.1.1', 'regional', 'HiNet', 'Taiwan', 'TW', true),
('168.95.192.1', 'regional', 'HiNet', 'Taiwan', 'TW', true);

-- 香港 PCCW
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('202.14.67.4', 'regional', 'PCCW', 'Hong Kong', 'HK', true),
('202.14.67.14', 'regional', 'PCCW', 'Hong Kong', 'HK', true);

-- 日本 IIJ
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('203.80.96.10', 'regional', 'IIJ', 'Japan', 'JP', true),
('210.130.137.3', 'regional', 'IIJ', 'Japan', 'JP', true);

-- 韓國 KT
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('168.126.63.1', 'regional', 'KT', 'South Korea', 'KR', true),
('168.126.63.2', 'regional', 'KT', 'South Korea', 'KR', true);

-- 新加坡 SingTel
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('165.21.83.88', 'regional', 'SingTel', 'Singapore', 'SG', true),
('165.21.100.88', 'regional', 'SingTel', 'Singapore', 'SG', true);

-- 澳洲 Telstra
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('139.130.4.5', 'regional', 'Telstra', 'Australia', 'AU', true),
('139.130.4.6', 'regional', 'Telstra', 'Australia', 'AU', true);

-- 泰國 TOT
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('203.113.131.1', 'regional', 'TOT', 'Thailand', 'TH', true),
('203.113.131.2', 'regional', 'TOT', 'Thailand', 'TH', true);

-- 馬來西亞 TM
INSERT INTO nameservers (dns_server, dns_type, isp, region, country_code, is_healthy) VALUES
('202.188.0.133', 'regional', 'TM', 'Malaysia', 'MY', true),
('202.188.1.5', 'regional', 'TM', 'Malaysia', 'MY', true);

-- =====================================================
-- 統計查詢
-- =====================================================

-- 查看各類型 DNS 數量
SELECT dns_type, COUNT(*) as count 
FROM nameservers 
GROUP BY dns_type;

-- 查看中國 ISP DNS 分布
SELECT isp, region, COUNT(*) as count 
FROM nameservers 
WHERE dns_type = 'china_isp' 
GROUP BY isp, region 
ORDER BY isp, region;

-- 查看所有 DNS 列表
SELECT dns_server, dns_type, isp, region, country_code 
FROM nameservers 
ORDER BY dns_type, isp, region;

