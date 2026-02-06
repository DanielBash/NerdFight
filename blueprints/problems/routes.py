"""СКРИПТ:Пути для отображения задач пользователям"""


# -- импорт модулей
from flask import Blueprint, render_template, redirect, url_for, current_app, flash
from flask import request, g
from sqlalchemy import select, update, func, distinct
from models import Problem, validation, User, db, solved_problems
from datetime import datetime

bp = Blueprint('problems', __name__, template_folder='templates')


@bp.route('/', methods=['GET'])
def problems():
    page = request.args.get('page', 0, type=int)
    sort = request.args.get('sort', 'id')

    per_page = current_app.config['PROBLEMS_PAGINATION_ADMIN']

    # --- subquery with solver count ---
    solvers_subquery = (
        db.session.query(
            solved_problems.c.problem_id,
            db.func.count(db.distinct(solved_problems.c.user_id)).label('solvers_count')
        )
        .filter(solved_problems.c.solved_at.isnot(None))
        .group_by(solved_problems.c.problem_id)
        .subquery()
    )

    # --- base query ---
    query = (
        db.session.query(
            Problem,
            db.func.coalesce(solvers_subquery.c.solvers_count, 0).label('solvers_count')
        )
        .outerjoin(solvers_subquery, Problem.id == solvers_subquery.c.problem_id)
    )

    if sort == 'name':
        query = query.order_by(Problem.name)
    elif sort == 'solvers_count':
        query = query.order_by(db.desc('solvers_count'))
    else:
        query = query.order_by(Problem.id)

    total_items = query.count()

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

    if page < 0:
        page = 0
    if page > last_page:
        return redirect(url_for('problems.problems', page=last_page, sort=sort))

    problems = (
        query
        .limit(per_page)
        .offset(page * per_page)
        .all()
    )

    return render_template(
        'problems.html',
        problems=problems,
        current_page=page,
        current_sort=sort,
        has_next=page < last_page,
        has_prev=page > 0
    )


@bp.route('/<string:name>', methods=['GET', 'POST'])
def problem(name):
    task = Problem.query.filter_by(name=name).first()
    return render_template('problem.html', task=task)


@bp.route('/<string:name>/solvers', methods=['GET'])
def problem_solvers(name):
    pagination_size = current_app.config['USERS_PAGINATION_ADMIN']
    task = Problem.query.filter_by(name=name).first_or_404()

    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'id')

    user_query = (
        db.session.query(User, solved_problems.c.attempts_count)
        .join(solved_problems, solved_problems.c.user_id == User.id)
        .filter(
            solved_problems.c.problem_id == task.id,
            solved_problems.c.solved_at.isnot(None)
        )
    )

    if sort == 'id':
        user_query = user_query.order_by(User.id)
    elif sort == 'username':
        user_query = user_query.order_by(User.username)
    elif sort == 'attempts_count':
        user_query = user_query.order_by(
            solved_problems.c.attempts_count.asc(),
            User.id.asc()
        )
    elif sort == 'elo':
        user_query = user_query.order_by(User.elo.desc())

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
        return redirect(url_for('problems.problem_solvers', page=last_page, sort=sort,
                                task=task, name=name))

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


@bp.route('/<string:name>/solve', methods=['POST'])
@validation.require_privileges(min_privileges=0)
def problem_solve(name):
    task = Problem.query.filter_by(name=name).first_or_404()

    user_answer = request.form.get('answer', '').strip().lower()
    correct_answer = task.answer.strip().lower()

    user_id = g.user.id

    record = db.session.execute(
        db.select(solved_problems).where(
            solved_problems.c.user_id == user_id,
            solved_problems.c.problem_id == task.id
        )
    ).mappings().first()

    is_correct = user_answer == correct_answer

    if record:
        db.session.execute(
            db.update(solved_problems)
            .where(
                solved_problems.c.user_id == user_id,
                solved_problems.c.problem_id == task.id
            )
            .values(attempts_count=record["attempts_count"] + 1)
        )

        if is_correct and record["solved_at"] is None:
            db.session.execute(
                db.update(solved_problems)
                .where(
                    solved_problems.c.user_id == user_id,
                    solved_problems.c.problem_id == task.id
                )
                .values(solved_at=datetime.now(),attempts_count=record["attempts_count"] + 1)
            )
            flash("Правильный ответ!")
        elif is_correct:
            # Правильно, но уже решал ранее
            db.session.execute(
                db.update(solved_problems)
                .where(
                    solved_problems.c.user_id == user_id,
                    solved_problems.c.problem_id == task.id
                )
                .values(
                    attempts_count=record["attempts_count"]
                )
            )
            flash("Задача уже была решена ранее, попытка не засчитана")
        else:
            # Неправильный ответ
            db.session.execute(
                db.update(solved_problems)
                .where(
                    solved_problems.c.user_id == user_id,
                    solved_problems.c.problem_id == task.id
                )
                .values(
                    attempts_count=record["attempts_count"] + 1  # увеличиваем счетчик
                )
            )
            flash("Неправильный ответ, +1 попытка")

    else:
        db.session.execute(
            solved_problems.insert().values(
                user_id=user_id,
                problem_id=task.id,
                attempts_count=1,
                solved_at=datetime.now() if is_correct else None
            )
        )

        if is_correct:
            flash("Правильный ответ!")
        else:
            flash("Неправильный ответ")

    db.session.commit()
    return redirect(url_for('problems.problem', name=name))
