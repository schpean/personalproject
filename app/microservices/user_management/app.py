from flask import Flask, Blueprint, request, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import os
from dotenv import load_dotenv

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


bp = Blueprint('user_management', __name__, url_prefix='/user_management')


@bp.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    try:
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return jsonify(message="User created"), 201
    except Exception as e:
        print(e)
        return jsonify(message="User already exists"), 409


@bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify(message="Invalid username or password"), 409

    # Store user ID in the session
    return jsonify(message="Logged in", user_id=user.id), 201


@bp.route('/')
def index():
    return jsonify(message="index warning page")




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@db/todo"
app.config['SECRET_KEY'] = "43ef12d7e7ab94a181473b6f46cb111a"
db.init_app(app)
app.register_blueprint(bp)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
