"""СКРИПТ:Пути для отображения пользователей"""

# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template
import sqlite3
from models import User

template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('users', __name__, template_folder=template_dir)


@bp.route('/', methods=['GET'])
def users():
    users_data = User.query.order_by(User.elo).all()
    users_data = zip(range(1, 100), users_data)
    return render_template('users.html', users_data=users_data)

@bp.route('/<string:username>', methods=['GET'])
def user(username):
    return render_template('user.html')