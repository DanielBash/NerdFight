"""СКРИПТ:Пути админ-панели"""

# -- импорт модулей
import random
import time
from threading import Thread
import re
import csv
import io
import json
import openai
from flask import current_app, g, flash, redirect, url_for, request, send_file
from flask import Blueprint, render_template
from models import validation, User, db, Problem

template_dir = current_app.config['TEMPLATE_PATH']
bp = Blueprint('admin', __name__, template_folder=template_dir)


# - главная
@bp.route('/', methods=['GET'])
@validation.require_privileges(min_privileges=1)
def index():
    users_count = db.session.query(User).count()
    problems_count = db.session.query(Problem).count()

    return render_template('admin.html',
                           users_count=users_count,
                           problems_count=problems_count)


# -- задачи
@bp.route('/problems', methods=['GET'])
@validation.require_privileges(min_privileges=1)
def problems():
    pagination_size = current_app.config['PROBLEMS_PAGINATION_ADMIN']

    page = request.args.get('page', 0, type=int)
    sort = request.args.get('sort', 'id')

    if sort == 'id':
        problem_query = Problem.query.order_by(Problem.id)
    elif sort == 'name':
        problem_query = Problem.query.order_by(Problem.name)
    else:
        problem_query = Problem.query

    total = problem_query.count()

    if total == 0:
        return render_template(
            'admin-problems.html',
            problems=[],
            current_page=0,
            current_sort=sort,
            has_next=False,
            has_prev=False
        )

    last_page = (total - 1) // pagination_size

    if page > last_page:
        return redirect(url_for('admin.problems', page=last_page, sort=sort))

    if page < 0:
        page = 0

    problem_list = (
        problem_query
        .limit(pagination_size)
        .offset(page * pagination_size)
        .all()
    )

    has_next = page < last_page
    has_prev = page > 0

    return render_template(
        'admin-problems.html',
        problems=problem_list,
        current_page=page,
        current_sort=sort,
        has_next=has_next,
        has_prev=has_prev
    )


@bp.route('/problems/create', methods=['GET', 'POST'])
@validation.require_privileges(min_privileges=1)
def problems_create():
    if request.method == 'GET':
        return render_template('admin-problems-create.html')

    name = request.form.get('name', '').strip()
    content = request.form.get('content', '')
    answer = request.form.get('answer', '')

    if name == '':
        name = f'auto_generated_problem_{random.randint(1, 999999)}'
    if content == '':
        content = f'auto generated content of a problem {name}'
    if answer == '':
        answer = f'answer'

    if Problem.query.filter_by(name=name).first():
        flash("Такая задача уже есть", 'danger')
        return render_template('admin-problems-create.html')

    try:
        new_problem = Problem(
            name=name,
            content=content,
            answer=answer
        )

        db.session.add(new_problem)
        db.session.commit()

        flash("Задача успешно добавлена, хотите добавить еще одну?", 'success')
        return render_template('admin-problems-create.html')

    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при добавлении задачи: {str(e)}", 'danger')
        return render_template('admin-users-create.html')


@bp.route('/problems/<string:name>', methods=['GET', 'POST'])
@validation.require_privileges(min_privileges=1)
def problems_edit(name):
    try:
        problem = Problem.query.filter_by(name=name).first()
    except Exception as e:
        flash('Задача не найдена')
        return redirect(url_for('admin.problems'))

    if request.method == 'GET':
        return render_template('admin-problems-edit.html', problem=problem)

    name = request.form.get('name', '').strip()
    content = request.form.get('content', '')
    answer = request.form.get('answer', '')

    if Problem.query.filter_by(name=name).first() and problem.name != name:
        flash('Такая задача уже есть')
        return render_template('admin-problems-edit.html', problem=problem)

    if name != '':
        problem.name = name
    if content != '':
        problem.content = content
    if answer != '':
        problem.answer = answer

    db.session.commit()

    flash('Задача успешно изменена')

    return render_template('admin-problems-edit.html', problem=problem)


def generate_task(app, problem_id, api_key, base_url, prompt):
    with app.app_context():
        problem = Problem.query.get(problem_id)
        if not problem:
            return

        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        result = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": problem.content}
            ]
        ).choices[0].message.content

        content = re.search(r"<content>(.*?)</content>", result, re.DOTALL).group(1).strip()
        answer = re.search(r"<answer>(.*?)</answer>", result, re.DOTALL).group(1).strip()

        db.session.add(
            Problem(
                name=f"{problem.name} копия {random.randint(1, 999999999)}",
                content=content,
                answer=answer
            )
        )
        db.session.commit()
        db.session.remove()


@bp.route('/problems/<string:name>/generate', methods=['POST'])
@validation.require_privileges(min_privileges=1)
def problems_generate_new(name):
    problem = Problem.query.filter_by(name=name).first()
    if problem:
        app = current_app._get_current_object()

        Thread(
            target=generate_task,
            args=(
                app,
                problem.id,
                current_app.config['MODEL_API_KEY'],
                current_app.config['MODEL_BASE'],
                current_app.config['MODEL_NEW_PROBLEM_PROMPT']
            )
        ).start()

        flash('Задача генерируется...')

    return redirect(url_for('admin.problems_edit', name=name))


@bp.route('/problems/<string:name>/delete', methods=['POST'])
@validation.require_privileges(min_privileges=1)
def problems_delete(name):
    problem = Problem.query.filter_by(name=name).first_or_404()
    db.session.delete(problem)
    db.session.commit()
    flash('Задача удалена', 'success')
    return redirect(url_for('admin.problems'))


@bp.route('/problems/export', methods=['GET', 'POST'])
@validation.require_privileges(min_privileges=1)
def problems_export():
    if request.method == 'GET':
        return render_template('admin-problems-export.html')

    file = request.files.get('file')
    if not file or file.filename == '':
        flash('Файл не выбран')
        return redirect(request.url)

    try:
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"))
            for row in csv.DictReader(stream):
                if Problem.query.filter_by(name=row['name'].strip()).first():
                    continue
                db.session.add(Problem(
                    name=row['name'].strip(),
                    content=row['content'].strip(),
                    answer=row['answer'].strip()
                ))

        elif file.filename.endswith('.json'):
            for item in json.load(file.stream):
                if Problem.query.filter_by(name=item['name'].strip()).first():
                    continue
                db.session.add(Problem(
                    name=item['name'].strip(),
                    content=item['content'].strip(),
                    answer=item['answer'].strip()
                ))

        db.session.commit()
        flash('Задачи успешно загружены')

    except Exception:
        db.session.rollback()
        flash('Произошла ошибка при загрузке файла')

    return redirect(request.url)


@bp.route('/problems/export/csv')
@validation.require_privileges(min_privileges=1)
def problems_export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['name', 'content', 'answer'])

    writer.writerows([
        [p.name, p.content, p.answer]
        for p in Problem.query.all()
    ])

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='problems_export.csv'
    )


@bp.route('/problems/export/json')
@validation.require_privileges(min_privileges=1)
def problems_export_json():
    data = [
        {'name': p.name, 'content': p.content, 'answer': p.answer}
        for p in Problem.query.all()
    ]

    return send_file(
        io.BytesIO(json.dumps(data).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name='problems_export.json'
    )


# -- пользователи
@bp.route('/users', methods=['GET'])
@validation.require_privileges(min_privileges=1)
def users():
    pagination_size = current_app.config['USERS_PAGINATION_ADMIN']

    page = request.args.get('page', 0, type=int)
    sort = request.args.get('sort', 'id')

    if sort == 'id':
        user_query = User.query.order_by(User.id)
    elif sort == 'username':
        user_query = User.query.order_by(User.username)
    elif sort == 'elo':
        user_query = User.query.order_by(User.elo)
    else:
        user_query = User.query

    total = user_query.count()

    if total == 0:
        return render_template(
            'admin-users.html',
            users=[],
            current_page=0,
            current_sort=sort,
            has_next=False,
            has_prev=False
        )

    last_page = (total - 1) // pagination_size

    if page > last_page:
        return redirect(url_for('admin.users', page=last_page, sort=sort))

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
        'admin-users.html',
        users=user_list,
        current_page=page,
        current_sort=sort,
        has_next=has_next,
        has_prev=has_prev
    )


@bp.route('/users/<string:username>', methods=['GET', 'POST'])
@validation.require_privileges(min_privileges=1)
def users_edit(username):
    try:
        user = User.query.filter_by(username=username).first()
    except Exception as e:
        return redirect(url_for('admin.users'))

    if request.method == 'GET':
        return render_template('admin-users-edit.html', viewing_user=user)

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    privileges = request.form.get('privileges', '')
    elo = request.form.get('elo', '')

    if username != '':
        user.username = username
    if privileges != '':
        user.privileges = privileges
    if password != '':
        user.password_sha256 = validation.hash_password(password)
    if elo != '':
        user.elo = elo

    db.session.commit()

    flash('Пользователь успешно изменен')

    return render_template('admin-users-edit.html', viewing_user=user)


@bp.route('/users/create', methods=['GET', 'POST'])
@validation.require_privileges(min_privileges=1)
def users_create():
    if request.method == 'GET':
        return render_template('admin-users-create.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    privileges = request.form.get('privileges', '')
    elo = request.form.get('elo', '')

    if username == '':
        username = f'auto_generated_user_{random.randint(1, 999999)}'
    if privileges == '':
        privileges = 0
    if password == '':
        password = current_app.config['DEFAULT_ADMIN_PASSWORD']
    if elo == '':
        elo = current_app.config['DEFAULT_ELO']

    if User.query.filter_by(username=username).first():
        flash("Пользователь с таким именем уже существует", 'danger')
        return render_template('admin-users-create.html')

    try:
        new_user = User(
            username=username,
            password_sha256=validation.hash_password(password),
            privileges=privileges,
            elo=elo
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Пользователь добавлен, добавить еще одного?", 'success')
        return render_template('admin-users-create.html')

    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при добавлении пользователя: {str(e)}", 'danger')
        return render_template('admin-users-create.html')


@bp.route('/users/<string:username>/delete', methods=['POST'])
@validation.require_privileges(min_privileges=1)
def users_delete(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.privileges == 1:
        if User.query.filter_by(privileges=1).count() == 1:
            flash('Нельзя удалить последнего админа', 'danger')
            return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удалён', 'success')
    return redirect(url_for('admin.users'))
