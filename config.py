"""СКРИПТ:Настройки"""

# -- импорт модулей
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# -- базовая конфигурация
class Config:
    # настройки flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'unsecure-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # настройки модели
    MODEL_API_KEY = os.environ.get('MODEL_API_KEY', '')

    # настройки путей
    STATIC_PATH = Path('static')
    TEMPLATE_PATH = Path('templates')

    @staticmethod
    def get_openai_client():
        return OpenAI(
            api_key=Config.MODEL_API_KEY,
            base_url="https://api.deepseek.com"
        )

# -- конфигурация для разработки
class DevelopmentConfig(Config):
    DEBUG = True

# -- конфигурация для продакшена
class ProductionConfig(Config):
    DEBUG = False

CONFIGS = {
    'default': Config(),
    'development': DevelopmentConfig(),
    'production': ProductionConfig()
}

CURRENT_CONFIG_NAME = os.environ.get('FLASK_ENV', 'development')