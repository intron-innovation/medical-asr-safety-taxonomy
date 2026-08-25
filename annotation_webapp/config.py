"""Configuration for ASR Annotation Web App."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
ANNOTATION_DATA_DIR = DATA_DIR / 'annotation_data'  # New: stores model JSON files

# Base directory for resolving relative audio paths like data/final_audio/foo.wav
# Defaults to the bio_ramp_asr project root (parent of annotation_webapp)
AUDIO_BASE_DIR = Path(os.environ.get('AUDIO_BASE_DIR', str(BASE_DIR.parent))).resolve()
AUDIO_STORAGE = os.environ.get('AUDIO_STORAGE', 'local').lower()
GCS_BUCKET = os.environ.get('GCS_BUCKET', '')
GCS_PREFIX = os.environ.get('GCS_PREFIX', 'final_audio').strip('/')
GCS_SIGNED_URL_TTL = int(os.environ.get('GCS_SIGNED_URL_TTL', '900'))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "annotation_tool.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Upload configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file upload
    UPLOAD_FOLDER = DATA_DIR
    
    # Annotators file
    ANNOTATORS_FILE = DATA_DIR / 'annotators.json'
    
    # Annotation data directory
    ANNOTATION_DATA_DIR = ANNOTATION_DATA_DIR

    # Base directory for serving session audio files
    AUDIO_BASE_DIR = AUDIO_BASE_DIR
    AUDIO_STORAGE = AUDIO_STORAGE
    GCS_BUCKET = GCS_BUCKET
    GCS_PREFIX = GCS_PREFIX
    GCS_SIGNED_URL_TTL = GCS_SIGNED_URL_TTL
    
    # Pagination
    ITEMS_PER_PAGE = 50


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Use PostgreSQL in production
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
