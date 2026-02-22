from waitress import serve
from app import create_app
from config import current_config

app = create_app()

if __name__ == '__main__':
    # Start production-ready WSGI server with Waitress
    # Nginx handles HTTPS/SSL termination, Flask serves HTTP internally
    print(f"Starting HTTP server on http://{current_config.HOST}:{current_config.PORT}")
    print("HTTPS is handled by Nginx reverse proxy")
    serve(
        app,
        host=current_config.HOST,
        port=current_config.PORT,
        threads=4
    )
