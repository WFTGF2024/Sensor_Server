#!/usr/bin/env python3
"""
快速重置后端数据（无需确认）
适合自动化脚本或开发环境使用
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime


def quick_reset():
    """快速重置所有数据"""

    print("=" * 60)
    print("  快速重置后端数据")
    print("=" * 60)
    print()

    project_root = Path(__file__).parent
    db_path = project_root / "sensor.db"
    upload_root = project_root / ".." / "data" / "download"
    log_dir = project_root / "log"

    start_time = datetime.now()

    # 1. 重置数据库
    print("[1/4] 重置数据库...")
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")

            conn.commit()
            conn.close()
            db_path.unlink()
            print("  ✓ 数据库已清空")
        except Exception as e:
            print(f"  ✗ 数据库重置失败: {e}")
    else:
        print("  - 数据库文件不存在")

    # 2. 删除上传文件
    print("[2/4] 删除上传文件...")
    if upload_root.exists():
        try:
            for item in upload_root.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print("  ✓ 文件已删除")
        except Exception as e:
            print(f"  ✗ 文件删除失败: {e}")
    else:
        print("  - 上传目录不存在")

    # 3. 清除日志
    print("[3/4] 清除日志...")
    if log_dir.exists():
        try:
            for log_file in log_dir.glob('*.txt'):
                log_file.unlink()
            print("  ✓ 日志已清除")
        except Exception as e:
            print(f"  ✗ 日志清除失败: {e}")
    else:
        print("  - 日志目录不存在")

    # 4. 清除缓存
    print("[4/4] 清除Python缓存...")
    cache_dirs = [
        project_root / "__pycache__",
        project_root / "controllers" / "__pycache__",
        project_root / "services" / "__pycache__",
        project_root / "models" / "__pycache__",
        project_root / "repositories" / "__pycache__",
    ]
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
            except:
                pass
    print("  ✓ 缓存已清除")

    # 5. 清除Redis（如果启用）
    try:
        from config import current_config
        if current_config.REDIS_ENABLED:
            print("[清除Redis]")
            import redis
            redis_config = current_config.get_redis_config()
            client = redis.Redis(**redis_config)
            keys = client.keys('*')
            if keys:
                client.delete(*keys)
                print(f"  ✓ Redis缓存已清除 ({len(keys)} 个键)")
    except:
        pass

    # 重新初始化数据库
    print("\n重新初始化数据库...")
    try:
        from db import init_db
        init_db()
        print("  ✓ 数据库初始化完成")
    except Exception as e:
        print(f"  ✗ 数据库初始化失败: {e}")

    elapsed = (datetime.now() - start_time).total_seconds()
    print()
    print("=" * 60)
    print(f"  重置完成！耗时: {elapsed:.2f} 秒")
    print("=" * 60)
    print()


if __name__ == "__main__":
    quick_reset()
