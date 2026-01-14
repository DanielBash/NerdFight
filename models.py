"""СКРИПТ:Инициализация СУБД"""
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


# - таблица пользователя
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    password_sha256 = db.Column(db.String(256), nullable=False)

    username = db.Column(db.String(32), nullable=False)
    privileges = db.Column(db.Integer, default=0)


# - задачи
class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)