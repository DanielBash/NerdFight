"""СКРИПТ: Файл запуска"""
# - импортирование модулей
from flask import Flask
from markupsafe import Markup
import markdown
from config import *
from models import db, User
from blueprints.registration.validation import hash_password
from flask import g, session


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

        from blueprints.registration.routes import inject_user, load_user

        app.context_processor(inject_user)
        app.before_request(load_user)

        app.register_blueprint(main_bp)
        app.register_blueprint(registration_bp, url_prefix='/registration')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(fight_bp, url_prefix='/fight')
        app.register_blueprint(problems_bp, url_prefix='/problems')
        app.register_blueprint(users_bp, url_prefix='/users')

        db.create_all()

        if not User.query.filter_by(username=app.config['DEFAULT_ADMIN_USERNAME']).first():
            admin_user = User(
                username=app.config['DEFAULT_ADMIN_USERNAME'],
                password_sha256=hash_password(app.config['DEFAULT_ADMIN_PASSWORD']),
                privileges=1,
                elo=app.config['DEFAULT_ELO']
            )

            db.session.add(admin_user)
            db.session.commit()

    def render_markdown(text):
        html = markdown.markdown(
            text,
            extensions=[
                "fenced_code",
                "codehilite",
                "tables",
                "nl2br",
                "sane_lists"
            ]
        )
        return Markup(html)

    app.jinja_env.filters["markdown"] = render_markdown

    return app


app = create_app(config_name=CURRENT_CONFIG_NAME)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=50000)
