-- 添加域名暫停相關字段
-- 執行時間: 2026-02-23

ALTER TABLE domains 
ADD COLUMN IF NOT EXISTS paused_until TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS pause_reason VARCHAR(200) NULL;

-- 添加索引以提高查詢效率
CREATE INDEX IF NOT EXISTS idx_domains_paused_until ON domains(paused_until);

COMMENT ON COLUMN domains.paused_until IS '暫停監控直到此時間（NULL 表示未暫停）';
COMMENT ON COLUMN domains.pause_reason IS '暫停原因（例如：無 DNS 記錄）';

