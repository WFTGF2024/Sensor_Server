-- 会员系统数据库表结构
-- 创建时间: 2026-02-05
-- 说明: 为 Sensor_Flask 项目添加会员系统功能

-- 1. 会员等级表
CREATE TABLE IF NOT EXISTS membership_levels (
    level_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '会员等级ID',
    level_name VARCHAR(50) NOT NULL UNIQUE COMMENT '会员等级名称',
    level_code VARCHAR(20) NOT NULL UNIQUE COMMENT '会员等级代码',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    description TEXT COMMENT '等级描述',
    storage_limit BIGINT DEFAULT 1073741824 COMMENT '存储容量限制（字节），默认1GB',
    max_file_size BIGINT DEFAULT 52428800 COMMENT '单文件最大大小（字节），默认50MB',
    max_file_count INT DEFAULT 100 COMMENT '最大文件数量限制',
    download_speed_limit INT DEFAULT 0 COMMENT '下载速度限制（KB/s），0表示无限制',
    upload_speed_limit INT DEFAULT 0 COMMENT '上传速度限制（KB/s），0表示无限制',
    daily_download_limit INT DEFAULT 0 COMMENT '每日下载次数限制，0表示无限制',
    daily_upload_limit INT DEFAULT 0 COMMENT '每日上传次数限制，0表示无限制',
    can_share_files BOOLEAN DEFAULT FALSE COMMENT '是否可以分享文件',
    can_create_public_links BOOLEAN DEFAULT FALSE COMMENT '是否可以创建公开链接',
    priority INT DEFAULT 0 COMMENT '会员优先级，数字越大优先级越高',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_level_code (level_code),
    INDEX idx_display_order (display_order),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员等级表';

-- 2. 用户会员关系表
CREATE TABLE IF NOT EXISTS user_memberships (
    membership_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '会员记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    level_id INT NOT NULL COMMENT '会员等级ID',
    start_date DATETIME NOT NULL COMMENT '会员开始时间',
    end_date DATETIME COMMENT '会员结束时间，NULL表示永久会员',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    auto_renew BOOLEAN DEFAULT FALSE COMMENT '是否自动续费',
    storage_used BIGINT DEFAULT 0 COMMENT '已使用的存储空间（字节）',
    file_count INT DEFAULT 0 COMMENT '已上传的文件数量',
    points_earned INT DEFAULT 0 COMMENT '累计获得的积分',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE RESTRICT,
    UNIQUE KEY uk_user_active (user_id, is_active) COMMENT '确保每个用户只有一个激活的会员',
    INDEX idx_user_id (user_id),
    INDEX idx_level_id (level_id),
    INDEX idx_end_date (end_date),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会员关系表';

-- 3. 会员权益表（详细权益配置）
CREATE TABLE IF NOT EXISTS membership_benefits (
    benefit_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '权益ID',
    level_id INT NOT NULL COMMENT '会员等级ID',
    benefit_type VARCHAR(50) NOT NULL COMMENT '权益类型（storage_limit/file_size_limit/file_count_limit等）',
    benefit_value VARCHAR(255) NOT NULL COMMENT '权益值',
    description TEXT COMMENT '权益描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE CASCADE,
    INDEX idx_level_id (level_id),
    INDEX idx_benefit_type (benefit_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员权益表';

-- 4. 会员订单表
CREATE TABLE IF NOT EXISTS membership_orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
    order_no VARCHAR(50) NOT NULL UNIQUE COMMENT '订单号',
    user_id INT NOT NULL COMMENT '用户ID',
    level_id INT NOT NULL COMMENT '购买的会员等级ID',
    price DECIMAL(10, 2) NOT NULL COMMENT '订单金额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '货币类型',
    duration_days INT NOT NULL COMMENT '会员有效期（天）',
    payment_method VARCHAR(50) COMMENT '支付方式',
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending' COMMENT '支付状态',
    payment_time TIMESTAMP NULL COMMENT '支付时间',
    transaction_id VARCHAR(100) COMMENT '第三方交易ID',
    remark TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE RESTRICT,
    INDEX idx_user_id (user_id),
    INDEX idx_order_no (order_no),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员订单表';

-- 5. 会员操作日志表
CREATE TABLE IF NOT EXISTS membership_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id INT NOT NULL COMMENT '用户ID',
    action_type VARCHAR(50) NOT NULL COMMENT '操作类型（upgrade/downgrade/renew/expire等）',
    action_detail TEXT COMMENT '操作详情',
    old_level_id INT COMMENT '原会员等级ID',
    new_level_id INT COMMENT '新会员等级ID',
    operator_id INT COMMENT '操作人ID',
    ip_address VARCHAR(100) COMMENT 'IP地址',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_action_type (action_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会员操作日志表';

-- 6. 积分记录表（扩展用户积分功能）
CREATE TABLE IF NOT EXISTS point_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    points_change INT NOT NULL COMMENT '积分变化（正数为增加，负数为减少）',
    points_after INT NOT NULL COMMENT '变化后的积分余额',
    change_type VARCHAR(50) NOT NULL COMMENT '变化类型（register/login/upload/download/purchase/refund等）',
    description TEXT COMMENT '描述',
    related_id INT COMMENT '关联ID（如订单ID、文件ID等）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_change_type (change_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分记录表';

-- 插入默认会员等级数据
INSERT INTO membership_levels (level_name, level_code, display_order, description, storage_limit, max_file_size, max_file_count, priority) VALUES
('普通用户', 'free', 1, '免费用户，基础功能', 1073741824, 52428800, 100, 1),
('白银会员', 'silver', 2, '白银会员，更多存储空间', 5368709120, 104857600, 500, 2),
('黄金会员', 'gold', 3, '黄金会员，高级功能', 10737418240, 209715200, 1000, 3),
('钻石会员', 'diamond', 4, '钻石会员，尊享特权', 53687091200, 1073741824, 10000, 4);

-- 插入默认会员权益数据
INSERT INTO membership_benefits (level_id, benefit_type, benefit_value, description) VALUES
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
INSERT INTO user_memberships (user_id, level_id, start_date, is_active)
SELECT user_id, 1, NOW(), TRUE
FROM users
WHERE user_id NOT IN (SELECT user_id FROM user_memberships WHERE is_active = TRUE);

-- 创建存储使用量统计视图
CREATE OR REPLACE VIEW v_user_storage_stats AS
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
    ROUND((um.storage_used / ml.storage_limit) * 100, 2) AS storage_usage_percentage,
    CASE 
        WHEN um.end_date IS NULL THEN '永久'
        ELSE DATE_FORMAT(um.end_date, '%Y-%m-%d')
    END AS membership_end_date,
    um.is_active AS membership_active
FROM user_memberships um
INNER JOIN membership_levels ml ON um.level_id = ml.level_id
WHERE um.is_active = TRUE;

-- 添加触发器：当文件上传时自动更新用户存储使用量
DELIMITER $$

CREATE TRIGGER trg_file_upload_update_storage
AFTER INSERT ON files
FOR EACH ROW
BEGIN
    UPDATE user_memberships
    SET storage_used = storage_used + NEW.file_size,
        file_count = file_count + 1
    WHERE user_id = NEW.user_id AND is_active = TRUE;
END$$

CREATE TRIGGER trg_file_delete_update_storage
AFTER DELETE ON files
FOR EACH ROW
BEGIN
    UPDATE user_memberships
    SET storage_used = GREATEST(0, storage_used - OLD.file_size),
        file_count = GREATEST(0, file_count - 1)
    WHERE user_id = OLD.user_id AND is_active = TRUE;
END$$

DELIMITER ;
