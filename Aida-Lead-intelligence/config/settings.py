import os
from datetime import timedelta

class Config:
    """Base configuration class for multi-tenant platform"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Database settings
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'platform.db')
    
    # Session settings
    SESSION_TIMEOUT = timedelta(hours=24)  # 24 hours
    SESSION_CLEANUP_INTERVAL = timedelta(hours=1)  # Clean up expired sessions every hour
    
    # Security settings
    PASSWORD_MIN_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    
    # Lead generation settings
    MAX_LEADS_PER_REQUEST = 50
    DEFAULT_LEADS_LIMIT = 20
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # API rate limiting
    RATE_LIMIT_PER_MINUTE = 60
    
    # Encryption settings
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'default-encryption-key-change-in-production'
    
    # ERPNext default settings
    DEFAULT_ERP_TIMEOUT = 30  # seconds
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(Config.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with more secure settings for production
    SESSION_TIMEOUT = timedelta(hours=8)  # Shorter session timeout
    MAX_LOGIN_ATTEMPTS = 3  # Stricter login attempts
    
class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, DevelopmentConfig)