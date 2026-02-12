import sqlite3
import os
from flask import g, current_app
from config import current_config

# 使用 SQLite 数据库
DB_PATH = os.path.join(os.path.dirname(__file__), 'sensor.db')

def get_db():
    """
    Cache the DB connection in Flask's `g` object to avoid reconnecting.
    """
    if 'db' not in g:
        # 确保数据库文件存在
        if not os.path.exists(DB_PATH):
            init_db()

        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # 返回字典格式
    return g.db

def close_db(error=None):
    """
    Close the DB connection at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    初始化数据库表结构
    """
    # 确保数据库目录存在
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 创建数据库连接
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            qq VARCHAR(20),
            wechat VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            last_login_ip VARCHAR(100),
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # 创建文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_size INTEGER NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_type VARCHAR(50),
            mime_type VARCHAR(100),
            file_permission VARCHAR(20) DEFAULT 'private',
            file_hash VARCHAR(64),
            description TEXT,
            is_public BOOLEAN DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')

    # 创建会员等级表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS membership_levels (
            level_id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_name VARCHAR(50) UNIQUE NOT NULL,
            level_code VARCHAR(20) UNIQUE NOT NULL,
            display_order INTEGER DEFAULT 0,
            description TEXT,
            storage_limit INTEGER DEFAULT 1073741824,
            max_file_size INTEGER DEFAULT 52428800,
            max_file_count INTEGER DEFAULT 100,
            download_speed_limit INTEGER DEFAULT 0,
            upload_speed_limit INTEGER DEFAULT 0,
            daily_download_limit INTEGER DEFAULT 0,
            daily_upload_limit INTEGER DEFAULT 0,
            can_share_files BOOLEAN DEFAULT 0,
            can_create_public_links BOOLEAN DEFAULT 0,
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建用户会员关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memberships (
            membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            auto_renew BOOLEAN DEFAULT 0,
            storage_used INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            points_earned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (level_id) REFERENCES membership_levels(level_id) ON DELETE RESTRICT,
            UNIQUE(user_id, is_active)
        )
    ''')

    # 创建用户登录状态表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_login_status (
            user_id INTEGER PRIMARY KEY,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(100),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')

    # 插入默认会员等级数据
    cursor.execute('''
        INSERT OR IGNORE INTO membership_levels
        (level_name, level_code, display_order, description, storage_limit, max_file_size, max_file_count, priority)
        VALUES
        ('普通用户', 'free', 1, '免费用户，基础功能', 1073741824, 52428800, 100, 1),
        ('白银会员', 'silver', 2, '白银会员，更多存储空间', 5368709120, 104857600, 500, 2),
        ('黄金会员', 'gold', 3, '黄金会员，高级功能', 10737418240, 209715200, 1000, 3),
        ('钻石会员', 'diamond', 4, '钻石会员，尊享特权', 53687091200, 1073741824, 10000, 4)
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")
