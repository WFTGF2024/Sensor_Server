"""
应用性能监控模块。
提供请求监控、性能指标收集和统计功能。
"""

import time
import random
import threading
import statistics
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import logging
from flask import request, g, current_app
from config import current_config
from redis_client import redis_client

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics_lock = threading.Lock()
        self.metrics = defaultdict(list)
        self.enabled = current_config.MONITOR_ENABLED
        self.sample_rate = current_config.MONITOR_SAMPLE_RATE
        self.retention = current_config.MONITOR_METRICS_RETENTION
        self.redis_initialized = False
    
    def _init_redis_storage(self):
        """初始化Redis存储"""
        if self.redis_initialized:
            return

        try:
            # 尝试在应用上下文中初始化
            from flask import current_app
            with current_app.app_context():
                client = redis_client.get_client()
                if client:
                    # 创建监控键空间
                    client.set("monitor:initialized", datetime.now().isoformat())
                    self.redis_initialized = True
                    logger.info("Performance monitoring initialized with Redis storage")
        except RuntimeError as e:
            # 如果不在应用上下文中,延迟初始化
            logger.debug(f"Cannot initialize Redis storage outside app context: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis storage for monitoring: {e}")

    def _ensure_redis_initialized(self):
        """确保Redis存储已初始化"""
        if self.enabled and redis_client.is_enabled() and not self.redis_initialized:
            try:
                # 尝试在应用上下文中初始化
                from flask import current_app
                with current_app.app_context():
                    self._init_redis_storage()
            except RuntimeError:
                # 如果不在应用上下文中,跳过初始化
                pass
    
    def should_sample(self) -> bool:
        """
        决定是否采样当前请求。
        
        Returns:
            bool: 是否采样
        """
        if not self.enabled:
            return False
        return random.random() < self.sample_rate
    
    def record_request(self, endpoint: str, method: str, status_code: int,
                      duration: float, user_id: Optional[int] = None):
        """
        记录请求性能指标。

        Args:
            endpoint: 请求端点
            method: HTTP方法
            status_code: 状态码
            duration: 请求处理时间（秒）
            user_id: 用户ID（可选）
        """
        if not self.should_sample():
            return

        self._ensure_redis_initialized()

        timestamp = datetime.now()
        metric = {
            "timestamp": timestamp.isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration": duration,
            "user_id": user_id
        }

        # 存储到内存
        with self.metrics_lock:
            self.metrics["requests"].append(metric)
            # 保持最近1000个请求
            if len(self.metrics["requests"]) > 1000:
                self.metrics["requests"] = self.metrics["requests"][-1000:]

        # 存储到Redis（如果可用）
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    # 使用有序集合存储请求时间线
                    score = timestamp.timestamp()
                    client.zadd("monitor:requests:timeline", {json.dumps(metric): score})

                    # 清理过期数据
                    cutoff = (timestamp - timedelta(seconds=self.retention)).timestamp()
                    client.zremrangebyscore("monitor:requests:timeline", 0, cutoff)

                    # 更新端点统计
                    endpoint_key = f"monitor:endpoint:{endpoint}:{method}"
                    client.hincrby(endpoint_key, "count", 1)
                    client.hincrbyfloat(endpoint_key, "total_duration", duration)
                    client.hsetnx(endpoint_key, "first_seen", timestamp.isoformat())
                    client.hset(endpoint_key, "last_seen", timestamp.isoformat())

                    # 更新状态码统计
                    status_key = f"monitor:status:{status_code}"
                    client.hincrby(status_key, "count", 1)

            except Exception as e:
                logger.error(f"Failed to store request metric in Redis: {e}")
    
    def record_cache_hit(self, cache_type: str, key: str):
        """
        记录缓存命中。
        
        Args:
            cache_type: 缓存类型（user/file/membership等）
            key: 缓存键
        """
        if not self.should_sample():
            return
        
        timestamp = datetime.now()
        metric = {
            "timestamp": timestamp.isoformat(),
            "type": "cache_hit",
            "cache_type": cache_type,
            "key": key
        }
        
        with self.metrics_lock:
            self.metrics["cache_hits"].append(metric)
        
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    client.hincrby("monitor:cache:stats", f"{cache_type}_hits", 1)
            except Exception as e:
                logger.error(f"Failed to record cache hit: {e}")
    
    def record_cache_miss(self, cache_type: str, key: str):
        """
        记录缓存未命中。
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
        """
        if not self.should_sample():
            return
        
        timestamp = datetime.now()
        metric = {
            "timestamp": timestamp.isoformat(),
            "type": "cache_miss",
            "cache_type": cache_type,
            "key": key
        }
        
        with self.metrics_lock:
            self.metrics["cache_misses"].append(metric)
        
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    client.hincrby("monitor:cache:stats", f"{cache_type}_misses", 1)
            except Exception as e:
                logger.error(f"Failed to record cache miss: {e}")
    
    def record_database_query(self, query_type: str, duration: float, success: bool = True):
        """
        记录数据库查询性能。
        
        Args:
            query_type: 查询类型（select/insert/update/delete）
            duration: 查询时间（秒）
            success: 是否成功
        """
        if not self.should_sample():
            return
        
        timestamp = datetime.now()
        metric = {
            "timestamp": timestamp.isoformat(),
            "type": "db_query",
            "query_type": query_type,
            "duration": duration,
            "success": success
        }
        
        with self.metrics_lock:
            self.metrics["db_queries"].append(metric)
        
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    key = f"monitor:db:{query_type}"
                    client.hincrby(key, "count", 1)
                    client.hincrbyfloat(key, "total_duration", duration)
                    if not success:
                        client.hincrby(key, "errors", 1)
            except Exception as e:
                logger.error(f"Failed to record database query: {e}")
    
    def get_request_stats(self, time_window: int = 3600) -> Dict[str, Any]:
        """
        获取请求统计信息。
        
        Args:
            time_window: 时间窗口（秒）
            
        Returns:
            dict: 请求统计信息
        """
        stats = {
            "total_requests": 0,
            "avg_duration": 0,
            "p95_duration": 0,
            "p99_duration": 0,
            "endpoints": {},
            "status_codes": {}
        }
        
        cutoff = datetime.now() - timedelta(seconds=time_window)
        
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    # 从Redis获取时间窗口内的数据
                    min_score = cutoff.timestamp()
                    max_score = datetime.now().timestamp()
                    
                    requests = client.zrangebyscore("monitor:requests:timeline", min_score, max_score)
                    durations = []
                    
                    for req_json in requests:
                        try:
                            req = json.loads(req_json)
                            durations.append(req["duration"])
                            
                            # 统计端点
                            endpoint_key = f"{req['endpoint']}:{req['method']}"
                            stats["endpoints"][endpoint_key] = stats["endpoints"].get(endpoint_key, 0) + 1
                            
                            # 统计状态码
                            status_code = str(req["status_code"])
                            stats["status_codes"][status_code] = stats["status_codes"].get(status_code, 0) + 1
                            
                        except (json.JSONDecodeError, KeyError):
                            continue
                    
                    if durations:
                        stats["total_requests"] = len(durations)
                        stats["avg_duration"] = statistics.mean(durations)
                        if len(durations) >= 5:
                            stats["p95_duration"] = statistics.quantiles(durations, n=20)[18]  # 95th percentile
                            stats["p99_duration"] = statistics.quantiles(durations, n=100)[98]  # 99th percentile
                    
            except Exception as e:
                logger.error(f"Failed to get request stats from Redis: {e}")
        
        return stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息。
        
        Returns:
            dict: 缓存统计信息
        """
        stats = {
            "user_hits": 0,
            "user_misses": 0,
            "file_hits": 0,
            "file_misses": 0,
            "membership_hits": 0,
            "membership_misses": 0,
            "total_hits": 0,
            "total_misses": 0
        }
        
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    cache_stats = client.hgetall("monitor:cache:stats")
                    for key, value in cache_stats.items():
                        if key in stats:
                            stats[key] = int(value)
                    
                    # 计算总计
                    stats["total_hits"] = stats["user_hits"] + stats["file_hits"] + stats["membership_hits"]
                    stats["total_misses"] = stats["user_misses"] + stats["file_misses"] + stats["membership_misses"]
                    
                    # 计算命中率
                    total = stats["total_hits"] + stats["total_misses"]
                    if total > 0:
                        stats["hit_rate"] = round(stats["total_hits"] / total * 100, 2)
                    
            except Exception as e:
                logger.error(f"Failed to get cache stats from Redis: {e}")
        
        return stats
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息。
        
        Returns:
            dict: 数据库统计信息
        """
        stats = {
            "select": {"count": 0, "total_duration": 0, "avg_duration": 0, "errors": 0},
            "insert": {"count": 0, "total_duration": 0, "avg_duration": 0, "errors": 0},
            "update": {"count": 0, "total_duration": 0, "avg_duration": 0, "errors": 0},
            "delete": {"count": 0, "total_duration": 0, "avg_duration": 0, "errors": 0}
        }
        
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    for query_type in ["select", "insert", "update", "delete"]:
                        key = f"monitor:db:{query_type}"
                        data = client.hgetall(key)
                        if data:
                            count = int(data.get("count", 0))
                            total_duration = float(data.get("total_duration", 0))
                            errors = int(data.get("errors", 0))
                            
                            stats[query_type] = {
                                "count": count,
                                "total_duration": total_duration,
                                "avg_duration": round(total_duration / count, 4) if count > 0 else 0,
                                "errors": errors
                            }
                    
            except Exception as e:
                logger.error(f"Failed to get database stats from Redis: {e}")
        
        return stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息。
        
        Returns:
            dict: 系统统计信息
        """
        import psutil
        import os
        
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
            "memory_total_mb": psutil.virtual_memory().total / 1024 / 1024,
            "disk_usage_percent": psutil.disk_usage('.').percent,
            "process_memory_mb": psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024,
            "active_threads": threading.active_count(),
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有统计信息。
        
        Returns:
            dict: 完整的统计信息
        """
        return {
            "requests": self.get_request_stats(),
            "cache": self.get_cache_stats(),
            "database": self.get_database_stats(),
            "system": self.get_system_stats(),
            "monitoring": {
                "enabled": self.enabled,
                "sample_rate": self.sample_rate,
                "retention": self.retention
            }
        }


# 全局性能监控实例
performance_monitor = PerformanceMetrics()


def monitor_request():
    """
    Flask请求监控装饰器工厂。
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not performance_monitor.enabled:
                return func(*args, **kwargs)
            
            # 记录开始时间
            start_time = time.time()
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 计算处理时间
                duration = time.time() - start_time
                
                # 记录请求指标
                user_id = None
                if hasattr(g, 'user_id'):
                    user_id = g.user_id
                elif 'user_id' in request.args:
                    user_id = request.args.get('user_id')
                
                performance_monitor.record_request(
                    endpoint=request.endpoint or request.path,
                    method=request.method,
                    status_code=200,  # 假设成功，实际应该从响应获取
                    duration=duration,
                    user_id=user_id
                )
                
                return result
                
            except Exception as e:
                # 记录错误请求
                duration = time.time() - start_time
                performance_monitor.record_request(
                    endpoint=request.endpoint or request.path,
                    method=request.method,
                    status_code=500,
                    duration=duration,
                    user_id=None
                )
                raise e
        
        return wrapper
    return decorator