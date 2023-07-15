from flask import Flask
from dotenv import load_dotenv
import os
from flask import Blueprint, jsonify, request
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


bp = Blueprint('time_tracking_management', __name__, url_prefix='/time_tracking_management')


@bp.route('/tasks/<int:task_id>/time_taken', methods=['POST'])
def track_time_taken(task_id):
    task_time_taken = request.json.get('task_time_taken')
    user_id = request.json.get('user_id')

    user = User.query.get(user_id)
    if user:
        user.time_spent += int(task_time_taken)
        db.session.commit()

        return jsonify(message='Time taken recorded successfully')
    else:
        return jsonify(message='User not found'), 404


@bp.route('/users/<int:user_id>/time_spent', methods=['GET'])
def get_user_time_spent(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify(user_id=user.id, time_spent=user.time_spent)
    else:
        return jsonify(message='User not found'), 404



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@db/todo"
app.config['SECRET_KEY'] = "43ef12d7e7ab94a181473b6f46cb111a"
db.init_app(app)

app.register_blueprint(bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
