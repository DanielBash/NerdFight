"""ФАЙЛ:Общий контекст тестов"""

# -- импорт модулей
import pytest, sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import main


# - приложение
@pytest.fixture()
def app():
    app = main.app
    app.config.update({"TESTING": True})
    yield app

# - клиент приложения
@pytest.fixture()
def client(app):
    return app.test_client()