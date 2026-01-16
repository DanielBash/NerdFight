"""СКРИПТ:Пути для отображения пользователей"""

# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template


template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('users', __name__, template_folder=template_dir)


@bp.route('/', methods=['GET'])
def users():
    return render_template('users.html')

@bp.route('/<string:username>', methods=['GET'])
def user(username):
    return render_template('user.html')