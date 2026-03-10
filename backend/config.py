import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class LocalDevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite3"
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "hospital-secret-key-dev")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "hospital-salt-dev")
    SECURITY_PASSWORD_HASH = 'argon2'
    
    # MailHog SMTP Configuration
    SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
    SMTP_USE_TLS = False
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@hospital.com")
    
    # Redis Cache Configuration
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/2")
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default
    
    # Custom cache timeouts (in seconds)
    CACHE_TIMEOUT_SHORT = 60  # 1 minute - for frequently changing data
    CACHE_TIMEOUT_MEDIUM = 300  # 5 minutes - for dashboard data
    CACHE_TIMEOUT_LONG = 3600  # 1 hour - for static data like departments


class ProductionConfig(BaseConfig):
    DEBUG = False
    
    # Production SMTP Configuration
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USE_TLS = True
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
