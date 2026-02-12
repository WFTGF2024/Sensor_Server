-- 会员系统数据库表结构
-- 创建时间: 2026-02-05
-- 说明: 为 Sensor_Flask 项目添加会员系统功能
-- 数据库: SQLite

-- 1. 会员等级表
CREATE TABLE IF NOT EXISTS membership_levels (
    level_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_name TEXT NOT NULL UNIQUE,
    level_code TEXT NOT NULL UNIQUE,
    display_order INTEGER DEFAULT 0,
    description TEXT,
    storage_limit INTEGER DEFAULT 1073741824,
    max_file_size INTEGER DEFAULT 52428800,
    max_file_count INTEGER DEFAULT 100,
    download_speed_limit INTEGER DEFAULT 0,
    upload_speed_limit INTEGER DEFAULT 0,
    daily_download_limit INTEGER DEFAULT 0,
    daily_upload_limit INTEGER DEFAULT 0,
    can_share_files INTEGER DEFAULT 0,
    can_create_public_links INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_level_code ON membership_levels(level_code);
CREATE INDEX IF NOT EXISTS idx_display_order ON membership_levels(display_order);
CREATE INDEX IF NOT EXISTS idx_priority ON membership_levels(priority);

-- 2. 用户会员关系表
CREATE TABLE IF NOT EXISTS user_memberships (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level_id INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    auto_renew INTEGER DEFAULT 0,
    storage_used INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE RESTRICT,
    UNIQUE (user_id, is_active)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_id ON user_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_level_id ON user_memberships(level_id);
CREATE INDEX IF NOT EXISTS idx_end_date ON user_memberships(end_date);
CREATE INDEX IF NOT EXISTS idx_is_active ON user_memberships(is_active);

-- 3. 会员权益表（详细权益配置）
CREATE TABLE IF NOT EXISTS membership_benefits (
    benefit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_id INTEGER NOT NULL,
    benefit_type TEXT NOT NULL,
    benefit_value TEXT NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_level_id_benefits ON membership_benefits(level_id);
CREATE INDEX IF NOT EXISTS idx_benefit_type ON membership_benefits(benefit_type);

-- 4. 会员订单表
CREATE TABLE IF NOT EXISTS membership_orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    level_id INTEGER NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'CNY',
    duration_days INTEGER NOT NULL,
    payment_method TEXT,
    payment_status TEXT DEFAULT 'pending',
    payment_time TIMESTAMP,
    transaction_id TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE RESTRICT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_id_orders ON membership_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_no ON membership_orders(order_no);
CREATE INDEX IF NOT EXISTS idx_payment_status ON membership_orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_created_at ON membership_orders(created_at);

-- 5. 会员操作日志表
CREATE TABLE IF NOT EXISTS membership_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    action_detail TEXT,
    old_level_id INTEGER,
    new_level_id INTEGER,
    operator_id INTEGER,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_id_logs ON membership_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_action_type ON membership_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_created_at_logs ON membership_logs(created_at);

-- 6. 积分记录表（扩展用户积分功能）
CREATE TABLE IF NOT EXISTS point_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    points_change INTEGER NOT NULL,
    points_after INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    description TEXT,
    related_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_user_id_points ON point_records(user_id);
CREATE INDEX IF NOT EXISTS idx_change_type ON point_records(change_type);
CREATE INDEX IF NOT EXISTS idx_created_at_points ON point_records(created_at);

-- 插入默认会员等级数据
INSERT OR IGNORE INTO membership_levels (level_name, level_code, display_order, description, storage_limit, max_file_size, max_file_count, priority) VALUES
('普通用户', 'free', 1, '免费用户，基础功能', 1073741824, 52428800, 100, 1),
('白银会员', 'silver', 2, '白银会员，更多存储空间', 5368709120, 104857600, 500, 2),
('黄金会员', 'gold', 3, '黄金会员，高级功能', 10737418240, 209715200, 1000, 3),
('钻石会员', 'diamond', 4, '钻石会员，尊享特权', 53687091200, 1073741824, 10000, 4);

-- 插入默认会员权益数据
INSERT OR IGNORE INTO membership_benefits (level_id, benefit_type, benefit_value, description) VALUES
-- 免费用户权益
(1, 'storage_limit', '1GB', '存储容量1GB'),
(1, 'max_file_size', '50MB', '单文件最大50MB'),
(1, 'max_file_count', '100', '最多100个文件'),
(1, 'can_share_files', 'false', '不能分享文件'),
(1, 'can_create_public_links', 'false', '不能创建公开链接'),
-- 白银会员权益
(2, 'storage_limit', '5GB', '存储容量5GB'),
(2, 'max_file_size', '100MB', '单文件最大100MB'),
(2, 'max_file_count', '500', '最多500个文件'),
(2, 'can_share_files', 'true', '可以分享文件'),
(2, 'can_create_public_links', 'false', '不能创建公开链接'),
-- 黄金会员权益
(3, 'storage_limit', '10GB', '存储容量10GB'),
(3, 'max_file_size', '200MB', '单文件最大200MB'),
(3, 'max_file_count', '1000', '最多1000个文件'),
(3, 'can_share_files', 'true', '可以分享文件'),
(3, 'can_create_public_links', 'true', '可以创建公开链接'),
(3, 'daily_download_limit', '100', '每日下载100次'),
-- 钻石会员权益
(4, 'storage_limit', '50GB', '存储容量50GB'),
(4, 'max_file_size', '1GB', '单文件最大1GB'),
(4, 'max_file_count', '10000', '最多10000个文件'),
(4, 'can_share_files', 'true', '可以分享文件'),
(4, 'can_create_public_links', 'true', '可以创建公开链接'),
(4, 'daily_download_limit', '1000', '每日下载1000次'),
(4, 'daily_upload_limit', '500', '每日上传500次');

-- 为现有用户创建默认的免费会员记录
INSERT OR IGNORE INTO user_memberships (user_id, level_id, start_date, is_active)
SELECT user_id, 1, datetime('now'), 1
FROM users
WHERE user_id NOT IN (SELECT user_id FROM user_memberships WHERE is_active = 1);

-- 创建存储使用量统计视图
CREATE VIEW IF NOT EXISTS v_user_storage_stats AS
SELECT
    um.user_id,
    um.level_id,
    um.storage_used,
    ml.storage_limit AS storage_limit,
    ml.max_file_size,
    ml.max_file_count,
    um.file_count,
    ml.level_name,
    ml.level_code,
    CASE
        WHEN um.storage_used >= ml.storage_limit THEN 1
        ELSE 0
    END AS is_storage_full,
    ROUND((CAST(um.storage_used AS REAL) / ml.storage_limit) * 100, 2) AS storage_usage_percentage,
    CASE
        WHEN um.end_date IS NULL THEN '永久'
        ELSE strftime('%Y-%m-%d', um.end_date)
    END AS membership_end_date,
    um.is_active AS membership_active
FROM user_memberships um
INNER JOIN membership_levels ml ON um.level_id = ml.level_id
WHERE um.is_active = 1;

-- 注意：SQLite不支持触发器在表创建后自动执行，需要手动创建触发器
-- 如果需要触发器功能，可以在应用层实现存储使用量的更新
