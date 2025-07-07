from flask import Flask, jsonify
from auth import auth_bp  
from db import get_db, close_db 

def create_app():
    app = Flask(__name__)
    app.secret_key = 'replace-with-your-secure-random-secret'

    app.register_blueprint(auth_bp)
    app.register_blueprint(auth_bp)

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
    create_app().run(debug=True, host='0.0.0.0', port=5000)
