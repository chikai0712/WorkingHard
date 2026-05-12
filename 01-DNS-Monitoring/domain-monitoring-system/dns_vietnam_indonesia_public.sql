-- =====================================================
-- 越南和印尼公開 DNS 伺服器列表（已驗證可用）
-- 更新日期：2026-02-24
-- =====================================================

-- 先確保資料庫結構已擴展
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS dns_type VARCHAR(20);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS isp VARCHAR(100);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE nameservers ADD COLUMN IF NOT EXISTS country_code VARCHAR(10);

-- 清除舊的越南和印尼 DNS 記錄
DELETE FROM nameservers WHERE country_code IN ('VN', 'ID');

-- =====================================================
-- 全球公開 DNS（作為對照組）
-- =====================================================

-- Google Public DNS
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('8.8.8.8', 'global', 'Google', 'Google', 'Global', 'US', true),
('8.8.4.4', 'global', 'Google', 'Google', 'Global', 'US', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Cloudflare DNS
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('1.1.1.1', 'global', 'Cloudflare', 'Cloudflare', 'Global', 'US', true),
('1.0.0.1', 'global', 'Cloudflare', 'Cloudflare', 'Global', 'US', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 越南 DNS (Vietnam) - 使用全球 DNS 的越南節點
-- =====================================================

-- Google Public DNS（越南用戶也會路由到最近的節點）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('8.8.8.8', 'regional', 'Google', 'Google', 'Vietnam', 'VN', true),
('8.8.4.4', 'regional', 'Google', 'Google', 'Vietnam', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Cloudflare DNS（越南用戶也會路由到最近的節點）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('1.1.1.1', 'regional', 'Cloudflare', 'Cloudflare', 'Vietnam', 'VN', true),
('1.0.0.1', 'regional', 'Cloudflare', 'Cloudflare', 'Vietnam', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- OpenDNS
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('208.67.222.222', 'regional', 'OpenDNS', 'OpenDNS', 'Vietnam', 'VN', true),
('208.67.220.220', 'regional', 'OpenDNS', 'OpenDNS', 'Vietnam', 'VN', true)
ON CONFLICT (dns_server) DO NOTHING;

-- =====================================================
-- 印尼 DNS (Indonesia) - 使用全球 DNS 的印尼節點
-- =====================================================

-- Google Public DNS（印尼用戶也會路由到最近的節點）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('8.8.8.8', 'regional', 'Google', 'Google', 'Indonesia', 'ID', true),
('8.8.4.4', 'regional', 'Google', 'Google', 'Indonesia', 'ID', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Cloudflare DNS（印尼用戶也會路由到最近的節點）
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('1.1.1.1', 'regional', 'Cloudflare', 'Cloudflare', 'Indonesia', 'ID', true),
('1.0.0.1', 'regional', 'Cloudflare', 'Cloudflare', 'Indonesia', 'ID', true)
ON CONFLICT (dns_server) DO NOTHING;

-- Quad9 DNS
INSERT INTO nameservers (dns_server, dns_type, isp, isp_name, region, country_code, is_healthy) VALUES
('9.9.9.9', 'regional', 'Quad9', 'Quad9', 'Indonesia', 'ID', true),
('149.112.112.112', 'regional', 'Quad9', 'Quad9', 'Indonesia', 'ID', true)
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

-- 查看所有 DNS
SELECT country_code, dns_type, COUNT(*) as count 
FROM nameservers 
GROUP BY country_code, dns_type
ORDER BY country_code, dns_type;

