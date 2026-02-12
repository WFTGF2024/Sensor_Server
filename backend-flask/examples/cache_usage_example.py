"""
缓存使用示例
演示如何在代码中使用缓存功能
"""

from utils import CacheManager, cache_result, performance_monitor
from repositories.user_repository import UserRepository
from repositories.file_repository import FileRepository
from repositories.membership_repository import UserMembershipRepository
import time

def example_1_direct_cache_usage():
    """示例1：直接使用CacheManager操作缓存"""
    print("\n=== 示例1：直接使用CacheManager ===")
    
    # 获取用户信息（会自动缓存）
    user_repo = UserRepository()
    user = user_repo.find_by_id(1)
    
    if user:
        print(f"用户信息: {user.get('username')}")
        
        # 获取缓存信息
        cached_user = CacheManager.get_user(1)
        print(f"缓存用户信息: {cached_user.get('username') if cached_user else 'None'}")
        
        # 使缓存失效
        CacheManager.invalidate_user(1)
        print("用户缓存已清除")

def example_2_cache_decorator():
    """示例2：使用缓存装饰器"""
    print("\n=== 示例2：使用缓存装饰器 ===")
    
    @cache_result(ttl=1800, prefix="expensive_calculation")
    def expensive_calculation(n):
        """模拟耗时计算"""
        print(f"执行耗时计算 {n}...")
        time.sleep(1)
        return n * n
    
    # 第一次调用（会执行计算）
    start = time.time()
    result1 = expensive_calculation(5)
    print(f"第一次结果: {result1}, 耗时: {time.time() - start:.2f}s")
    
    # 第二次调用（从缓存获取）
    start = time.time()
    result2 = expensive_calculation(5)
    print(f"第二次结果: {result2}, 耗时: {time.time() - start:.2f}s")

def example_3_file_cache():
    """示例3：文件缓存"""
    print("\n=== 示例3：文件缓存 ===")
    
    file_repo = FileRepository()
    
    # 获取文件信息（会自动缓存）
    file = file_repo.find_by_id(1)
    
    if file:
        print(f"文件名: {file.get('file_name')}")
        
        # 检查缓存
        cached_file = CacheManager.get_file(1)
        print(f"缓存文件信息: {cached_file.get('file_name') if cached_file else 'None'}")

def example_4_membership_cache():
    """示例4：会员信息缓存"""
    print("\n=== 示例4：会员信息缓存 ===")
    
    membership_repo = UserMembershipRepository()
    
    # 获取会员信息（会自动缓存）
    membership = membership_repo.find_active_by_user_id(1)
    
    if membership:
        print(f"会员等级: {membership.get('level_name')}")
        
        # 检查缓存
        cached_membership = CacheManager.get_membership(1)
        print(f"缓存会员信息: {cached_membership.get('level_name') if cached_membership else 'None'}")

def example_5_performance_monitoring():
    """示例5：性能监控"""
    print("\n=== 示例5：性能监控 ===")
    
    # 获取系统统计
    system_stats = performance_monitor.get_system_stats()
    print(f"CPU使用率: {system_stats.get('cpu_percent', 0)}%")
    print(f"内存使用率: {system_stats.get('memory_percent', 0)}%")
    
    # 获取缓存统计
    cache_stats = performance_monitor.get_cache_stats()
    print(f"缓存命中率: {cache_stats.get('hit_rate', 0)}%")
    print(f"缓存命中次数: {cache_stats.get('total_hits', 0)}")
    print(f"缓存未命中次数: {cache_stats.get('total_misses', 0)}")
    
    # 获取数据库统计
    db_stats = performance_monitor.get_database_stats()
    print(f"SELECT查询次数: {db_stats.get('select', {}).get('count', 0)}")
    print(f"SELECT平均耗时: {db_stats.get('select', {}).get('avg_duration', 0):.4f}s")

def example_6_cache_statistics():
    """示例6：缓存统计"""
    print("\n=== 示例6：缓存统计 ===")
    
    # 获取应用缓存统计
    cache_stats = CacheManager.get_stats()
    print(f"用户缓存数量: {cache_stats.get('user_cache_count', 0)}")
    print(f"文件缓存数量: {cache_stats.get('file_cache_count', 0)}")
    print(f"会员缓存数量: {cache_stats.get('membership_cache_count', 0)}")
    print(f"总缓存数量: {cache_stats.get('total_cache_count', 0)}")
    
    # 清除所有缓存（谨慎使用）
    # CacheManager.clear_all()
    # print("所有缓存已清除")

def main():
    """运行所有示例"""
    print("🚀 缓存使用示例")
    print("=" * 50)
    
    try:
        # 运行各个示例
        example_1_direct_cache_usage()
        example_2_cache_decorator()
        example_3_file_cache()
        example_4_membership_cache()
        example_5_performance_monitoring()
        example_6_cache_statistics()
        
        print("\n" + "=" * 50)
        print("✅ 所有示例运行完成！")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        print("\n请确保：")
        print("1. 应用已启动 (python app.py)")
        print("2. Redis服务已启动")
        print("3. 数据库中有测试数据")

if __name__ == "__main__":
    main()