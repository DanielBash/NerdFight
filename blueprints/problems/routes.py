"""СКРИПТ:Пути для отображения задач пользователям"""

# -- импорт модулей
from flask import Blueprint, render_template, redirect, url_for, current_app
from flask import request

from models import Problem, validation, User

bp = Blueprint('problems', __name__, template_folder='templates')


@bp.route('/', methods=['GET', ])
def problems():
    # Получаем текущую страницу из параметров запроса, по умолчанию страница 1
    page = request.args.get('page', 0, type=int)
    sort = request.args.get('sort', 'id')

    # Устанавливаем количество элементов на одной странице
    per_page = current_app.config['PROBLEMS_PAGINATION_ADMIN']

    problem_query = Problem.query
    if sort == 'name':
        problem_query = Problem.query.order_by(Problem.name)
    # Общее количество элементов
    total_items = problem_query.count()

    last_page = (total_items - 1) // per_page

    has_next = page < last_page
    has_prev = page > 0
    if total_items == 0:
        return render_template(
            'problems.html',
            problems=[],
            current_page=0,
            current_sort=sort,
            has_next=False,
            has_prev=False
        )

    last_page = (total_items - 1) // per_page

    if page > last_page:
        return redirect(url_for('problems.problems', page=last_page, sort=sort))

    if page < 0:
        page = 0

    problem_list = (
        problem_query
        .limit(per_page)
        .offset(page * per_page)
        .all()
    )

    # Общее количество страниц (округляем вверх)
    total_pages = (total_items + per_page - 1) // per_page

    # Определяем начальный и конечный индекс для текущей страницы
    has_next = page < last_page
    has_prev = page > 0

    return render_template(
        'problems.html',
        problems=problem_list,
        current_page=page,
        current_sort=sort,
        has_next=has_next,
        has_prev=has_prev
    )


@bp.route('/<string:name>', methods=['GET', 'POST'])
def problem(name):
    task = Problem.query.filter_by(name=name).first()
    return render_template('problem.html', task=task)


@bp.route('/<string:name>/solvers', methods=['GET'])
@validation.require_privileges(min_privileges=1)
def problem_solvers(name):
    pagination_size = current_app.config['USERS_PAGINATION_ADMIN']
    task = Problem.query.filter_by(name=name).first()
    User_solved = task.solvers

    page = request.args.get('page', 0, type=int)
    sort = request.args.get('sort', 'id')

    if sort == 'id':
        user_query = task.solvers.order_by(User.id)
    elif sort == 'username':
        user_query = task.solvers.order_by(User.username)
    elif sort == 'elo':
        user_query = task.solvers.order_by(User.elo)
    else:
        user_query = task.solvers

    total = user_query.count()

    if total == 0:
        return render_template(
            'problem-solvers.html',
            users=[],
            current_page=0,
            current_sort=sort,
            has_next=False,
            has_prev=False,
            task=task.name
        )

    last_page = (total - 1) // pagination_size

    if page > last_page:
        return redirect(url_for('problems.problem_solvers', page=last_page, sort=sort))

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
        'problem-solvers.html',
        users=user_list,
        current_page=page,
        current_sort=sort,
        has_next=has_next,
        has_prev=has_prev,
        task=task
    )