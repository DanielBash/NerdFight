"""СКРИПТ:Пути для отображения задач"""

# -- импорт модулей
import datetime
from flask import current_app, redirect, url_for, flash, g
from flask import Blueprint, render_template, request, jsonify, session
import os, re, hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from .validation import *
from models import db, User

bp = Blueprint('registration', __name__, template_folder=current_app.config['TEMPLATE_PATH'])


# получить пользователя
def inject_user():
    user_id = session.get('user_id')
    if user_id is None:
        user = None
    else:
        user = User.query.get(user_id)
    return dict(user=user)


def load_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


# вход
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('main.index'))
        return render_template('login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    user = User.query.filter_by(username=username).first()

    if not user or user.password_sha256 != hash_password(password):
        flash("Неверное имя пользователя или пароль", 'danger')
        return render_template('login.html', username=username)

    session['user_id'] = user.id

    flash(f"Добро пожаловать, {user.username}!", 'success')
    return redirect(url_for('main.index'))


# регистрация
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('main.index'))
        return render_template('register.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    password_confirm = request.form.get('password_confirm', '')

    is_valid, error = validate_username(username)
    if not is_valid:
        flash(error, 'danger')
        return render_template('register.html')

    is_valid, error = validate_password(password)
    if not is_valid:
        flash(error, 'danger')
        return render_template('register.html')

    if password != password_confirm:
        flash("Пароли не совпадают", 'danger')
        return render_template('register.html')

    if User.query.filter_by(username=username).first():
        flash("Пользователь с таким именем уже существует", 'danger')
        return render_template('register.html')

    try:
        new_user = User(
            username=username,
            password_sha256=hash_password(password),
            privileges=0,
            elo=current_app.config['DEFAULT_ELO']
        )

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        flash("Регистрация успешна! Добро пожаловать!", 'success')
        return redirect(url_for('main.index'))

    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при регистрации: {str(e)}", 'danger')
        return render_template('register.html')


@bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('main.index'))
