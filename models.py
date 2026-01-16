"""СКРИПТ:Инициализация СУБД"""

# -- импорт модулей
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

# - связь пользователя с задачей
solved_problems = db.Table('solved_problems',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('problem_id', db.Integer, db.ForeignKey('problems.id'), primary_key=True),
    db.Column('solved_at', db.DateTime, default=datetime.now),
    db.Column('attempts_count', db.Integer, default=1),
)

# -- таблица пользователя
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    password_sha256 = db.Column(db.String(256), nullable=False)

    username = db.Column(db.String(32), nullable=False)
    privileges = db.Column(db.Integer, default=0)

    elo = db.Column(db.Integer, default=1000)

    solved_problems = db.relationship(
        'Problem',
        secondary=solved_problems,
        lazy='dynamic',
        backref=db.backref('solvers', lazy='dynamic')
    )

    matches_as_first = db.relationship(
        'Match',
        foreign_keys='Match.first_player_id',
        backref='first_player',
        lazy='dynamic'
    )
    matches_as_second = db.relationship(
        'Match',
        foreign_keys='Match.second_player_id',
        backref='second_player',
        lazy='dynamic'
    )

    @property
    def solved_count(self):
        return self.solved_problems.count()

    @property
    def won_matches(self):
        won_as_first = self.matches_as_first.filter(Match.result == 1).count()
        won_as_second = self.matches_as_second.filter(Match.result == 2).count()
        return won_as_first + won_as_second

    @property
    def total_matches(self):
        return self.matches_as_first.count() + self.matches_as_second.count()

    @property
    def win_rate(self):
        total = self.total_matches
        if total == 0:
            return 0
        return (self.won_matches / total) * 100

    @property
    def all_matches(self):
        matches_as_first = self.matches_as_first.all()
        matches_as_second = self.matches_as_second.all()
        all_matches = list(matches_as_first) + list(matches_as_second)
        all_matches.sort(key=lambda m: m.created_at if hasattr(m, 'created_at') else m.id, reverse=True)
        return all_matches

    def update_elo(self, match, K):
        if match.second_player_id == self.id:
            other_player_elo = match.first_player.elo
            match_result = match.result
            if match_result == 2:
                match_result = 1
            elif match_result == 1:
                match_result = 0
            elif match_result == 0:
                match_result = 0.5
        else:
            other_player_elo = match.second_player.elo
            match_result = match.result
            if match_result == 1:
                match_result = 1
            elif match_result == 2:
                match_result = 0
            elif match_result == 0:
                match_result = 0.5

        expected_score = 1 / (1 + 10 ** ((other_player_elo - self.elo) / 400))

        self.elo = round(self.elo + K * (match_result - expected_score))

        return self.elo

    def solve_problem(self, problem, attempts=1):
        if problem not in self.solved_problems:
            stmt = solved_problems.insert().values(
                user_id=self.id,
                problem_id=problem.id,
                attempts_count=attempts,
                solved_at=datetime.now()
            )
            db.session.execute(stmt)

# -- задачи
class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)

# -- матчи
class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)

    first_player_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    second_player_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)

    result = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    __table_args__ = (
        CheckConstraint('result IN (0, 1, 2)', name='check_match_result'),
        CheckConstraint('first_player_id != second_player_id', name='check_different_players'),
    )