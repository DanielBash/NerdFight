"""СКРИПТ:Пути для отображения задач"""

# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template, request, jsonify, session
import os, re, hashlib
from werkzeug.security import generate_password_hash, check_password_hash

template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('registration', __name__, template_folder=template_dir)


@bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@bp.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@bp.route('/logout', methods=['GET'])
def logout():
    return render_template('logout.html')