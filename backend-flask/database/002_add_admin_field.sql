-- 添加管理员字段
-- 创建时间: 2026-02-20
-- 说明: 为用户表添加管理员标识字段

-- 添加 is_admin 字段到 users 表
ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_is_admin ON users(is_admin);

-- 设置第一个用户为管理员（如果存在）
UPDATE users SET is_admin = 1 WHERE user_id = 1;
