#!/usr/bin/env python3
"""
清空重置后端所有数据
包括：数据库数据、上传的文件、Redis缓存、日志文件
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime


class DataResetter:
    """数据重置类"""

    def __init__(self):
        # 获取项目根目录
        self.project_root = Path(__file__).parent
        self.db_path = self.project_root / "sensor.db"
        self.upload_root = self.project_root / ".." / "data" / "download"
        self.log_dir = self.project_root / "log"
        self.cache_dir = self.project_root / "__pycache__"
        self.controllers_cache = self.project_root / "controllers" / "__pycache__"
        self.services_cache = self.project_root / "services" / "__pycache__"
        self.models_cache = self.project_root / "models" / "__pycache__"
        self.repositories_cache = self.project_root / "repositories" / "__pycache__"

        # 统计信息
        self.stats = {
            'users_deleted': 0,
            'files_deleted': 0,
            'memberships_deleted': 0,
            'files_removed': 0,
            'log_files_removed': 0,
            'cache_removed': 0
        }

    def print_banner(self):
        """打印横幅"""
        print("=" * 60)
        print("  后端数据重置工具")
        print("=" * 60)
        print()

    def confirm_reset(self):
        """确认是否执行重置"""
        print("警告：此操作将清空以下所有数据：")
        print("  - 数据库中的所有用户、文件、会员记录")
        print("  - 所有上传的文件")
        print("  - 所有日志文件")
        print("  - Python缓存文件")
        print("  - Redis缓存（如果启用）")
        print()
        print("此操作不可逆！")
        print()

        response = input("确认要继续吗？(输入 'yes' 确认): ")
        return response.lower() == 'yes'

    def reset_database(self):
        """重置数据库"""
        print("\n[1/5] 正在重置数据库...")

        if not self.db_path.exists():
            print(f"  数据库文件不存在: {self.db_path}")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # 禁用外键约束
            cursor.execute("PRAGMA foreign_keys = OFF")

            # 删除所有表
            for table in tables:
                table_name = table[0]
                # 统计删除的记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                print(f"  - 删除表: {table_name} ({count} 条记录)")

            # 重新启用外键约束
            cursor.execute("PRAGMA foreign_keys = ON")

            conn.commit()
            conn.close()

            # 删除数据库文件
            self.db_path.unlink()
            print(f"  ✓ 数据库已清空并删除")

        except Exception as e:
            print(f"  ✗ 数据库重置失败: {e}")

    def reset_upload_files(self):
        """重置上传文件"""
        print("\n[2/5] 正在删除上传文件...")

        if not self.upload_root.exists():
            print(f"  上传目录不存在: {self.upload_root}")
            return

        try:
            # 统计文件数量
            file_count = sum(1 for _ in self.upload_root.rglob('*') if _.is_file())

            # 删除目录中的所有内容
            for item in self.upload_root.iterdir():
                if item.is_file():
                    item.unlink()
                    self.stats['files_removed'] += 1
                elif item.is_dir():
                    shutil.rmtree(item)

            print(f"  ✓ 已删除 {file_count} 个文件")
            self.stats['files_removed'] = file_count

        except Exception as e:
            print(f"  ✗ 文件删除失败: {e}")

    def clear_redis_cache(self):
        """清除Redis缓存"""
        print("\n[3/5] 正在清除Redis缓存...")

        try:
            from config import current_config
            import redis

            if not current_config.REDIS_ENABLED:
                print("  - Redis未启用，跳过")
                return

            redis_config = current_config.get_redis_config()
            client = redis.Redis(**redis_config)

            # 测试连接
            client.ping()

            # 获取所有键
            keys = client.keys('*')
            count = len(keys)

            if count > 0:
                client.delete(*keys)
                print(f"  ✓ 已清除 {count} 个Redis键")
                self.stats['cache_removed'] = count
            else:
                print("  - Redis缓存为空")

        except ImportError:
            print("  - Redis模块未安装，跳过")
        except Exception as e:
            print(f"  - Redis清除失败: {e}")

    def clear_logs(self):
        """清除日志文件"""
        print("\n[4/5] 正在清除日志文件...")

        if not self.log_dir.exists():
            print(f"  日志目录不存在: {self.log_dir}")
            return

        try:
            log_files = list(self.log_dir.glob('*.txt'))
            count = len(log_files)

            for log_file in log_files:
                log_file.unlink()

            print(f"  ✓ 已删除 {count} 个日志文件")
            self.stats['log_files_removed'] = count

        except Exception as e:
            print(f"  ✗ 日志清除失败: {e}")

    def clear_python_cache(self):
        """清除Python缓存"""
        print("\n[5/5] 正在清除Python缓存...")

        cache_dirs = [
            self.cache_dir,
            self.controllers_cache,
            self.services_cache,
            self.models_cache,
            self.repositories_cache
        ]

        total_removed = 0

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                    total_removed += 1
                    print(f"  - 已删除: {cache_dir.name}")
                except Exception as e:
                    print(f"  - 删除失败: {cache_dir.name} - {e}")

        if total_removed > 0:
            print(f"  ✓ 已清除 {total_removed} 个缓存目录")
        else:
            print("  - 没有需要清除的缓存")

    def reinit_database(self):
        """重新初始化数据库"""
        print("\n正在重新初始化数据库...")

        try:
            from db import init_db
            init_db()
            print("  ✓ 数据库重新初始化完成")

        except Exception as e:
            print(f"  ✗ 数据库初始化失败: {e}")

    def print_summary(self):
        """打印重置摘要"""
        print("\n" + "=" * 60)
        print("  重置完成！")
        print("=" * 60)
        print("\n统计信息：")
        print(f"  - 删除的文件数: {self.stats['files_removed']}")
        print(f"  - 删除的日志数: {self.stats['log_files_removed']}")
        print(f"  - 清除的缓存键: {self.stats['cache_removed']}")
        print()
        print("数据库已重新初始化，包含默认的会员等级数据。")
        print()
        print("提示：如果需要测试，可以使用以下API创建测试用户：")
        print("  POST /api/auth/register")
        print("  {")
        print('    "username": "testuser",')
        print('    "password": "password123"')
        print("  }")
        print()

    def run(self):
        """执行重置操作"""
        self.print_banner()

        if not self.confirm_reset():
            print("操作已取消")
            return

        start_time = datetime.now()

        # 执行重置步骤
        self.reset_database()
        self.reset_upload_files()
        self.clear_redis_cache()
        self.clear_logs()
        self.clear_python_cache()

        # 重新初始化数据库
        self.reinit_database()

        # 打印摘要
        self.print_summary()

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"总耗时: {elapsed:.2f} 秒\n")


def main():
    """主函数"""
    resetter = DataResetter()
    resetter.run()


if __name__ == "__main__":
    main()
