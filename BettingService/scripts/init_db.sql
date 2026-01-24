-- 創建數據庫
CREATE DATABASE IF NOT EXISTS betting_db;

-- 使用數據庫
\c betting_db;

-- 創建注單表
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    order_no VARCHAR(64) NOT NULL UNIQUE,
    game_type VARCHAR(32) NOT NULL,
    bet_amount DECIMAL(18, 2) NOT NULL,
    win_amount DECIMAL(18, 2) DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    bet_time TIMESTAMP NOT NULL,
    settle_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_no ON orders(order_no);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_bet_time ON orders(bet_time);
CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status);

-- 創建分區表（按月分區，可選）
-- CREATE TABLE orders_2025_01 PARTITION OF orders
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

