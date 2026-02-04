"""СКРИПТ: Функции валидации сессий и другие помощники в регистрации"""

# -- импорт модулей
import re, hashlib
from functools import wraps

from flask import flash, g, redirect, url_for


# - проверка имени пользователя
def validate_username(username):
    if not username or len(username) < 3:
        return False, "Имя пользователя должно содержать минимум 3 символа"
    if len(username) > 32:
        return False, "Имя пользователя должно быть не длиннее 32 символов"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Имя пользователя может содержать только буквы, цифры и нижние подчёркивания"
    return True, ""


# - проверка пароля
def validate_password(password):
    if not password or len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    return True, ""


# - хеширование пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def require_privileges(min_privileges=0):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                flash('Пожалуйста, войдите в систему', 'warning')
                return redirect(url_for('registration.login'))
            if g.user.privileges < min_privileges:
                flash('Недостаточно прав доступа', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
