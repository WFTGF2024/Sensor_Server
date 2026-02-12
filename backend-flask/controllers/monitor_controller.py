"""
Monitor Controller - 监控控制器
提供性能监控、缓存统计和系统健康检查的API端点
"""
from flask import Blueprint, jsonify, request, session
from utils import CacheManager, performance_monitor
from redis_client import redis_client
from config import current_config
from errors import AuthenticationError, AuthorizationError

monitor_bp = Blueprint('monitor', __name__, url_prefix='/monitor')


@monitor_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /monitor/health
    系统健康检查
    
    Returns:
        JSON response with system health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": performance_monitor.get_system_stats().get('timestamp'),
        "components": {}
    }
    
    # 检查数据库连接
    try:
        from db import get_db
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
    
    # 检查Redis连接
    if redis_client.is_enabled():
        try:
            client = redis_client.get_client()
            if client:
                client.ping()
                health_status["components"]["redis"] = "healthy"
            else:
                health_status["status"] = "degraded"
                health_status["components"]["redis"] = "unavailable"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["components"]["redis"] = f"unhealthy: {str(e)}"
    else:
        health_status["components"]["redis"] = "disabled"
    
    return jsonify(health_status), 200


@monitor_bp.route('/stats/requests', methods=['GET'])
def get_request_stats():
    """
    GET /monitor/stats/requests
    获取请求统计信息
    
    Query Parameters:
        time_window: 时间窗口（秒），默认3600（1小时）
        
    Returns:
        JSON response with request statistics
    """
    time_window = request.args.get('time_window', 3600, type=int)
    
    try:
        stats = performance_monitor.get_request_stats(time_window)
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/stats/cache', methods=['GET'])
def get_cache_stats():
    """
    GET /monitor/stats/cache
    获取缓存统计信息
    
    Returns:
        JSON response with cache statistics
    """
    try:
        # 获取应用层缓存统计
        app_cache_stats = CacheManager.get_stats()
        
        # 获取Redis统计
        redis_stats = redis_client.get_stats()
        
        # 获取监控层缓存统计
        monitor_cache_stats = performance_monitor.get_cache_stats()
        
        return jsonify({
            "success": True,
            "data": {
                "application_cache": app_cache_stats,
                "redis": redis_stats,
                "monitoring": monitor_cache_stats
            }
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/stats/database', methods=['GET'])
def get_database_stats():
    """
    GET /monitor/stats/database
    获取数据库统计信息
    
    Returns:
        JSON response with database statistics
    """
    try:
        stats = performance_monitor.get_database_stats()
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/stats/system', methods=['GET'])
def get_system_stats():
    """
    GET /monitor/stats/system
    获取系统统计信息
    
    Returns:
        JSON response with system statistics
    """
    try:
        stats = performance_monitor.get_system_stats()
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/stats/all', methods=['GET'])
def get_all_stats():
    """
    GET /monitor/stats/all
    获取所有统计信息
    
    Returns:
        JSON response with all statistics
    """
    try:
        stats = performance_monitor.get_all_stats()
        
        # 添加缓存统计
        cache_stats = CacheManager.get_stats()
        redis_stats = redis_client.get_stats()
        
        stats["cache"] = {
            "application": cache_stats,
            "redis": redis_stats
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/config', methods=['GET'])
def get_config():
    """
    GET /monitor/config
    获取监控配置信息
    
    Returns:
        JSON response with monitoring configuration
    """
    try:
        config = {
            "monitoring": {
                "enabled": current_config.MONITOR_ENABLED,
                "sample_rate": current_config.MONITOR_SAMPLE_RATE,
                "metrics_retention": current_config.MONITOR_METRICS_RETENTION
            },
            "cache": {
                "redis_enabled": current_config.REDIS_ENABLED,
                "redis_host": current_config.REDIS_HOST,
                "redis_port": current_config.REDIS_PORT,
                "cache_ttl": current_config.REDIS_CACHE_TTL
            },
            "logging": {
                "log_level": current_config.LOG_LEVEL,
                "log_dir": current_config.LOG_DIR
            }
        }
        
        return jsonify({
            "success": True,
            "data": config
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    POST /monitor/cache/clear
    清除所有缓存
    
    Returns:
        JSON response with clear result
    """
    # 需要管理员权限
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    try:
        # 清除应用缓存
        app_cleared = CacheManager.clear_all()
        
        # 清除Redis缓存（如果启用）
        redis_cleared = 0
        if redis_client.is_enabled():
            try:
                client = redis_client.get_client()
                if client:
                    # 清除所有应用相关的键
                    patterns = ['cache:*', 'user:*', 'file:*', 'membership:*', 'monitor:*']
                    for pattern in patterns:
                        redis_cleared += redis_client.clear_pattern(pattern)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Failed to clear Redis cache: {str(e)}"
                }), 500
        
        return jsonify({
            "success": True,
            "message": f"Cache cleared successfully",
            "data": {
                "application_cache_cleared": app_cleared,
                "redis_cache_cleared": redis_cleared,
                "total_cleared": app_cleared + redis_cleared
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@monitor_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    GET /monitor/alerts
    获取系统告警信息
    
    Returns:
        JSON response with system alerts
    """
    alerts = []
    
    # 检查系统资源
    try:
        system_stats = performance_monitor.get_system_stats()
        
        # CPU使用率告警
        if system_stats.get('cpu_percent', 0) > 80:
            alerts.append({
                "level": "warning",
                "type": "high_cpu_usage",
                "message": f"CPU usage is high: {system_stats['cpu_percent']}%",
                "value": system_stats['cpu_percent']
            })
        
        # 内存使用率告警
        if system_stats.get('memory_percent', 0) > 80:
            alerts.append({
                "level": "warning",
                "type": "high_memory_usage",
                "message": f"Memory usage is high: {system_stats['memory_percent']}%",
                "value": system_stats['memory_percent']
            })
        
        # 磁盘使用率告警
        if system_stats.get('disk_usage_percent', 0) > 80:
            alerts.append({
                "level": "warning",
                "type": "high_disk_usage",
                "message": f"Disk usage is high: {system_stats['disk_usage_percent']}%",
                "value": system_stats['disk_usage_percent']
            })
        
    except Exception as e:
        alerts.append({
            "level": "error",
            "type": "system_monitor_error",
            "message": f"Failed to get system stats: {str(e)}"
        })
    
    # 检查缓存命中率
    try:
        cache_stats = performance_monitor.get_cache_stats()
        hit_rate = cache_stats.get('hit_rate', 0)
        
        if hit_rate < 50 and cache_stats.get('total_hits') + cache_stats.get('total_misses') > 100:
            alerts.append({
                "level": "info",
                "type": "low_cache_hit_rate",
                "message": f"Cache hit rate is low: {hit_rate}%",
                "value": hit_rate
            })
    except Exception as e:
        pass
    
    return jsonify({
        "success": True,
        "data": {
            "alerts": alerts,
            "count": len(alerts)
        }
    }), 200


@monitor_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    GET /monitor/metrics
    获取Prometheus格式的指标
    
    Returns:
        Prometheus format metrics
    """
    try:
        stats = performance_monitor.get_all_stats()
        system_stats = performance_monitor.get_system_stats()
        cache_stats = performance_monitor.get_cache_stats()
        
        metrics = []
        
        # 请求指标
        request_stats = stats.get('requests', {})
        metrics.append(f"http_requests_total {request_stats.get('total_requests', 0)}")
        metrics.append(f"http_request_duration_seconds_avg {request_stats.get('avg_duration', 0)}")
        metrics.append(f"http_request_duration_seconds_p95 {request_stats.get('p95_duration', 0)}")
        metrics.append(f"http_request_duration_seconds_p99 {request_stats.get('p99_duration', 0)}")
        
        # 缓存指标
        metrics.append(f"cache_hits_total {cache_stats.get('total_hits', 0)}")
        metrics.append(f"cache_misses_total {cache_stats.get('total_misses', 0)}")
        metrics.append(f"cache_hit_rate {cache_stats.get('hit_rate', 0)}")
        
        # 系统指标
        metrics.append(f"system_cpu_percent {system_stats.get('cpu_percent', 0)}")
        metrics.append(f"system_memory_percent {system_stats.get('memory_percent', 0)}")
        metrics.append(f"system_disk_usage_percent {system_stats.get('disk_usage_percent', 0)}")
        metrics.append(f"system_process_memory_mb {system_stats.get('process_memory_mb', 0)}")
        metrics.append(f"system_active_threads {system_stats.get('active_threads', 0)}")
        
        return "\n".join(metrics), 200, {
            'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
        }
        
    except Exception as e:
        return f"# Error: {str(e)}", 500, {
            'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
        }