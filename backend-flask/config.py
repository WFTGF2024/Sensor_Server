"""
Configuration management for Sensor_Flask application.
Uses environment variables with fallback defaults for development.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration class."""
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'replace-with-your-secure-random-secret')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'zjh')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '20040624ZJH')
    DB_NAME = os.getenv('DB_NAME', 'modality')
    DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')

    # File upload settings
    UPLOAD_ROOT = os.getenv('UPLOAD_ROOT', '/root/pythonproject_remote/download/')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB default (16 * 1024 * 1024)

    # Redis settings
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'False').lower() == 'true'
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_CACHE_TTL = int(os.getenv('REDIS_CACHE_TTL', '3600'))  # 1 hour default

    # Session settings
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', '86400'))  # 24 hours in seconds

    # Monitor settings
    MONITOR_ENABLED = os.getenv('MONITOR_ENABLED', 'False').lower() == 'true'
    MONITOR_SAMPLE_RATE = float(os.getenv('MONITOR_SAMPLE_RATE', '100'))  # Sample every 100 requests
    MONITOR_METRICS_RETENTION = int(os.getenv('MONITOR_METRICS_RETENTION', '3600'))  # Retain metrics for 1 hour

    # Rate limiting settings
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '10'))  # seconds
    RATE_LIMIT_MAX_CALLS = int(os.getenv('RATE_LIMIT_MAX_CALLS', '1000'))

    # Server settings
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', '5000'))

    # Logging settings
    LOG_DIR = os.getenv('LOG_DIR', 'log')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def get_db_config(cls):
        """Get database configuration as a dictionary."""
        return {
            "host": cls.DB_HOST,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "database": cls.DB_NAME,
            "charset": cls.DB_CHARSET,
            "use_unicode": True,
            "cursorclass": None  # Will be set in db.py
        }

    @classmethod
    def get_redis_config(cls):
        """Get Redis configuration as a dictionary."""
        return {
            "host": cls.REDIS_HOST,
            "port": cls.REDIS_PORT,
            "password": cls.REDIS_PASSWORD if cls.REDIS_PASSWORD else None,
            "db": cls.REDIS_DB,
            "decode_responses": True
        }

    @classmethod
    def validate_config(cls):
        """Validate configuration and log warnings for insecure defaults."""
        warnings = []

        # Check for insecure default secret key
        if cls.SECRET_KEY == 'replace-with-your-secure-random-secret':
            warnings.append("Using default SECRET_KEY. Set FLASK_SECRET_KEY environment variable for production.")

        # Check for default database password
        if cls.DB_PASSWORD == '20040624ZJH':
            warnings.append("Using default database password. Set DB_PASSWORD environment variable for production.")

        return warnings


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    DB_NAME = os.getenv('TEST_DB_NAME', 'modality_test')
    LOG_LEVEL = 'CRITICAL'  # Suppress logs during testing


# Configuration mapping
configs = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}

# Default configuration based on environment
env = os.getenv('FLASK_ENV', 'development')
current_config = configs.get(env, DevelopmentConfig)
