from flask import Flask, render_template, request, redirect, session, flash
from flask_login import login_required, LoginManager
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
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



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@db/todo"
app.config['SECRET_KEY'] = "43ef12d7e7ab94a181473b6f46cb111a"
app.config['USE_SESSION_FOR_NEXT'] = True

login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)  

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

@login_manager.request_loader
def load_user_from_request(request):
    with app.app_context():
        user_id = session.get('user_id')
        if user_id:
            return User.query.get(int(user_id))
    return None

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    user_id = session.get('user_id')
    if request.method == 'POST':
        data = dict(request.form)
        data['user_id'] = user_id
        r = requests.post('http://task_management:5001/task_management/tasks', data=data)
        return redirect('/tasks')
    if request.method == 'GET':
        r = requests.get(f'http://task_management:5001/task_management/tasks?user_id={user_id}')
        all_tasks = r.json()
        for task in all_tasks:
            timestamp_str = task['created_at'] + "Z"
            created_datetime = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            task['created_at_formatted'] = created_datetime.strftime('%Y-%m-%d %H:%M')
            task['created_at'] = created_datetime.timestamp()

        user_id = session.get('user_id')
        time_tracking_endpoint = f'http://time_tracking_management:5002/time_tracking_management/users/{user_id}/time_spent'
        r = requests.get(time_tracking_endpoint)
        total_time_spent = r.json().get('time_spent')

        return render_template('tasks.html', tasks=all_tasks, total_time_spent=total_time_spent)


@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task_management_endpoint = f'http://task_management:5001/task_management/complete_task/{task_id}'
    r = requests.post(task_management_endpoint)

    if r.status_code == 200:
        task_time_taken = r.json().get('task_time_taken') 
        user_id = session.get('user_id') 
        time_tracking_endpoint = f'http://time_tracking_management:5002/time_tracking_management/tasks/{task_id}/time_taken'
        time_data = {'task_time_taken': int(task_time_taken), 'user_id': user_id}
        requests.post(time_tracking_endpoint, json=time_data)

    return redirect('/tasks')


@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    r = requests.delete(f'http://task_management:5001/task_management/tasks/{task_id}')
    return redirect('/tasks')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        r = requests.post('http://user_management:5003/user_management/login', data=request.form)
        response = r.json()
        if 'message' in response and response['message'] == 'Logged in':
            # Store user ID in the session
            session['user_id'] = response['user_id']
            return redirect('/tasks')
        flash(response['message'])
        return redirect('/login')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        r = requests.post('http://user_management:5003/user_management/register', data=request.form)
        response = r.json()
        if 'message' in response and response['message'] == 'User created':
            return redirect('/login')
        flash(response['message'])
        return redirect('/register')
    return render_template('register.html')

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    session.clear()  
    return redirect('/login')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
