import os

class Config:
 SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
 SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///movies.db')
 SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
 TESTING = True
 WTF_CSRF_ENABLED = False

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test_secret"
