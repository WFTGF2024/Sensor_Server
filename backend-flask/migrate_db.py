"""
数据库迁移脚本 - 添加缺失的字段
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'sensor.db')

def migrate_database():
    """迁移数据库，添加缺失的字段"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查并添加 file_permission 字段
        cursor.execute("PRAGMA table_info(files)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'file_permission' not in columns:
            print("添加 file_permission 字段...")
            cursor.execute("ALTER TABLE files ADD COLUMN file_permission VARCHAR(20) DEFAULT 'private'")
            conn.commit()
            print("file_permission 字段添加成功")
        else:
            print("file_permission 字段已存在")

        if 'file_hash' not in columns:
            print("添加 file_hash 字段...")
            cursor.execute("ALTER TABLE files ADD COLUMN file_hash VARCHAR(64)")
            conn.commit()
            print("file_hash 字段添加成功")
        else:
            print("file_hash 字段已存在")

        if 'description' not in columns:
            print("添加 description 字段...")
            cursor.execute("ALTER TABLE files ADD COLUMN description TEXT")
            conn.commit()
            print("description 字段添加成功")
        else:
            print("description 字段已存在")

        print("\n数据库迁移完成！")

    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
