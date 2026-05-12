-- =====================================================
-- 亞洲 ISP / 區域公開 DNS 伺服器列表（增量匯入、不刪除既有資料）
-- 目標：讓 Dashboard「DNS 監控器」可直接檢視多個亞洲國家/地區的 DNS 節點
-- 注意：nameservers.dns_server 為 UNIQUE，因此同一個 DNS IP 只能屬於一筆資料
-- 更新日期：2026-03-03
-- =====================================================

-- 先確保資料庫結構已擴展（與專案現有 SQL 檔保持一致）
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS dns_type VARCHAR(20);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS isp VARCHAR(100);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS isp_name VARCHAR(100);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS country_code VARCHAR(10);

-- =====================================================
-- 台灣 (TW)
-- =====================================================

-- HiNet (Chunghwa Telecom)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('168.95.1.1', 'regional', 'HiNet', 'HiNet', 'Taiwan', 'TW', true),
('168.95.192.1', 'regional', 'HiNet', 'HiNet', 'Taiwan', 'TW', true)
ON CONFLICT (dns_server) DO NOTHING;

-- 台灣固網 (Taiwan Fixed Network)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('61.31.233.1', 'regional', 'Taiwan Fixed Network', 'Taiwan Fixed Network', 'Taiwan', 'TW', true),
('61.31.1.1', 'regional', 'Taiwan Fixed Network', 'Taiwan Fixed Network', 'Taiwan', 'TW', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Quad101 (TWNIC 公開 DNS)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('101.101.101.101', 'regional', 'Quad101', 'Quad101', 'Taiwan', 'TW', true),
('101.102.103.104', 'regional', 'Quad101', 'Quad101', 'Taiwan', 'TW', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 香港 (HK)
-- =====================================================

-- PCCW
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('202.14.67.4', 'regional', 'PCCW', 'PCCW', 'Hong Kong', 'HK', true),
('202.14.67.14', 'regional', 'PCCW', 'PCCW', 'Hong Kong', 'HK', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 日本 (JP)
-- =====================================================

-- IIJ
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('203.80.96.10', 'regional', 'IIJ', 'IIJ', 'Japan', 'JP', true),
('210.130.137.3', 'regional', 'IIJ', 'IIJ', 'Japan', 'JP', true)
ON CONFLICT (dns_server) DO NOTHING;

-- NTT / OCN（專案 README 既有示例）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('210.141.112.163', 'regional', 'NTT', 'NTT', 'Japan', 'JP', true),
('210.196.3.183', 'regional', 'OCN', 'OCN', 'Japan', 'JP', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 韓國 (KR)
-- =====================================================

-- KT
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('168.126.63.1', 'regional', 'KT', 'KT', 'South Korea', 'KR', true),
('168.126.63.2', 'regional', 'KT', 'KT', 'South Korea', 'KR', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 新加坡 (SG)
-- =====================================================

-- SingTel
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('165.21.83.88', 'regional', 'SingTel', 'SingTel', 'Singapore', 'SG', true),
('165.21.100.88', 'regional', 'SingTel', 'SingTel', 'Singapore', 'SG', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 馬來西亞 (MY)
-- =====================================================

-- Telekom Malaysia (TM)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('202.188.0.133', 'regional', 'TM', 'Telekom Malaysia', 'Malaysia', 'MY', true),
('202.188.1.5', 'regional', 'TM', 'Telekom Malaysia', 'Malaysia', 'MY', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 中國 (CN) - 公開 Resolver（不綁定特定省份）
-- =====================================================

-- AliDNS (Alibaba Public DNS)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('223.5.5.5', 'regional', 'AliDNS', 'AliDNS', 'China', 'CN', true),
('223.6.6.6', 'regional', 'AliDNS', 'AliDNS', 'China', 'CN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- DNSPod Public DNS (Tencent)
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('119.29.29.29', 'regional', 'DNSPod', 'DNSPod', 'China', 'CN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Baidu Public DNS（常見公開 Resolver）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('180.76.76.76', 'regional', 'Baidu', 'Baidu', 'China', 'CN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 統計查詢（可選）
-- =====================================================
-- SELECT country_code, COUNT(*) as count
-- FROM nameservers
-- WHERE country_code IN ('TW','HK','JP','KR','SG','MY','CN')
-- GROUP BY country_code
-- ORDER BY count DESC;


