"""СКРИПТ:Пути для отображения пользователей"""

# -- импорт модулей
import datetime
from flask import current_app
from flask import Blueprint, render_template
import sqlite3
from models import User
import plotly.express as px
import numpy as np
import pandas as pd
template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('users', __name__, template_folder=template_dir)


@bp.route('/', methods=['GET'])
def users():
    # получение рейтинга пользователей
    users_data = User.query.order_by(User.elo).all()
    return render_template('users.html', users_data=users_data)

@bp.route('/<string:username>', methods=['GET'])
def user(username):
    ## я пидо
    users_data = User.query.filter_by(username=username).first()
    ## заполнение данных для диаграммы
    if users_data.total_matches != 0:
        data = {'Object':['Wins', 'Losses'], 'Count': [users_data.won_matches, users_data.total_matches - users_data.won_matches]}
    else:
        data = {'Object':['You have not games yet'], 'Count': [1]}
    fig = px.pie(data, values='Count', names='Object')

    ## настройка вида диаграммы
    fig.update_layout(
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',

        font=dict(
            family='Courier New, monospace',
            size=18,
            color='#22b14c',
        ),
        margin = dict(t=20, b=0, l=0, r=0),
        showlegend = False,
    )

    fig.update_traces(
        marker=dict(colors=['#22b14c', '#00ff00']),
        hole = 0.4,
        textinfo='percent+label',
    )
    ## конец инизиализации
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cnd')
    return render_template('user.html', user=users_data, graph_html=graph_html)