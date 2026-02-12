"""
缓存工具类，提供缓存装饰器和缓存管理功能。
"""

import hashlib
import json
import time
import functools
import logging
from typing import Any, Callable, Optional, Dict, List, Tuple
from redis_client import redis_client

logger = logging.getLogger(__name__)

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键。
    
    Args:
        prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        str: 缓存键
    """
    # 将参数转换为字符串表示
    args_str = str(args)
    kwargs_str = str(sorted(kwargs.items()))
    
    # 生成MD5哈希
    key_string = f"{prefix}:{args_str}:{kwargs_str}"
    key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    return f"cache:{prefix}:{key_hash}"

def cache_result(ttl: Optional[int] = None, prefix: str = "func"):
    """
    缓存函数结果的装饰器。
    
    Args:
        ttl: 缓存过期时间（秒），如果为None则使用默认TTL
        prefix: 缓存键前缀
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 如果Redis未启用，直接执行函数
            if not redis_client.is_enabled():
                return func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = generate_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # 尝试从缓存获取结果
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # 缓存未命中，执行函数
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            
            # 将结果存入缓存
            if result is not None:
                redis_client.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str) -> int:
    """
    使匹配模式的缓存失效。
    
    Args:
        pattern: 缓存键模式
        
    Returns:
        int: 删除的缓存键数量
    """
    if not redis_client.is_enabled():
        return 0
    
    full_pattern = f"cache:{pattern}:*"
    return redis_client.clear_pattern(full_pattern)

class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def cache_user(user_id: int, user_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        缓存用户信息。
        
        Args:
            user_id: 用户ID
            user_data: 用户数据
            ttl: 过期时间
            
        Returns:
            bool: 是否缓存成功
        """
        if not redis_client.is_enabled():
            return False
        
        cache_key = f"user:{user_id}"
        return redis_client.set(cache_key, user_data, ttl)
    
    @staticmethod
    def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存的用户信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户数据，如果不存在则返回None
        """
        if not redis_client.is_enabled():
            return None
        
        cache_key = f"user:{user_id}"
        return redis_client.get(cache_key)
    
    @staticmethod
    def invalidate_user(user_id: int) -> bool:
        """
        使用户缓存失效。
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        if not redis_client.is_enabled():
            return False
        
        cache_key = f"user:{user_id}"
        return redis_client.delete(cache_key)
    
    @staticmethod
    def cache_file(file_id: int, file_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        缓存文件信息。
        
        Args:
            file_id: 文件ID
            file_data: 文件数据
            ttl: 过期时间
            
        Returns:
            bool: 是否缓存成功
        """
        if not redis_client.is_enabled():
            return False
        
        cache_key = f"file:{file_id}"
        return redis_client.set(cache_key, file_data, ttl)
    
    @staticmethod
    def get_file(file_id: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存的文件信息。
        
        Args:
            file_id: 文件ID
            
        Returns:
            dict: 文件数据，如果不存在则返回None
        """
        if not redis_client.is_enabled():
            return None
        
        cache_key = f"file:{file_id}"
        return redis_client.get(cache_key)
    
    @staticmethod
    def invalidate_file(file_id: int) -> bool:
        """
        使文件缓存失效。
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否删除成功
        """
        if not redis_client.is_enabled():
            return False
        
        cache_key = f"file:{file_id}"
        return redis_client.delete(cache_key)
    
    @staticmethod
    def cache_membership(user_id: int, membership_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        缓存会员信息。
        
        Args:
            user_id: 用户ID
            membership_data: 会员数据
            ttl: 过期时间
            
        Returns:
            bool: 是否缓存成功
        """
        if not redis_client.is_enabled():
            return False
        
        cache_key = f"membership:{user_id}"
        return redis_client.set(cache_key, membership_data, ttl)
    
    @staticmethod
    def get_membership(user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存的会员信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 会员数据，如果不存在则返回None
        """
        if not redis_client.is_enabled():
            return None
        
        cache_key = f"membership:{user_id}"
        return redis_client.get(cache_key)
    
    @staticmethod
    def invalidate_membership(user_id: int) -> bool:
        """
        使会员缓存失效。
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        if not redis_client.is_enabled():
            return False
        
        cache_key = f"membership:{user_id}"
        return redis_client.delete(cache_key)
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """
        获取缓存统计信息。
        
        Returns:
            dict: 统计信息
        """
        if not redis_client.is_enabled():
            return {"enabled": False}
        
        # 获取各种缓存的统计
        stats = {
            "enabled": True,
            "user_cache_count": 0,
            "file_cache_count": 0,
            "membership_cache_count": 0,
            "total_cache_count": 0
        }
        
        try:
            client = redis_client.get_client()
            if client:
                # 统计各种缓存的数量
                user_keys = client.keys("user:*")
                file_keys = client.keys("file:*")
                membership_keys = client.keys("membership:*")
                
                stats.update({
                    "user_cache_count": len(user_keys),
                    "file_cache_count": len(file_keys),
                    "membership_cache_count": len(membership_keys),
                    "total_cache_count": len(user_keys) + len(file_keys) + len(membership_keys)
                })
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
        
        return stats
    
    @staticmethod
    def clear_all() -> int:
        """
        清除所有缓存。
        
        Returns:
            int: 删除的缓存键数量
        """
        if not redis_client.is_enabled():
            return 0
        
        return redis_client.clear_pattern("cache:*") + redis_client.clear_pattern("user:*") + \
               redis_client.clear_pattern("file:*") + redis_client.clear_pattern("membership:*")