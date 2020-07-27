# init.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


db = SQLAlchemy()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from models import User


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)
from main import main as main_blueprint
app.register_blueprint(main_blueprint)
from admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)


if __name__ == '__main__':
    app.run()
