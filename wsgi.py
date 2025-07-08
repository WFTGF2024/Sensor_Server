from waitress import serve
from app import create_app

app = create_app()

if __name__ == '__main__':
    # 使用 Waitress 生产就绪的 WSGI 服务器启动
    serve(app, host='0.0.0.0', port=5000, threads=4)
