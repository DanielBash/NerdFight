"""СКРИПТ:Пути для битв между пользователями"""

# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template
from models import validation

template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('fight', __name__, template_folder=template_dir)

@validation.require_privileges(min_privileges=0)
@bp.route('/', methods=['GET'])
def index():
    return render_template('fight.html')