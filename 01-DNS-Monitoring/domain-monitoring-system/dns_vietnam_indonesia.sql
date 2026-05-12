-- =====================================================
-- 越南和印尼 DNS 伺服器列表
-- 來源：public-dns.info
-- 更新日期：2026-02-24
-- =====================================================

-- 先確保資料庫結構已擴展
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS dns_type VARCHAR(20);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS isp VARCHAR(100);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS country_code VARCHAR(10);

-- =====================================================
-- 越南 DNS (Vietnam)
-- =====================================================

-- VNPT (Vietnam Posts and Telecommunications Group)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('203.162.4.191', 'regional', 'VNPT', 'VNPT', 'Hanoi', 'VN', true),
('203.162.4.190', 'regional', 'VNPT', 'VNPT', 'Hanoi', 'VN', true),
('203.113.131.1', 'regional', 'VNPT', 'VNPT', 'Ho Chi Minh', 'VN', true),
('203.113.131.2', 'regional', 'VNPT', 'VNPT', 'Ho Chi Minh', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Viettel (Military Telecom Corporation)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('123.30.128.15', 'regional', 'Viettel', 'Viettel', 'Ho Chi Minh', 'VN', true),
('123.30.128.16', 'regional', 'Viettel', 'Viettel', 'Ho Chi Minh', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- FPT Telecom
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('210.245.24.20', 'regional', 'FPT', 'FPT', 'Hanoi', 'VN', true),
('210.245.24.21', 'regional', 'FPT', 'FPT', 'Hanoi', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Vietnam Data Communication (VDC)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('14.225.5.5', 'regional', 'VDC', 'VDC', 'Hanoi', 'VN', true),
('14.225.5.6', 'regional', 'VDC', 'VDC', 'Hanoi', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 印尼 DNS (Indonesia)
-- =====================================================

-- Telkom Indonesia
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('202.134.0.155', 'regional', 'Telkom', 'Telkom', 'Jakarta', 'ID', true),
('202.134.2.5', 'regional', 'Telkom', 'Telkom', 'Jakarta', 'ID', true),
('203.130.193.74', 'regional', 'Telkom', 'Telkom', 'Surabaya', 'ID', true),
('203.130.206.250', 'regional', 'Telkom', 'Telkom', 'Surabaya', 'ID', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Indosat Ooredoo
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('202.155.0.15', 'regional', 'Indosat', 'Indosat', 'Jakarta', 'ID', true),
('202.155.0.19', 'regional', 'Indosat', 'Indosat', 'Jakarta', 'ID', true),
('202.155.46.66', 'regional', 'Indosat', 'Indosat', 'Bandung', 'ID', true),
('202.155.46.77', 'regional', 'Indosat', 'Indosat', 'Bandung', 'ID', true)
ON CONFLICT (dns_server) DO NOTHING;

-- XL Axiata
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('202.152.0.2', 'regional', 'XL Axiata', 'XL Axiata', 'Jakarta', 'ID', true),
('202.152.2.2', 'regional', 'XL Axiata', 'XL Axiata', 'Jakarta', 'ID', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Biznet Networks
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('103.10.67.200', 'regional', 'Biznet', 'Biznet', 'Jakarta', 'ID', true),
('103.10.67.201', 'regional', 'Biznet', 'Biznet', 'Jakarta', 'ID', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 統計查詢
-- =====================================================

-- 查看越南和印尼 DNS 數量
SELECT country_code, COUNT(*) as count 
FROM nameservers 
WHERE country_code IN ('VN', 'ID')
GROUP BY country_code;

-- 查看詳細列表
SELECT dns_server, isp, region, country_code 
FROM nameservers 
WHERE country_code IN ('VN', 'ID')
ORDER BY country_code, isp, region;

-- 查看所有區域 DNS
SELECT country_code, COUNT(*) as count 
FROM nameservers 
WHERE dns_type = 'regional'
GROUP BY country_code
ORDER BY count DESC;

