"""
Redis client management for Sensor_Flask application.
Provides Redis connection pooling and cache management.
"""

import json
import pickle
import time
import logging
from typing import Any, Optional, Union, Dict, List
from flask import g, current_app
from config import current_config

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis客户端管理类"""
    
    def __init__(self):
        self._client = None
        self._enabled = current_config.REDIS_ENABLED
        self._default_ttl = current_config.REDIS_CACHE_TTL
        
    def get_client(self):
        """
        获取Redis客户端连接。
        使用Flask的g对象缓存连接，避免重复创建。
        
        Returns:
            Redis客户端实例，如果Redis未启用则返回None
        """
        if not self._enabled:
            return None
            
        if 'redis' not in g:
            try:
                import redis
                redis_config = current_config.get_redis_config()
                g.redis = redis.Redis(**redis_config)
                
                # 测试连接
                g.redis.ping()
                logger.info("Redis connection established successfully")
                
            except ImportError:
                logger.warning("Redis module not installed. Install with: pip install redis")
                g.redis = None
                self._enabled = False
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                g.redis = None
                # 在开发环境中，如果Redis连接失败，可以降级到内存缓存
                if current_config.DEBUG:
                    logger.warning("Falling back to in-memory cache for development")
                    g.redis = None
                    self._enabled = False
                else:
                    raise
        
        return g.redis
    
    def close(self, error=None):
        """
        关闭Redis连接。
        
        Args:
            error: 错误信息（如果有）
        """
        redis_client = g.pop('redis', None)
        if redis_client is not None:
            try:
                redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
    
    def is_enabled(self) -> bool:
        """
        检查Redis是否启用。
        
        Returns:
            bool: 如果Redis启用返回True，否则返回False
        """
        return self._enabled
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值。
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认TTL
            
        Returns:
            bool: 是否设置成功
        """
        if not self._enabled:
            return False
            
        client = self.get_client()
        if not client:
            return False
            
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple, int, float, str, bool, type(None))):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = pickle.dumps(value)
            
            # 设置缓存
            expire_time = ttl if ttl is not None else self._default_ttl
            result = client.setex(key, expire_time, serialized_value)
            
            if result:
                logger.debug(f"Cache set: {key} (TTL: {expire_time}s)")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值。
        
        Args:
            key: 缓存键
            default: 默认值（如果缓存不存在）
            
        Returns:
            缓存值或默认值
        """
        if not self._enabled:
            return default
            
        client = self.get_client()
        if not client:
            return default
            
        try:
            value = client.get(key)
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return default
            
            # 尝试反序列化
            try:
                result = json.loads(value)
            except json.JSONDecodeError:
                try:
                    result = pickle.loads(value)
                except:
                    result = value.decode('utf-8') if isinstance(value, bytes) else value
            
            logger.debug(f"Cache hit: {key}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """
        删除缓存键。
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if not self._enabled:
            return False
            
        client = self.get_client()
        if not client:
            return False
            
        try:
            result = client.delete(key)
            if result:
                logger.debug(f"Cache deleted: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在。
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        if not self._enabled:
            return False
            
        client = self.get_client()
        if not client:
            return False
            
        try:
            return bool(client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间。
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        if not self._enabled:
            return False
            
        client = self.get_client()
        if not client:
            return False
            
        try:
            return bool(client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Failed to set expire for cache key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存键。
        
        Args:
            pattern: 键模式（支持通配符）
            
        Returns:
            int: 删除的键数量
        """
        if not self._enabled:
            return 0
            
        client = self.get_client()
        if not client:
            return 0
            
        try:
            keys = client.keys(pattern)
            if keys:
                deleted = client.delete(*keys)
                logger.debug(f"Cleared cache pattern {pattern}: {deleted} keys deleted")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取Redis统计信息。
        
        Returns:
            dict: 统计信息
        """
        if not self._enabled:
            return {"enabled": False, "status": "disabled"}
            
        client = self.get_client()
        if not client:
            return {"enabled": False, "status": "connection_failed"}
            
        try:
            info = client.info()
            stats = {
                "enabled": True,
                "status": "connected",
                "version": info.get('redis_version', 'unknown'),
                "uptime": info.get('uptime_in_seconds', 0),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": info.get('used_memory_human', '0B'),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": 0
            }
            
            # 计算命中率
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            total = hits + misses
            if total > 0:
                stats['hit_rate'] = round(hits / total * 100, 2)
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"enabled": True, "status": "error", "error": str(e)}


# 全局Redis客户端实例
redis_client = RedisClient()

def get_redis():
    """
    获取Redis客户端。
    
    Returns:
        Redis客户端实例
    """
    return redis_client.get_client()

def close_redis(error=None):
    """
    关闭Redis连接。
    
    Args:
        error: 错误信息
    """
    redis_client.close(error)