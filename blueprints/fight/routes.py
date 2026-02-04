import datetime
import random
import threading
from typing import Optional

from flask import current_app, g, session, request, Blueprint, render_template
from flask_socketio import emit, join_room, leave_room

from models import validation, socketio, Problem, db, User, Match

bp = Blueprint('fight', __name__, template_folder=current_app.config.get('TEMPLATE_PATH'))

connections = {}
waiting_queue = []
active_queue= []
active_matches = {}

_state_lock = threading.Lock()


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('/', methods=['GET'])
@validation.require_privileges(min_privileges=0)
def index():
    return render_template('fight.html', user=g.user)


@socketio.on('connect')
def handle_connect():
    user = get_current_user()
    if not user:
        return False

    sid = request.sid

    with _state_lock:
        connections[user.id] = sid

    join_room(f'user_{user.id}')

@socketio.on('disconnect')
def handle_disconnect():
    user = get_current_user()
    sid = request.sid

    if not user:
        return

    with _state_lock:
        connections.pop(user.id, None)

        if user.id in waiting_queue:
            waiting_queue.remove(user.id)

        if user.id in active_queue:
            active_queue.remove(user.id)

    try:
        leave_room(f'user_{user.id}')
    except Exception:
        pass


@socketio.on('queue_for_fight')
def queue_for_fight():
    user = get_current_user()
    if not user:
        return

    user_id = user.id

    with _state_lock:
        if user_id in waiting_queue or user_id in active_queue or user_id not in connections:
            return

        if waiting_queue:
            opponent_id = waiting_queue.pop(0)
            active_queue.extend([opponent_id, user_id])

            p1, p2 = opponent_id, user_id
        else:
            waiting_queue.append(user_id)
            emit('queue_status', {'status': 'waiting'})
            return

    start_match(p1, p2)


def start_match(p1_id: int, p2_id: int):
    problem = Problem.query.order_by(db.func.random()).first()

    room = f"match_{p1_id}_{p2_id}_{random.randint(1000,9999)}"

    with _state_lock:
        active_matches[room] = {
            'problem_id': problem.id,
            'players': [p1_id, p2_id],
            'answers': {},
            'started_at': datetime.datetime.utcnow()
        }

        sid1 = connections.get(p1_id)
        sid2 = connections.get(p2_id)

    if not sid1 or not sid2:
        with _state_lock:
            if p1_id in active_queue:
                active_queue.remove(p1_id)
            if p2_id in active_queue:
                active_queue.remove(p2_id)
            active_matches.pop(room, None)
        return

    try:
        socketio.server.enter_room(sid1, room)
        socketio.server.enter_room(sid2, room)
    except Exception:
        socketio.emit('match_found', {'room': room, 'problem': problem.content}, room=sid1)
        socketio.emit('match_found', {'room': room, 'problem': problem.content}, room=sid2)
    else:
        socketio.emit('match_found', {'room': room, 'problem': problem.content}, room=room)

@socketio.on('submit_answer')
def submit_answer(data):
    user = get_current_user()
    if not user:
        return

    room = data.get('room')
    answer = (data.get('answer') or '').strip().lower()
    user_id = user.id

    with _state_lock:
        match_data = active_matches.get(room)

    if not match_data:
        emit('wrong_answer')
        return

    problem = Problem.query.get(match_data['problem_id'])

    if user_id in match_data['answers']:
        return

    if answer == (problem.answer or '').strip().lower():
        with _state_lock:
            match_data['answers'][user_id] = datetime.datetime.utcnow()
        finish_match(room)
    else:
        emit('wrong_answer')


def finish_match(room: str):
    with _state_lock:
        match_data = active_matches.get(room)
        if not match_data:
            return

        p1, p2 = match_data['players']
        answers = match_data['answers'].copy()

    winner = None
    result = 0

    if len(answers) == 1:
        winner = next(iter(answers.keys()))
        result = 1 if winner == p1 else 2

    match = Match(
        first_player_id=p1,
        second_player_id=p2,
        problem_id=match_data['problem_id'],
        result=result,
        created_at=match_data['started_at'],
        ended_at=datetime.datetime.utcnow()
    )

    try:
        db.session.add(match)
        db.session.commit()

        user1 = match.first_player
        user2 = match.second_player
        if user1 and hasattr(user1, 'update_elo'):
            user1.update_elo(match, K=32)
        if user2 and hasattr(user2, 'update_elo'):
            user2.update_elo(match, K=32)
        db.session.commit()
    except Exception:
        db.session.rollback()

    payload = {'result': result, 'winner_id': winner}
    socketio.emit('match_result', payload, room=room)

    with _state_lock:
        active_matches.pop(room, None)
        try:
            if p1 in active_queue:
                active_queue.remove(p1)
            if p2 in active_queue:
                active_queue.remove(p2)
        except ValueError:
            pass