"""СКРИПТ:Пути для отображения пользователей"""

import plotly.express as px
from flask import Blueprint, render_template, request, redirect, url_for, g
# -- импорт модулей
from flask import current_app

from models import User

template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('users', __name__, template_folder=template_dir)


@bp.route('/users', methods=['GET'])
def users():
    pagination_size = current_app.config['USERS_PAGINATION_ADMIN']

    page = request.args.get('page', 0, type=int)
    sort = request.args.get('sort', 'elo')

    if sort == 'id':
        user_query = User.query.order_by(User.id)
    elif sort == 'username':
        user_query = User.query.order_by(User.username)
    elif sort == 'elo':
        user_query = User.query.order_by(User.elo.desc())
    else:
        user_query = User.query.order_by(User.elo.desc())

    total = user_query.count()

    if total == 0:
        return render_template(
            'users.html',
            users=[],
            current_page=0,
            current_sort=sort,
            has_next=False,
            has_prev=False
        )

    last_page = (total - 1) // pagination_size

    if page > last_page:
        return redirect(url_for('users.users', page=last_page, sort=sort))

    if page < 0:
        page = 0

    user_list = (
        user_query
        .limit(pagination_size)
        .offset(page * pagination_size)
        .all()
    )

    has_next = page < last_page
    has_prev = page > 0

    return render_template(
        'users.html',
        users=user_list,
        current_page=page,
        current_sort=sort,
        has_next=has_next,
        has_prev=has_prev
    )


@bp.route('/<string:username>', methods=['GET'])
def user(username):
    users_data = User.query.filter_by(username=username).first_or_404()

    if users_data.total_matches > 0:
        wins = users_data.won_matches
        losses = users_data.total_matches - wins

        labels = ['Победы', 'Поражения']
        values = [wins, losses]
        textinfo = 'percent+label'
        hovertemplate = '%{label}: %{value} (%{percent})<extra></extra>'
        colors = ['#22b14c', '#0b5d1e']

    else:
        labels = ['Игры отсутствуют']
        values = [1]
        textinfo = 'label'
        hovertemplate = 'Пользователь ещё не играл<extra></extra>'
        colors = ['#22b14c']

    fig = px.pie(
        names=labels,
        values=values,
        hole=0.4
    )

    fig.update_traces(
        textinfo=textinfo,
        hovertemplate=hovertemplate,
        marker=dict(colors=colors)
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family='Courier New, monospace',
            size=18,
            color='#22b14c'
        ),
        margin=dict(t=20, b=0, l=0, r=0),
        showlegend=False
    )

    graph_html = fig.to_html(
        full_html=False,
        config={
            'displayModeBar': False,
            'displaylogo': False
        }
    )

    return render_template(
        'user.html',
        graph_html=graph_html,
        req_user=users_data
    )


@bp.route('/<string:username>/matches', methods=['GET'])
def user_matches(username):
    req_user = User.query.filter_by(username=username).first_or_404()

    return render_template(
        'user-matches.html',
        req_user=req_user
    )