import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
from controllers.auth_controller import auth_bp
from controllers.file_controller import download_bp
from controllers.membership_controller import membership_bp
from controllers.user_controller import list_users
from controllers.web_controller import web_bp
from controllers.monitor_controller import monitor_bp
from controllers.admin_controller import admin_bp
from db import get_db, close_db
from redis_client import get_redis, close_redis
from config import current_config
from errors import register_error_handlers
from utils.monitor import performance_monitor

# Rate limit globals
_call_count = 0
_window_start = time.time()

def create_app():
    global _call_count, _window_start

    app = Flask(__name__)
    app.secret_key = current_config.SECRET_KEY
    app.config['UPLOAD_ROOT'] = current_config.UPLOAD_ROOT
    app.config['MAX_CONTENT_LENGTH'] = current_config.MAX_CONTENT_LENGTH

    # Session 配置
    app.config['SESSION_COOKIE_HTTPONLY'] = current_config.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = current_config.SESSION_COOKIE_SAMESITE
    app.config['PERMANENT_SESSION_LIFETIME'] = current_config.PERMANENT_SESSION_LIFETIME

    # 启用CORS支持 - 支持前端和安卓客户端 (HTTP + HTTPS)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://10.8.0.24:5173",
                "http://120.79.25.184:5000",
                "http://120.79.25.184",
                "https://localhost:5173",
                "https://127.0.0.1:5173",
                "https://10.8.0.24:5173",
                "https://120.79.25.184:5000",
                "https://120.79.25.184"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # Validate configuration and log warnings
    warnings = current_config.validate_config()
    for warning in warnings:
        app.logger.warning(f"Configuration warning: {warning}")

    # Ensure log directory exists
    log_dir = current_config.LOG_DIR if os.path.isabs(current_config.LOG_DIR) else os.path.join(os.getcwd(), current_config.LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)

    # Ensure upload directory exists
    upload_root = current_config.UPLOAD_ROOT if os.path.isabs(current_config.UPLOAD_ROOT) else os.path.join(os.getcwd(), current_config.UPLOAD_ROOT)
    os.makedirs(upload_root, exist_ok=True)
    app.logger.info(f"上传目录已创建: {upload_root}")

    # Logging configuration
    log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

    # Set log level from config
    log_level = getattr(logging, current_config.LOG_LEVEL.upper(), logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_formatter)
    app.logger.addHandler(console_handler)

    today = datetime.now().strftime('%Y-%m-%d')
    log_path = os.path.join(log_dir, f"{today}.txt")
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_formatter)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(log_level)
    app.logger.propagate = False

    @app.before_request
    def rate_limit_and_log_request():
        global _call_count, _window_start

        now = time.time()
        if now - _window_start <= current_config.RATE_LIMIT_WINDOW:
            _call_count += 1
        else:
            _window_start = now
            _call_count = 1

        if _call_count > current_config.RATE_LIMIT_MAX_CALLS:
            app.logger.error(f"Rate limit exceeded: {_call_count} calls in {current_config.RATE_LIMIT_WINDOW}s. Exiting.")
            os._exit(1)

        app.logger.info(f"-> {request.remote_addr} {request.method} {request.full_path}")

    @app.after_request
    def log_response(response):
        app.logger.info(f"<- {request.remote_addr} {request.method} {request.full_path} -> {response.status}")

        # 添加CORS头 - 支持前端和安卓客户端 (HTTP + HTTPS)
        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin', 'http://localhost:5173')
            allowed_origins = [
                'http://localhost:5173',
                'http://127.0.0.1:5173',
                'http://10.8.0.24:5173',
                'http://120.79.25.184:5000',
                'http://120.79.25.184',
                'https://localhost:5173',
                'https://127.0.0.1:5173',
                'https://10.8.0.24:5173',
                'https://120.79.25.184:5000',
                'https://120.79.25.184'
            ]
            if origin in allowed_origins:
                response.headers.add('Access-Control-Allow-Origin', origin)
            else:
                # 如果请求源不在允许列表中，允许所有源以支持安卓客户端
                response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

        return response

    # 处理OPTIONS预检请求 - 支持前端和安卓客户端 (HTTP + HTTPS)
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin', 'http://localhost:5173')
        allowed_origins = [
            'http://localhost:5173',
            'http://127.0.0.1:5173',
            'http://10.8.0.24:5173',
            'http://120.79.25.184:5000',
            'http://120.79.25.184',
            'https://localhost:5173',
            'https://127.0.0.1:5173',
            'https://10.8.0.24:5173',
            'https://120.79.25.184:5000',
            'https://120.79.25.184'
        ]
        if origin in allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            # 如果请求源不在允许列表中，允许所有源以支持安卓客户端
            response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    # API blueprints with /api prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(download_bp, url_prefix='/api/download')
    app.register_blueprint(membership_bp, url_prefix='/api/membership')
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # Web blueprint without /api prefix (for HTML pages)
    app.register_blueprint(web_bp)

    # Close database connection on teardown
    app.teardown_appcontext(close_db)

    # Close Redis connection on teardown
    app.teardown_appcontext(close_redis)

    # Add request monitoring middleware
    @app.before_request
    def start_request_timer():
        if performance_monitor.enabled:
            g.start_time = time.time()

    @app.after_request
    def record_request_metrics(response):
        if performance_monitor.enabled and hasattr(g, 'start_time'):
            duration = time.time() - g.start_time

            # 获取用户ID
            user_id = None
            if 'user_id' in session:
                user_id = session['user_id']

            # 记录请求指标
            performance_monitor.record_request(
                endpoint=request.endpoint or request.path,
                method=request.method,
                status_code=response.status_code,
                duration=duration,
                user_id=user_id
            )

        return response

    # Register user routes
    app.route('/users')(list_users)

    return app

if __name__ == '__main__':
    # Enable debug mode only for local development; use a WSGI server (e.g., Waitress) in production
    app = create_app()
    app.run(
        host=current_config.HOST,
        port=current_config.PORT,
        debug=current_config.DEBUG
    )
