"""СКРИПТ: Файл запуска"""
# - импортирование модулей
from flask import Flask
from config import *
from models import db


# - инициализация приложения
def create_app(config_name='default') -> Flask:
    app = Flask(__name__)

    config_class = CONFIGS.get(config_name)
    app.config.from_object(config_class)

    db.init_app(app)

    with app.app_context():
        from blueprints.main.routes import bp as main_bp

        app.register_blueprint(main_bp)

        db.create_all()

    return app


app = create_app(config_name=CURRENT_CONFIG_NAME)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)