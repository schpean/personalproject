from flask import Flask
from dotenv import load_dotenv
import os
from datetime import datetime
from flask import Blueprint, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(160), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    time_spent = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(50), unique=True, nullable=False)
    done = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    created_at = db.Column(db.DateTime, nullable=False)
    time_left = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'task_name': self.task_name,
            'done': self.done,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_left': self.time_left,
        }


bp = Blueprint('task_management', __name__, url_prefix='/task_management')


@bp.route('/')
def index():
    return jsonify(message="Hello, this is the index page of the task_management microservice!")


@bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        data = request.form
        task_name = data.get('task_name')
        time_left = data.get('time_left')
        user_id = data.get('user_id')
        task = Task(task_name=task_name, done=False, created_at=datetime.now(), time_left=time_left, user_id=user_id)

        db.session.add(task)
        db.session.commit()
        return jsonify(message="Task created"), 201

    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if user_id is not None:
            user_tasks = Task.query.filter_by(user_id=user_id).all()
            user_tasks = [task.to_dict() for task in user_tasks]
            return jsonify(user_tasks), 200
        else:
            return jsonify(message="No user_id provided"), 400

@bp.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return redirect('/tasks')

    task.done = True
    db.session.commit()

   
    current_time = datetime.now()
    task_time_taken = (current_time - task.created_at).total_seconds()


    return jsonify(task_time_taken=task_time_taken)

@bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify(message="Task deleted"), 200
    else:
        return jsonify(message="Task not found"), 404


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@db/todo"
app.config['SECRET_KEY'] = "43ef12d7e7ab94a181473b6f46cb111a"

db.init_app(app)

app.register_blueprint(bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
