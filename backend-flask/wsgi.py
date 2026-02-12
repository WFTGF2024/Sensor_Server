from waitress import serve
from app import create_app
from config import current_config

app = create_app()

if __name__ == '__main__':
    # Start production-ready WSGI server with Waitress
    serve(
        app,
        host=current_config.HOST,
        port=current_config.PORT,
        threads=4
    )
