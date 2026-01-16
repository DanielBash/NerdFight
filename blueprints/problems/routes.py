"""СКРИПТ:Пути для отображения задач пользователям"""

# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template

template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('problems', __name__, template_folder=template_dir)


@bp.route('/', methods=['GET'])
def problems():
    return render_template('problems.html')


@bp.route('/<problem_id>', methods=['GET'])
def problem():
    return render_template('problem.html')
