"""СКРИПТ: Функции валидации сессий и другие помощники в регистрации"""

# -- импорт модулей
import re, hashlib


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