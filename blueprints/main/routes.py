"""СКРИПТ:Пути главного блупринта приложения"""
# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template
import os


template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('main', __name__, template_folder=template_dir)


@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html', title='Nerd Fight')