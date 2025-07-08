import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from auth import auth_bp
from download import download_bp
from db import get_db, close_db

def create_app():
    app = Flask(__name__)
    app.secret_key = 'replace-with-your-secure-random-secret'
    app.config['UPLOAD_ROOT'] = '/root/pythonproject_remote/download/'

    #Ensure log directory exists
    log_dir = os.path.join(os.getcwd(), 'log')
    os.makedirs(log_dir, exist_ok=True)
    #End ensure

    #Logging configuration
    log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    app.logger.addHandler(console_handler)

    # File handler, one file per day
    today = datetime.now().strftime('%Y-%m-%d')
    log_path = os.path.join(log_dir, f"{today}.txt")
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_formatter)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False
    #End logging configuration

    @app.before_request
    def log_request():
        app.logger.info(f"-> {request.remote_addr} {request.method} {request.full_path}")

    @app.after_request
    def log_response(response):
        app.logger.info(f"<- {request.remote_addr} {request.method} {request.full_path} -> {response.status}")
        return response

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(download_bp)

    # Close database connection on teardown
    app.teardown_appcontext(close_db)

    # Example route to list all users
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
    app.run(host='0.0.0.0', port=5000, debug=True)