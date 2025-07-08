import logging
from flask import Flask, request, jsonify
from auth import auth_bp
from download import download_bp
from db import get_db, close_db

def create_app():
    app = Flask(__name__)
    app.secret_key = 'replace-with-your-secure-random-secret'
    app.config['UPLOAD_ROOT'] = '/root/pythonproject_remote/download/'

    # —— 日志配置 ——  
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    @app.before_request
    def log_request():
        app.logger.info(f"-> {request.remote_addr} {request.method} {request.full_path}")

    @app.after_request
    def log_response(response):
        app.logger.info(f"<- {request.remote_addr} {request.method} {request.full_path} -> {response.status}")
        return response
    # —— 日志配置结束 ——  

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(download_bp)

    # 在上下文结束时关闭数据库连接
    app.teardown_appcontext(close_db)

    # 示例查询所有用户
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
