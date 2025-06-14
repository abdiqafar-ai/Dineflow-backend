import os

class Config:
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    """Base configuration class with common settings"""
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/avatars")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Email configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587)) if os.getenv("SMTP_PORT") else 587
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "notifications@example.com")
    
    # Database configuration
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        uri = os.getenv("DATABASE_URL")
        if uri and uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        return uri or "sqlite:///app.db"

class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    # Allow insecure transport for OAuth in development
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    SESSION_COOKIE_DOMAIN = None
    SERVER_NAME = '127.0.0.1:5000'

class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    # Ensure secure cookies in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_DOMAIN = '.yourdomain.com'