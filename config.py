"""Skillora application configuration."""

import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SKILLORA_SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE = os.path.join(BASE_DIR, 'instance', 'skillora.db')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    def __init__(self):
        if self.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError(
                "Production requires a secure SKILLORA_SECRET_KEY environment variable. "
                "Do not use the default development key."
            )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE = os.path.join(BASE_DIR, 'instance', 'test_skillora.db')
    WTF_CSRF_ENABLED = False
