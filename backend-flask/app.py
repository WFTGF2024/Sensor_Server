import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify
from auth import auth_bp
from download import download_bp
from db import get_db, close_db
from config import current_config
from errors import register_error_handlers

# Rate limit globals
_call_count = 0
_window_start = time.time()

def create_app():
    global _call_count, _window_start

    app = Flask(__name__)
    app.secret_key = current_config.SECRET_KEY
    app.config['UPLOAD_ROOT'] = current_config.UPLOAD_ROOT
    app.config['MAX_CONTENT_LENGTH'] = current_config.MAX_CONTENT_LENGTH

    # Validate configuration and log warnings
    warnings = current_config.validate_config()
    for warning in warnings:
        app.logger.warning(f"Configuration warning: {warning}")

    # Ensure log directory exists
    log_dir = os.path.join(os.getcwd(), current_config.LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)

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
        return response

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(download_bp)

    # Close database connection on teardown
    app.teardown_appcontext(close_db)

    @app.route('/users')
    def list_users():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, email, phone, point, qq, wechat FROM users"
            )
            users = cursor.fetchall()
        return jsonify(users)

    return app

if __name__ == '__main__':
    # Enable debug mode only for local development; use a WSGI server (e.g., Waitress) in production
    app = create_app()
    app.run(
        host=current_config.HOST,
        port=current_config.PORT,
        debug=current_config.DEBUG
    )
