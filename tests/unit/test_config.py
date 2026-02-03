"""
Unit tests for configuration management.
"""

import os
import sys
import pytest
from unittest.mock import patch, mock_open

# Remove config from imported modules to force reload
if 'config' in sys.modules:
    del sys.modules['config']

def test_config_defaults():
    """Test that Config class has expected default values."""
    # Clear environment variables that might interfere
    env_backup = {}
    env_keys = ['FLASK_SECRET_KEY', 'FLASK_DEBUG', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 
                'DB_NAME', 'DB_CHARSET', 'UPLOAD_ROOT', 'MAX_CONTENT_LENGTH', 'RATE_LIMIT_WINDOW',
                'RATE_LIMIT_MAX_CALLS', 'FLASK_HOST', 'FLASK_PORT', 'LOG_DIR', 'LOG_LEVEL']
    for key in env_keys:
        if key in os.environ:
            env_backup[key] = os.environ[key]
            del os.environ[key]
    
    try:
        # Force reload config module
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        
        # Check default values
        assert config.SECRET_KEY == 'replace-with-your-secure-random-secret'
        assert config.DEBUG is False
        assert config.DB_HOST == 'localhost'
        assert config.DB_USER == 'zjh'
        assert config.DB_PASSWORD == '20040624ZJH'
        assert config.DB_NAME == 'modality'
        assert config.DB_CHARSET == 'utf8mb4'
        assert config.UPLOAD_ROOT == '/root/pythonproject_remote/download/'
        assert config.MAX_CONTENT_LENGTH == 16777216  # 16MB (16 * 1024 * 1024)
        assert config.RATE_LIMIT_WINDOW == 10
        assert config.RATE_LIMIT_MAX_CALLS == 1000
        assert config.HOST == '0.0.0.0'
        assert config.PORT == 5000
        assert config.LOG_DIR == 'log'
        assert config.LOG_LEVEL == 'INFO'
    finally:
        # Restore environment variables
        os.environ.update(env_backup)
        if 'config' in sys.modules:
            del sys.modules['config']

def test_config_get_db_config():
    """Test get_db_config method."""
    # Clear environment variables
    env_backup = {}
    env_keys = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_CHARSET']
    for key in env_keys:
        if key in os.environ:
            env_backup[key] = os.environ[key]
            del os.environ[key]
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        db_config = config.get_db_config()
        
        expected_keys = ["host", "user", "password", "database", "charset", "use_unicode", "cursorclass"]
        for key in expected_keys:
            assert key in db_config
        
        assert db_config["host"] == config.DB_HOST
        assert db_config["user"] == config.DB_USER
        assert db_config["password"] == config.DB_PASSWORD
        assert db_config["database"] == config.DB_NAME
        assert db_config["charset"] == config.DB_CHARSET
        assert db_config["use_unicode"] is True
        assert db_config["cursorclass"] is None  # Set in get_db_config method
    finally:
        os.environ.update(env_backup)
        if 'config' in sys.modules:
            del sys.modules['config']

def test_config_validate_config():
    """Test validate_config method."""
    env_backup = {}
    env_keys = ['FLASK_SECRET_KEY', 'DB_PASSWORD']
    for key in env_keys:
        if key in os.environ:
            env_backup[key] = os.environ[key]
            del os.environ[key]
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        warnings = config.validate_config()
        
        # Should have warnings for insecure defaults
        assert len(warnings) >= 2
        assert any("SECRET_KEY" in warning for warning in warnings)
        assert any("database password" in warning for warning in warnings)
    finally:
        os.environ.update(env_backup)
        if 'config' in sys.modules:
            del sys.modules['config']

def test_config_validate_config_custom():
    """Test validate_config with custom secure values."""
    env_backup = {}
    env_values = {
        'FLASK_SECRET_KEY': 'secure-random-key',
        'DB_PASSWORD': 'secure-password'
    }
    for key, value in env_values.items():
        if key in os.environ:
            env_backup[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        warnings = config.validate_config()
        
        # Should have no warnings for secure values
        assert len(warnings) == 0
    finally:
        # Restore environment
        for key in env_values:
            if key in env_backup:
                os.environ[key] = env_backup[key]
            else:
                del os.environ[key]
        if 'config' in sys.modules:
            del sys.modules['config']

def test_development_config():
    """Test DevelopmentConfig settings."""
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import DevelopmentConfig
    
    config = DevelopmentConfig()
    
    assert config.DEBUG is True
    assert config.LOG_LEVEL == 'DEBUG'

def test_production_config():
    """Test ProductionConfig settings."""
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import ProductionConfig
    
    config = ProductionConfig()
    
    assert config.DEBUG is False
    assert config.LOG_LEVEL == 'WARNING'

def test_testing_config():
    """Test TestingConfig settings."""
    with patch.dict(os.environ, {'TEST_DB_NAME': 'test_db'}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import TestingConfig
        
        config = TestingConfig()
        
        assert config.DEBUG is True
        assert config.TESTING is True
        assert config.DB_NAME == 'test_db'
        assert config.LOG_LEVEL == 'CRITICAL'

def test_testing_config_default():
    """Test TestingConfig with default test database name."""
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import TestingConfig
    
    config = TestingConfig()
    assert config.DB_NAME == 'modality_test'

def test_config_env_variables():
    """Test that environment variables override defaults."""
    env_backup = {}
    env_values = {
        'FLASK_SECRET_KEY': 'custom-secret',
        'DB_HOST': 'custom-host',
        'DB_USER': 'custom-user',
        'DB_PASSWORD': 'custom-password',
        'DB_NAME': 'custom-db',
        'FLASK_DEBUG': 'true',
        'FLASK_HOST': '127.0.0.1',
        'FLASK_PORT': '8080',
        'LOG_LEVEL': 'DEBUG'
    }
    for key, value in env_values.items():
        if key in os.environ:
            env_backup[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        
        assert config.SECRET_KEY == 'custom-secret'
        assert config.DB_HOST == 'custom-host'
        assert config.DB_USER == 'custom-user'
        assert config.DB_PASSWORD == 'custom-password'
        assert config.DB_NAME == 'custom-db'
        assert config.DEBUG is True
        assert config.HOST == '127.0.0.1'
        assert config.PORT == 8080
        assert config.LOG_LEVEL == 'DEBUG'
    finally:
        for key in env_values:
            if key in env_backup:
                os.environ[key] = env_backup[key]
            else:
                del os.environ[key]
        if 'config' in sys.modules:
            del sys.modules['config']

def test_config_env_variable_parsing():
    """Test parsing of environment variables."""
    env_backup = {}
    env_values = {
        'FLASK_DEBUG': 'false',
        'FLASK_PORT': '9000',
        'RATE_LIMIT_WINDOW': '30',
        'RATE_LIMIT_MAX_CALLS': '500',
        'MAX_CONTENT_LENGTH': '10485760'  # 10MB
    }
    for key, value in env_values.items():
        if key in os.environ:
            env_backup[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        
        assert config.DEBUG is False
        assert config.PORT == 9000
        assert config.RATE_LIMIT_WINDOW == 30
        assert config.RATE_LIMIT_MAX_CALLS == 500
        assert config.MAX_CONTENT_LENGTH == 10485760
    finally:
        for key in env_values:
            if key in env_backup:
                os.environ[key] = env_backup[key]
            else:
                del os.environ[key]
        if 'config' in sys.modules:
            del sys.modules['config']

def test_config_env_variable_invalid():
    """Test handling of invalid environment variables."""
    env_backup = {}
    env_values = {
        'FLASK_PORT': 'not-a-number',
        'FLASK_DEBUG': 'not-a-boolean'
    }
    for key, value in env_values.items():
        if key in os.environ:
            env_backup[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        # Should raise ValueError for invalid port
        if 'config' in sys.modules:
            del sys.modules['config']
        
        with pytest.raises(ValueError):
            from config import Config
        
    finally:
        for key in env_values:
            if key in env_backup:
                os.environ[key] = env_backup[key]
            else:
                if key in os.environ:
                    del os.environ[key]
        if 'config' in sys.modules:
            del sys.modules['config']

def test_current_config_development():
    """Test current_config for development environment."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development'}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import current_config, DevelopmentConfig
        
        # current_config is a class, not an instance
        assert current_config == DevelopmentConfig
        assert current_config.DEBUG is True

def test_current_config_production():
    """Test current_config for production environment."""
    with patch.dict(os.environ, {'FLASK_ENV': 'production'}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import current_config, ProductionConfig
        
        # current_config is a class, not an instance
        assert current_config == ProductionConfig
        assert current_config.DEBUG is False

def test_current_config_testing():
    """Test current_config for testing environment."""
    with patch.dict(os.environ, {'FLASK_ENV': 'testing'}):
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import current_config, TestingConfig
        
        # current_config is a class, not an instance
        assert current_config == TestingConfig
        assert current_config.TESTING is True

def test_current_config_default():
    """Test current_config default (development)."""
    # Remove FLASK_ENV if it exists
    if 'FLASK_ENV' in os.environ:
        env_backup = os.environ['FLASK_ENV']
        del os.environ['FLASK_ENV']
    else:
        env_backup = None
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import current_config, DevelopmentConfig
        
        # current_config is a class, not an instance
        assert current_config == DevelopmentConfig
    finally:
        if env_backup:
            os.environ['FLASK_ENV'] = env_backup
        if 'config' in sys.modules:
            del sys.modules['config']

def test_configs_mapping():
    """Test configs mapping contains all expected configurations."""
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import configs, DevelopmentConfig, ProductionConfig, TestingConfig
    
    expected_keys = ['development', 'production', 'testing']
    for key in expected_keys:
        assert key in configs
    
    assert configs['development'] == DevelopmentConfig
    assert configs['production'] == ProductionConfig
    assert configs['testing'] == TestingConfig

def test_config_environment_variable_case_sensitivity():
    """Test that environment variable names are case-sensitive."""
    env_backup = {}
    env_values = {
        'flask_secret_key': 'lowercase-wont-work',
        'FLASK_SECRET_KEY': 'uppercase-works'
    }
    for key, value in env_values.items():
        if key in os.environ:
            env_backup[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import Config
        
        config = Config()
        
        # Should use uppercase version
        assert config.SECRET_KEY == 'uppercase-works'
        assert config.SECRET_KEY != 'lowercase-wont-work'
    finally:
        for key in env_values:
            if key in env_backup:
                os.environ[key] = env_backup[key]
            else:
                del os.environ[key]
        if 'config' in sys.modules:
            del sys.modules['config']