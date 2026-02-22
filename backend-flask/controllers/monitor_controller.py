"""
Monitor Controller - 监控控制器
提供性能监控、缓存统计和系统健康检查的API端点
"""
from flask import Blueprint, jsonify, request, session, current_app
from utils import CacheManager, performance_monitor
from redis_client import redis_client
from config import current_config
from errors import (
    AuthenticationError, AuthorizationError, ServerError, 
    ValidationError, safe_int
)

monitor_bp = Blueprint('monitor', __name__, url_prefix='/monitor')


def get_current_user_id():
    """获取当前登录用户的ID"""
    if 'user_id' not in session:
        raise AuthenticationError("请先登录")
    return session['user_id']


def admin_required():
    """检查管理员权限"""
    if 'user_id' not in session:
        raise AuthenticationError("请先登录")
    if not session.get('is_admin', False):
        raise AuthorizationError("需要管理员权限")
    return session['user_id']


@monitor_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /monitor/health
    系统健康检查
    
    Returns:
        JSON response with system health status
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": None,
            "components": {}
        }
        
        try:
            system_stats = performance_monitor.get_system_stats()
            health_status["timestamp"] = system_stats.get('timestamp')
        except Exception as e:
            current_app.logger.warning(f"获取系统时间失败: {str(e)}")
        
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
            current_app.logger.error(f"数据库健康检查失败: {str(e)}")
        
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
                current_app.logger.warning(f"Redis健康检查失败: {str(e)}")
        else:
            health_status["components"]["redis"] = "disabled"
        
        # 检查上传目录
        try:
            import os
            upload_root = current_config.UPLOAD_ROOT
            if os.path.exists(upload_root) and os.access(upload_root, os.W_OK):
                health_status["components"]["upload_directory"] = "healthy"
            else:
                health_status["status"] = "degraded"
                health_status["components"]["upload_directory"] = "unhealthy: directory not accessible"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["components"]["upload_directory"] = f"unhealthy: {str(e)}"
        
        return jsonify(health_status), 200
        
    except Exception as e:
        current_app.logger.error(f"健康检查接口异常: {str(e)}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@monitor_bp.route('/stats/requests', methods=['GET'])
def get_request_stats():
    """
    GET /monitor/stats/requests
    获取请求统计信息
    
    Query Parameters:
        time_window: 时间窗口（秒），默认3600（1小时）
        
    Returns:
        JSON response with request statistics
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        time_window = safe_int(request.args.get('time_window', 3600), 'time_window', default=3600, min_val=1, max_val=86400)
        
        try:
            stats = performance_monitor.get_request_stats(time_window)
            return jsonify({
                "success": True,
                "data": stats
            }), 200
        except Exception as e:
            current_app.logger.error(f"获取请求统计失败: {str(e)}", exc_info=True)
            raise ServerError("获取请求统计失败")
            
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"请求统计接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取请求统计时发生错误")


@monitor_bp.route('/stats/cache', methods=['GET'])
def get_cache_stats():
    """
    GET /monitor/stats/cache
    获取缓存统计信息
    
    Returns:
        JSON response with cache statistics
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
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
            current_app.logger.error(f"获取缓存统计失败: {str(e)}", exc_info=True)
            raise ServerError("获取缓存统计失败")
            
    except Exception as e:
        current_app.logger.error(f"缓存统计接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取缓存统计时发生错误")


@monitor_bp.route('/stats/database', methods=['GET'])
def get_database_stats():
    """
    GET /monitor/stats/database
    获取数据库统计信息
    
    Returns:
        JSON response with database statistics
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        try:
            stats = performance_monitor.get_database_stats()
            return jsonify({
                "success": True,
                "data": stats
            }), 200
        except Exception as e:
            current_app.logger.error(f"获取数据库统计失败: {str(e)}", exc_info=True)
            raise ServerError("获取数据库统计失败")
            
    except Exception as e:
        current_app.logger.error(f"数据库统计接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取数据库统计时发生错误")


@monitor_bp.route('/stats/system', methods=['GET'])
def get_system_stats():
    """
    GET /monitor/stats/system
    获取系统统计信息
    
    Returns:
        JSON response with system statistics
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        try:
            stats = performance_monitor.get_system_stats()
            return jsonify({
                "success": True,
                "data": stats
            }), 200
        except Exception as e:
            current_app.logger.error(f"获取系统统计失败: {str(e)}", exc_info=True)
            raise ServerError("获取系统统计失败")
            
    except Exception as e:
        current_app.logger.error(f"系统统计接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取系统统计时发生错误")


@monitor_bp.route('/stats/all', methods=['GET'])
def get_all_stats():
    """
    GET /monitor/stats/all
    获取所有统计信息
    
    Returns:
        JSON response with all statistics
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
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
            current_app.logger.error(f"获取所有统计失败: {str(e)}", exc_info=True)
            raise ServerError("获取所有统计失败")
            
    except Exception as e:
        current_app.logger.error(f"所有统计接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取所有统计时发生错误")


@monitor_bp.route('/config', methods=['GET'])
def get_config():
    """
    GET /monitor/config
    获取监控配置信息
    
    Returns:
        JSON response with monitoring configuration
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
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
            current_app.logger.error(f"获取监控配置失败: {str(e)}", exc_info=True)
            raise ServerError("获取监控配置失败")
            
    except Exception as e:
        current_app.logger.error(f"监控配置接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取监控配置时发生错误")


@monitor_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    POST /monitor/cache/clear
    清除所有缓存（需要管理员权限）
    
    Returns:
        JSON response with clear result
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        500: 服务器内部错误
    """
    try:
        admin_required()
        
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
                    current_app.logger.warning(f"清除Redis缓存部分失败: {str(e)}")
            
            current_app.logger.info(f"缓存清除成功: app_cleared={app_cleared}, redis_cleared={redis_cleared}")
            
            return jsonify({
                "success": True,
                "message": "缓存清除成功",
                "data": {
                    "application_cache_cleared": app_cleared,
                    "redis_cache_cleared": redis_cleared,
                    "total_cleared": app_cleared + redis_cleared
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"清除缓存失败: {str(e)}", exc_info=True)
            raise ServerError("清除缓存失败")
            
    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except Exception as e:
        current_app.logger.error(f"清除缓存接口异常: {str(e)}", exc_info=True)
        raise ServerError("清除缓存时发生错误")


@monitor_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    GET /monitor/alerts
    获取系统告警信息
    
    Returns:
        JSON response with system alerts
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        alerts = []
        
        # 检查系统资源
        try:
            system_stats = performance_monitor.get_system_stats()
            
            # CPU使用率告警
            cpu_percent = system_stats.get('cpu_percent', 0)
            if cpu_percent > 90:
                alerts.append({
                    "level": "critical",
                    "type": "high_cpu_usage",
                    "message": f"CPU使用率过高: {cpu_percent}%",
                    "value": cpu_percent
                })
            elif cpu_percent > 80:
                alerts.append({
                    "level": "warning",
                    "type": "high_cpu_usage",
                    "message": f"CPU使用率较高: {cpu_percent}%",
                    "value": cpu_percent
                })
            
            # 内存使用率告警
            memory_percent = system_stats.get('memory_percent', 0)
            if memory_percent > 90:
                alerts.append({
                    "level": "critical",
                    "type": "high_memory_usage",
                    "message": f"内存使用率过高: {memory_percent}%",
                    "value": memory_percent
                })
            elif memory_percent > 80:
                alerts.append({
                    "level": "warning",
                    "type": "high_memory_usage",
                    "message": f"内存使用率较高: {memory_percent}%",
                    "value": memory_percent
                })
            
            # 磁盘使用率告警
            disk_usage_percent = system_stats.get('disk_usage_percent', 0)
            if disk_usage_percent > 90:
                alerts.append({
                    "level": "critical",
                    "type": "high_disk_usage",
                    "message": f"磁盘使用率过高: {disk_usage_percent}%",
                    "value": disk_usage_percent
                })
            elif disk_usage_percent > 80:
                alerts.append({
                    "level": "warning",
                    "type": "high_disk_usage",
                    "message": f"磁盘使用率较高: {disk_usage_percent}%",
                    "value": disk_usage_percent
                })
            
        except Exception as e:
            alerts.append({
                "level": "error",
                "type": "system_monitor_error",
                "message": f"获取系统统计失败: {str(e)}"
            })
        
        # 检查缓存命中率
        try:
            cache_stats = performance_monitor.get_cache_stats()
            hit_rate = cache_stats.get('hit_rate', 0)
            total_requests = cache_stats.get('total_hits', 0) + cache_stats.get('total_misses', 0)
            
            if total_requests > 100 and hit_rate < 50:
                alerts.append({
                    "level": "info",
                    "type": "low_cache_hit_rate",
                    "message": f"缓存命中率较低: {hit_rate}%",
                    "value": hit_rate
                })
        except Exception:
            pass
        
        # 检查数据库连接
        try:
            from db import get_db
            db = get_db()
            with db.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception as e:
            alerts.append({
                "level": "critical",
                "type": "database_connection_error",
                "message": f"数据库连接异常: {str(e)}"
            })
        
        return jsonify({
            "success": True,
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "critical_count": len([a for a in alerts if a.get('level') == 'critical']),
                "warning_count": len([a for a in alerts if a.get('level') == 'warning'])
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"告警信息接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取告警信息时发生错误")


@monitor_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    GET /monitor/metrics
    获取Prometheus格式的指标
    
    Returns:
        Prometheus format metrics
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
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
            current_app.logger.error(f"获取Prometheus指标失败: {str(e)}", exc_info=True)
            return f"# Error: {str(e)}", 500, {
                'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
            }
            
    except Exception as e:
        current_app.logger.error(f"Prometheus指标接口异常: {str(e)}", exc_info=True)
        return f"# Error: {str(e)}", 500, {
            'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
        }


@monitor_bp.route('/logs', methods=['GET'])
def get_recent_logs():
    """
    GET /monitor/logs
    获取最近的日志（需要管理员权限）
    
    Query Parameters:
        lines: 日志行数（默认100，最大1000）
        level: 日志级别过滤（可选）
    
    Returns:
        JSON response with recent logs
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        500: 服务器内部错误
    """
    try:
        admin_required()
        
        lines = safe_int(request.args.get('lines', 100), 'lines', default=100, min_val=1, max_val=1000)
        level = request.args.get('level', '').upper()
        
        try:
            import os
            from datetime import datetime
            
            log_dir = current_config.LOG_DIR
            if not os.path.isabs(log_dir):
                log_dir = os.path.join(os.getcwd(), log_dir)
            
            today = datetime.now().strftime('%Y-%m-%d')
            log_path = os.path.join(log_dir, f"{today}.txt")
            
            if not os.path.exists(log_path):
                return jsonify({
                    "success": True,
                    "logs": [],
                    "message": "今日暂无日志"
                }), 200
            
            # 读取日志文件
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
            
            # 过滤日志级别
            if level:
                all_lines = [line for line in all_lines if f' {level} ' in line]
            
            # 获取最后N行
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            return jsonify({
                "success": True,
                "logs": [line.strip() for line in recent_lines],
                "total_lines": len(all_lines),
                "returned_lines": len(recent_lines)
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取日志失败: {str(e)}", exc_info=True)
            raise ServerError("获取日志失败")
            
    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"日志接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取日志时发生错误")
