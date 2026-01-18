"""СКРИПТ:Настройки"""

# -- импорт модулей
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import re

load_dotenv()


# -- базовая конфигурация
class Config:
    # настройки flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'unsecure-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # настройки ИИ модели
    MODEL_API_KEY = os.environ.get('MODEL_API_KEY', 'model-api-key')
    MODEL_BASE = "https://api.deepseek.com"
    MODEL_NEW_PROBLEM_PROMPT = '''Ты - копирайтер. Мастер переформулировок и любитель переделывать задачки, давая им 
новый смысл. Пользователь пришлет тебе задачку. Переделай ее, переформулируй. Положи условие задачи в тег 
<content>, а ответ в тег <answer>, вот так: <content>Сколько будет 2+2?</content><answer>2</answer>. Не бойся 
глобально переделывать задачи. Главное, оставь алгоритм решения таким же'''

    # Настройка сессий
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True if os.environ.get('FLASK_ENV') == 'production' else False
    SESSION_COOKIE_SAMESITE = 'Lax'

    # настройки путей
    STATIC_PATH = Path('static')
    TEMPLATE_PATH = Path('templates')

    # хранение сессий на сервере
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'auth:'

    # настройки elo
    DEFAULT_ELO = 1000
    DEFAULT_ELO_K = 32

    # настройки пользователей
    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'password')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = ['csv', 'json']

    # настройки админ панели
    PROBLEMS_PAGINATION_ADMIN = 20
    USERS_PAGINATION_ADMIN = 20


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
