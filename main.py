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
        from blueprints.registration.routes import bp as registration_bp
        from blueprints.admin.routes import bp as admin_bp
        from blueprints.fight.routes import bp as fight_bp
        from blueprints.problems.routes import bp as problems_bp
        from blueprints.users.routes import bp as users_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(registration_bp, url_prefix='/registration')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(fight_bp, url_prefix='/fight')
        app.register_blueprint(problems_bp, url_prefix='/problems')
        app.register_blueprint(users_bp, url_prefix='/users')

        db.create_all()
        app.config['DATABASE_INSTANCE'] = db

    return app


app = create_app(config_name=CURRENT_CONFIG_NAME)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=50000)